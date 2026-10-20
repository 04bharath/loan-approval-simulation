import sqlite3
import config

def conn():
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS applications(
          id TEXT PRIMARY KEY, name TEXT, reference TEXT UNIQUE, amount REAL, purpose TEXT,
          status TEXT, reason TEXT, agent_result TEXT, reviewer TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS history(
          id INTEGER PRIMARY KEY AUTOINCREMENT, app_id TEXT, status TEXT, reason TEXT, at TEXT);
        """)
