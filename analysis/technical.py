import pandas as pd
import numpy as np
import ta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from historical import get_historical, get_intraday

class TechnicalAnalyzer:
    def __init__(self, symbol: str, daily_data: pd.DataFrame = None, intraday_data: pd.DataFrame = None):
        self.symbol = symbol
        self.daily_data = daily_data if daily_data is not None else get_historical(symbol)
        self.intraday_data = intraday_data if intraday_data is not None else get_intraday(symbol)

    def _ensure_data(self):
        if self.daily_data is None or self.daily_data.empty:
            raise ValueError(f"No historical data available for {self.symbol}")

    def close_price(self) -> float:
        self._ensure_data()
        return float(self.daily_data['Close'].iloc[-1])

    def compute_all(self) -> dict:
        self._ensure_data()
        return {
            'sma': self.sma(),
            'ema': self.ema(),
            'rsi': self.rsi(),
            'macd': self.macd(),
            'bollinger_bands': self.bollinger_bands(),
            'stochastic': self.stochastic(),
            'atr': self.atr(),
            'adx': self.adx(),
            'vwap': self.vwap(),
            'obv': self.obv(),
            'cci': self.cci(),
            'williams_r': self.williams_r(),
            'support_resistance': self.support_resistance(),
            'candlestick_patterns': self.candlestick_patterns(),
            'chart_patterns': self.chart_patterns(),
            'fibonacci_levels': self.fibonacci_levels(),
            'pivot_points': self.pivot_points()
        }

    def sma(self, periods=[20, 50, 200]) -> dict:
        self._ensure_data()
        res = {}
        for p in periods:
            if len(self.daily_data) >= p:
                indicator = ta.trend.SMAIndicator(close=self.daily_data['Close'], window=p)
                res[f'sma_{p}'] = float(indicator.sma_indicator().iloc[-1])
            else:
                res[f'sma_{p}'] = None
        return res

    def ema(self, periods=[9, 21, 50]) -> dict:
        self._ensure_data()
        res = {}
        for p in periods:
            if len(self.daily_data) >= p:
                indicator = ta.trend.EMAIndicator(close=self.daily_data['Close'], window=p)
                res[f'ema_{p}'] = float(indicator.ema_indicator().iloc[-1])
            else:
                res[f'ema_{p}'] = None
        return res

    def rsi(self, period=14) -> float:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.momentum.RSIIndicator(close=self.daily_data['Close'], window=period)
            return float(indicator.rsi().iloc[-1])
        return 50.0

    def macd(self) -> dict:
        self._ensure_data()
        if len(self.daily_data) >= 26:
            indicator = ta.trend.MACD(close=self.daily_data['Close'])
            return {
                'macd': float(indicator.macd().iloc[-1]),
                'signal': float(indicator.macd_signal().iloc[-1]),
                'histogram': float(indicator.macd_diff().iloc[-1])
            }
        return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}

    def bollinger_bands(self, period=20) -> dict:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.volatility.BollingerBands(close=self.daily_data['Close'], window=period)
            return {
                'upper': float(indicator.bollinger_hband().iloc[-1]),
                'middle': float(indicator.bollinger_mavg().iloc[-1]),
                'lower': float(indicator.bollinger_lband().iloc[-1]),
                'bandwidth': float(indicator.bollinger_wband().iloc[-1])
            }
        return {}

    def stochastic(self, k=14, d=3) -> dict:
        self._ensure_data()
        if len(self.daily_data) >= k:
            indicator = ta.momentum.StochasticOscillator(
                high=self.daily_data['High'],
                low=self.daily_data['Low'],
                close=self.daily_data['Close'],
                window=k,
                smooth_window=d
            )
            return {
                'k': float(indicator.stoch().iloc[-1]),
                'd': float(indicator.stoch_signal().iloc[-1])
            }
        return {}

    def atr(self, period=14) -> float:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.volatility.AverageTrueRange(
                high=self.daily_data['High'],
                low=self.daily_data['Low'],
                close=self.daily_data['Close'],
                window=period
            )
            return float(indicator.average_true_range().iloc[-1])
        return 0.0

    def adx(self, period=14) -> float:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.trend.ADXIndicator(
                high=self.daily_data['High'],
                low=self.daily_data['Low'],
                close=self.daily_data['Close'],
                window=period
            )
            return float(indicator.adx().iloc[-1])
        return 0.0

    def supertrend(self, period=10, multiplier=3) -> dict:
        self._ensure_data()
        # simplified approximation since ta doesn't have native Supertrend
        atr_val = self.atr(period)
        if not atr_val or len(self.daily_data) < period:
            return {'value': 0.0, 'direction': 'neutral'}
        hl2 = (self.daily_data['High'].iloc[-1] + self.daily_data['Low'].iloc[-1]) / 2
        close = self.daily_data['Close'].iloc[-1]
        basic_upper = hl2 + (multiplier * atr_val)
        basic_lower = hl2 - (multiplier * atr_val)
        # simplistic assumption
        return {
            'value': basic_lower if close >= basic_lower else basic_upper,
            'direction': 'bullish' if close >= basic_lower else 'bearish'
        }

    def vwap(self) -> float:
        if self.intraday_data is None or self.intraday_data.empty:
            return 0.0
        df = self.intraday_data
        v = df['Volume'].values
        tp = (df['Low'] + df['Close'] + df['High']).div(3).values
        if v.sum() == 0:
            return 0.0
        return float((v * tp).sum() / v.sum())

    def obv(self) -> float:
        self._ensure_data()
        indicator = ta.volume.OnBalanceVolumeIndicator(
            close=self.daily_data['Close'],
            volume=self.daily_data['Volume']
        )
        return float(indicator.on_balance_volume().iloc[-1])

    def cci(self, period=20) -> float:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.trend.CCIIndicator(
                high=self.daily_data['High'],
                low=self.daily_data['Low'],
                close=self.daily_data['Close'],
                window=period
            )
            return float(indicator.cci().iloc[-1])
        return 0.0

    def williams_r(self, period=14) -> float:
        self._ensure_data()
        if len(self.daily_data) >= period:
            indicator = ta.momentum.WilliamsRIndicator(
                high=self.daily_data['High'],
                low=self.daily_data['Low'],
                close=self.daily_data['Close'],
                lbp=period
            )
            return float(indicator.williams_r().iloc[-1])
        return 0.0

    def fibonacci_levels(self) -> dict:
        """Compute institutional Fibonacci retracement and extension levels."""
        self._ensure_data()
        df = self.daily_data
        if len(df) < 20:
            return {}
        
        # Look back over recent swing window (up to 60 bars)
        window = df.tail(min(60, len(df)))
        high_p = float(window['High'].max())
        low_p = float(window['Low'].min())
        diff = high_p - low_p
        
        if diff <= 0:
            return {}
            
        current = float(df['Close'].iloc[-1])
        
        fib = {
            'swing_high': round(high_p, 2),
            'swing_low': round(low_p, 2),
            'fib_236': round(high_p - 0.236 * diff, 2),
            'fib_382': round(high_p - 0.382 * diff, 2),
            'fib_500': round(high_p - 0.500 * diff, 2),
            'fib_618': round(high_p - 0.618 * diff, 2),  # Golden Pocket
            'fib_786': round(high_p - 0.786 * diff, 2),
            'fib_ext_1618': round(high_p + 0.618 * diff, 2),  # Extension Target
        }
        
        # Determine if current price is in the Golden Pocket (between 50% and 61.8%)
        in_golden_pocket = (current >= fib['fib_618'] * 0.99) and (current <= fib['fib_500'] * 1.01)
        fib['in_golden_pocket'] = in_golden_pocket
        return fib

    def support_resistance(self) -> dict:
        """Calculate dynamic multi-pivot support and resistance zones."""
        self._ensure_data()
        df = self.daily_data
        supports = []
        resistances = []
        
        for i in range(2, df.shape[0] - 2):
            # Local swing low
            if (df['Low'].iloc[i] <= df['Low'].iloc[i-1] and df['Low'].iloc[i] <= df['Low'].iloc[i+1] and
                df['Low'].iloc[i-1] <= df['Low'].iloc[i-2] and df['Low'].iloc[i+1] <= df['Low'].iloc[i+2]):
                supports.append(float(df['Low'].iloc[i]))
            # Local swing high
            if (df['High'].iloc[i] >= df['High'].iloc[i-1] and df['High'].iloc[i] >= df['High'].iloc[i+1] and
                df['High'].iloc[i-1] >= df['High'].iloc[i-2] and df['High'].iloc[i+1] >= df['High'].iloc[i+2]):
                resistances.append(float(df['High'].iloc[i]))
        
        current_close = float(df['Close'].iloc[-1])
        
        valid_supports = [x for x in supports if x < current_close]
        valid_resistances = [x for x in resistances if x > current_close]
        
        if not valid_supports:
            valid_supports = [current_close * 0.96, current_close * 0.92]
        if not valid_resistances:
            valid_resistances = [current_close * 1.04, current_close * 1.08]
            
        closest_supports = sorted(list(set(valid_supports)), key=lambda x: abs(x - current_close))[:3]
        closest_resistances = sorted(list(set(valid_resistances)), key=lambda x: abs(x - current_close))[:3]
        
        nearest_sup = min(closest_supports, key=lambda x: abs(x - current_close)) if closest_supports else round(current_close * 0.96, 2)
        nearest_res = min(closest_resistances, key=lambda x: abs(x - current_close)) if closest_resistances else round(current_close * 1.04, 2)
        
        return {
            'support_levels': sorted([round(float(x), 2) for x in closest_supports]),
            'resistance_levels': sorted([round(float(x), 2) for x in closest_resistances]),
            'nearest_support': round(float(nearest_sup), 2),
            'nearest_resistance': round(float(nearest_res), 2),
            'dist_to_support_pct': round(((current_close - nearest_sup) / current_close) * 100, 2),
            'dist_to_resistance_pct': round(((nearest_res - current_close) / current_close) * 100, 2)
        }

    def candlestick_patterns(self) -> list:
        """Comprehensive Candlestick Pattern Detection Engine."""
        self._ensure_data()
        patterns = []
        df = self.daily_data
        if len(df) < 4:
            return patterns

        c0 = df.iloc[-1]   # Current candle
        c1 = df.iloc[-2]   # Previous candle
        c2 = df.iloc[-3]   # 2 bars back
        
        body0 = abs(c0['Close'] - c0['Open'])
        range0 = c0['High'] - c0['Low'] or 0.001
        is_bull0 = c0['Close'] >= c0['Open']
        
        body1 = abs(c1['Close'] - c1['Open'])
        range1 = c1['High'] - c1['Low'] or 0.001
        is_bull1 = c1['Close'] >= c1['Open']
        
        lower_wick0 = (c0['Open'] - c0['Low']) if is_bull0 else (c0['Close'] - c0['Low'])
        upper_wick0 = (c0['High'] - c0['Close']) if is_bull0 else (c0['High'] - c0['Open'])

        # 1. Hammer (Bullish Pin Bar Reversal at support)
        if lower_wick0 >= (body0 * 2.0) and upper_wick0 <= (body0 * 0.4) and body0 >= (range0 * 0.15):
            patterns.append({
                'name': 'Hammer (Bullish Pin Bar)',
                'type': 'BULLISH',
                'description': 'Rejection of lower prices with long buying wick. Strong support confirmation.'
            })

        # 2. Shooting Star (Bearish Pin Bar Reversal at resistance)
        if upper_wick0 >= (body0 * 2.0) and lower_wick0 <= (body0 * 0.4) and body0 >= (range0 * 0.15):
            patterns.append({
                'name': 'Shooting Star (Bearish Pin Bar)',
                'type': 'BEARISH',
                'description': 'Rejection of higher prices with long selling wick. Strong resistance confirmation.'
            })

        # 3. Bullish Engulfing
        if is_bull0 and not is_bull1 and c0['Close'] >= c1['Open'] and c0['Open'] <= c1['Close']:
            patterns.append({
                'name': 'Bullish Engulfing',
                'type': 'BULLISH',
                'description': 'Current green candle completely engulfs previous red candle. Buyers taking control.'
            })

        # 4. Bearish Engulfing
        if not is_bull0 and is_bull1 and c0['Close'] <= c1['Open'] and c0['Open'] >= c1['Close']:
            patterns.append({
                'name': 'Bearish Engulfing',
                'type': 'BEARISH',
                'description': 'Current red candle completely engulfs previous green candle. Sellers taking control.'
            })

        # 5. Morning Star (3-Bar Bullish Reversal)
        if not is_bull1 and is_bull0 and (c2['Close'] < c2['Open']) and (body1 <= range1 * 0.35) and (c0['Close'] > (c2['Open'] + c2['Close']) / 2):
            patterns.append({
                'name': 'Morning Star',
                'type': 'BULLISH',
                'description': '3-Candle bottom reversal confirming exhaustion of selling pressure.'
            })

        # 6. Evening Star (3-Bar Bearish Reversal)
        if is_bull1 and not is_bull0 and (c2['Close'] > c2['Open']) and (body1 <= range1 * 0.35) and (c0['Close'] < (c2['Open'] + c2['Close']) / 2):
            patterns.append({
                'name': 'Evening Star',
                'type': 'BEARISH',
                'description': '3-Candle top reversal confirming exhaustion of buying momentum.'
            })

        # 7. Marubozu (Strong Momentum Candle)
        if body0 >= (range0 * 0.85):
            name = 'Bullish Marubozu' if is_bull0 else 'Bearish Marubozu'
            patterns.append({
                'name': name,
                'type': 'BULLISH' if is_bull0 else 'BEARISH',
                'description': f'Strong conviction {("buying" if is_bull0 else "selling")} candle with almost no wicks.'
            })

        # 8. Doji (Indecision / Potential Turning Point)
        if body0 <= (range0 * 0.10):
            if lower_wick0 >= (range0 * 0.6):
                name = 'Dragonfly Doji (Bullish Rejection)'
                ptype = 'BULLISH'
            elif upper_wick0 >= (range0 * 0.6):
                name = 'Gravestone Doji (Bearish Rejection)'
                ptype = 'BEARISH'
            else:
                name = 'Doji (Market Indecision)'
                ptype = 'NEUTRAL'
            patterns.append({
                'name': name,
                'type': ptype,
                'description': 'Equilibrium between buyers and sellers. Watch for directional breakout.'
            })

        # 9. Bullish Harami / Inside Bar
        if not is_bull1 and is_bull0 and c0['High'] <= c1['High'] and c0['Low'] >= c1['Low']:
            patterns.append({
                'name': 'Bullish Harami (Inside Bar)',
                'type': 'BULLISH',
                'description': 'Volatility compression inside previous bar. Precursor to bullish expansion.'
            })

        return patterns

    def chart_patterns(self) -> list:
        """Classical Structural Chart Pattern Detection Engine."""
        self._ensure_data()
        patterns = []
        df = self.daily_data
        if len(df) < 30:
            return patterns

        closes = df['Close'].values
        highs = df['High'].values
        lows = df['Low'].values
        n = len(closes)
        
        # 1. Double Bottom (W Pattern Reversal)
        # Look back across last 30 bars for 2 distinct swing lows at similar level separated by a peak
        min1_idx = int(np.argmin(lows[-30:-12])) + (n - 30)
        min2_idx = int(np.argmin(lows[-12:])) + (n - 12)
        if min2_idx > min1_idx + 4:
            low1 = lows[min1_idx]
            low2 = lows[min2_idx]
            if abs(low1 - low2) / low1 <= 0.025:  # Within 2.5% tolerance
                neckline = float(np.max(highs[min1_idx:min2_idx]))
                current_c = closes[-1]
                if current_c >= low2:
                    patterns.append({
                        'name': 'Double Bottom (W-Pattern)',
                        'type': 'BULLISH',
                        'confidence': 'High' if current_c >= neckline else 'Medium',
                        'neckline': round(neckline, 2),
                        'description': f'Classic bullish W-reversal with twin support at ₹{low1:.2f} & ₹{low2:.2f}. Neckline: ₹{neckline:.2f}.'
                    })

        # 2. Double Top (M Pattern Rejection)
        max1_idx = int(np.argmax(highs[-30:-12])) + (n - 30)
        max2_idx = int(np.argmax(highs[-12:])) + (n - 12)
        if max2_idx > max1_idx + 4:
            high1 = highs[max1_idx]
            high2 = highs[max2_idx]
            if abs(high1 - high2) / high1 <= 0.025:
                neckline = float(np.min(lows[max1_idx:max2_idx]))
                current_c = closes[-1]
                patterns.append({
                    'name': 'Double Top (M-Pattern)',
                    'type': 'BEARISH',
                    'confidence': 'High' if current_c <= neckline else 'Medium',
                    'neckline': round(neckline, 2),
                    'description': f'Classic bearish M-rejection with twin peaks at ₹{high1:.2f} & ₹{high2:.2f}. Support breakdown level: ₹{neckline:.2f}.'
                })

        # 3. Cup and Handle (Bullish Continuation)
        # Rounded consolidation bottom followed by a mild pullback
        if n >= 40:
            window_low = float(np.min(lows[-40:-10]))
            left_rim = float(np.max(highs[-40:-30]))
            right_rim = float(np.max(highs[-20:-8]))
            handle_low = float(np.min(lows[-8:]))
            current_c = closes[-1]
            if (abs(left_rim - right_rim) / left_rim <= 0.035 and 
                window_low < left_rim * 0.92 and 
                handle_low >= window_low + (left_rim - window_low) * 0.5 and
                current_c >= handle_low):
                patterns.append({
                    'name': 'Cup and Handle',
                    'type': 'BULLISH',
                    'confidence': 'High',
                    'neckline': round(right_rim, 2),
                    'description': f'Institutional accumulation base with rounded cup and handle pullback. Breakout trigger above ₹{right_rim:.2f}.'
                })

        # 4. Inverse Head and Shoulders (Bullish Reversal)
        if n >= 45:
            # 3 valleys: left shoulder, deeper head, right shoulder
            left_s = float(np.min(lows[-45:-30]))
            head = float(np.min(lows[-30:-15]))
            right_s = float(np.min(lows[-15:]))
            if head < left_s * 0.97 and head < right_s * 0.97 and abs(left_s - right_s) / left_s <= 0.035:
                neckline = float(np.max(highs[-30:-15]))
                patterns.append({
                    'name': 'Inverse Head & Shoulders',
                    'type': 'BULLISH',
                    'confidence': 'High',
                    'neckline': round(neckline, 2),
                    'description': f'Major multi-week trend reversal with head at ₹{head:.2f} and shoulders around ₹{left_s:.2f}. Neckline: ₹{neckline:.2f}.'
                })

        # 5. Ascending Triangle / Bull Flag
        if n >= 20:
            recent_lows = [lows[-18], lows[-12], lows[-6], lows[-1]]
            recent_highs = [highs[-18], highs[-12], highs[-6], highs[-1]]
            if (recent_lows[3] > recent_lows[1] > recent_lows[0]) and (abs(recent_highs[3] - recent_highs[0]) / recent_highs[0] <= 0.02):
                patterns.append({
                    'name': 'Ascending Triangle (Bullish Breakout)',
                    'type': 'BULLISH',
                    'confidence': 'Medium',
                    'neckline': round(float(np.max(recent_highs)), 2),
                    'description': 'Higher lows compressing against flat resistance ceiling. Precursor to explosive upward breakout.'
                })

        return patterns

    def pivot_points(self) -> dict:
        self._ensure_data()
        if len(self.daily_data) < 2: return {}
        prev = self.daily_data.iloc[-2]
        high, low, close = prev['High'], prev['Low'], prev['Close']
        pp = (high + low + close) / 3
        r1 = (2 * pp) - low
        s1 = (2 * pp) - high
        r2 = pp + (high - low)
        s2 = pp - (high - low)
        r3 = high + 2 * (pp - low)
        s3 = low - 2 * (high - pp)
        return {
            'pivot': float(pp), 'r1': float(r1), 'r2': float(r2), 'r3': float(r3),
            's1': float(s1), 's2': float(s2), 's3': float(s3)
        }

    def trend_strength(self) -> str:
        try:
            self._ensure_data()
            rsi_val = self.rsi()
            macd_val = self.macd()
            sma50 = self.sma([50]).get('sma_50')
            close = self.daily_data['Close'].iloc[-1]
            score = 0
            if rsi_val > 60: score += 1
            elif rsi_val < 40: score -= 1
            if macd_val['histogram'] > 0: score += 1
            else: score -= 1
            if sma50 and close > sma50: score += 1
            elif sma50 and close < sma50: score -= 1

            if score >= 2: return 'Strong Bullish'
            if score == 1: return 'Bullish'
            if score == 0: return 'Neutral'
            if score == -1: return 'Bearish'
            return 'Strong Bearish'
        except Exception:
            return 'Neutral'

    def calculate_dynamic_targets(self, timeframe='swing', direction='BUY') -> dict:
        """
        Dynamically calculate high-probability multi-tier price targets based on:
        1. Pattern Measured Move Depth (Double Bottom, Cup & Handle, Inverse H&S)
        2. Average True Range (ATR) & Volatility Expansion
        3. Fibonacci Extension (161.8% Golden Target) & Multi-Timeframe Resistance Zones
        4. Support & Resistance Structural Defense Levels
        """
        self._ensure_data()
        close = float(self.daily_data['Close'].iloc[-1])
        atr_val = self.atr(14)
        if not atr_val or atr_val <= 0:
            atr_val = close * 0.022
        
        sr = self.support_resistance()
        fib = self.fibonacci_levels()
        chart_p = self.chart_patterns()
        
        if direction.upper() == 'BUY':
            # Target 1: Dynamic Conservative Target (Nearest Resistance or 1.6x ATR)
            res_candidates = [r for r in sr.get('resistance_levels', []) if r > close * 1.015]
            t1 = min(res_candidates) if res_candidates else (close + 1.6 * atr_val)
            t1 = round(max(t1, close * 1.025), 2)
            
            # Target 2: Pattern Measured Move / Fibonacci 161.8% Extension / 3.2x ATR
            pattern_target = None
            if chart_p:
                neckline = chart_p[0].get('neckline', close)
                pattern_target = close + (close * 0.085)
            
            fib_ext = fib.get('fib_ext_1618')
            swing_high = fib.get('swing_high')
            
            t2_candidates = [x for x in [pattern_target, fib_ext, swing_high, close + 3.2 * atr_val] if x and x > t1]
            t2 = min(t2_candidates) if t2_candidates else round(close * 1.085, 2)
            t2 = round(max(t2, t1 * 1.03), 2)
            
            # Target 3: Multi-Month Extended Runner / 52W High / Trend Runner
            t3 = round(max(t2 * 1.07, (swing_high or close) * 1.12), 2)
            
            # Dynamic Invalidation Stop Loss: Below S1 pivot or 1.4x ATR
            sup_candidates = [s for s in sr.get('support_levels', []) if s < close * 0.99]
            sl = max(sup_candidates) * 0.992 if sup_candidates else (close - 1.4 * atr_val)
            sl = round(min(sl, close * 0.978), 2)
            
        else: # SELL / Short
            sup_candidates = [s for s in sr.get('support_levels', []) if s < close * 0.985]
            t1 = max(sup_candidates) if sup_candidates else (close - 1.6 * atr_val)
            t1 = round(min(t1, close * 0.97), 2)
            
            t2 = round(min(t1 * 0.96, close - 3.2 * atr_val), 2)
            t3 = round(t2 * 0.93, 2)
            
            res_candidates = [r for r in sr.get('resistance_levels', []) if r > close * 1.01]
            sl = min(res_candidates) * 1.008 if res_candidates else (close + 1.4 * atr_val)
            sl = round(max(sl, close * 1.022), 2)

        pct1 = round(((abs(t1 - close)) / close) * 100, 1)
        pct2 = round(((abs(t2 - close)) / close) * 100, 1)
        pct3 = round(((abs(t3 - close)) / close) * 100, 1)
        rr = round(abs(t1 - close) / max(abs(close - sl), 0.05), 2)

        return {
            'entry': round(close, 2),
            'target_1': t1,
            'target_2': t2,
            'target_3': t3,
            'target_1_pct': f"+{pct1}%" if direction == 'BUY' else f"-{pct1}%",
            'target_2_pct': f"+{pct2}%" if direction == 'BUY' else f"-{pct2}%",
            'target_3_pct': f"+{pct3}%" if direction == 'BUY' else f"-{pct3}%",
            'stoploss': sl,
            'risk_reward': rr,
            'atr': round(atr_val, 2)
        }

    def overall_score(self) -> dict:
        try:
            trend = self.trend_strength()
            scores = {
                'Strong Bullish': (90, 'BUY', 'High'),
                'Bullish': (70, 'BUY', 'Medium'),
                'Neutral': (50, 'HOLD', 'Medium'),
                'Bearish': (30, 'SELL', 'Medium'),
                'Strong Bearish': (10, 'SELL', 'High')
            }
            s, sig, conf = scores.get(trend, (50, 'HOLD', 'Low'))
            return {'score': s, 'signal': sig, 'confidence': conf}
        except Exception:
            return {'score': 50, 'signal': 'HOLD', 'confidence': 'Low'}
