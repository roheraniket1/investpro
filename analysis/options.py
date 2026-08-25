import requests
import json
import time

class OptionAnalyzer:
    def __init__(self, symbol: str):
        self.symbol = symbol.replace('.NS', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        # Hit homepage for cookies
        try:
            self.session.get('https://www.nseindia.com', timeout=5)
        except:
            pass
        self.chain_data = None

    def _fetch_chain(self):
        if self.chain_data: return self.chain_data
        try:
            if self.symbol in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']:
                url = f"https://www.nseindia.com/api/option-chain-indices?symbol={self.symbol}"
            else:
                url = f"https://www.nseindia.com/api/option-chain-equities?symbol={self.symbol}"
            resp = self.session.get(url, timeout=5)
            if resp.status_code == 200:
                self.chain_data = resp.json()
        except Exception as e:
            print(f"Option fetch error: {e}")
            self.chain_data = {}
        return self.chain_data or {}

    def get_option_chain(self, expiry=None) -> dict:
        data = self._fetch_chain()
        if not data or 'records' not in data:
            return {'calls': [], 'puts': [], 'spot_price': 0, 'expiry_date': ''}
        
        records = data['records']
        if not expiry:
            expiry = records['expiryDates'][0] if records['expiryDates'] else None
            
        calls = []
        puts = []
        for d in records.get('data', []):
            if d['expiryDate'] == expiry:
                if 'CE' in d:
                    ce = d['CE']
                    calls.append({
                        'strike': ce.get('strikePrice'), 'ltp': ce.get('lastPrice'), 'oi': ce.get('openInterest'),
                        'volume': ce.get('totalTradedVolume'), 'iv': ce.get('impliedVolatility'),
                        'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'change_oi': ce.get('changeinOpenInterest')
                    })
                if 'PE' in d:
                    pe = d['PE']
                    puts.append({
                        'strike': pe.get('strikePrice'), 'ltp': pe.get('lastPrice'), 'oi': pe.get('openInterest'),
                        'volume': pe.get('totalTradedVolume'), 'iv': pe.get('impliedVolatility'),
                        'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'change_oi': pe.get('changeinOpenInterest')
                    })
        return {
            'calls': calls,
            'puts': puts,
            'spot_price': records.get('underlyingValue', 0),
            'expiry_date': expiry
        }

    def pcr(self) -> float:
        chain = self.get_option_chain()
        total_put_oi = sum(p['oi'] for p in chain['puts'] if p['oi'])
        total_call_oi = sum(c['oi'] for c in chain['calls'] if c['oi'])
        if total_call_oi == 0: return 0.0
        return round(total_put_oi / total_call_oi, 2)

    def max_pain(self) -> float:
        chain = self.get_option_chain()
        if not chain['calls']: return 0.0
        strikes = sorted(list(set(c['strike'] for c in chain['calls'])))
        min_loss = float('inf')
        max_pain_strike = 0
        for spot in strikes:
            loss = 0
            for c in chain['calls']:
                if spot > c['strike']: loss += (spot - c['strike']) * c['oi']
            for p in chain['puts']:
                if spot < p['strike']: loss += (p['strike'] - spot) * p['oi']
            if loss < min_loss:
                min_loss = loss
                max_pain_strike = spot
        return max_pain_strike

    def iv_skew(self) -> dict:
        chain = self.get_option_chain()
        return {
            'calls': {c['strike']: c['iv'] for c in chain['calls']},
            'puts': {p['strike']: p['iv'] for p in chain['puts']}
        }

    def oi_analysis(self) -> dict:
        chain = self.get_option_chain()
        if not chain['calls'] or not chain['puts']: return {}
        highest_call = max(chain['calls'], key=lambda x: x['oi'] or 0)
        highest_put = max(chain['puts'], key=lambda x: x['oi'] or 0)
        top5_call_change = sorted(chain['calls'], key=lambda x: x['change_oi'] or 0, reverse=True)[:5]
        top5_put_change = sorted(chain['puts'], key=lambda x: x['change_oi'] or 0, reverse=True)[:5]
        return {
            'highest_oi_call_strike': highest_call['strike'],
            'highest_oi_put_strike': highest_put['strike'],
            'call_oi_change_top5': [c['strike'] for c in top5_call_change],
            'put_oi_change_top5': [p['strike'] for p in top5_put_change],
            'support_level': highest_put['strike'],
            'resistance_level': highest_call['strike']
        }

    def suggest_strategies(self, view='neutral') -> list:
        # Mocking for simplicity, typically needs robust calculation
        return [{
            'name': 'Long Call' if view == 'bullish' else 'Iron Condor',
            'legs': [{'type': 'CE', 'strike': 0, 'action': 'BUY', 'premium': 0}],
            'max_profit': 0, 'max_loss': 0, 'breakeven': 0, 'risk_reward': 0,
            'payoff_data': []
        }]
