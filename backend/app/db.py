from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS layers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    provider TEXT NOT NULL DEFAULT 'procedural',
    default_scheme TEXT NOT NULL DEFAULT 'xyz',
    min_z INTEGER NOT NULL DEFAULT 0,
    max_z INTEGER NOT NULL DEFAULT 3,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_slug TEXT NOT NULL,
    scheme TEXT NOT NULL,
    requested_max_z INTEGER,
    max_z_cap INTEGER,
    max_z INTEGER NOT NULL,
    status TEXT NOT NULL,
    total INTEGER NOT NULL DEFAULT 0,
    missing INTEGER NOT NULL DEFAULT 0,
    y_flip INTEGER NOT NULL DEFAULT 0,
    meta_missing INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    finished_at TEXT,
    FOREIGN KEY (layer_slug) REFERENCES layers(slug)
);

CREATE TABLE IF NOT EXISTS scan_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    z INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES scan_runs(id)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_slug TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    result TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    finished_at TEXT,
    FOREIGN KEY (layer_slug) REFERENCES layers(slug)
);

CREATE TABLE IF NOT EXISTS repair_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_slug TEXT NOT NULL,
    z INTEGER NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """老库补列：scan_runs 早期只有实际 max_z，没有请求值/上限可核对字段。"""
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(scan_runs)")}
    for column in ("requested_max_z", "max_z_cap"):
        if column not in existing:
            conn.execute(f"ALTER TABLE scan_runs ADD COLUMN {column} INTEGER")


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()


@contextmanager
def session(db_path: Path):
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)
