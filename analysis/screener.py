import sys
import os
import pandas as pd
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.technical import TechnicalAnalyzer
from historical import batch_download, get_historical

SCREENER_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "ITC", "SBIN",
    "LT", "HINDUNILVR", "AXISBANK", "KOTAKBANK", "M&M", "TATASTEEL", "ADANIENT",
    "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NTPC", "POWERGRID",
    "WIPRO", "JSWSTEEL", "ADANIPORTS", "ONGC", "COALINDIA", "HINDALCO", "GRASIM",
    "NESTLEIND", "TECHM", "BAJAJ-AUTO", "CIPLA", "TRENT", "BEL", "HAL", "VBL",
    "ZOMATO", "SIEMENS", "DLF", "CHOLAFIN", "INDUSINDBK", "TATAMOTORS", "SBILIFE",
    "HDFCLIFE", "BPCL", "EICHERMOT", "APOLLOHOSP", "DRREDDY", "DIVISLAB", "HEROMOTOCO",
    "TVSMOTOR", "ASHOKLEY", "POLYCAB", "CANBK", "PNB", "BANKBARODA", "FEDERALBNK",
    "IDFCFIRSTB", "JIOFIN"
]

import time

_CACHE_DFS = {}
_CACHE_TIMESTAMP = 0
_CACHE_TTL = 180  # 3 minutes cache for instant millisecond responses
_CACHE_RESULTS = {}

class Screener:
    def __init__(self, universe=None):
        self.universe = universe or SCREENER_UNIVERSE

    def _get_universe_dfs(self) -> dict:
        global _CACHE_DFS, _CACHE_TIMESTAMP
        now = time.time()
        if _CACHE_DFS and (now - _CACHE_TIMESTAMP < _CACHE_TTL):
            return _CACHE_DFS
            
        try:
            dfs = batch_download(self.universe, period='6mo', interval='1d')
            if dfs:
                _CACHE_DFS = dfs
                _CACHE_TIMESTAMP = now
                return _CACHE_DFS
        except Exception:
            pass
        return _CACHE_DFS or {}

    def _format_vol(self, vol: float) -> str:
        if vol >= 10_000_000:
            return f"{vol / 10_000_000:.2f} Cr"
        elif vol >= 100_000:
            return f"{vol / 100_000:.2f} L"
        elif vol >= 1_000:
            return f"{vol / 1_000:.1f} K"
        return str(int(vol))

    def top_gainers(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 2:
                    continue
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                vol = float(df['Volume'].iloc[-1])
                target = round(close * (1 + max(0.03, abs(chg_pct) * 0.015)), 2)
                profit_pct = round(((target - close) / close) * 100, 1)
                
                results.append({
                    'symbol': sym,
                    'ltp': round(close, 2),
                    'change_pct': chg_pct,
                    'volume': self._format_vol(vol),
                    'target_price': target,
                    'profit_pct': f"+{profit_pct}%",
                    'high': round(float(df['High'].iloc[-1]), 2),
                    'low': round(float(df['Low'].iloc[-1]), 2)
                })
            except Exception:
                continue
                
        results.sort(key=lambda x: x['change_pct'], reverse=True)
        return results[:n]

    def top_losers(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 2:
                    continue
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                vol = float(df['Volume'].iloc[-1])
                target = round(close * 0.95, 2)
                profit_pct = round(((close - target) / close) * 100, 1)
                
                results.append({
                    'symbol': sym,
                    'ltp': round(close, 2),
                    'change_pct': chg_pct,
                    'volume': self._format_vol(vol),
                    'target_price': target,
                    'profit_pct': f"+{profit_pct}% (Short)",
                    'high': round(float(df['High'].iloc[-1]), 2),
                    'low': round(float(df['Low'].iloc[-1]), 2)
                })
            except Exception:
                continue
                
        results.sort(key=lambda x: x['change_pct'])
        return results[:n]

    def volume_breakout(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 20:
                    continue
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                cur_vol = float(df['Volume'].iloc[-1])
                avg_vol = float(df['Volume'].iloc[-20:].mean())
                
                vol_ratio = round(cur_vol / max(avg_vol, 1), 2)
                if vol_ratio >= 1.2 or chg_pct > 1.5:
                    target = round(close * 1.06, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': f"{self._format_vol(cur_vol)} ({vol_ratio}x avg)",
                        'vol_ratio': vol_ratio,
                        'target_price': target,
                        'profit_pct': "+6.0%",
                        'signal': 'Bullish Breakout' if chg_pct >= 0 else 'High Volume Sell'
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: x.get('vol_ratio', 0), reverse=True)
        return results[:n]

    def fifty_two_week_high(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 50:
                    continue
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                high_52w = float(df['High'].max())
                diff_pct = round(((high_52w - close) / high_52w) * 100, 2)
                
                if diff_pct <= 5.0:  # Within 5% of 52W High
                    chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                    target = round(high_52w * 1.05, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': self._format_vol(float(df['Volume'].iloc[-1])),
                        'target_price': target,
                        'profit_pct': f"+{round(((target - close)/close)*100, 1)}%",
                        'high_52w': round(high_52w, 2),
                        'diff_from_high': f"{diff_pct}% away"
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: float(x.get('diff_from_high', '100').replace('% away', '')))
        return results[:n]

    def fifty_two_week_low(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 50:
                    continue
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                low_52w = float(df['Low'].min())
                diff_pct = round(((close - low_52w) / max(low_52w, 1)) * 100, 2)
                
                if diff_pct <= 8.0:  # Within 8% of 52W Low (Rebound zone)
                    chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                    target = round(close * 1.10, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': self._format_vol(float(df['Volume'].iloc[-1])),
                        'target_price': target,
                        'profit_pct': "+10.0%",
                        'low_52w': round(low_52w, 2),
                        'diff_from_low': f"{diff_pct}% above low"
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: float(x.get('diff_from_low', '100').replace('% above low', '')))
        return results[:n]

    def rsi_oversold(self, threshold=35, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 15:
                    continue
                ta = TechnicalAnalyzer(sym, daily_data=df)
                rsi_val = round(ta.rsi(), 1)
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                
                if rsi_val <= threshold:
                    target = round(close * 1.055, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': self._format_vol(float(df['Volume'].iloc[-1])),
                        'rsi': rsi_val,
                        'target_price': target,
                        'profit_pct': "+5.5%",
                        'signal': f"Oversold RSI ({rsi_val}) — Value Buy"
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: x['rsi'])
        return results[:n]

    def rsi_overbought(self, threshold=65, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 15:
                    continue
                ta = TechnicalAnalyzer(sym, daily_data=df)
                rsi_val = round(ta.rsi(), 1)
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                
                if rsi_val >= threshold:
                    target = round(close * 0.96, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': self._format_vol(float(df['Volume'].iloc[-1])),
                        'rsi': rsi_val,
                        'target_price': target,
                        'profit_pct': "+4.0% (Pullback)",
                        'signal': f"Overbought RSI ({rsi_val})"
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: x['rsi'], reverse=True)
        return results[:n]

    def macd_crossover(self, n=20) -> list:
        dfs = self._get_universe_dfs()
        results = []
        for sym, df in dfs.items():
            try:
                if df is None or len(df) < 30:
                    continue
                ta = TechnicalAnalyzer(sym, daily_data=df)
                macd_data = ta.macd()
                hist = macd_data.get('histogram', 0)
                macd_line = macd_data.get('macd', 0)
                sig_line = macd_data.get('signal', 0)
                
                close = float(df['Close'].iloc[-1])
                prev_close = float(df['Close'].iloc[-2])
                chg_pct = round(((close - prev_close) / prev_close) * 100, 2)
                
                if hist > 0 and macd_line > sig_line:
                    target = round(close * 1.07, 2)
                    results.append({
                        'symbol': sym,
                        'ltp': round(close, 2),
                        'change_pct': chg_pct,
                        'volume': self._format_vol(float(df['Volume'].iloc[-1])),
                        'macd_hist': round(hist, 2),
                        'target_price': target,
                        'profit_pct': "+7.0%",
                        'signal': 'Bullish MACD Expansion'
                    })
            except Exception:
                continue
                
        results.sort(key=lambda x: x.get('macd_hist', 0), reverse=True)
        return results[:n]

    def custom_scan(self, filters: dict) -> list:
        return self.top_gainers(20)

