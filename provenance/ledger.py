import sqlite3
import pathlib
import uuid
from typing import List, Optional
from .models import ContextItem

DB_PATH = pathlib.Path(__file__).parent.parent / ".tripline" / "provenance.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS context_items (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                trust_level TEXT NOT NULL,
                content TEXT NOT NULL,
                normalized_content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_id ON context_items (run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON context_items (source_type, source_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hash ON context_items (content_hash)")

def record_item(item: ContextItem):
    """Immutable append-only write of a ContextItem to the ledger."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO context_items (
                id, run_id, source_type, source_id, trust_level,
                content, normalized_content, content_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id, item.run_id, item.source_type, item.source_id, item.trust_level,
                item.content, item.normalized_content, item.content_hash, item.created_at
            )
        )

def get_run_context(run_id: str) -> List[ContextItem]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT id, run_id, source_type, source_id, trust_level,
                   content, normalized_content, content_hash, created_at
            FROM context_items
            WHERE run_id = ?
            ORDER BY created_at ASC
            """,
            (run_id,)
        )
        return [ContextItem(*row) for row in cursor.fetchall()]

init_db()
