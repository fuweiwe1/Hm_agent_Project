"""API 端点测试 — 鉴权、业务数据、安全头、requestId。"""
import time
import unittest

from fastapi.testclient import TestClient

from api.app import app
from api.auth import create_signed_jwt, get_jwt_settings


def _make_token(user_id: str = "u001", city: str = "深圳") -> str:
    settings = get_jwt_settings()
    now = int(time.time())
    claims = {
        "sub": user_id,
        "user_id": user_id,
        "city": city,
        "iat": now,
        "nbf": now,
        "exp": now + 3600,
    }
    if settings.issuer:
        claims["iss"] = settings.issuer
    if settings.audience:
        claims["aud"] = settings.audience
    return create_signed_jwt(claims, secret=settings.secret)


class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_returns_ok(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_health_has_request_id_header(self):
        resp = self.client.get("/health")
        self.assertIn("X-Request-ID", resp.headers)

    def test_health_has_security_headers(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")


class TestAuthEnforcement(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_me_requires_token(self):
        resp = self.client.get("/auth/me")
        self.assertIn(resp.status_code, (401, 403))

    def test_me_with_valid_token(self):
        token = _make_token()
        resp = self.client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["user_id"], "u001")

    def test_me_with_bad_token(self):
        resp = self.client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
        self.assertIn(resp.status_code, (401, 403))


class TestBusinessEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = _make_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_get_my_profile(self):
        resp = self.client.get("/business/me", headers=self.headers)
        self.assertIn(resp.status_code, (200, 404))

    def test_list_my_months(self):
        resp = self.client.get("/business/me/months", headers=self.headers)
        self.assertIn(resp.status_code, (200, 404))

    def test_current_month(self):
        resp = self.client.get("/business/current-month", headers=self.headers)
        self.assertEqual(resp.status_code, 200)

    def test_weather(self):
        resp = self.client.get("/business/weather/深圳", headers=self.headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["city"], "深圳")

    def test_cannot_access_other_user(self):
        resp = self.client.get("/business/users/u999", headers=self.headers)
        self.assertEqual(resp.status_code, 403)


class TestChatEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = _make_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_chat_requires_auth(self):
        resp = self.client.post("/api/chat", json={"message": "你好"})
        self.assertIn(resp.status_code, (401, 403))

    def test_chat_rejects_blank_message(self):
        resp = self.client.post("/api/chat", json={"message": "   "}, headers=self.headers)
        self.assertEqual(resp.status_code, 422)

    def test_chat_rejects_too_long_message(self):
        resp = self.client.post("/api/chat", json={"message": "x" * 4001}, headers=self.headers)
        self.assertEqual(resp.status_code, 422)

    def test_chat_rejects_missing_message(self):
        resp = self.client.post("/api/chat", json={}, headers=self.headers)
        self.assertEqual(resp.status_code, 422)


class TestReportEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.token = _make_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_report_rejects_bad_month(self):
        resp = self.client.post("/api/report", json={"month": "2024-1"}, headers=self.headers)
        self.assertEqual(resp.status_code, 422)

    def test_report_accepts_valid_month(self):
        # 不实际调用 LLM，只验证参数校验通过（可能后续 LLM 报错，但不是 422）
        resp = self.client.post("/api/report", json={"month": "2024-01"}, headers=self.headers)
        self.assertNotEqual(resp.status_code, 422)

    def test_report_accepts_no_month(self):
        resp = self.client.post("/api/report", json={}, headers=self.headers)
        self.assertNotEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
