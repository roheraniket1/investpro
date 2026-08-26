"""
database.py
SQLite Database for Kotak Neo Scrip Master, Trade Signals, Multi-User Auth, and Paper Portfolios
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import DATABASE_PATH
from auth_user import hash_password, verify_password, generate_session_token, sanitize_mobile

Path("data").mkdir(exist_ok=True)


class ScripDatabase:

    def __init__(self):
        # Auto-unpack 160,000+ instrument master seed if database is missing or empty
        from pathlib import Path
        db_file = Path(DATABASE_PATH)
        seed_file = Path("data/scrip_master_seed.db.gz")
        if (not db_file.exists() or db_file.stat().st_size == 0) and seed_file.exists():
            import gzip, shutil
            try:
                Path("data").mkdir(exist_ok=True)
                with gzip.open(seed_file, 'rb') as f_in:
                    with open(db_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            except Exception as e:
                pass

        self.conn = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row

        # Verify instruments count - if 0 and seed exists, unpack
        try:
            cur = self.conn.execute("SELECT count(*) as c FROM instruments")
            if cur.fetchone()["c"] == 0 and seed_file.exists():
                self.conn.close()
                import gzip, shutil
                with gzip.open(seed_file, 'rb') as f_in:
                    with open(db_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
                self.conn.row_factory = sqlite3.Row
        except Exception:
            pass

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
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_trading_symbol ON instruments (trading_symbol)")
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
            
        # Multi-User Authentication Tables
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TEXT,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_users_mobile ON users (mobile)")

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            virtual_balance REAL DEFAULT 1000000.0,
            initial_capital REAL DEFAULT 1000000.0,
            watchlist TEXT DEFAULT '["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"]',
            custom_settings TEXT DEFAULT '{}',
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT,
            expires_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
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
        try:
            self.conn.execute("ALTER TABLE paper_portfolio ADD COLUMN user_id INTEGER DEFAULT 1")
        except Exception:
            pass
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_paper_user ON paper_portfolio (user_id)")

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS paper_profile (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        self.conn.execute("INSERT OR IGNORE INTO paper_profile (key, value) VALUES ('balance', '1000000')")
        self.conn.commit()

    # ---------------- USER AUTHENTICATION & PROFILE METHODS ---------------- #

    def register_user(self, mobile: str, password: str, full_name: str) -> Tuple[bool, str, Optional[Dict]]:
        """Register a new user with 10-digit mobile number and password."""
        clean_mob = sanitize_mobile(mobile)
        if not clean_mob:
            return False, "Invalid mobile number. Please enter a valid 10-digit Indian mobile number.", None
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters long.", None
        name = (full_name or "").strip() or f"Trader {clean_mob[-4:]}"

        # Check if already exists
        cur = self.conn.execute("SELECT id FROM users WHERE mobile=?", (clean_mob,))
        if cur.fetchone():
            return False, f"Account with mobile number {clean_mob} already exists. Please Sign In.", None

        pw_hash, salt = hash_password(password)
        now_str = datetime.now().isoformat()
        try:
            cur = self.conn.execute("""
            INSERT INTO users (mobile, password_hash, salt, full_name, created_at, last_login, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (clean_mob, pw_hash, salt, name, now_str, now_str))
            user_id = cur.lastrowid

            # Create default user profile with ₹10,00,000 initial capital
            default_wl = json.dumps(["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"])
            self.conn.execute("""
            INSERT INTO user_profiles (user_id, virtual_balance, initial_capital, watchlist, custom_settings, updated_at)
            VALUES (?, 1000000.0, 1000000.0, ?, '{}', ?)
            """, (user_id, default_wl, now_str))

            # Generate session token
            token, expires_at = generate_session_token()
            self.conn.execute("""
            INSERT INTO user_sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """, (token, user_id, now_str, expires_at))

            self.conn.commit()

            user_data = {
                "id": user_id,
                "mobile": clean_mob,
                "full_name": name,
                "virtual_balance": 1000000.0,
                "initial_capital": 1000000.0,
                "watchlist": ["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"],
                "token": token
            }
            return True, "Account created successfully!", user_data
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None

    def authenticate_user(self, mobile: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Verify user login with mobile number and password."""
        clean_mob = sanitize_mobile(mobile)
        if not clean_mob:
            return False, "Invalid mobile number. Please enter a valid 10-digit number.", None

        cur = self.conn.execute("SELECT * FROM users WHERE mobile=?", (clean_mob,))
        user = cur.fetchone()
        if not user:
            return False, "No account found with this mobile number. Please Create an Account first.", None

        if not user["is_active"]:
            return False, "Account is disabled. Please contact support.", None

        if not verify_password(password, user["password_hash"], user["salt"]):
            return False, "Incorrect password. Please try again.", None

        user_id = user["id"]
        now_str = datetime.now().isoformat()

        # Update last login
        self.conn.execute("UPDATE users SET last_login=? WHERE id=?", (now_str, user_id))

        # Generate new session token
        token, expires_at = generate_session_token()
        self.conn.execute("""
        INSERT INTO user_sessions (token, user_id, created_at, expires_at)
        VALUES (?, ?, ?, ?)
        """, (token, user_id, now_str, expires_at))
        self.conn.commit()

        # Fetch profile
        profile = self.get_user_profile(user_id)
        user_data = {
            "id": user_id,
            "mobile": user["mobile"],
            "full_name": user["full_name"],
            "virtual_balance": profile.get("virtual_balance", 1000000.0),
            "initial_capital": profile.get("initial_capital", 1000000.0),
            "watchlist": profile.get("watchlist", []),
            "token": token
        }
        return True, "Login successful!", user_data

    def get_user_by_token(self, token: str) -> Optional[Dict]:
        """Validate session token and return user details with profile."""
        if not token:
            return None
        cur = self.conn.execute("""
        SELECT u.id, u.mobile, u.full_name, u.created_at, u.last_login, s.expires_at
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        """, (token,))
        row = cur.fetchone()
        if not row:
            return None

        # Check expiration
        try:
            exp = datetime.fromisoformat(row["expires_at"])
            if exp < datetime.utcnow():
                self.delete_session(token)
                return None
        except Exception:
            pass

        user_id = row["id"]
        profile = self.get_user_profile(user_id)
        return {
            "id": user_id,
            "mobile": row["mobile"],
            "full_name": row["full_name"],
            "created_at": row["created_at"],
            "last_login": row["last_login"],
            "virtual_balance": profile.get("virtual_balance", 1000000.0),
            "initial_capital": profile.get("initial_capital", 1000000.0),
            "watchlist": profile.get("watchlist", []),
            "custom_settings": profile.get("custom_settings", {})
        }

    def delete_session(self, token: str) -> bool:
        """Logout: invalidate session token."""
        self.conn.execute("DELETE FROM user_sessions WHERE token=?", (token,))
        self.conn.commit()
        return True

    def get_user_profile(self, user_id: int) -> Dict:
        """Fetch user profile (balance, watchlist, settings)."""
        cur = self.conn.execute("SELECT * FROM user_profiles WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            # Create default if missing
            default_wl = json.dumps(["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"])
            self.conn.execute("""
            INSERT OR IGNORE INTO user_profiles (user_id, virtual_balance, initial_capital, watchlist, custom_settings, updated_at)
            VALUES (?, 1000000.0, 1000000.0, ?, '{}', ?)
            """, (user_id, default_wl, datetime.now().isoformat()))
            self.conn.commit()
            return {
                "virtual_balance": 1000000.0,
                "initial_capital": 1000000.0,
                "watchlist": ["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"],
                "custom_settings": {}
            }

        try:
            wl = json.loads(row["watchlist"]) if row["watchlist"] else []
        except Exception:
            wl = ["NIFTY 50", "RELIANCE", "TATASTEEL", "HDFCBANK", "INFY"]

        try:
            settings = json.loads(row["custom_settings"]) if row["custom_settings"] else {}
        except Exception:
            settings = {}

        return {
            "virtual_balance": float(row["virtual_balance"] or 1000000.0),
            "initial_capital": float(row["initial_capital"] or 1000000.0),
            "watchlist": wl,
            "custom_settings": settings
        }

    def update_user_profile(self, user_id: int, balance: Optional[float] = None,
                            watchlist: Optional[List[str]] = None,
                            custom_settings: Optional[Dict] = None) -> bool:
        """Auto-save user balance, watchlist, or preferences."""
        current = self.get_user_profile(user_id)
        new_balance = balance if balance is not None else current["virtual_balance"]
        new_wl = json.dumps(watchlist) if watchlist is not None else json.dumps(current["watchlist"])
        new_settings = json.dumps(custom_settings) if custom_settings is not None else json.dumps(current["custom_settings"])

        self.conn.execute("""
        INSERT INTO user_profiles (user_id, virtual_balance, initial_capital, watchlist, custom_settings, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            virtual_balance=excluded.virtual_balance,
            watchlist=excluded.watchlist,
            custom_settings=excluded.custom_settings,
            updated_at=excluded.updated_at
        """, (user_id, new_balance, current["initial_capital"], new_wl, new_settings, datetime.now().isoformat()))
        self.conn.commit()
        return True

    # ---------------- INSTRUMENTS & SEARCH METHODS ---------------- #

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

        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)

        """, (

            item.get("token"),
            item.get("symbol"),
            item.get("trading_symbol"),
            item.get("name"),
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

    def insert_batch(self, items):

        self.conn.executemany("""

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

        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)

        """, [
            (
                item.get("token"),
                item.get("symbol"),
                item.get("trading_symbol"),
                item.get("name"),
                item.get("exchange"),
                item.get("segment"),
                item.get("instrument_type"),
                item.get("expiry"),
                item.get("strike"),
                item.get("option_type"),
                item.get("lot_size"),
                item.get("tick_size"),
                item.get("isin")
            )
            for item in items
        ])

        self.conn.commit()

    def search_symbol(self, query, limit=10):
        # Prefer exact match or starting with query
        cur = self.conn.execute("""
        SELECT symbol, name, trading_symbol, exchange, instrument_type, token, lot_size
        FROM instruments
        WHERE symbol = ? COLLATE NOCASE
           OR symbol LIKE ?
           OR trading_symbol LIKE ?
           OR name LIKE ?
        ORDER BY
            CASE
                WHEN symbol = ? COLLATE NOCASE THEN 1
                WHEN symbol LIKE ? THEN 2
                WHEN trading_symbol LIKE ? THEN 3
                ELSE 4
            END,
            CASE WHEN exchange = 'NSE' THEN 1 WHEN exchange = 'BSE' THEN 2 ELSE 3 END
        LIMIT ?
        """, (query, f"{query}%", f"{query}%", f"%{query}%", query, f"{query}%", f"{query}%", limit))
        return [dict(x) for x in cur.fetchall()]

    def search_instruments(self, query: str, limit: int = 15, category: str = None) -> list:
        q = query.strip()
        if not q:
            return []
        
        # Build category filter clause if requested
        cat_filter = ""
        cat_params = []
        if category:
            cat = category.lower().strip()
            if cat in ['stock', 'equity', 'eq']:
                cat_filter = "AND (instrument_type IN ('EQ', 'EQUITY') OR segment = 'CASH' OR segment = 'EQUITY')"
            elif cat in ['commodity', 'mcx']:
                cat_filter = "AND (exchange = 'MCX' OR segment = 'COMMODITY')"
            elif cat in ['index', 'indices', 'idx']:
                cat_filter = "AND (instrument_type IN ('INDEX', 'INDICES') OR segment = 'INDEX')"
            elif cat in ['option', 'options', 'opt']:
                cat_filter = "AND (instrument_type IN ('OPTIDX', 'OPTSTK', 'OPTCUR', 'OPTCOM', 'CE', 'PE') OR option_type IN ('CE', 'PE'))"
            elif cat in ['future', 'futures', 'fut']:
                cat_filter = "AND (instrument_type IN ('FUTIDX', 'FUTSTK', 'FUTCUR', 'FUTCOM', 'FUT'))"
        
        base_query = f"""
        SELECT token, symbol, trading_symbol, name, exchange, segment, instrument_type, expiry, strike, option_type, lot_size, tick_size
        FROM instruments
        WHERE (
            symbol LIKE ? 
            OR trading_symbol LIKE ? 
            OR name LIKE ?
        )
        {cat_filter}
        ORDER BY 
            CASE 
                WHEN symbol = ? COLLATE NOCASE THEN 1
                WHEN trading_symbol = ? COLLATE NOCASE THEN 2
                WHEN symbol LIKE ? THEN 3
                WHEN trading_symbol LIKE ? THEN 4
                WHEN name LIKE ? THEN 5
                ELSE 6
            END,
            CASE 
                WHEN exchange = 'NSE' THEN 1
                WHEN exchange = 'MCX' THEN 2
                WHEN exchange = 'BSE' THEN 3
                ELSE 4
            END
        LIMIT ?
        """
        
        prefix = f"{q}%"
        contains = f"%{q}%"
        params = [contains, contains, contains] + cat_params + [q, q, prefix, prefix, prefix, limit]
        
        cur = self.conn.execute(base_query, tuple(params))
        rows = [dict(x) for x in cur.fetchall()]
        
        # Add rich display badge metadata
        for r in rows:
            inst_type = (r.get("instrument_type") or "").upper()
            opt_type = (r.get("option_type") or "").upper()
            exch = (r.get("exchange") or "").upper()
            
            if exch == "MCX":
                r["category_badge"] = "🛢️ MCX"
                r["category"] = "COMMODITY"
            elif opt_type in ["CE", "PE"] or inst_type in ["OPTIDX", "OPTSTK", "OPTCUR", "OPTCOM"]:
                r["category_badge"] = f"🎯 {opt_type or 'OPT'}"
                r["category"] = "OPTION"
            elif "FUT" in inst_type:
                r["category_badge"] = "⚡ FUT"
                r["category"] = "FUTURE"
            elif inst_type in ["INDEX", "INDICES"]:
                r["category_badge"] = "📊 INDEX"
                r["category"] = "INDEX"
            else:
                r["category_badge"] = "📈 EQ"
                r["category"] = "EQUITY"
                
        return rows

    def get_token(self, symbol, exchange=None):
        query = "SELECT token FROM instruments WHERE (symbol = ? OR trading_symbol = ?)"
        params = [symbol, symbol]
        if exchange:
            query += " AND exchange = ?"
            params.append(exchange)
        query += " LIMIT 1"
        cur = self.conn.execute(query, tuple(params))
        row = cur.fetchone()
        return row["token"] if row else None

    def get_instrument_info(self, symbol, exchange=None):
        query = "SELECT * FROM instruments WHERE (symbol = ? OR trading_symbol = ?)"
        params = [symbol, symbol]
        if exchange:
            query += " AND exchange = ?"
            params.append(exchange)
        query += " LIMIT 1"
        cur = self.conn.execute(query, tuple(params))
        row = cur.fetchone()
        return dict(row) if row else None

    def count(self):

        cur = self.conn.execute("SELECT COUNT(*) as total FROM instruments")
        return cur.fetchone()["total"]

    # ---------------- SIGNALS METHODS ---------------- #

    def save_signal(self, sig: dict):
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

    # ---------------- PER-USER PAPER TRADING METHODS ---------------- #

    def get_paper_balance(self, user_id: int = 1) -> float:
        profile = self.get_user_profile(user_id)
        return profile.get("virtual_balance", 1000000.0)

    def update_paper_balance(self, amount: float, user_id: int = 1):
        self.update_user_profile(user_id, balance=amount)

    def add_paper_trade(self, symbol: str, direction: str, qty: int, entry_price: float,
                        target: float, stoploss: float, user_id: int = 1) -> int:
        cur = self.conn.execute("""
        INSERT INTO paper_portfolio (
            user_id, symbol, direction, qty, entry_price, target_price, stoploss_price, status, entry_time
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """, (user_id, symbol, direction, qty, entry_price, target, stoploss, "ACTIVE", datetime.now().isoformat()))
        self.conn.commit()
        return cur.lastrowid

    def get_active_paper_trades(self, user_id: Optional[int] = None):
        if user_id is not None:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE user_id=? AND status='ACTIVE' ORDER BY entry_time DESC", (user_id,))
        else:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE status='ACTIVE' ORDER BY entry_time DESC")
        return [dict(x) for x in cur.fetchall()]

    def get_closed_paper_trades(self, user_id: Optional[int] = None):
        if user_id is not None:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE user_id=? AND status <> 'ACTIVE' ORDER BY exit_time DESC", (user_id,))
        else:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE status <> 'ACTIVE' ORDER BY exit_time DESC")
        return [dict(x) for x in cur.fetchall()]

    def close_paper_trade(self, trade_id: int, exit_price: float, status: str = "CLOSED", user_id: Optional[int] = None):
        if user_id is not None:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE id=? AND user_id=?", (trade_id, user_id))
        else:
            cur = self.conn.execute("SELECT * FROM paper_portfolio WHERE id=?", (trade_id,))
        trade = cur.fetchone()
        if not trade:
            return False
        
        trade_user_id = trade["user_id"] or 1
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
        
        current_balance = self.get_paper_balance(trade_user_id)
        margin_locked = entry_price * qty
        new_balance = current_balance + margin_locked + pnl
        self.update_paper_balance(new_balance, trade_user_id)
        self.conn.commit()
        return True

    def reset_paper_trading(self, user_id: int = 1):
        self.conn.execute("DELETE FROM paper_portfolio WHERE user_id=?", (user_id,))
        self.update_paper_balance(1000000.0, user_id)
        self.conn.commit()

    def close(self):
        self.conn.close()


db = ScripDatabase()
