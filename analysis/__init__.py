from .technical import TechnicalAnalyzer
from .fundamental import FundamentalAnalyzer
from .options import OptionAnalyzer
from .signals import SignalGenerator
from .screener import Screener

def analyze_stock(symbol: str) -> dict:
    """Full analysis combining technical, fundamental, and options data."""
    try:
        tech = TechnicalAnalyzer(symbol)
        fund = FundamentalAnalyzer(symbol)
        opt = OptionAnalyzer(symbol)
        
        return {
            'symbol': symbol,
            'technical': {
                'score': tech.overall_score(),
                'trend': tech.trend_strength(),
                'indicators': tech.compute_all()
            },
            'fundamental': {
                'rating': fund.overall_rating(),
                'overview': fund.get_overview(),
                'valuation': fund.get_fair_value()
            },
            'options': {
                'pcr': opt.pcr(),
                'max_pain': opt.max_pain(),
                'strategies': opt.suggest_strategies(tech.trend_strength().lower().split(' ')[-1])
            }
        }
    except Exception as e:
        return {'error': str(e)}

from database import db
from datetime import datetime

def _is_signals_stale(sigs, max_age_hours=3) -> bool:
    if not sigs:
        return True
    try:
        first_sig = sigs[0]
        ts_str = first_sig.get("timestamp")
        if not ts_str:
            return True
        ts = datetime.fromisoformat(ts_str)
        now = datetime.now()
        if ts.date() < now.date() or (now - ts).total_seconds() > max_age_hours * 3600:
            return True
        return False
    except Exception:
        return True

import threading

_scan_in_progress = False

def _trigger_background_scan():
    global _scan_in_progress
    if _scan_in_progress:
        return
    _scan_in_progress = True
    def _run():
        global _scan_in_progress
        try:
            sg = SignalGenerator()
            sg.scan_and_save_all()
        finally:
            _scan_in_progress = False
    threading.Thread(target=_run, daemon=True).start()

def get_intraday_signals(force_refresh=False):
    sigs = db.get_signals("intraday", limit=25)
    if sigs:
        if force_refresh or _is_signals_stale(sigs):
            _trigger_background_scan()
        return sigs
    sg = SignalGenerator()
    sg.scan_and_save_all()
    return db.get_signals("intraday", limit=25)

def get_shortterm_signals(force_refresh=False):
    sigs = db.get_signals("shortterm", limit=25)
    if sigs:
        if force_refresh or _is_signals_stale(sigs):
            _trigger_background_scan()
        return sigs
    sg = SignalGenerator()
    sg.scan_and_save_all()
    return db.get_signals("shortterm", limit=25)

def get_longterm_signals(force_refresh=False):
    sigs = db.get_signals("longterm", limit=25)
    if sigs:
        if force_refresh or _is_signals_stale(sigs):
            _trigger_background_scan()
        return sigs
    sg = SignalGenerator()
    sg.scan_and_save_all()
    return db.get_signals("longterm", limit=25)

def get_futures_signals(force_refresh=False):
    sigs = db.get_signals("futures", limit=25)
    if sigs:
        if force_refresh or _is_signals_stale(sigs):
            _trigger_background_scan()
        return sigs
    sg = SignalGenerator()
    sg.scan_and_save_all()
    return db.get_signals("futures", limit=25)

def get_options_signals(force_refresh=False):
    sigs = db.get_signals("options", limit=25)
    if sigs:
        if force_refresh or _is_signals_stale(sigs):
            _trigger_background_scan()
        return sigs
    sg = SignalGenerator()
    sg.scan_and_save_all()
    return db.get_signals("options", limit=25)

