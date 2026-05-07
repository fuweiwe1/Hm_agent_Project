from typing import Optional

import httpx

from repositories.business_repository import UsageRecordRow
from utils.config_handler import business_conf


class HTTPBusinessRepository:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: Optional[float] = None):
        self.base_url = (base_url or business_conf.get("http_base_url", "")).rstrip("/")
        self.timeout_seconds = timeout_seconds or float(business_conf.get("http_timeout_seconds", 10))
        if not self.base_url:
            raise ValueError("business.http_base_url must be configured when provider=http")

    def list_user_ids(self) -> list[str]:
        return self._get_json("/users")

    def list_available_months(self, user_id: str) -> list[str]:
        return self._get_json(f"/users/{user_id}/months")

    def get_usage_record(self, user_id: str, month: str) -> Optional[UsageRecordRow]:
        data = self._get_json(f"/users/{user_id}/usage-records/{month}", allow_404=True)
        return self._to_usage_record_row(data)

    def get_latest_usage_record(self, user_id: str) -> Optional[UsageRecordRow]:
        data = self._get_json(f"/users/{user_id}/usage-records/latest", allow_404=True)
        return self._to_usage_record_row(data)

    def _get_json(self, path: str, allow_404: bool = False):
        response = httpx.get(f"{self.base_url}{path}", timeout=self.timeout_seconds)
        if allow_404 and response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _to_usage_record_row(data: dict | None) -> Optional[UsageRecordRow]:
        if data is None:
            return None
        return UsageRecordRow(
            user_id=data["user_id"],
            month=data["month"],
            feature=data["feature"],
            efficiency=data["efficiency"],
            consumables=data["consumables"],
            comparison=data["comparison"],
        )
