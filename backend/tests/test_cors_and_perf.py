from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["FLASK_DEBUG"] = "0"
os.environ["ALLOWED_ORIGINS"] = (
    "https://collegefindr-frontend.onrender.com,"
    "https://mouleesh-user.github.io,"
    "https://moulesh-user.github.io,"
    "null"
)
os.environ["REQUIRE_ALLOWED_ORIGIN"] = "1"
os.environ["REQUIRE_CLIENT_API_KEY"] = "0"
os.environ["CAPTCHA_ENABLED"] = "0"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-cors-perf-only-32+chars"
os.environ["AUTO_CREATE_DB"] = "1"
os.environ["OPENROUTER_API_KEY"] = "test-not-used"
os.environ["SIGNUP_ENABLED"] = "1"
os.environ["CHAT_RATE_LIMIT"] = "100000 per minute"
os.environ["CHAT_DAILY_RATE_LIMIT"] = "100000 per day"
os.environ["CHAT_IP_RATE_LIMIT"] = "100000 per minute"

spec = importlib.util.spec_from_file_location("collegefindr_app_cors_perf", BACKEND_DIR / "app.py")
assert spec and spec.loader
app_module = importlib.util.module_from_spec(spec)
sys.modules["collegefindr_app_cors_perf"] = app_module
spec.loader.exec_module(app_module)

app_module.app.config["RATELIMIT_ENABLED"] = False
app_module.limiter.enabled = False


def mocked_llm(_: str, __: List[Any], **___: Any) -> Dict[str, Any]:
    return {
        "reply": "Based on your profile, consider colleges in Bangalore and verify current cutoffs officially.",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


class CorsAndPerfTests(unittest.TestCase):
    allowed_origin = "https://collegefindr-frontend.onrender.com"

    @classmethod
    def setUpClass(cls) -> None:
        with app_module.app.app_context():
            app_module.db.drop_all()
            app_module.db.create_all()
        cls.client = app_module.app.test_client()

    def setUp(self) -> None:
        with app_module.app.app_context():
            app_module.ApiRequestLog.query.delete()
            app_module.ChatAuditLog.query.delete()
            app_module.Message.query.delete()
            app_module.UserSettings.query.delete()
            app_module.User.query.delete()
            app_module.db.session.commit()

    def _register_token(self, email: str = "cors@test.com") -> str:
        response = self.client.post(
            "/auth/register",
            headers={"Origin": self.allowed_origin},
            json={"email": email, "password": "test12345678", "full_name": "CORS Tester"},
        )
        body = response.get_json() or {}
        self.assertEqual(response.status_code, 201, body)
        return body["token"]

    def test_options_chat_from_allowed_origin_includes_cors_header(self) -> None:
        response = self.client.open(
            "/chat",
            method="OPTIONS",
            headers={
                "Origin": self.allowed_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )

        self.assertIn(response.status_code, {200, 204})
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), self.allowed_origin)

    def test_login_auth_error_from_allowed_origin_keeps_cors_header(self) -> None:
        response = self.client.post(
            "/auth/login",
            headers={"Origin": self.allowed_origin},
            json={"email": "missing@test.com", "password": "test12345678"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), self.allowed_origin)

    def test_unknown_origin_is_rejected_for_protected_request(self) -> None:
        response = self.client.get(
            "/messages/chat-messages",
            headers={"Origin": "https://unknown.example.com"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Origin not allowed", (response.get_json() or {}).get("error", ""))

    def test_null_origin_is_allowed_when_configured(self) -> None:
        response = self.client.get(
            "/messages/chat-messages",
            headers={"Origin": "null"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), "null")

    def test_health_ping_and_preflight_do_not_create_api_request_logs(self) -> None:
        self.client.get("/ping", headers={"Origin": self.allowed_origin})
        self.client.get("/health", headers={"Origin": self.allowed_origin})
        self.client.open(
            "/chat",
            method="OPTIONS",
            headers={
                "Origin": self.allowed_origin,
                "Access-Control-Request-Method": "POST",
            },
        )

        with app_module.app.app_context():
            self.assertEqual(app_module.ApiRequestLog.query.count(), 0)

    def test_chat_still_creates_audit_message_and_request_logs(self) -> None:
        token = self._register_token()
        with app_module.app.app_context():
            app_module.ApiRequestLog.query.delete()
            app_module.db.session.commit()

        with patch.object(app_module, "_get_openrouter_reply_with_history", mocked_llm):
            response = self.client.post(
                "/chat",
                headers={
                    "Origin": self.allowed_origin,
                    "Authorization": f"Bearer {token}",
                },
                json={
                    "message": "I scored 92% in JEE Main, budget 3 lakh per year, want CSE in Bangalore",
                    "context": "chat-messages",
                },
            )

        self.assertEqual(response.status_code, 200, response.get_json())
        with app_module.app.app_context():
            self.assertEqual(app_module.ApiRequestLog.query.count(), 1)
            self.assertEqual(app_module.Message.query.count(), 2)
            self.assertEqual(app_module.ChatAuditLog.query.count(), 1)


if __name__ == "__main__":
    unittest.main()
