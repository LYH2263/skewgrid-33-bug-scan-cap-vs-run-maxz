from pathlib import Path

from app.config import SCAN_MAX_Z_CAP_DEFAULT
from app.db import init_db, session
from app.store import (
    create_layer,
    get_scan,
    resolve_scan_cap,
    run_scan,
    set_setting,
)


def _layer(db: Path, slug: str = "demo-grid", max_z: int = 5) -> None:
    create_layer(
        db,
        {"slug": slug, "name": slug, "max_z": max_z},
    )


def test_cap_defaults_when_setting_missing(tmp_path: Path):
    db = tmp_path / "x.db"
    init_db(db)
    assert resolve_scan_cap(db) == SCAN_MAX_Z_CAP_DEFAULT


def test_cap_falls_back_on_garbage(tmp_path: Path):
    db = tmp_path / "x.db"
    init_db(db)
    for bad in ("", "abc", "3.5", "-1", "99"):
        set_setting(db, "scan_max_z_cap", bad)
        assert resolve_scan_cap(db) == SCAN_MAX_Z_CAP_DEFAULT


def test_run_scan_clamped_to_cap(tmp_path: Path):
    db = tmp_path / "x.db"
    data = tmp_path / "data"
    init_db(db)
    _layer(db, max_z=5)
    set_setting(db, "scan_max_z_cap", "2")

    run = run_scan(db, data, "demo-grid", "xyz", 5)

    assert run["requested_max_z"] == 5
    assert run["max_z_cap"] == 2
    assert run["max_z"] == 2


def test_run_scan_layer_max_z_is_ceiling(tmp_path: Path):
    db = tmp_path / "x.db"
    data = tmp_path / "data"
    init_db(db)
    _layer(db, max_z=1)
    set_setting(db, "scan_max_z_cap", "6")

    run = run_scan(db, data, "demo-grid", "xyz", 6)

    assert run["max_z_cap"] == 6
    assert run["max_z"] == 1


def test_run_scan_uses_safe_default_cap(tmp_path: Path):
    db = tmp_path / "x.db"
    data = tmp_path / "data"
    init_db(db)
    _layer(db, max_z=3)

    run = run_scan(db, data, "demo-grid", "xyz", 3)

    assert run["max_z_cap"] == SCAN_MAX_Z_CAP_DEFAULT
    assert run["max_z"] == 3
    persisted = get_scan(db, run["id"])
    assert persisted["requested_max_z"] == 3
    assert persisted["max_z_cap"] == SCAN_MAX_Z_CAP_DEFAULT


def test_init_db_migrates_legacy_scan_runs(tmp_path: Path):
    db = tmp_path / "x.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    with session(db) as conn:
        conn.execute(
            """CREATE TABLE scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_slug TEXT NOT NULL,
                scheme TEXT NOT NULL,
                max_z INTEGER NOT NULL,
                status TEXT NOT NULL,
                total INTEGER NOT NULL DEFAULT 0,
                missing INTEGER NOT NULL DEFAULT 0,
                y_flip INTEGER NOT NULL DEFAULT 0,
                meta_missing INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                finished_at TEXT
            )"""
        )
        conn.execute(
            "INSERT INTO scan_runs (layer_slug, scheme, max_z, status, created_at) "
            "VALUES ('demo-grid', 'xyz', 3, 'done', '2026-01-01T00:00:00+00:00')"
        )

    init_db(db)  # 不应报错，且补出新列

    with session(db) as conn:
        row = conn.execute("SELECT requested_max_z, max_z_cap FROM scan_runs").fetchone()
    assert row["requested_max_z"] is None
    assert row["max_z_cap"] is None
