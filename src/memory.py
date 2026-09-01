import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class Memory:
    def __init__(self, config):
        db_path = Path(config.get("db_path", "logs/memory.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_transmissions = config.get("max_transmissions", 1000)
        self.context_window = config.get("context_window", 20)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()
        log.info("memory db: %s", db_path)

    def _init_schema(self):
        c = self._conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS transmissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent TEXT,
                metadata TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                sensor_distance REAL,
                expression TEXT,
                image_hash TEXT,
                notes TEXT
            )
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_tx_ts ON transmissions(ts)
        """)
        self._conn.commit()

    def record(self, role: str, content: str, agent: str = None, metadata: dict = None):
        ts = time.time()
        meta_str = json.dumps(metadata) if metadata else None
        c = self._conn.cursor()
        c.execute(
            "INSERT INTO transmissions (ts, role, content, agent, metadata) VALUES (?,?,?,?,?)",
            (ts, role, content, agent, meta_str),
        )
        self._conn.commit()
        self._prune_transmissions()

    def _prune_transmissions(self):
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*) FROM transmissions")
        count = c.fetchone()[0]
        if count > self.max_transmissions:
            excess = count - self.max_transmissions
            c.execute(
                "DELETE FROM transmissions WHERE id IN "
                "(SELECT id FROM transmissions ORDER BY ts ASC LIMIT ?)",
                (excess,),
            )
            self._conn.commit()

    def get_context(self, n: Optional[int] = None) -> list:
        n = n or self.context_window
        c = self._conn.cursor()
        c.execute(
            "SELECT role, content, agent, ts FROM transmissions "
            "ORDER BY ts DESC LIMIT ?",
            (n,),
        )
        rows = c.fetchall()
        rows.reverse()
        return [
            {"role": r[0], "content": r[1], "agent": r[2], "ts": r[3]}
            for r in rows
        ]

    def record_observation(self, sensor_distance: float = None, expression: str = None,
                           image_hash: str = None, notes: str = None):
        ts = time.time()
        c = self._conn.cursor()
        c.execute(
            "INSERT INTO observations (ts, sensor_distance, expression, image_hash, notes) "
            "VALUES (?,?,?,?,?)",
            (ts, sensor_distance, expression, image_hash, notes),
        )
        self._conn.commit()

    def get_recent_observations(self, n: int = 10) -> list:
        c = self._conn.cursor()
        c.execute(
            "SELECT ts, sensor_distance, expression, image_hash, notes "
            "FROM observations ORDER BY ts DESC LIMIT ?",
            (n,),
        )
        rows = c.fetchall()
        return [
            {"ts": r[0], "sensor_distance": r[1], "expression": r[2],
             "image_hash": r[3], "notes": r[4]}
            for r in rows
        ]

    def close(self):
        if self._conn:
            self._conn.close()

    def search(self, query: str, limit: int = 10) -> list:
        c = self._conn.cursor()
        c.execute(
            "SELECT role, content, agent, ts FROM transmissions "
            "WHERE content LIKE ? ORDER BY ts DESC LIMIT ?",
            (f"%{query}%", limit),
        )
        return [{"role": r[0], "content": r[1], "agent": r[2], "ts": r[3]} for r in c.fetchall()]

    def count(self) -> int:
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*) FROM transmissions")
        return c.fetchone()[0]
