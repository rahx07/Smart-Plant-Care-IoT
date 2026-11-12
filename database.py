"""SQLite data layer for sensor readings and irrigation events."""
import sqlite3
from datetime import datetime
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "data" / "plant.db"

def connection(path=None):
    db_path = path or DATABASE_PATH
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables(path=None):
    with connection(path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            location TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            soil_moisture REAL NOT NULL CHECK(soil_moisture BETWEEN 0 AND 100),
            pump_on INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(device_id) REFERENCES devices(device_id)
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            FOREIGN KEY(device_id) REFERENCES devices(device_id)
        );
        """)

def add_device(device_id, location, path=None):
    try:
        with connection(path) as conn:
            conn.execute(
                "INSERT INTO devices VALUES (?, ?, ?)",
                (device_id, location, datetime.now().isoformat(timespec="seconds"))
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("A device with this ID already exists.") from exc

def ensure_device(device_id, location, path=None):
    with connection(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO devices VALUES (?, ?, ?)",
            (device_id, location, datetime.now().isoformat(timespec="seconds"))
        )

def add_reading(device_id, temperature, humidity, soil_moisture, pump_on, ts=None, path=None):
    with connection(path) as conn:
        conn.execute(
            """INSERT INTO readings
            (device_id, ts, temperature, humidity, soil_moisture, pump_on)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (device_id, ts or datetime.now().isoformat(timespec="seconds"),
             temperature, humidity, soil_moisture, int(bool(pump_on)))
        )

def latest_reading(device_id, path=None):
    with connection(path) as conn:
        row = conn.execute(
            "SELECT * FROM readings WHERE device_id=? ORDER BY id DESC LIMIT 1",
            (device_id,)
        ).fetchone()
        return dict(row) if row else None

def get_readings(device_id, limit=200, path=None):
    with connection(path) as conn:
        rows = conn.execute(
            "SELECT * FROM readings WHERE device_id=? ORDER BY id DESC LIMIT ?",
            (device_id, limit)
        ).fetchall()
        return [dict(row) for row in rows][::-1]

def log_event(device_id, action, reason, ts=None, path=None):
    with connection(path) as conn:
        conn.execute(
            "INSERT INTO events (device_id, ts, action, reason) VALUES (?, ?, ?, ?)",
            (device_id, ts or datetime.now().isoformat(timespec="seconds"), action, reason)
        )

def get_events(device_id, limit=50, path=None):
    with connection(path) as conn:
        rows = conn.execute(
            "SELECT ts, action, reason FROM events WHERE device_id=? ORDER BY id DESC LIMIT ?",
            (device_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]

def daily_summary(device_id, day, path=None):
    with connection(path) as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS samples,
            ROUND(AVG(temperature),1) AS avg_temp,
            ROUND(AVG(humidity),1) AS avg_humidity,
            ROUND(AVG(soil_moisture),1) AS avg_moisture,
            ROUND(MIN(soil_moisture),1) AS min_moisture
            FROM readings WHERE device_id=? AND substr(ts,1,10)=?""",
            (device_id, day)
        ).fetchone()
        pumps = conn.execute(
            """SELECT COUNT(*) FROM events
            WHERE device_id=? AND action='PUMP_ON' AND substr(ts,1,10)=?""",
            (device_id, day)
        ).fetchone()[0]
        result = dict(row)
        result["pump_cycles"] = pumps
        return result
