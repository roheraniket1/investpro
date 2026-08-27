"""
cloud_sync.py
Permanent Cloudflare KV Storage Sync for InvestPro User Accounts & Portfolios.
Ensures zero data loss across Render deployments, container restarts, and device switches.
"""

import json
import logging
import threading
import urllib.request
from typing import Dict, List, Optional

logger = logging.getLogger("CloudSync")

from config import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CLOUDFLARE_KV_NAMESPACE_ID

KV_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/storage/kv/namespaces/{CLOUDFLARE_KV_NAMESPACE_ID}/values"


class CloudKVSync:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }

    def _kv_put(self, key: str, value_str: str) -> bool:
        """Write key-value to Cloudflare KV."""
        url = f"{KV_BASE}/{key}"
        try:
            req = urllib.request.Request(url, data=value_str.encode("utf-8"), headers=self.headers, method="PUT")
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("success", False)
        except Exception as e:
            logger.error(f"Cloudflare KV PUT error for {key}: {e}")
            return False

    def _kv_get(self, key: str) -> Optional[str]:
        """Read key-value from Cloudflare KV."""
        url = f"{KV_BASE}/{key}"
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as he:
            if he.code == 404:
                return None
            logger.error(f"Cloudflare KV GET HTTP error for {key}: {he}")
            return None
        except Exception as e:
            logger.error(f"Cloudflare KV GET error for {key}: {e}")
            return None

    def async_backup_all_user_data(self, db_conn):
        """Run full database user backup to Cloudflare KV in background thread."""
        threading.Thread(target=self._backup_worker, args=(db_conn,), daemon=True).start()

    def _backup_worker(self, db_conn):
        try:
            # 1. Backup users table
            cur = db_conn.execute("SELECT id, mobile, password_hash, salt, full_name, created_at, last_login, is_active FROM users")
            users = [dict(x) for x in cur.fetchall()]
            if users:
                self._kv_put("users_manifest", json.dumps(users))

            # 2. Backup user_profiles table
            cur = db_conn.execute("SELECT user_id, virtual_balance, initial_capital, watchlist, custom_settings, updated_at FROM user_profiles")
            profiles = [dict(x) for x in cur.fetchall()]
            if profiles:
                self._kv_put("profiles_manifest", json.dumps(profiles))

            # 3. Backup paper_portfolio table
            cur = db_conn.execute("SELECT id, user_id, symbol, direction, qty, entry_price, target_price, stoploss_price, status, entry_time, exit_time, exit_price, pnl FROM paper_portfolio")
            trades = [dict(x) for x in cur.fetchall()]
            if trades:
                self._kv_put("trades_manifest", json.dumps(trades))

            logger.info(f"✅ Cloudflare KV Backup completed: {len(users)} users, {len(profiles)} profiles, {len(trades)} trades.")
        except Exception as e:
            logger.error(f"Cloudflare KV backup worker error: {e}")

    def restore_all_user_data_to_db(self, db_conn):
        """Restore all users, profiles, and trade history from Cloudflare KV into SQLite on startup."""
        try:
            # 1. Restore Users
            raw_users = self._kv_get("users_manifest")
            if raw_users:
                users = json.loads(raw_users)
                for u in users:
                    db_conn.execute("""
                    INSERT OR REPLACE INTO users (id, mobile, password_hash, salt, full_name, created_at, last_login, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u.get("id"), u.get("mobile"), u.get("password_hash"), u.get("salt"),
                        u.get("full_name"), u.get("created_at"), u.get("last_login"), u.get("is_active", 1)
                    ))
                db_conn.commit()
                logger.info(f"✅ Restored {len(users)} registered users from Cloudflare KV store.")

            # 2. Restore User Profiles
            raw_profiles = self._kv_get("profiles_manifest")
            if raw_profiles:
                profiles = json.loads(raw_profiles)
                for p in profiles:
                    db_conn.execute("""
                    INSERT OR REPLACE INTO user_profiles (user_id, virtual_balance, initial_capital, watchlist, custom_settings, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        p.get("user_id"), float(p.get("virtual_balance", 1000000.0)),
                        float(p.get("initial_capital", 1000000.0)), str(p.get("watchlist")),
                        str(p.get("custom_settings", "{}")), p.get("updated_at")
                    ))
                db_conn.commit()
                logger.info(f"✅ Restored {len(profiles)} user profiles from Cloudflare KV store.")

            # 3. Restore Paper Portfolio Trades
            raw_trades = self._kv_get("trades_manifest")
            if raw_trades:
                trades = json.loads(raw_trades)
                for t in trades:
                    db_conn.execute("""
                    INSERT OR REPLACE INTO paper_portfolio (id, user_id, symbol, direction, qty, entry_price, target_price, stoploss_price, status, entry_time, exit_time, exit_price, pnl)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        t.get("id"), t.get("user_id", 1), t.get("symbol"), t.get("direction"),
                        t.get("qty"), t.get("entry_price"), t.get("target_price"), t.get("stoploss_price"),
                        t.get("status"), t.get("entry_time"), t.get("exit_time"), t.get("exit_price"),
                        t.get("pnl", 0.0)
                    ))
                db_conn.commit()
                logger.info(f"✅ Restored {len(trades)} paper trades from Cloudflare KV store.")

        except Exception as e:
            logger.error(f"Failed to restore user data from Cloudflare KV: {e}")


cloud_kv = CloudKVSync()
