import csv
import os
import sqlite3
from typing import Optional

from repositories.business_repository import UsageRecordRow
from utils.config_handler import business_conf
from utils.path_tool import get_abs_path


class SQLiteBusinessRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_abs_path(business_conf["database_path"])
        self.seed_csv_path = get_abs_path(business_conf["seed_csv_path"])
        self._ensure_parent_dir()
        self._initialize_database()
        self._seed_if_needed()

    def _ensure_parent_dir(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_database(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_records (
                    user_id TEXT NOT NULL,
                    month TEXT NOT NULL,
                    feature TEXT NOT NULL,
                    efficiency TEXT NOT NULL,
                    consumables TEXT NOT NULL,
                    comparison TEXT NOT NULL,
                    PRIMARY KEY (user_id, month)
                )
                """
            )
            conn.commit()

    def _seed_if_needed(self) -> None:
        with self._connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0]
            if count > 0:
                return

        self.import_seed_data()

    def import_seed_data(self) -> None:
        with open(self.seed_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            rows = []
            for row in reader:
                if len(row) < 6:
                    continue
                rows.append((row[0], row[5], row[1], row[2], row[3], row[4]))

        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO usage_records (
                    user_id, month, feature, efficiency, consumables, comparison
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()

    def list_user_ids(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT user_id FROM usage_records ORDER BY user_id"
            ).fetchall()
        return [row["user_id"] for row in rows]

    def list_available_months(self, user_id: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT month FROM usage_records WHERE user_id = ? ORDER BY month",
                (user_id,),
            ).fetchall()
        return [row["month"] for row in rows]

    def get_usage_record(self, user_id: str, month: str) -> Optional[UsageRecordRow]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, month, feature, efficiency, consumables, comparison
                FROM usage_records
                WHERE user_id = ? AND month = ?
                """,
                (user_id, month),
            ).fetchone()
        return self._row_to_usage_record(row)

    def get_latest_usage_record(self, user_id: str) -> Optional[UsageRecordRow]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, month, feature, efficiency, consumables, comparison
                FROM usage_records
                WHERE user_id = ?
                ORDER BY month DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_usage_record(row)

    @staticmethod
    def _row_to_usage_record(row: sqlite3.Row | None) -> Optional[UsageRecordRow]:
        if row is None:
            return None
        return UsageRecordRow(
            user_id=row["user_id"],
            month=row["month"],
            feature=row["feature"],
            efficiency=row["efficiency"],
            consumables=row["consumables"],
            comparison=row["comparison"],
        )
