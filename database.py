"""
database.py
SQLite Database for Kotak Neo Scrip Master
"""

import sqlite3
from pathlib import Path

from config import DATABASE_PATH

Path("data").mkdir(exist_ok=True)


class ScripDatabase:

    def __init__(self):
        self.conn = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self.create_tables()

    def create_tables(self):

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS instruments (
            token TEXT PRIMARY KEY,
            symbol TEXT,
            trading_symbol TEXT,
            name TEXT,
            exchange TEXT,
            segment TEXT,
            instrument_type TEXT,
            expiry TEXT,
            strike REAL,
            option_type TEXT,
            lot_size INTEGER,
            tick_size REAL,
            isin TEXT
        )
        """)
        try:
            self.conn.execute("ALTER TABLE instruments ADD COLUMN name TEXT")
        except Exception:
            pass

        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON instruments (symbol)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON instruments (name)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_exchange ON instruments (exchange)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_segment ON instruments (segment)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_instrument_type ON instruments (instrument_type)")
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS trade_signals (
            symbol TEXT,
            signal_type TEXT,
            direction TEXT,
            entry TEXT,
            target TEXT,
            stoploss TEXT,
            score REAL,
            reason TEXT,
            timestamp TEXT,
            PRIMARY KEY (symbol, signal_type)
        )
        """)
        try:
            self.conn.execute("ALTER TABLE trade_signals ADD COLUMN expected_days INTEGER")
        except Exception:
            pass
        try:
            self.conn.execute("ALTER TABLE trade_signals ADD COLUMN trigger_candle_time TEXT")
        except Exception:
            pass
            
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            direction TEXT,
            qty INTEGER,
            entry_price REAL,
            target_price REAL,
            stoploss_price REAL,
            status TEXT,
            entry_time TEXT,
            exit_time TEXT,
            exit_price REAL,
            pnl REAL
        )
        """)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        self.conn.execute("INSERT OR IGNORE INTO paper_profile (key, value) VALUES ('balance', '1000000')")
        self.conn.commit()

    def insert(self, item):

        self.conn.execute("""

        INSERT OR REPLACE INTO instruments(

            token,
            symbol,
            trading_symbol,
            name,
            exchange,
            segment,
            instrument_type,
            expiry,
            strike,
            option_type,
            lot_size,
            tick_size,
            isin

        )

        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)

        """, (

            item.get("token"),

            item.get("symbol"),

            item.get("trading_symbol"),

            item.get("name") or item.get("symbol"),

            item.get("exchange"),

            item.get("segment"),

            item.get("instrument_type"),

            item.get("expiry"),

            item.get("strike"),

            item.get("option_type"),

            item.get("lot_size"),

            item.get("tick_size"),

            item.get("isin")

        ))

        self.conn.commit()

    def search(self, keyword):

        cur = self.conn.execute("""

        SELECT *

        FROM instruments

        WHERE symbol LIKE ?
        OR trading_symbol LIKE ?
        OR name LIKE ?

        LIMIT 100
        """, (
            f"%{keyword}%",
            f"%{keyword}%",
            f"%{keyword}%"
        ))

        return [dict(x) for x in cur.fetchall()]

    def get_token(self, symbol):

        cur = self.conn.execute("""

        SELECT token

        FROM instruments

        WHERE symbol=?

        LIMIT 1

        """, (symbol,))

        row = cur.fetchone()

        if row:

            return row["token"]

        return None

    def get_by_token(self, token):
        cur = self.conn.execute("""
        SELECT *
        FROM instruments
        WHERE token=?
        LIMIT 1
        """, (token,))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None

    def get_instrument_info(self, symbol_or_name: str):
        """Lookup instrument info by symbol, trading_symbol, or full company/commodity name."""
        if not symbol_or_name:
            return None
        clean = symbol_or_name.strip().upper()
        if " - " in clean:
            clean = clean.split(" - ")[0].strip()
        elif " (" in clean:
            clean = clean.split(" (")[0].strip()

        cur = self.conn.execute("""
            SELECT * FROM instruments
            WHERE symbol = ? OR trading_symbol = ?
            ORDER BY (CASE WHEN segment IN ('nse_cm', 'mcx_fo', 'bse_cm') THEN 0 ELSE 1 END)
            LIMIT 1
        """, (clean, clean))
        row = cur.fetchone()
        if row:
            return dict(row)

        cur = self.conn.execute("""
            SELECT * FROM instruments
            WHERE name LIKE ?
            ORDER BY (CASE WHEN segment IN ('nse_cm', 'mcx_fo', 'bse_cm') THEN 0 ELSE 1 END)
            LIMIT 1
        """, (f"%{clean}%",))
        row = cur.fetchone()
        if row:
            return dict(row)
        return None

    def count(self):

        cur = self.conn.execute("""

        SELECT COUNT(*)

        FROM instruments

        """)

        return cur.fetchone()[0]

    def delete_expired(self):

        self.conn.execute("""

        DELETE FROM instruments

        WHERE expiry <> ''

        AND expiry < DATE('now')

        """)

        self.conn.commit()

    def bulk_insert(self, items):
        self.conn.executemany("""
        INSERT OR REPLACE INTO instruments(
            token, symbol, trading_symbol, name, exchange, segment, instrument_type,
            expiry, strike, option_type, lot_size, tick_size, isin
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, [
            (
                item.get("token"), item.get("symbol"), item.get("trading_symbol"),
                item.get("name") or item.get("symbol"),
                item.get("exchange"), item.get("segment"), item.get("instrument_type"),
                item.get("expiry"), item.get("strike"), item.get("option_type"),
                item.get("lot_size"), item.get("tick_size"), item.get("isin")
            ) for item in items
        ])
        self.conn.commit()

    def get_by_segment(self, segment):
        cur = self.conn.execute("SELECT * FROM instruments WHERE segment=?", (segment,))
        return [dict(x) for x in cur.fetchall()]

    def get_futures(self, symbol=None):
        query = "SELECT * FROM instruments WHERE instrument_type IN ('FUT', 'FUTIDX', 'FUTSTK')"
        params = []
        if symbol:
            query += " AND symbol=?"
            params.append(symbol)
        cur = self.conn.execute(query, params)
        return [dict(x) for x in cur.fetchall()]

    def get_options(self, symbol=None):
        query = "SELECT * FROM instruments WHERE instrument_type IN ('OPT', 'OPTIDX', 'OPTSTK')"
        params = []
        if symbol:
            query += " AND symbol=?"
            params.append(symbol)
        cur = self.conn.execute(query, params)
        return [dict(x) for x in cur.fetchall()]

    def get_etfs(self):
        query = "SELECT * FROM instruments WHERE instrument_type LIKE '%ETF%' OR symbol LIKE '%ETF%'"
        cur = self.conn.execute(query)
        return [dict(x) for x in cur.fetchall()]

    def clear_all(self):
        self.conn.execute("DELETE FROM instruments")
        self.conn.commit()

    def get_all_symbols(self, segment=None):
        if segment:
            cur = self.conn.execute("SELECT DISTINCT symbol FROM instruments WHERE segment=?", (segment,))
        else:
            cur = self.conn.execute("SELECT DISTINCT symbol FROM instruments")
        return [x["symbol"] for x in cur.fetchall() if x["symbol"]]

    def save_signal(self, sig):
        self.conn.execute("""
        INSERT OR REPLACE INTO trade_signals (
            symbol, signal_type, direction, entry, target, stoploss, score, reason, timestamp, expected_days, trigger_candle_time
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            sig.get("symbol"), sig.get("signal_type"), sig.get("direction"),
            str(sig.get("entry")), str(sig.get("target")), str(sig.get("stoploss")),
            float(sig.get("score", 50.0)), sig.get("reason"), sig.get("timestamp"),
            sig.get("expected_days"), sig.get("trigger_candle_time")
        ))
        self.conn.commit()

    def get_signals(self, signal_type, limit=25):
        cur = self.conn.execute("""
        SELECT symbol, direction as type, direction, entry, target, stoploss, score, reason, timestamp, expected_days, trigger_candle_time
        FROM trade_signals
        WHERE signal_type=?
        ORDER BY score DESC
        LIMIT ?
        """, (signal_type, limit))
        rows = [dict(x) for x in cur.fetchall()]
        from historical import fetch_realtime_nse_price
        for r in rows:
            sym = r.get("symbol", "")
            base_sym = sym.split("-")[0].split(" ")[0].strip()
            info = self.get_instrument_info(base_sym)
            cname = info.get("name") if info else base_sym
            if not cname or cname == base_sym:
                cname = base_sym
            r["company_name"] = cname
            r["display_name"] = f"{sym} - {cname}" if cname != sym else sym
            
            # LTP
            try:
                live_p = fetch_realtime_nse_price(base_sym)
                r["ltp"] = round(float(live_p), 2) if live_p else (float(r.get("entry", 0)) if str(r.get("entry", "")).replace(".", "").isdigit() else 0.0)
            except Exception:
                r["ltp"] = float(r.get("entry", 0)) if str(r.get("entry", "")).replace(".", "").isdigit() else 0.0
        return rows

    def get_paper_balance(self) -> float:
        cur = self.conn.execute("SELECT value FROM paper_profile WHERE key='balance'")
        row = cur.fetchone()
        return float(row["value"]) if row else 1000000.0

    def update_paper_balance(self, amount: float):
        self.conn.execute("""
        INSERT OR REPLACE INTO paper_profile (key, value)
        VALUES ('balance', ?)
        """, (str(amount),))
        self.conn.commit()

    def add_paper_trade(self, symbol: str, direction: str, qty: int, entry_price: float, target: float, stoploss: float) -> int:
        from datetime import datetime
        cur = self.conn.execute("""
        INSERT INTO paper_portfolio (
            symbol, direction, qty, entry_price, target_price, stoploss_price, status, entry_time
        ) VALUES (?,?,?,?,?,?,?,?)
        """, (symbol, direction, qty, entry_price, target, stoploss, "ACTIVE", datetime.now().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def get_active_paper_trades(self):
        cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE status='ACTIVE' ORDER BY entry_time DESC")
        return [dict(x) for x in cur.fetchall()]

    def get_closed_paper_trades(self):
        cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE status <> 'ACTIVE' ORDER BY exit_time DESC")
        return [dict(x) for x in cur.fetchall()]

    def close_paper_trade(self, trade_id: int, exit_price: float, status: str = "CLOSED"):
        from datetime import datetime
        cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE id=?", (trade_id,))
        trade = cur.fetchone()
        if not trade:
            return False
        
        qty = trade["qty"]
        entry_price = trade["entry_price"]
        direction = trade["direction"]
        
        if direction == "BUY":
            pnl = (exit_price - entry_price) * qty
        else:
            pnl = (entry_price - exit_price) * qty
            
        self.conn.execute("""
        UPDATE paper_portfolio
        SET status=?, exit_time=?, exit_price=?, pnl=?
        WHERE id=?
        """, (status, datetime.now().isoformat(), exit_price, pnl, trade_id))
        
        current_balance = self.get_paper_balance()
        margin_locked = entry_price * qty
        new_balance = current_balance + margin_locked + pnl
        self.update_paper_balance(new_balance)
        self.conn.commit()
        return True

    def reset_paper_trading(self):
        self.conn.execute("DELETE FROM paper_portfolio")
        self.conn.execute("INSERT OR REPLACE INTO paper_profile (key, value) VALUES ('balance', '1000000')")
        self.conn.commit()

    def close(self):
        self.conn.close()


db = ScripDatabase()