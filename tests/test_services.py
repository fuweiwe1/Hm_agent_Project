"""Service 层单元测试 — BusinessService + ChatService。"""
import unittest
from unittest.mock import MagicMock

from schemas.app_models import (
    BusinessLookupResult,
    UsageRecord,
    UserContext,
)
from services.business_service import BusinessService
from services.chat_service import ChatService


class TestBusinessService(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = BusinessService(self.repo)
        self.ctx = UserContext(user_id="u001", city="深圳")

    def test_get_current_month_format(self):
        month = self.service.get_current_month()
        self.assertRegex(month, r"^\d{4}-\d{2}$")

    def test_get_weather_known_city(self):
        weather = self.service.get_weather("深圳")
        self.assertEqual(weather.city, "深圳")

    def test_get_weather_unknown_city_fallback(self):
        weather = self.service.get_weather("火星")
        self.assertEqual(weather.city, "火星")

    def test_list_available_months_raises_on_missing_user(self):
        self.repo.list_available_months.return_value = []
        with self.assertRaises(KeyError):
            self.service.list_available_months("nonexistent")

    def test_get_user_profile_raises_on_missing_user(self):
        self.repo.get_latest_usage_record.return_value = None
        with self.assertRaises(KeyError):
            self.service.get_user_profile(self.ctx)

    def test_resolve_usage_record_prefers_preferred_month(self):
        record = MagicMock()
        record.month = "2024-01"
        record.to_usage_record.return_value = UsageRecord(
            user_id="u001", month="2024-01",
            feature="f", efficiency="e", consumables="c", comparison="cmp",
        )
        self.repo.get_usage_record.return_value = record

        result = self.service.resolve_usage_record("u001", preferred_month="2024-01")
        self.assertEqual(result.resolved_month, "2024-01")
        self.assertFalse(result.used_latest_available)

    def test_resolve_usage_record_falls_back_to_latest(self):
        self.repo.get_usage_record.return_value = None
        latest = MagicMock()
        latest.month = "2024-03"
        latest.to_usage_record.return_value = UsageRecord(
            user_id="u001", month="2024-03",
            feature="f", efficiency="e", consumables="c", comparison="cmp",
        )
        self.repo.get_latest_usage_record.return_value = latest

        result = self.service.resolve_usage_record("u001", preferred_month="2024-01")
        self.assertEqual(result.resolved_month, "2024-03")
        self.assertTrue(result.used_latest_available)


class TestChatService(unittest.TestCase):
    def setUp(self):
        self.biz = MagicMock()
        self.service = ChatService(self.biz)

    def test_report_keyword_detection(self):
        self.assertTrue(ChatService._is_report_request("给我生成一份报告"))
        self.assertTrue(ChatService._is_report_request("查看使用记录"))
        self.assertTrue(ChatService._is_report_request("保养建议"))
        self.assertTrue(ChatService._is_report_request("月报"))
        self.assertFalse(ChatService._is_report_request("你好"))

    def test_extract_month(self):
        self.assertEqual(ChatService._extract_month("2024-01的报告"), "2024-01")
        self.assertIsNone(ChatService._extract_month("给我一份报告"))
        self.assertEqual(ChatService._extract_month("2025-12"), "2025-12")


if __name__ == "__main__":
    unittest.main()
