import time
import unittest

from api.auth import JWTSettings, JWTValidationError, create_signed_jwt, decode_and_validate_jwt


class JWTAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "unit-test-secret"
        self.settings = JWTSettings(
            secret=self.secret,
            algorithms=("HS256",),
            issuer="unit-tests",
            audience="robot-agent",
            user_id_claim="user_id",
            city_claim="city",
            tenant_id_claim="tenant_id",
            roles_claim="roles",
            clock_skew_seconds=0,
        )

    # ── positive cases ──────────────────────────────────────────

    def test_decode_valid_token_returns_claims(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "sub": "1001",
                "user_id": "1001",
                "city": "Shanghai",
                "roles": ["user"],
                "iss": "unit-tests",
                "aud": "robot-agent",
                "iat": now,
                "nbf": now,
                "exp": now + 60,
            },
            secret=self.secret,
        )

        claims = decode_and_validate_jwt(token, self.settings)
        self.assertEqual(claims["user_id"], "1001")
        self.assertEqual(claims["city"], "Shanghai")

    def test_hs384_algorithm(self):
        settings = JWTSettings(
            secret=self.secret,
            algorithms=("HS384",),
            issuer=None,
            audience=None,
            user_id_claim="user_id",
            city_claim="city",
            tenant_id_claim="tenant_id",
            roles_claim="roles",
            clock_skew_seconds=0,
        )
        now = int(time.time())
        token = create_signed_jwt(
            {"user_id": "2001", "city": "Hefei", "exp": now + 60},
            secret=self.secret,
            algorithm="HS384",
        )
        claims = decode_and_validate_jwt(token, settings)
        self.assertEqual(claims["user_id"], "2001")

    def test_hs512_algorithm(self):
        settings = JWTSettings(
            secret=self.secret,
            algorithms=("HS512",),
            issuer=None,
            audience=None,
            user_id_claim="user_id",
            city_claim="city",
            tenant_id_claim="tenant_id",
            roles_claim="roles",
            clock_skew_seconds=0,
        )
        now = int(time.time())
        token = create_signed_jwt(
            {"user_id": "3001", "city": "Hangzhou", "exp": now + 60},
            secret=self.secret,
            algorithm="HS512",
        )
        claims = decode_and_validate_jwt(token, settings)
        self.assertEqual(claims["user_id"], "3001")

    # ── signature / integrity ────────────────────────────────────

    def test_rejects_bad_signature(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "user_id": "1001",
                "city": "Shanghai",
                "iss": "unit-tests",
                "aud": "robot-agent",
                "exp": now + 60,
            },
            secret="another-secret",
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    def test_rejects_malformed_token(self):
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt("not.a.jwt.token.structure", self.settings)

    def test_rejects_garbage_token(self):
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt("garbage", self.settings)

    # ── expiry / nbf ─────────────────────────────────────────────

    def test_rejects_expired_token(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "user_id": "1001",
                "city": "Shanghai",
                "iss": "unit-tests",
                "aud": "robot-agent",
                "exp": now - 1,
            },
            secret=self.secret,
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    def test_rejects_not_yet_active_token(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "user_id": "1001",
                "city": "Shanghai",
                "iss": "unit-tests",
                "aud": "robot-agent",
                "nbf": now + 3600,
                "exp": now + 7200,
            },
            secret=self.secret,
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    # ── issuer / audience ────────────────────────────────────────

    def test_rejects_wrong_issuer(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "user_id": "1001",
                "city": "Shanghai",
                "iss": "wrong-issuer",
                "aud": "robot-agent",
                "exp": now + 60,
            },
            secret=self.secret,
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    def test_rejects_wrong_audience(self):
        now = int(time.time())
        token = create_signed_jwt(
            {
                "user_id": "1001",
                "city": "Shanghai",
                "iss": "unit-tests",
                "aud": "wrong-audience",
                "exp": now + 60,
            },
            secret=self.secret,
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    # ── algorithm mismatch ───────────────────────────────────────

    def test_rejects_algorithm_not_in_allowlist(self):
        now = int(time.time())
        token = create_signed_jwt(
            {"user_id": "4001", "city": "Shenzhen", "exp": now + 60},
            secret=self.secret,
            algorithm="HS384",
        )
        with self.assertRaises(JWTValidationError):
            decode_and_validate_jwt(token, self.settings)

    # ── clok skew leeway ────────────────────────────────────────

    def test_clock_skew_allows_slightly_expired_token(self):
        settings = JWTSettings(
            secret=self.secret,
            algorithms=("HS256",),
            issuer=None,
            audience=None,
            user_id_claim="user_id",
            city_claim="city",
            tenant_id_claim="tenant_id",
            roles_claim="roles",
            clock_skew_seconds=30,
        )
        now = int(time.time())
        token = create_signed_jwt(
            {"user_id": "5001", "city": "Beijing", "exp": now - 10},
            secret=self.secret,
        )
        claims = decode_and_validate_jwt(token, settings)
        self.assertEqual(claims["user_id"], "5001")


if __name__ == "__main__":
    unittest.main()
