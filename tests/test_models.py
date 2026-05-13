"""Pydantic 模型校验测试。"""
import unittest

from pydantic import ValidationError

from schemas.app_models import ChatRequest, ReportRequest, UserContext


class TestUserContext(unittest.TestCase):
    def test_valid_context(self):
        ctx = UserContext(user_id="u001", city="深圳")
        self.assertEqual(ctx.user_id, "u001")

    def test_rejects_empty_user_id(self):
        with self.assertRaises(ValidationError):
            UserContext(user_id="", city="深圳")

    def test_rejects_empty_city(self):
        with self.assertRaises(ValidationError):
            UserContext(user_id="u001", city="")

    def test_rejects_overlong_user_id(self):
        with self.assertRaises(ValidationError):
            UserContext(user_id="x" * 65, city="深圳")

    def test_rejects_overlong_city(self):
        with self.assertRaises(ValidationError):
            UserContext(user_id="u001", city="x" * 65)


class TestChatRequest(unittest.TestCase):
    def test_valid_message(self):
        req = ChatRequest(message="你好")
        self.assertEqual(req.message, "你好")

    def test_rejects_empty_string(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="")

    def test_rejects_blank_whitespace(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="   ")

    def test_rejects_too_long(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="x" * 4001)

    def test_accepts_max_length(self):
        req = ChatRequest(message="x" * 4000)
        self.assertEqual(len(req.message), 4000)


class TestReportRequest(unittest.TestCase):
    def test_accepts_valid_month(self):
        req = ReportRequest(month="2024-01")
        self.assertEqual(req.month, "2024-01")

    def test_accepts_no_month(self):
        req = ReportRequest()
        self.assertIsNone(req.month)

    def test_rejects_bad_format_single_digit(self):
        with self.assertRaises(ValidationError):
            ReportRequest(month="2024-1")

    def test_rejects_bad_format_no_dash(self):
        with self.assertRaises(ValidationError):
            ReportRequest(month="202401")

    def test_rejects_bad_format_slash(self):
        with self.assertRaises(ValidationError):
            ReportRequest(month="2024/01")

    def test_rejects_bad_format_text(self):
        with self.assertRaises(ValidationError):
            ReportRequest(month="January")


if __name__ == "__main__":
    unittest.main()
