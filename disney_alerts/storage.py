"""SQLite persistence for watch requests and availability opportunities."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import AvailabilityOpportunity, WatchRequest, WatchType


SCHEMA = """
CREATE TABLE IF NOT EXISTS watch_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_type TEXT NOT NULL,
    destination TEXT NOT NULL,
    item_name TEXT NOT NULL,
    party_size INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    preferred_time TEXT NOT NULL,
    contact TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id INTEGER NOT NULL,
    watch_type TEXT NOT NULL,
    destination TEXT NOT NULL,
    item_name TEXT NOT NULL,
    available_date TEXT NOT NULL,
    available_time TEXT NOT NULL,
    booking_url TEXT NOT NULL,
    notes TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watch_id) REFERENCES watch_requests(id)
);
"""


class WatchStore:
    """Tiny repository layer around SQLite."""

    def __init__(self, database_path: str | Path = "disney_alerts.db") -> None:
        self.database_path = str(database_path)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def add_watch(self, watch: WatchRequest) -> WatchRequest:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO watch_requests (
                    watch_type, destination, item_name, party_size,
                    start_date, end_date, preferred_time, contact, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    watch.watch_type.value,
                    watch.destination,
                    watch.item_name,
                    watch.party_size,
                    watch.start_date,
                    watch.end_date,
                    watch.preferred_time,
                    watch.contact,
                    int(watch.active),
                ),
            )
            return WatchRequest(id=cursor.lastrowid, **{k: v for k, v in watch.__dict__.items() if k != "id"})

    def list_watches(self) -> list[WatchRequest]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM watch_requests ORDER BY id DESC").fetchall()
        return [self._row_to_watch(row) for row in rows]

    def save_opportunities(self, opportunities: list[AvailabilityOpportunity]) -> None:
        if not opportunities:
            return
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO opportunities (
                    watch_id, watch_type, destination, item_name, available_date,
                    available_time, booking_url, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        opportunity.watch_id,
                        opportunity.watch_type.value,
                        opportunity.destination,
                        opportunity.item_name,
                        opportunity.available_date,
                        opportunity.available_time,
                        opportunity.booking_url,
                        opportunity.notes,
                    )
                    for opportunity in opportunities
                ],
            )

    def list_opportunities(self) -> list[AvailabilityOpportunity]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM opportunities ORDER BY created_at DESC, id DESC").fetchall()
        return [self._row_to_opportunity(row) for row in rows]

    @staticmethod
    def _row_to_watch(row: sqlite3.Row) -> WatchRequest:
        return WatchRequest(
            id=row["id"],
            watch_type=WatchType(row["watch_type"]),
            destination=row["destination"],
            item_name=row["item_name"],
            party_size=row["party_size"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            preferred_time=row["preferred_time"],
            contact=row["contact"],
            active=bool(row["active"]),
        )

    @staticmethod
    def _row_to_opportunity(row: sqlite3.Row) -> AvailabilityOpportunity:
        return AvailabilityOpportunity(
            watch_id=row["watch_id"],
            watch_type=WatchType(row["watch_type"]),
            destination=row["destination"],
            item_name=row["item_name"],
            available_date=row["available_date"],
            available_time=row["available_time"],
            booking_url=row["booking_url"],
            notes=row["notes"],
        )
