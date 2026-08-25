from datetime import datetime
import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.technical import TechnicalAnalyzer
from analysis.fundamental import FundamentalAnalyzer
from historical import batch_download

# Expanded liquid universe (Top 60 NSE Nifty 50 and F&O constituents)
LIQUID_UNIVERSE = [
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

class SignalGenerator:
    def __init__(self):
        pass

    def _get_batch_data(self, symbols):
        daily_data = batch_download(symbols, period='3mo', interval='1d')
        intraday_data = batch_download(symbols, period='5d', interval='15m')
        return daily_data, intraday_data

    def scan_intraday(self, symbols=None, daily_dfs=None, intra_dfs=None) -> list:
        from database import db
        symbols = symbols or LIQUID_UNIVERSE
        if daily_dfs is None or intra_dfs is None:
            daily_dfs, intra_dfs = self._get_batch_data(symbols)
        buy_signals = []
        sell_signals = []
        
        for sym in symbols:
            try:
                daily = daily_dfs.get(sym)
                intra = intra_dfs.get(sym)
                if daily is None or intra is None or daily.empty or intra.empty:
                    continue
                
                ta = TechnicalAnalyzer(sym, daily_data=daily, intraday_data=intra)
                rsi = ta.rsi()
                macd = ta.macd()
                hist = macd.get('histogram', 0)
                trend = ta.trend_strength()
                close = float(daily['Close'].iloc[-1])
                sr = ta.support_resistance()
                candle_patterns = ta.candlestick_patterns()
                chart_patterns = ta.chart_patterns()
                fib = ta.fibonacci_levels()
                t_time = intra.index[-1].strftime("%Y-%m-%d %H:%M") if hasattr(intra.index[-1], "strftime") else datetime.now().strftime("%Y-%m-%d %H:%M")
                
                c_name = candle_patterns[0].get('name') if candle_patterns else None
                c_type = candle_patterns[0].get('type') if candle_patterns else None
                cp_name = chart_patterns[0].get('name') if chart_patterns else None
                cp_type = chart_patterns[0].get('type') if chart_patterns else None
                
                info = db.get_instrument_info(sym)
                comp_name = info.get("name") if info else sym
                if not comp_name or comp_name == sym:
                    comp_name = sym

                # Multi-factor Intraday BUY Criteria
                is_buy = (50 <= rsi <= 72 and hist >= 0 and 'Bullish' in str(trend)) or \
                         (rsi < 48) or \
                         (c_type == 'BULLISH') or (cp_type == 'BULLISH') or \
                         fib.get('in_golden_pocket')
                         
                # Multi-factor Intraday SELL Criteria
                is_sell = (30 <= rsi <= 50 and hist < 0 and 'Bearish' in str(trend)) or \
                          (rsi > 72 and (c_type == 'BEARISH' or hist < 0 or 'Bearish' in str(trend))) or \
                          (c_type == 'BEARISH') or (cp_type == 'BEARISH')

                if is_buy:
                    dyn = ta.calculate_dynamic_targets(timeframe='intraday', direction='BUY')
                    pct_str = dyn['target_1_pct']
                    pattern_note = f" [{c_name or cp_name}]" if (c_name or cp_name) else ""
                    score = 65.0
                    if 50 <= rsi <= 68: score += 10
                    if hist > 0: score += 8
                    if 'Bullish' in str(trend): score += 10
                    if c_type == 'BULLISH' or cp_type == 'BULLISH': score += 12
                    if fib.get('in_golden_pocket'): score += 5
                    
                    reason = f'Bullish momentum breakout (RSI: {rsi:.1f}){pattern_note} above S1 (₹{sr.get("nearest_support")}). Target: {pct_str}'
                    if rsi < 48:
                        reason = f'Oversold demand bounce (RSI: {rsi:.1f}){pattern_note} near S1 (₹{sr.get("nearest_support")}). Target: {pct_str}'

                    buy_signals.append({
                        'symbol': sym,
                        'company_name': comp_name,
                        'signal_type': 'intraday',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': dyn['entry'],
                        'target': dyn['target_1'],
                        'stoploss': dyn['stoploss'],
                        'score': round(min(98.0, score), 1),
                        'risk_reward': dyn['risk_reward'],
                        'confidence': 'High' if score >= 80 else 'Medium',
                        'reason': reason,
                        'pattern': c_name or cp_name or "Bullish Momentum Expansion",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 1,
                        'trigger_candle_time': t_time
                    })
                elif is_sell:
                    dyn = ta.calculate_dynamic_targets(timeframe='intraday', direction='SELL')
                    pct_str = dyn['target_1_pct']
                    pattern_note = f" [{c_name or cp_name}]" if (c_name or cp_name) else ""
                    score = 65.0
                    if rsi > 70 or rsi < 45: score += 10
                    if hist < 0: score += 8
                    if 'Bearish' in str(trend): score += 10
                    if c_type == 'BEARISH' or cp_type == 'BEARISH': score += 12
                    
                    reason = f'Bearish momentum breakdown (RSI: {rsi:.1f}){pattern_note} below R1 (₹{sr.get("nearest_resistance")}). Target: {pct_str}'
                    if rsi > 70:
                        reason = f'Overbought resistance rejection (RSI: {rsi:.1f}){pattern_note} at R1 (₹{sr.get("nearest_resistance")}). Target: {pct_str}'

                    sell_signals.append({
                        'symbol': sym,
                        'company_name': comp_name,
                        'signal_type': 'intraday',
                        'type': 'SELL',
                        'direction': 'SELL',
                        'ltp': round(close, 2),
                        'entry': dyn['entry'],
                        'target': dyn['target_1'],
                        'stoploss': dyn['stoploss'],
                        'score': round(min(98.0, score), 1),
                        'risk_reward': dyn['risk_reward'],
                        'confidence': 'High' if score >= 80 else 'Medium',
                        'reason': reason,
                        'pattern': c_name or cp_name or "Resistance Rejection",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 1,
                        'trigger_candle_time': t_time
                    })
            except Exception:
                pass
                
        buy_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        sell_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        combined = []
        max_len = max(len(buy_signals), len(sell_signals))
        for i in range(max_len):
            if i < len(buy_signals):
                combined.append(buy_signals[i])
            if i < len(sell_signals):
                combined.append(sell_signals[i])
        return combined if combined else (buy_signals + sell_signals)

    def scan_shortterm(self, symbols=None, daily_dfs=None) -> list:
        from database import db
        symbols = symbols or LIQUID_UNIVERSE
        if daily_dfs is None:
            daily_dfs, _ = self._get_batch_data(symbols)
        buy_signals = []
        sell_signals = []
        
        for sym in symbols:
            try:
                daily = daily_dfs.get(sym)
                if daily is None or daily.empty:
                    continue
                
                ta = TechnicalAnalyzer(sym, daily_data=daily)
                macd = ta.macd()
                hist = macd.get('histogram', 0)
                trend = ta.trend_strength()
                rsi = ta.rsi()
                close = float(daily['Close'].iloc[-1])
                chart_patterns = ta.chart_patterns()
                candle_patterns = ta.candlestick_patterns()
                fib = ta.fibonacci_levels()
                sr = ta.support_resistance()
                t_time = daily.index[-1].strftime("%Y-%m-%d") if hasattr(daily.index[-1], "strftime") else datetime.now().strftime("%Y-%m-%d")
                
                cp_name = chart_patterns[0].get('name') if chart_patterns else (candle_patterns[0].get('name') if candle_patterns else None)
                cp_type = chart_patterns[0].get('type') if chart_patterns else (candle_patterns[0].get('type') if candle_patterns else None)
                
                info = db.get_instrument_info(sym)
                comp_name = info.get("name") if info else sym
                if not comp_name or comp_name == sym:
                    comp_name = sym

                is_bullish = (hist > 0 and macd['macd'] > macd['signal']) or (cp_type == 'BULLISH') or fib.get('in_golden_pocket') or ('Bullish' in str(trend) and rsi < 70)
                is_bearish = (hist < 0 and macd['macd'] < macd['signal']) or (cp_type == 'BEARISH') or ('Bearish' in str(trend))
                
                if is_bullish:
                    dyn = ta.calculate_dynamic_targets(timeframe='swing', direction='BUY')
                    pct_str = dyn['target_2_pct']
                    score = min(96.0, 60.0 + float(abs(hist) * 5) + (15 if cp_type == 'BULLISH' else 0) + (10 if fib.get('in_golden_pocket') else 0))
                    pattern_txt = f" [{cp_name}]" if cp_name else ""
                    buy_signals.append({
                        'symbol': sym,
                        'company_name': comp_name,
                        'signal_type': 'shortterm',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': dyn['entry'],
                        'target': dyn['target_2'],
                        'stoploss': dyn['stoploss'],
                        'score': round(score, 1),
                        'risk_reward': dyn['risk_reward'],
                        'confidence': 'High' if score >= 75 else 'Medium',
                        'reason': f'Bullish Swing Momentum & S/R Confluence{pattern_txt}. Target: {pct_str}',
                        'pattern': cp_name or "MACD Momentum Expansion",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 7,
                        'trigger_candle_time': t_time
                    })
                elif is_bearish:
                    dyn = ta.calculate_dynamic_targets(timeframe='swing', direction='SELL')
                    pct_str = dyn['target_2_pct']
                    score = min(92.0, 55.0 + float(abs(hist) * 5) + (15 if cp_type == 'BEARISH' else 0))
                    pattern_txt = f" [{cp_name}]" if cp_name else ""
                    sell_signals.append({
                        'symbol': sym,
                        'company_name': comp_name,
                        'signal_type': 'shortterm',
                        'type': 'SELL',
                        'direction': 'SELL',
                        'ltp': round(close, 2),
                        'entry': dyn['entry'],
                        'target': dyn['target_2'],
                        'stoploss': dyn['stoploss'],
                        'score': round(score, 1),
                        'risk_reward': dyn['risk_reward'],
                        'confidence': 'Medium',
                        'reason': f'Bearish Swing Breakdown & S/R Rejection{pattern_txt}. Target: {pct_str}',
                        'pattern': cp_name or "Bearish Distribution",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 7,
                        'trigger_candle_time': t_time
                    })
            except Exception:
                pass
                
        buy_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        sell_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        combined = []
        max_len = max(len(buy_signals), len(sell_signals))
        for i in range(max_len):
            if i < len(buy_signals):
                combined.append(buy_signals[i])
            if i < len(sell_signals):
                combined.append(sell_signals[i])
        return combined if combined else (buy_signals + sell_signals)

    def scan_longterm(self, symbols=None, daily_dfs=None) -> list:
        from database import db
        symbols = symbols or LIQUID_UNIVERSE
        if daily_dfs is None:
            daily_dfs, _ = self._get_batch_data(symbols)
        signals = []
        
        for sym in symbols:
            try:
                daily = daily_dfs.get(sym)
                if daily is None or daily.empty:
                    continue
                
                fa = FundamentalAnalyzer(sym)
                overview = fa.get_overview()
                rating = fa.overall_rating()
                close = float(daily['Close'].iloc[-1])
                score = rating['score']
                pe = overview.get('pe_ratio', 20.0)
                peg = overview.get('peg_ratio', 1.2)
                mcap_cat = overview.get('market_cap_category', 'Large Cap')
                t_time = daily.index[-1].strftime("%Y-%m-%d") if hasattr(daily.index[-1], "strftime") else datetime.now().strftime("%Y-%m-%d")
                
                info = db.get_instrument_info(sym)
                comp_name = info.get("name") if info else sym
                if not comp_name or comp_name == sym:
                    comp_name = sym

                # High quality compounder: ROE > 15%, safe debt, reasonable PEG
                if score >= 55:
                    entry = round(close, 2)
                    target = round(entry * 1.28, 2)
                    sl = round(entry * 0.88, 2)
                    signals.append({
                        'symbol': sym,
                        'company_name': comp_name,
                        'signal_type': 'longterm',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': entry,
                        'target': target,
                        'stoploss': sl,
                        'score': score,
                        'risk_reward': 2.33,
                        'confidence': 'High' if score >= 70 else 'Medium',
                        'reason': f"{mcap_cat} Compounder (P/E: {pe}, PEG: {peg}) with strong balance sheet ({rating['rating']}). Target: +28.0%",
                        'pattern': f"Institutional Value ({mcap_cat})",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 180,
                        'trigger_candle_time': t_time
                    })
            except Exception:
                pass
                
        signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        return signals

    def scan_futures(self, symbols=None, daily_dfs=None) -> list:
        from database import db
        symbols = symbols or ["NIFTY", "BANKNIFTY"] + LIQUID_UNIVERSE[:25]
        if daily_dfs is None:
            daily_dfs, _ = self._get_batch_data(symbols)
        buy_signals = []
        sell_signals = []
        
        for sym in symbols:
            try:
                daily = daily_dfs.get(sym)
                if daily is None or daily.empty:
                    continue
                
                ta = TechnicalAnalyzer(sym, daily_data=daily)
                trend = ta.trend_strength()
                close = float(daily['Close'].iloc[-1])
                t_time = daily.index[-1].strftime("%Y-%m-%d") if hasattr(daily.index[-1], "strftime") else datetime.now().strftime("%Y-%m-%d")
                
                info = db.get_instrument_info(sym)
                comp_name = info.get("name") if info else f"{sym} Futures"
                if not comp_name or comp_name == sym:
                    comp_name = f"{sym} Futures"

                if 'Bullish' in str(trend):
                    entry = round(close, 2)
                    target = round(entry * 1.032, 2)
                    sl = round(entry * 0.987, 2)
                    score = 90 if 'Strong' in str(trend) else 75
                    buy_signals.append({
                        'symbol': f"{sym}-FUT",
                        'company_name': f"{comp_name} Futures",
                        'signal_type': 'futures',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': entry,
                        'target': target,
                        'stoploss': sl,
                        'score': score,
                        'risk_reward': 2.46,
                        'confidence': 'High' if 'Strong' in str(trend) else 'Medium',
                        'reason': f"Long Build-up & momentum breakout: {trend}. Target: +3.2%",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 15,
                        'trigger_candle_time': t_time
                    })
                elif 'Bearish' in str(trend):
                    entry = round(close, 2)
                    target = round(entry * 0.968, 2)
                    sl = round(entry * 1.013, 2)
                    score = 90 if 'Strong' in str(trend) else 75
                    sell_signals.append({
                        'symbol': f"{sym}-FUT",
                        'company_name': f"{comp_name} Futures",
                        'signal_type': 'futures',
                        'type': 'SELL',
                        'direction': 'SELL',
                        'ltp': round(close, 2),
                        'entry': entry,
                        'target': target,
                        'stoploss': sl,
                        'score': score,
                        'risk_reward': 2.46,
                        'confidence': 'High' if 'Strong' in str(trend) else 'Medium',
                        'reason': f"Short Build-up & bearish breakdown: {trend}. Target: +3.2%",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 15,
                        'trigger_candle_time': t_time
                    })
            except Exception:
                pass
                
        buy_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        sell_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        combined = []
        max_len = max(len(buy_signals), len(sell_signals))
        for i in range(max_len):
            if i < len(buy_signals):
                combined.append(buy_signals[i])
            if i < len(sell_signals):
                combined.append(sell_signals[i])
        return combined if combined else (buy_signals + sell_signals)

    def scan_options(self, symbols=None, daily_dfs=None) -> list:
        from database import db
        symbols = symbols or ["NIFTY", "BANKNIFTY"] + LIQUID_UNIVERSE[:20]
        if daily_dfs is None:
            daily_dfs, _ = self._get_batch_data(symbols)
        buy_signals = []
        sell_signals = []
        
        for sym in symbols:
            try:
                daily = daily_dfs.get(sym)
                if daily is None or daily.empty:
                    continue
                
                ta = TechnicalAnalyzer(sym, daily_data=daily)
                trend = ta.trend_strength()
                close = float(daily['Close'].iloc[-1])
                strike_diff = 50 if sym in ["NIFTY", "BANKNIFTY"] else (10 if close < 500 else 20)
                atm_strike = round(close / strike_diff) * strike_diff
                otm_strike = atm_strike + strike_diff
                otm_put_strike = atm_strike - strike_diff
                t_time = daily.index[-1].strftime("%Y-%m-%d") if hasattr(daily.index[-1], "strftime") else datetime.now().strftime("%Y-%m-%d")
                
                info = db.get_instrument_info(sym)
                comp_name = info.get("name") if info else f"{sym} Options"
                if not comp_name or comp_name == sym:
                    comp_name = f"{sym} Options"

                if 'Bullish' in str(trend):
                    score = 90 if 'Strong' in str(trend) else 75
                    buy_signals.append({
                        'symbol': f"{sym} {atm_strike} CE",
                        'company_name': f"{comp_name} Call Spread",
                        'signal_type': 'options',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': f"Bull Call Spread ({atm_strike} CE / {otm_strike} CE)",
                        'target': "Max profit at expiry",
                        'stoploss': "Net debit premium paid",
                        'score': score,
                        'risk_reward': 1.8,
                        'confidence': 'Medium',
                        'reason': f"Bullish momentum continuation ({trend}). Spread caps risk.",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 10,
                        'trigger_candle_time': t_time
                    })
                elif 'Bearish' in str(trend):
                    score = 90 if 'Strong' in str(trend) else 75
                    sell_signals.append({
                        'symbol': f"{sym} {atm_strike} PE",
                        'company_name': f"{comp_name} Put Spread",
                        'signal_type': 'options',
                        'type': 'BUY',
                        'direction': 'BUY',
                        'ltp': round(close, 2),
                        'entry': f"Bear Put Spread ({atm_strike} PE / {otm_put_strike} PE)",
                        'target': "Max profit at expiry",
                        'stoploss': "Net debit premium paid",
                        'score': score,
                        'risk_reward': 1.8,
                        'confidence': 'Medium',
                        'reason': f"Bearish trend protection ({trend}). Protected put spread.",
                        'timestamp': datetime.now().isoformat(),
                        'expected_days': 10,
                        'trigger_candle_time': t_time
                    })
            except Exception:
                pass
                
        buy_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        sell_signals.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        combined = []
        max_len = max(len(buy_signals), len(sell_signals))
        for i in range(max_len):
            if i < len(buy_signals):
                combined.append(buy_signals[i])
            if i < len(sell_signals):
                combined.append(sell_signals[i])
        return combined if combined else (buy_signals + sell_signals)

    def scan_and_save_all(self):
        """Scan all liquid stocks and save the top signals directly to database."""
        from database import db
        import time
        
        # Clear out existing signals to ensure database only holds latest fresh signals
        try:
            db.conn.execute("DELETE FROM trade_signals")
            db.conn.commit()
        except Exception:
            pass

        # Batch download data ONCE for all categories
        daily_dfs, intra_dfs = self._get_batch_data(LIQUID_UNIVERSE)

        # 1. Intraday
        intraday_signals = self.scan_intraday(LIQUID_UNIVERSE, daily_dfs=daily_dfs, intra_dfs=intra_dfs)
        for s in intraday_signals[:15]:
            db.save_signal(s)

        # 2. Short Term
        shortterm_signals = self.scan_shortterm(LIQUID_UNIVERSE, daily_dfs=daily_dfs)
        for s in shortterm_signals[:15]:
            db.save_signal(s)

        # 3. Long Term
        longterm_signals = self.scan_longterm(LIQUID_UNIVERSE, daily_dfs=daily_dfs)
        for s in longterm_signals[:15]:
            db.save_signal(s)

        # 4. Futures
        fut_symbols = ["NIFTY", "BANKNIFTY"] + LIQUID_UNIVERSE[:20]
        futures_signals = self.scan_futures(fut_symbols, daily_dfs=daily_dfs)
        for s in futures_signals[:15]:
            db.save_signal(s)

        # 5. Options
        opt_symbols = ["NIFTY", "BANKNIFTY"] + LIQUID_UNIVERSE[:15]
        options_signals = self.scan_options(opt_symbols, daily_dfs=daily_dfs)
        for s in options_signals[:15]:
            db.save_signal(s)

        total = len(intraday_signals[:15]) + len(shortterm_signals[:15]) + len(longterm_signals[:15]) + len(futures_signals[:15]) + len(options_signals[:15])
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Live stock scan complete. Saved {total} high-profit trade signals.")

    def find_profit_setup(self, symbol: str) -> dict:
        """Manual Profit Setup Finder for any user-selected instrument."""
        import math
        from historical import resolve_symbol, get_historical
        from analysis.technical import TechnicalAnalyzer
        from analysis.fundamental import FundamentalAnalyzer
        from database import db

        sym = resolve_symbol(symbol)
        info = db.get_instrument_info(sym) or db.get_instrument_info(symbol)
        comp_name = info.get("name") if info else sym
        if not comp_name or comp_name == sym:
            comp_name = sym
        disp_name = f"{sym} - {comp_name}" if comp_name != sym else sym
        exch = info.get("exchange", "NSE") if info else "NSE"

        df = get_historical(sym, period='3mo', interval='1d')
        if df is None or df.empty:
            return {"symbol": sym, "company_name": comp_name, "display_name": disp_name, "error": "Unable to fetch instrument data"}

        close = float(df['Close'].iloc[-1])
        ta = TechnicalAnalyzer(sym, daily_data=df)
        fa = FundamentalAnalyzer(sym)
        fund_overview = fa.get_overview()

        rsi_val = ta.rsi()
        rsi = float(rsi_val) if (rsi_val is not None and not math.isnan(rsi_val) and not math.isinf(rsi_val)) else 50.0
        
        macd = ta.macd()
        hist_val = macd.get('histogram', 0)
        hist = float(hist_val) if (hist_val is not None and not math.isnan(hist_val) and not math.isinf(hist_val)) else 0.0
        
        trend = ta.trend_strength() or "Neutral"
        sr = ta.support_resistance()
        chart_patterns = ta.chart_patterns()
        candle_patterns = ta.candlestick_patterns()
        fib = ta.fibonacci_levels()

        # Check for pattern triggers
        cp_name = chart_patterns[0].get('name') if chart_patterns else (candle_patterns[0].get('name') if candle_patterns else None)
        cp_type = chart_patterns[0].get('type') if chart_patterns else (candle_patterns[0].get('type') if candle_patterns else None)

        is_bullish = ('Bullish' in str(trend)) or (hist >= 0) or (rsi < 50) or (cp_type == 'BULLISH') or fib.get('in_golden_pocket')
        direction = "BUY" if is_bullish else "SELL"

        # Calculate dynamic targets from ATR, Pattern Depth, Fib Extension, and S/R
        dyn = ta.calculate_dynamic_targets(timeframe="swing", direction=direction)
        t1 = dyn["target_1"]
        t2 = dyn["target_2"]
        sl = dyn["stoploss"]
        rr = dyn["risk_reward"]
        pct1_str = dyn["target_1_pct"]
        pct2_str = dyn["target_2_pct"]

        pattern_note = f" [{cp_name}]" if cp_name else ""
        fib_note = " (in Fib Golden Pocket)" if fib.get('in_golden_pocket') else ""
        pe = fund_overview.get('pe_ratio', 20.0)
        mcap_cat = fund_overview.get('market_cap_category', 'Large Cap')

        return {
            "symbol": sym,
            "company_name": comp_name,
            "display_name": disp_name,
            "exchange": exch,
            "ltp": round(close, 2),
            "direction": direction,
            "entry": round(close, 2),
            "target_1": t1,
            "target_2": t2,
            "stoploss": sl,
            "profit_pct": f"{pct1_str} (T1) / {pct2_str} (T2)",
            "risk_reward": rr,
            "trend": str(trend),
            "rsi": round(rsi, 1),
            "detected_pattern": cp_name or "Support/Resistance Channel",
            "nearest_support": sr.get('nearest_support'),
            "nearest_resistance": sr.get('nearest_resistance'),
            "fib_golden_pocket": f"₹{fib.get('fib_618', 0)} - ₹{fib.get('fib_500', 0)}" if fib else "N/A",
            "pe_ratio": pe,
            "market_cap_category": mcap_cat,
            "holding_period": "3-10 Days",
            "rationale": f"{disp_name} ({mcap_cat}, P/E: {pe}) multi-factor setup with dynamic {pct1_str} Target 1 & {pct2_str} Target 2{pattern_note}{fib_note}."
        }
