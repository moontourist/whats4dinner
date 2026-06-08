"""SQLite storage for What's 4 Dinner.

Uses the stdlib sqlite3 module to keep the image small. The database file
lives under DATA_DIR (a mounted volume in Docker) so dinner lists and the
pick history survive container restarts.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import date

DATA_DIR = os.environ.get("DATA_DIR", "/data")
DB_PATH = os.path.join(DATA_DIR, "dinners.db")


@contextmanager
def get_conn():
    """Yield a connection with row access by column name."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables on first run."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dinners (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                active     INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS selections (
                pick_date TEXT PRIMARY KEY,          -- YYYY-MM-DD, one pick per day
                dinner_id INTEGER,
                name      TEXT NOT NULL,             -- denormalised so history survives deletes
                chosen_at TEXT NOT NULL DEFAULT (datetime('now')),
                manual    INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (dinner_id) REFERENCES dinners(id) ON DELETE SET NULL
            );
            """
        )


# ---------------------------------------------------------------------------
# Dinners
# ---------------------------------------------------------------------------

def list_dinners():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM dinners ORDER BY active DESC, name COLLATE NOCASE"
        ).fetchall()
        return [dict(r) for r in rows]


def add_dinner(name: str):
    name = name.strip()
    if not name:
        raise ValueError("Dinner name cannot be empty")
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO dinners (name) VALUES (?)", (name,))
        row = conn.execute(
            "SELECT * FROM dinners WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def update_dinner(dinner_id: int, name=None, active=None):
    sets, params = [], []
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("Dinner name cannot be empty")
        sets.append("name = ?")
        params.append(name)
    if active is not None:
        sets.append("active = ?")
        params.append(1 if active else 0)
    if not sets:
        return get_dinner(dinner_id)
    params.append(dinner_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE dinners SET {', '.join(sets)} WHERE id = ?", params)
    return get_dinner(dinner_id)


def get_dinner(dinner_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM dinners WHERE id = ?", (dinner_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_dinner(dinner_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM dinners WHERE id = ?", (dinner_id,))


# ---------------------------------------------------------------------------
# Selections
# ---------------------------------------------------------------------------

def get_selection(day: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM selections WHERE pick_date = ?", (day,)
        ).fetchone()
        return dict(row) if row else None


def set_selection(day: str, dinner: dict, manual: bool = False):
    """Insert or replace the pick for a given day."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO selections (pick_date, dinner_id, name, chosen_at, manual)
            VALUES (?, ?, ?, datetime('now'), ?)
            ON CONFLICT(pick_date) DO UPDATE SET
                dinner_id = excluded.dinner_id,
                name      = excluded.name,
                chosen_at = excluded.chosen_at,
                manual    = excluded.manual
            """,
            (day, dinner["id"], dinner["name"], 1 if manual else 0),
        )
    return get_selection(day)


def history(limit: int = 30):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM selections ORDER BY pick_date DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def last_pick_name():
    """Name of the most recent pick, used to avoid back-to-back repeats."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT name FROM selections ORDER BY pick_date DESC LIMIT 1"
        ).fetchone()
        return row["name"] if row else None
