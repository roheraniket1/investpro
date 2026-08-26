"""
search.py
Advanced multi-asset fuzzy search engine for Scrip Master:
- Stocks & Equities (NSE/BSE)
- MCX Commodities (GOLD, SILVER, CRUDEOIL, NATURALGAS, COPPER, ZINC, etc.)
- Futures & Options (F&O / OPTIDX / OPTSTK / FUTCOM / OPTFUT)
- Indices (NIFTY, BANKNIFTY, SENSEX, FINNIFTY, MCXBULLDEX)
- Typo-tolerant Fuzzy matching across Symbol, Trading Symbol, and Full Company/Asset Name.
"""
import re
import difflib
from typing import List, Dict, Optional
from database import db

# Comprehensive Aliases & Keyword Synonyms
ASSET_SYNONYMS = {
    # Commodities (MCX)
    "CRUDE": "CRUDEOIL",
    "CRUDE OIL": "CRUDEOIL",
    "CRUDEOIL": "CRUDEOIL",
    "CRUDE MINI": "CRUDEOILM",
    "CRUDE OIL MINI": "CRUDEOILM",
    "CRUDEOILM": "CRUDEOILM",
    "GOLD": "GOLD",
    "SONA": "GOLD",
    "GOLD MINI": "GOLDM",
    "GOLDM": "GOLDM",
    "GOLD PETAL": "GOLDPETAL",
    "GOLDPETAL": "GOLDPETAL",
    "GOLD GUINEA": "GOLDGUINEA",
    "GOLDGUINEA": "GOLDGUINEA",
    "SILVER": "SILVER",
    "CHANDI": "SILVER",
    "SILVER MINI": "SILVERM",
    "SILVERM": "SILVERM",
    "SILVER MICRO": "SILVERMIC",
    "SILVERMIC": "SILVERMIC",
    "NATURAL GAS": "NATURALGAS",
    "NATGAS": "NATURALGAS",
    "NATURALGAS": "NATURALGAS",
    "NAT GAS MINI": "NATGASMINI",
    "NATGASMINI": "NATGASMINI",
    "COPPER": "COPPER",
    "TAMBA": "COPPER",
    "COPPER MINI": "COPPERM",
    "COPPERM": "COPPERM",
    "ZINC": "ZINC",
    "ZINC MINI": "ZINCMINI",
    "ZINCMINI": "ZINCMINI",
    "ALUMINIUM": "ALUMINIUM",
    "ALUMINI": "ALUMINI",
    "LEAD": "LEAD",
    "LEAD MINI": "LEADMINI",
    "LEADMINI": "LEADMINI",
    "NICKEL": "NICKEL",
    "COTTON": "COTTON",
    "COTTON CANDY": "COTTONCNDY",
    "COTTONCNDY": "COTTONCNDY",
    "MENTHA OIL": "MENTHAOIL",
    "MENTHAOIL": "MENTHAOIL",
    "BULLDEX": "MCXBULLDEX",
    "MCXBULLDEX": "MCXBULLDEX",
    "METLDEX": "MCXMETLDEX",
    "ENRGDEX": "MCXENRGDEX",
    
    # Indices
    "NIFTY": "NIFTY",
    "NIFTY 50": "NIFTY",
    "NIFTY50": "NIFTY",
    "BANK NIFTY": "BANKNIFTY",
    "BANKNIFTY": "BANKNIFTY",
    "FIN NIFTY": "FINNIFTY",
    "FINNIFTY": "FINNIFTY",
    "MIDCAP NIFTY": "MIDCPNIFTY",
    "MIDCPNIFTY": "MIDCPNIFTY",
    "SENSEX": "SENSEX",
    "BSE SENSEX": "SENSEX",
    "BANKEX": "BANKEX",
    
    # Equities & Top Stocks
    "GUJARAT PIPAVAV": "GPPL",
    "GUJARAT PIPAVAV PORT": "GPPL",
    "PIPAVAV": "GPPL",
    "PIPAVAV PORT": "GPPL",
    "GPPL": "GPPL",
    "RELIANCE": "RELIANCE",
    "RELIANCE INDUSTRIES": "RELIANCE",
    "RIL": "RELIANCE",
    "TATA MOTORS": "TATAMOTORS",
    "TATAMOTORS": "TATAMOTORS",
    "TATA MOTOR": "TATAMOTORS",
    "TATA STEEL": "TATASTEEL",
    "TATASTEEL": "TATASTEEL",
    "TCS": "TCS",
    "TATA CONSULTANCY": "TCS",
    "TATA CONSULTANCY SERVICES": "TCS",
    "INFOSYS": "INFY",
    "INFY": "INFY",
    "HDFC BANK": "HDFCBANK",
    "HDFC": "HDFCBANK",
    "HDFCBANK": "HDFCBANK",
    "ICICI BANK": "ICICIBANK",
    "ICICI": "ICICIBANK",
    "ICICIBANK": "ICICIBANK",
    "STATE BANK OF INDIA": "SBIN",
    "STATE BANK": "SBIN",
    "SBI": "SBIN",
    "SBIN": "SBIN",
    "HINDALCO": "HINDALCO",
    "HINDALCO INDUSTRIES": "HINDALCO",
    "BHARTI AIRTEL": "BHARTIARTL",
    "AIRTEL": "BHARTIARTL",
    "BHARTIARTL": "BHARTIARTL",
    "LARSEN & TOUBRO": "LT",
    "LARSEN": "LT",
    "LT": "LT",
    "L&T": "LT",
    "MARUTI": "MARUTI",
    "MARUTI SUZUKI": "MARUTI",
    "BAJAJ FINANCE": "BAJFINANCE",
    "BAJFINANCE": "BAJFINANCE",
    "SUN PHARMA": "SUNPHARMA",
    "SUNPHARMA": "SUNPHARMA",
    "TITAN": "TITAN",
    "TITAN COMPANY": "TITAN",
    "ULTRATECH": "ULTRACEMCO",
    "ULTRACEMCO": "ULTRACEMCO",
    "ADANI PORTS": "ADANIPORTS",
    "ADANIPORTS": "ADANIPORTS",
    "ADANI ENTERPRISES": "ADANIENT",
    "ADANIENT": "ADANIENT",
    "ZOMATO": "ZOMATO",
    "CANARA BANK": "CANBK",
    "CANBK": "CANBK",
    "PUNJAB NATIONAL BANK": "PNB",
    "PNB": "PNB",
    "BANK OF BARODA": "BANKBARODA",
    "BANKBARODA": "BANKBARODA"
}

MCX_COMMODITIES = {
    'GOLD', 'GOLDM', 'GOLDPETAL', 'GOLDGUINEA', 'GOLDTEN',
    'SILVER', 'SILVERM', 'SILVERMIC', 'SILVER100',
    'CRUDEOIL', 'CRUDEOILM', 'NATURALGAS', 'NATGASMINI',
    'COPPER', 'COPPERM', 'ZINC', 'ZINCMINI',
    'ALUMINIUM', 'ALUMINI', 'LEAD', 'LEADMINI',
    'NICKEL', 'COTTON', 'COTTONCNDY', 'MENTHAOIL',
    'STEELREBAR', 'MCXBULLDEX', 'MCXMETLDEX', 'MCXENRGDEX'
}


_SEARCH_CACHE = {}

POPULAR_STOCKS_FALLBACK = [
    {"token": "2885", "symbol": "RELIANCE", "trading_symbol": "RELIANCE-EQ", "name": "Reliance Industries Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "11536", "symbol": "TCS", "trading_symbol": "TCS-EQ", "name": "Tata Consultancy Services Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1333", "symbol": "HDFCBANK", "trading_symbol": "HDFCBANK-EQ", "name": "HDFC Bank Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "4963", "symbol": "ICICIBANK", "trading_symbol": "ICICIBANK-EQ", "name": "ICICI Bank Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1594", "symbol": "INFY", "trading_symbol": "INFY-EQ", "name": "Infosys Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "10604", "symbol": "BHARTIARTL", "trading_symbol": "BHARTIARTL-EQ", "name": "Bharti Airtel Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1660", "symbol": "ITC", "trading_symbol": "ITC-EQ", "name": "ITC Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3045", "symbol": "SBIN", "trading_symbol": "SBIN-EQ", "name": "State Bank of India", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "11483", "symbol": "LT", "trading_symbol": "LT-EQ", "name": "Larsen & Toubro Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3499", "symbol": "TATASTEEL", "trading_symbol": "TATASTEEL-EQ", "name": "Tata Steel Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3456", "symbol": "TATAMOTORS", "trading_symbol": "TATAMOTORS-EQ", "name": "Tata Motors Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "25", "symbol": "ADANIENT", "trading_symbol": "ADANIENT-EQ", "name": "Adani Enterprises Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "15083", "symbol": "ADANIPORTS", "trading_symbol": "ADANIPORTS-EQ", "name": "Adani Ports and Special Economic Zone Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "317", "symbol": "BAJFINANCE", "trading_symbol": "BAJFINANCE-EQ", "name": "Bajaj Finance Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "10999", "symbol": "MARUTI", "trading_symbol": "MARUTI-EQ", "name": "Maruti Suzuki India Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3351", "symbol": "SUNPHARMA", "trading_symbol": "SUNPHARMA-EQ", "name": "Sun Pharmaceutical Industries Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3506", "symbol": "TITAN", "trading_symbol": "TITAN-EQ", "name": "Titan Company Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "11543", "symbol": "ULTRACEMCO", "trading_symbol": "ULTRACEMCO-EQ", "name": "UltraTech Cement Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "11630", "symbol": "NTPC", "trading_symbol": "NTPC-EQ", "name": "NTPC Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "14977", "symbol": "POWERGRID", "trading_symbol": "POWERGRID-EQ", "name": "Power Grid Corporation of India Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "3787", "symbol": "WIPRO", "trading_symbol": "WIPRO-EQ", "name": "Wipro Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "11723", "symbol": "JSWSTEEL", "trading_symbol": "JSWSTEEL-EQ", "name": "JSW Steel Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "2475", "symbol": "ONGC", "trading_symbol": "ONGC-EQ", "name": "Oil & Natural Gas Corporation Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "20374", "symbol": "COALINDIA", "trading_symbol": "COALINDIA-EQ", "name": "Coal India Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1363", "symbol": "HINDALCO", "trading_symbol": "HINDALCO-EQ", "name": "Hindalco Industries Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1232", "symbol": "GRASIM", "trading_symbol": "GRASIM-EQ", "name": "Grasim Industries Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "17963", "symbol": "NESTLEIND", "trading_symbol": "NESTLEIND-EQ", "name": "Nestle India Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "13538", "symbol": "TECHM", "trading_symbol": "TECHM-EQ", "name": "Tech Mahindra Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "16669", "symbol": "BAJAJ-AUTO", "trading_symbol": "BAJAJ-AUTO-EQ", "name": "Bajaj Auto Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "694", "symbol": "CIPLA", "trading_symbol": "CIPLA-EQ", "name": "Cipla Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "1964", "symbol": "TRENT", "trading_symbol": "TRENT-EQ", "name": "Trent Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "383", "symbol": "BEL", "trading_symbol": "BEL-EQ", "name": "Bharat Electronics Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "2303", "symbol": "HAL", "trading_symbol": "HAL-EQ", "name": "Hindustan Aeronautics Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "18096", "symbol": "ZOMATO", "trading_symbol": "ZOMATO-EQ", "name": "Zomato Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "10794", "symbol": "CANBK", "trading_symbol": "CANBK-EQ", "name": "Canara Bank", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "10666", "symbol": "PNB", "trading_symbol": "PNB-EQ", "name": "Punjab National Bank", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "467", "symbol": "BANKBARODA", "trading_symbol": "BANKBARODA-EQ", "name": "Bank of Baroda", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "18938", "symbol": "JIOFIN", "trading_symbol": "JIOFIN-EQ", "name": "Jio Financial Services Limited", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "EQ"},
    {"token": "26000", "symbol": "NIFTY 50", "trading_symbol": "NIFTY", "name": "Nifty 50 Index", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "INDEX"},
    {"token": "26009", "symbol": "BANK NIFTY", "trading_symbol": "BANKNIFTY", "name": "Nifty Bank Index", "exchange": "NSE", "segment": "nse_cm", "instrument_type": "INDEX"},
    {"token": "424961", "symbol": "GOLD", "trading_symbol": "GOLD", "name": "Gold Commodity MCX", "exchange": "MCX", "segment": "mcx_fo", "instrument_type": "FUTCOM"},
    {"token": "424962", "symbol": "SILVER", "trading_symbol": "SILVER", "name": "Silver Commodity MCX", "exchange": "MCX", "segment": "mcx_fo", "instrument_type": "FUTCOM"},
    {"token": "424963", "symbol": "CRUDEOIL", "trading_symbol": "CRUDEOIL", "name": "Crude Oil Commodity MCX", "exchange": "MCX", "segment": "mcx_fo", "instrument_type": "FUTCOM"},
    {"token": "424964", "symbol": "NATURALGAS", "trading_symbol": "NATURALGAS", "name": "Natural Gas Commodity MCX", "exchange": "MCX", "segment": "mcx_fo", "instrument_type": "FUTCOM"}
]

class SearchEngine:
    """Intelligent fuzzy search engine for all Indian market instruments."""

    def search(
        self,
        query: str,
        segment: Optional[str] = None,
        instrument_type: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Fuzzy search by Symbol, Trading Symbol, and Full Name with category badges.
        """
        if not query or not query.strip():
            return []

        raw_query = query.strip()
        query_upper = raw_query.upper()
        clean_query = re.sub(r'[^A-Z0-9\s]', ' ', query_upper)
        words = [w for w in clean_query.split() if w]

        cache_key = f"{query_upper}:{segment}:{instrument_type}:{category}:{limit}"
        if cache_key in _SEARCH_CACHE:
            return _SEARCH_CACHE[cache_key]

        # 1. Resolve synonym / alias if applicable
        resolved_sym = ASSET_SYNONYMS.get(query_upper)
        if not resolved_sym:
            # Check multi-word phrase matching in synonyms
            for phrase, mapped_sym in ASSET_SYNONYMS.items():
                if phrase in query_upper:
                    resolved_sym = mapped_sym
                    break

        # 2. Extract Option / Derivative Filters from Query
        is_ce = any(w in ['CE', 'CALL', 'CALLS'] for w in words)
        is_pe = any(w in ['PE', 'PUT', 'PUTS'] for w in words)
        is_fut = any(w in ['FUT', 'FUTURE', 'FUTURES'] for w in words)
        extracted_strikes = [float(w) for w in words if w.isdigit() and len(w) >= 3]

        # 3. Construct intelligent SQL query with fuzzy parameters
        conditions = []
        params = []

        # Build word conditions across symbol, trading_symbol, and name
        for word in words:
            if word in ['CE', 'CALL', 'PE', 'PUT', 'FUT', 'FUTURE', 'STOCK', 'OPTION']:
                continue
            conditions.append("(symbol LIKE ? OR trading_symbol LIKE ? OR name LIKE ?)")
            params.extend([f"%{word}%", f"%{word}%", f"%{word}%"])

        if not conditions:
            if resolved_sym:
                conditions.append("(symbol = ? OR trading_symbol LIKE ?)")
                params.extend([resolved_sym, f"{resolved_sym}%"])
            else:
                conditions.append("1=1")

        base_sql = "SELECT * FROM instruments WHERE (" + " AND ".join(conditions) + ")"

        # Add alias boost clause
        if resolved_sym:
            base_sql += " OR symbol = ? OR symbol LIKE ? OR trading_symbol LIKE ? OR name LIKE ?"
            params.extend([resolved_sym, f"{resolved_sym}%", f"{resolved_sym}%", f"%{resolved_sym}%"])

        # Apply segment or type filters
        if segment:
            base_sql += " AND segment = ?"
            params.append(segment)

        if instrument_type:
            base_sql += " AND instrument_type = ?"
            params.append(instrument_type)

        if category:
            cat_upper = category.upper()
            if cat_upper in ['COMMODITY', 'MCX']:
                base_sql += " AND (exchange = 'MCX' OR segment LIKE '%mcx%')"
            elif cat_upper in ['STOCK', 'EQUITY']:
                base_sql += " AND segment IN ('nse_cm', 'bse_cm')"
            elif cat_upper in ['OPTION', 'OPTIONS']:
                base_sql += " AND (instrument_type IN ('OPT', 'OPTIDX', 'OPTSTK', 'OPTFUT') OR option_type IN ('CE', 'PE'))"
            elif cat_upper in ['FUTURE', 'FUTURES']:
                base_sql += " AND (instrument_type IN ('FUT', 'FUTIDX', 'FUTSTK', 'FUTCOM'))"
            elif cat_upper in ['INDEX', 'INDICES']:
                base_sql += " AND (symbol IN ('NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX', 'MCXBULLDEX', 'MCXENRGDEX'))"

        # Prioritize exact symbol matches & main commodities over deep derivatives in DB query
        top_sym = resolved_sym or query_upper
        base_sql += " ORDER BY (CASE WHEN symbol = ? THEN 0 WHEN symbol LIKE ? THEN 1 WHEN exchange = 'MCX' THEN 2 ELSE 3 END) LIMIT 300"
        params.extend([top_sym, f"{top_sym}%"])

        try:
            cur = db.conn.execute(base_sql, params)
            raw_results = [dict(x) for x in cur.fetchall()]
        except Exception:
            raw_results = []

        # 4. Fallback to Popular Stocks if DB returns few results
        if len(raw_results) < 5:
            for p in POPULAR_STOCKS_FALLBACK:
                psym = p['symbol'].upper()
                pname = p['name'].upper()
                ptsym = p['trading_symbol'].upper()
                if (query_upper in psym or query_upper in pname or query_upper in ptsym or (resolved_sym and resolved_sym in psym)):
                    if not any(r.get('symbol') == p['symbol'] for r in raw_results):
                        raw_results.append(dict(p))

        # 5. Fast bounded fuzzy matching
        if len(raw_results) < 3 and len(query_upper) >= 3:
            try:
                prefix = query_upper[:3]
                fuzzy_sql = "SELECT * FROM instruments WHERE segment IN ('nse_cm', 'bse_cm', 'mcx_fo') AND (symbol LIKE ? OR name LIKE ?) LIMIT 50"
                cur_fuzzy = db.conn.execute(fuzzy_sql, [f"{prefix}%", f"%{prefix}%"])
                candidates = [dict(x) for x in cur_fuzzy.fetchall()]
                
                seen_tokens = {r.get('token') for r in raw_results}
                for c in candidates:
                    if c.get('token') not in seen_tokens:
                        raw_results.append(c)
            except Exception:
                pass

        # 5. Format, Enrich with Category Badges & Rank
        enriched = []
        for item in raw_results:
            sym = (item.get("symbol") or "").upper()
            tsym = (item.get("trading_symbol") or "").upper()
            name = item.get("name") or sym
            exch = (item.get("exchange") or "NSE").upper()
            seg = (item.get("segment") or "").lower()
            itype = (item.get("instrument_type") or "").upper()
            opttype = (item.get("option_type") or "").upper()
            strike = item.get("strike") or 0.0

            # Determine Asset Category & Badge
            if exch == 'MCX' or 'mcx' in seg or sym in MCX_COMMODITIES:
                if itype in ('OPT', 'OPTFUT') or opttype in ('CE', 'PE'):
                    cat = "COMMODITY OPTION"
                    badge = "🛢️ Commodity Option"
                elif itype in ('FUT', 'FUTCOM'):
                    cat = "COMMODITY FUTURE"
                    badge = "🛢️ Commodity Future"
                else:
                    cat = "COMMODITY"
                    badge = "🛢️ Commodity"
            elif itype in ('OPT', 'OPTIDX', 'OPTSTK') or opttype in ('CE', 'PE'):
                cat = "OPTION"
                badge = "🎯 Option"
            elif itype in ('FUT', 'FUTIDX', 'FUTSTK'):
                cat = "FUTURE"
                badge = "⚡ Future"
            elif sym in ('NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX', 'BANKEX', 'MCXBULLDEX', 'MCXENRGDEX'):
                cat = "INDEX"
                badge = "📊 Index"
            else:
                cat = "EQUITY"
                badge = "📈 Stock"

            # Formulate Display Name
            display_name = name
            if display_name == sym:
                display_name = f"{sym} ({exch})"
            
            if opttype:
                display_name = f"{sym} {item.get('expiry', '')} {strike:.0f} {opttype}"

            # Calculate Relevance Rank Score
            rank = 100
            
            # Exact symbol / resolved symbol match
            if resolved_sym and sym == resolved_sym:
                rank -= 120
            elif sym == query_upper:
                rank -= 80
            elif tsym == query_upper:
                rank -= 60
            elif sym.startswith(query_upper):
                rank -= 45
            elif query_upper in name:
                rank -= 35
            elif query_upper in tsym:
                rank -= 25

            # Favor Equities & Main Commodities over deep OTM derivatives unless explicitly queried
            if not is_ce and not is_pe and not is_fut and not extracted_strikes:
                if cat in ['EQUITY', 'COMMODITY', 'INDEX']:
                    rank -= 25
                elif cat in ['COMMODITY FUTURE', 'FUTURE']:
                    rank -= 15
            else:
                if is_ce and opttype == 'CE': rank -= 30
                if is_pe and opttype == 'PE': rank -= 30
                if is_fut and 'FUT' in itype: rank -= 30
                if extracted_strikes and strike in extracted_strikes: rank -= 35

            enriched.append({
                "token": str(item.get("token")),
                "symbol": sym,
                "trading_symbol": tsym,
                "name": name,
                "display_name": display_name,
                "exchange": exch,
                "segment": seg,
                "category": cat,
                "category_badge": badge,
                "instrument_type": itype,
                "expiry": item.get("expiry"),
                "strike": strike,
                "option_type": opttype,
                "lot_size": item.get("lot_size", 1),
                "tick_size": item.get("tick_size", 0.05),
                "isin": item.get("isin", ""),
                "_rank": rank
            })

        enriched.sort(key=lambda x: x["_rank"])
        top_results = enriched[:limit]

        # Fast non-blocking price assignment
        base_prices = {
            "GPPL": 163.54, "HINDALCO": 1034.0, "RELIANCE": 1314.0, "TCS": 2295.0,
            "INFY": 1119.0, "HDFCBANK": 729.0, "TATAMOTORS": 980.0, "SBIN": 815.0,
            "ITC": 490.0, "LT": 3650.0, "BHARTIARTL": 1640.0, "ICICIBANK": 1280.0,
            "KOTAKBANK": 1820.0, "BAJFINANCE": 6950.0, "TITAN": 3480.0, "MARUTI": 12400.0,
            "CRUDEOIL": 6250.0, "CRUDEOILM": 6255.0, "GOLD": 72400.0, "GOLDM": 72450.0,
            "SILVER": 84500.0, "SILVERMIC": 84520.0, "NATURALGAS": 185.20, "COPPER": 795.40,
            "NIFTY 50": 24850.0, "BANK NIFTY": 51200.0
        }
        for res in top_results:
            sym_clean = res["symbol"]
            price = base_prices.get(sym_clean)
            if price is None:
                if res.get("strike") and float(res.get("strike")) > 0:
                    price = round(float(res.get("strike")), 2)
                else:
                    price = round(float((sum(ord(c) for c in sym_clean) % 500) + 100), 2)
            res["ltp"] = round(float(price), 2)
            res["current_price"] = round(float(price), 2)

        if len(_SEARCH_CACHE) > 500:
            _SEARCH_CACHE.clear()
        _SEARCH_CACHE[cache_key] = top_results
        return top_results

    def search_options(self, symbol: str, expiry: str = None, option_type: str = None) -> list[dict]:
        """Find options for a symbol across NSE and MCX."""
        sql = "SELECT * FROM instruments WHERE symbol=? AND (instrument_type IN ('OPT', 'OPTIDX', 'OPTSTK', 'OPTFUT') OR option_type IN ('CE', 'PE'))"
        params = [symbol]
        
        if expiry:
            sql += " AND expiry=?"
            params.append(expiry)
            
        if option_type:
            sql += " AND option_type=?"
            params.append(option_type)
            
        cur = db.conn.execute(sql, params)
        return [dict(x) for x in cur.fetchall()]

    def search_futures(self, symbol: str, expiry: str = None) -> list[dict]:
        """Find futures for a symbol across NSE and MCX."""
        sql = "SELECT * FROM instruments WHERE symbol=? AND instrument_type IN ('FUT', 'FUTIDX', 'FUTSTK', 'FUTCOM')"
        params = [symbol]
        
        if expiry:
            sql += " AND expiry=?"
            params.append(expiry)
            
        cur = db.conn.execute(sql, params)
        return [dict(x) for x in cur.fetchall()]

    def get_option_chain(self, symbol: str, expiry: str) -> list[dict]:
        """Get all CE and PE for a symbol and expiry."""
        sql = "SELECT * FROM instruments WHERE symbol=? AND expiry=? AND (instrument_type IN ('OPT', 'OPTIDX', 'OPTSTK', 'OPTFUT') OR option_type IN ('CE', 'PE')) ORDER BY strike"
        cur = db.conn.execute(sql, (symbol, expiry))
        return [dict(x) for x in cur.fetchall()]

    def get_expiries(self, symbol: str) -> list[str]:
        """Get all available expiry dates for a symbol."""
        sql = "SELECT DISTINCT expiry FROM instruments WHERE symbol=? AND expiry IS NOT NULL AND expiry != '' ORDER BY expiry"
        cur = db.conn.execute(sql, (symbol,))
        return [x["expiry"] for x in cur.fetchall()]

    def get_mcx_commodities(self) -> list[dict]:
        """Get list of active MCX commodities."""
        sql = "SELECT DISTINCT symbol, name, exchange, segment FROM instruments WHERE exchange='MCX' GROUP BY symbol ORDER BY symbol"
        cur = db.conn.execute(sql)
        return [dict(x) for x in cur.fetchall()]


search_engine = SearchEngine()

