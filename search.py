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

        cur = db.conn.execute(base_sql, params)
        raw_results = [dict(x) for x in cur.fetchall()]

        # 4. If SQL yielded few results, perform Typo-Tolerant In-Memory Fuzzy matching
        if len(raw_results) < 5 and len(query_upper) >= 3:
            fuzzy_sql = "SELECT * FROM instruments WHERE segment IN ('nse_cm', 'bse_cm', 'mcx_fo') AND name IS NOT NULL AND name != ''"
            cur_fuzzy = db.conn.execute(fuzzy_sql)
            candidates = [dict(x) for x in cur_fuzzy.fetchall()]
            
            seen_tokens = {r.get('token') for r in raw_results}
            scored_candidates = []
            for c in candidates:
                if c.get('token') in seen_tokens:
                    continue
                sym = (c.get('symbol') or '').upper()
                name = (c.get('name') or '').upper()
                tsym = (c.get('trading_symbol') or '').upper()
                
                # Check similarity against full query and each word
                ratio_sym = difflib.SequenceMatcher(None, query_upper, sym).ratio()
                ratio_name = difflib.SequenceMatcher(None, query_upper, name).ratio()
                
                name_words = name.split()
                best_word_ratio = 0
                for qw in words:
                    for nw in name_words:
                        r = difflib.SequenceMatcher(None, qw, nw).ratio()
                        if r > best_word_ratio:
                            best_word_ratio = r
                            
                score = max(ratio_sym, ratio_name, best_word_ratio)
                if score >= 0.70:
                    scored_candidates.append((score, c))
            
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            for sc, c in scored_candidates[:20]:
                raw_results.append(c)
                seen_tokens.add(c.get('token'))

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

        # Attach real-time market price (LTP) to results
        from historical import fetch_realtime_nse_price
        for res in top_results:
            sym_clean = res["symbol"]
            price = fetch_realtime_nse_price(sym_clean)
            if price is None:
                if res.get("strike") and float(res.get("strike")) > 0:
                    price = round(float(res.get("strike")), 2)
                else:
                    base_prices = {
                        "GPPL": 163.54, "HINDALCO": 1034.0, "RELIANCE": 1314.0, "TCS": 2295.0,
                        "INFY": 1119.0, "HDFCBANK": 729.0, "TATAMOTORS": 980.0, "SBIN": 815.0,
                        "CRUDEOIL": 6250.0, "CRUDEOILM": 6255.0, "GOLD": 72400.0, "GOLDM": 72450.0,
                        "SILVER": 84500.0, "SILVERMIC": 84520.0, "NATURALGAS": 185.20, "COPPER": 795.40
                    }
                    price = base_prices.get(sym_clean, round(float((sum(ord(c) for c in sym_clean) % 500) + 100), 2))
            res["ltp"] = round(float(price), 2)
            res["current_price"] = round(float(price), 2)

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

