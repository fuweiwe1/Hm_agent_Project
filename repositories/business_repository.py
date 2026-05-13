from dataclasses import dataclass
from typing import Optional, Protocol

from schemas.app_models import UsageRecord
from utils.config_handler import business_conf


@dataclass
class UsageRecordRow:
    user_id: str
    month: str
    feature: str
    efficiency: str
    consumables: str
    comparison: str

    def to_usage_record(self) -> UsageRecord:
        return UsageRecord(
            user_id=self.user_id,
            month=self.month,
            feature=self.feature,
            efficiency=self.efficiency,
            consumables=self.consumables,
            comparison=self.comparison,
        )


class BusinessRepository(Protocol):
    def list_user_ids(self) -> list[str]:
        ...

    def list_available_months(self, user_id: str) -> list[str]:
        ...

    def get_usage_record(self, user_id: str, month: str) -> Optional[UsageRecordRow]:
        ...

    def get_latest_usage_record(self, user_id: str) -> Optional[UsageRecordRow]:
        ...


def create_business_repository() -> BusinessRepository:
    provider = business_conf.get("provider", "sqlite").lower()

    if provider == "sqlite":
        from repositories.sqlite_business_repository import SQLiteBusinessRepository

        return SQLiteBusinessRepository()

    if provider == "postgresql":
        from repositories.postgresql_business_repository import PostgreSQLBusinessRepository

        return PostgreSQLBusinessRepository()

    if provider == "http":
        from repositories.http_business_repository import HTTPBusinessRepository

        return HTTPBusinessRepository()

    raise ValueError(f"Unsupported business repository provider: {provider}")
