import sqlite3
from typing import Optional

from . import settings

_conn: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(settings.DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            code        TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            currency    TEXT,
            price_retail  REAL,
            price_dealer  REAL,
            price_partner REAL,
            vat         TEXT,
            section     TEXT,
            date_start  TEXT,
            registry    TEXT,
            comment     TEXT,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
            name,
            code UNINDEXED,
            content='products',
            content_rowid='rowid',
            tokenize='unicode61'
        );
    """)
    conn.commit()


def replace_all(products: list[dict]) -> int:
    conn = get_conn()
    with conn:
        conn.execute("DELETE FROM products")
        conn.executemany(
            """INSERT INTO products
               (code, name, currency, price_retail, price_dealer, price_partner,
                vat, section, date_start, registry, comment)
               VALUES (:code, :name, :currency, :price_retail, :price_dealer, :price_partner,
                       :vat, :section, :date_start, :registry, :comment)""",
            products,
        )
        conn.execute("INSERT INTO products_fts(products_fts) VALUES('rebuild')")
    return len(products)


def search(query: str, limit: int = 10) -> list[dict]:
    conn = get_conn()

    # Wrap each word in quotes + prefix wildcard for FTS5
    words = [w for w in query.split() if w]
    fts_query = " ".join(f'"{w}"*' for w in words)

    if fts_query:
        try:
            rows = conn.execute(
                """SELECT p.code, p.name, p.currency, p.price_retail, p.vat, p.section
                   FROM products_fts f
                   JOIN products p ON p.rowid = f.rowid
                   WHERE products_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, limit),
            ).fetchall()
            if rows:
                return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            pass

    # LIKE fallback (when FTS returns nothing or query is malformed)
    rows = conn.execute(
        """SELECT code, name, currency, price_retail, vat, section
           FROM products
           WHERE name LIKE ?
           LIMIT ?""",
        (f"%{query}%", limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_by_code(code: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE code = ?", (code,)).fetchone()
    return dict(row) if row else None


def meta() -> dict:
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    updated_at = conn.execute("SELECT MAX(updated_at) FROM products").fetchone()[0]
    return {"count": count, "updated_at": updated_at}
