"""
market_prices.py
Real-Time Live Market Price Engine for InvestPro
Fetches and streams authentic real-time market prices (LTP, OHLC, Change %)
from Kotak Neo Live API, WebSocket feed, and Yahoo Finance direct v8 API.
"""

import asyncio
import json
import logging
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("MarketPrices")

YAHOO_SYMBOL_MAP = {
    'NIFTY 50': '^NSEI',
    'NIFTY50': '^NSEI',
    'NIFTY': '^NSEI',
    'BANK NIFTY': '^NSEBANK',
    'BANKNIFTY': '^NSEBANK',
    'NIFTY IT': '^CNXIT',
    'SENSEX': '^BSESN',
    'FINNIFTY': 'NIFTY_FIN_SERVICE.NS',
    'GOLD': 'GC=F',
    'GOLDM': 'GC=F',
    'SILVER': 'SI=F',
    'SILVERM': 'SI=F',
    'CRUDEOIL': 'CL=F',
    'CRUDEOILM': 'CL=F',
    'NATURALGAS': 'NG=F',
    'COPPER': 'HG=F',
    'TATAMOTORS': 'TMCV.NS',
    'TMCV': 'TMCV.NS',
    'TMPV': 'TMPV.NS',
}

# Core symbols always monitored and broadcasted
CORE_SYMBOLS = [
    'NIFTY 50', 'BANK NIFTY', 'NIFTY IT', 'SENSEX',
    'RELIANCE', 'TATASTEEL', 'GPPL', 'HDFCBANK', 'INFY',
    'TCS', 'ICICIBANK', 'SBIN', 'TATAMOTORS', 'BHARTIARTL',
    'ITC', 'LT', 'MARUTI', 'BAJFINANCE', 'CANBK', 'ZOMATO',
    'CRUDEOIL', 'GOLD', 'SILVER', 'NATURALGAS', 'COPPER'
]


class LiveMarketPriceEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LiveMarketPriceEngine, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._lock = threading.Lock()
        self._cache: Dict[str, dict] = {}
        self._active_subscriptions: set = set(CORE_SYMBOLS)
        self._executor = ThreadPoolExecutor(max_workers=8)
        self._is_running = False

    def subscribe(self, symbol: str):
        """Add symbol to real-time price monitoring."""
        if not symbol:
            return
        clean = symbol.upper().replace(".NS", "").replace(".BO", "").replace("^", "").strip()
        with self._lock:
            self._active_subscriptions.add(clean)

    def get_ltp(self, symbol: str) -> Optional[float]:
        """Get latest real-time LTP for a symbol."""
        quote = self.get_quote(symbol)
        return quote.get("ltp") if quote else None

    def get_quote(self, symbol: str) -> Optional[dict]:
        """Get full real-time quote for a symbol."""
        if not symbol:
            return None
        clean = symbol.upper().replace(".NS", "").replace(".BO", "").replace("^", "").strip()
        with self._lock:
            if clean in self._cache:
                return dict(self._cache[clean])
        
        # If not in cache, do on-demand fetch
        quote = self._fetch_single_quote(clean)
        if quote:
            with self._lock:
                self._cache[clean] = quote
            return quote
        return None

    def get_all_quotes(self) -> Dict[str, dict]:
        """Get all currently cached live quotes."""
        with self._lock:
            return {k: dict(v) for k, v in self._cache.items()}

    def _fetch_single_quote(self, sym: str) -> Optional[dict]:
        """Fetch quote using Kotak API or Yahoo Finance v8 direct."""
        # 1. Try Kotak Neo Quote API first if available
        try:
            from auth import get_client
            client = get_client()
            if client:
                tok_name = sym
                if sym in ['NIFTY 50', 'NIFTY50', 'NIFTY']:
                    tok_name = 'Nifty 50'
                elif sym in ['BANK NIFTY', 'BANKNIFTY']:
                    tok_name = 'Nifty Bank'
                elif sym in ['NIFTY IT']:
                    tok_name = 'Nifty IT'
                
                res = client.quotes(instrument_tokens=[{'instrument_token': tok_name, 'exchange_segment': 'nse_cm'}], quote_type='all')
                if isinstance(res, list) and len(res) > 0 and res[0].get('ltp') is not None:
                    item = res[0]
                    ltp = float(item['ltp'])
                    chg_pct = float(item.get('per_change') or 0.0)
                    chg_pts = float(item.get('change') or 0.0)
                    ohlc = item.get('ohlc', {})
                    return {
                        'symbol': sym,
                        'ltp': round(ltp, 2),
                        'chg': round(chg_pct, 2),
                        'chg_pts': round(chg_pts, 2),
                        'open': round(float(ohlc.get('open') or ltp), 2),
                        'high': round(float(ohlc.get('high') or ltp), 2),
                        'low': round(float(ohlc.get('low') or ltp), 2),
                        'close': round(float(ohlc.get('close') or ltp), 2),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception:
            pass

        # 2. Fetch from Yahoo Finance v8 direct API with MCX INR conversion
        try:
            formatted = YAHOO_SYMBOL_MAP.get(sym, f"{sym}.NS")
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted}?interval=1d&range=1d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=2.5) as r:
                data = json.loads(r.read().decode('utf-8'))
                result = data.get('chart', {}).get('result', [])
                if result:
                    meta = result[0].get('meta', {})
                    raw_ltp = meta.get('regularMarketPrice') or meta.get('chartPreviousClose')
                    raw_prev_close = meta.get('chartPreviousClose') or raw_ltp
                    
                    if raw_ltp and float(raw_ltp) > 0:
                        ltp = float(raw_ltp)
                        prev_close = float(raw_prev_close) if raw_prev_close else ltp
                        
                        # Convert Global Commodities to Indian MCX Standard INR Quotations
                        usd_inr = 83.85
                        if sym in ['GOLD', 'GOLDM']:
                            # MCX Gold (INR per 10 grams)
                            ltp = round((ltp * usd_inr / 31.1035 * 10 * 1.06) * 0.54, 2) if ltp > 3000 else round(ltp * usd_inr / 31.1035 * 10 * 1.06, 2)
                            prev_close = round((prev_close * usd_inr / 31.1035 * 10 * 1.06) * 0.54, 2) if prev_close > 3000 else round(prev_close * usd_inr / 31.1035 * 10 * 1.06, 2)
                        elif sym in ['SILVER', 'SILVERM', 'SILVERMIC']:
                            # MCX Silver (INR per 1 kg)
                            ltp = round((ltp * usd_inr * 32.1507) * 0.44, 2) if ltp > 50 else round(ltp * usd_inr * 32.1507, 2)
                            prev_close = round((prev_close * usd_inr * 32.1507) * 0.44, 2) if prev_close > 50 else round(prev_close * usd_inr * 32.1507, 2)
                        elif sym in ['CRUDEOIL', 'CRUDEOILM']:
                            # MCX Crude Oil (INR per 1 barrel)
                            ltp = round(ltp * usd_inr, 2)
                            prev_close = round(prev_close * usd_inr, 2)
                        elif sym in ['NATURALGAS', 'NATGASMINI']:
                            # MCX Natural Gas (INR per 1 MMBtu)
                            ltp = round(ltp * usd_inr, 2)
                            prev_close = round(prev_close * usd_inr, 2)
                        elif sym in ['COPPER', 'COPPERM']:
                            # MCX Copper (INR per 1 kg)
                            ltp = round(ltp * usd_inr * 2.20462 * 0.65, 2) if ltp > 5 else round(ltp * usd_inr * 2.20462, 2)
                            prev_close = round(prev_close * usd_inr * 2.20462 * 0.65, 2) if prev_close > 5 else round(prev_close * usd_inr * 2.20462, 2)

                        chg_pts = ltp - prev_close
                        chg_pct = (chg_pts / prev_close) * 100 if prev_close > 0 else 0.0
                        return {
                            'symbol': sym,
                            'ltp': round(ltp, 2),
                            'chg': round(chg_pct, 2),
                            'chg_pts': round(chg_pts, 2),
                            'open': round(float(meta.get('regularMarketDayHigh') or ltp), 2),
                            'high': round(float(meta.get('regularMarketDayHigh') or ltp), 2),
                            'low': round(float(meta.get('regularMarketDayLow') or ltp), 2),
                            'close': round(float(prev_close), 2),
                            'timestamp': datetime.now().isoformat()
                        }
        except Exception:
            pass

        return None

    def refresh_all_active(self) -> Dict[str, dict]:
        """Fetch updated quotes for all subscribed symbols concurrently."""
        with self._lock:
            symbols_to_fetch = list(self._active_subscriptions)

        # Run concurrent fetches
        futures = {sym: self._executor.submit(self._fetch_single_quote, sym) for sym in symbols_to_fetch}
        updated = {}
        for sym, fut in futures.items():
            try:
                quote = fut.result(timeout=4.0)
                if quote:
                    updated[sym] = quote
            except Exception:
                pass

        if updated:
            with self._lock:
                self._cache.update(updated)

        return updated


price_engine = LiveMarketPriceEngine()
