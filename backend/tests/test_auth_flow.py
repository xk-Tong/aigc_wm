import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from crud import auth as crud_auth
from routers import auth as auth_router
from schemas.auth import UserInfo, UserLogin


class TestAuthCrud(unittest.IsolatedAsyncioTestCase):
    async def test_generate_access_token_stores_session_in_redis(self):
        user = SimpleNamespace(id=1, username="alice", role="USER", status=1)
        redis_mock = AsyncMock()

        with patch.object(crud_auth, "redis_client", redis_mock), patch.object(
            crud_auth, "create_session_token", return_value="fixedtoken123"
        ), patch.object(crud_auth, "SESSION_TOKEN_TTL_SECONDS", 3600):
            token = await crud_auth.generate_access_token(user)

        self.assertEqual(token, "fixedtoken123")
        redis_mock.setex.assert_awaited_once()

        key, ttl, payload = redis_mock.setex.await_args.args
        self.assertEqual(key, "session:fixedtoken123")
        self.assertEqual(ttl, 3600)

        payload_data = json.loads(payload)
        self.assertEqual(payload_data["id"], 1)
        self.assertEqual(payload_data["username"], "alice")
        self.assertEqual(payload_data["role"], "USER")
        self.assertEqual(payload_data["status"], 1)

    async def test_verify_session_token_returns_data_and_refreshes_ttl(self):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = json.dumps({"id": 1, "username": "alice"})

        with patch.object(crud_auth, "redis_client", redis_mock), patch.object(
            crud_auth, "SESSION_TOKEN_TTL_SECONDS", 7200
        ):
            session = await crud_auth.verify_session_token("token-123", refresh_ttl=True)

        self.assertEqual(session["id"], 1)
        redis_mock.get.assert_awaited_once_with("session:token-123")
        redis_mock.expire.assert_awaited_once_with("session:token-123", 7200)

    async def test_delete_session_token_returns_true_when_deleted(self):
        redis_mock = AsyncMock()
        redis_mock.delete.return_value = 1

        with patch.object(crud_auth, "redis_client", redis_mock):
            deleted = await crud_auth.delete_session_token("token-123")

        self.assertTrue(deleted)
        redis_mock.delete.assert_awaited_once_with("session:token-123")


class TestAuthRouter(unittest.IsolatedAsyncioTestCase):
    async def test_login_success(self):
        user = SimpleNamespace(
            id=1,
            username="alice",
            email="alice@example.com",
            role="USER",
            status=1,
        )
        user_info = UserInfo(id=1, username="alice", email="alice@example.com", role="USER")

        with patch("routers.auth.crud_auth.authenticate_user", new=AsyncMock(return_value=user)), patch(
            "routers.auth.crud_auth.generate_access_token", new=AsyncMock(return_value="token-123")
        ), patch("routers.auth.crud_auth.get_user_info", return_value=user_info), patch(
            "routers.auth.crud_auth.get_current_timestamp", return_value="2026-04-20T00:00:00Z"
        ):
            response = await auth_router.login(
                UserLogin(username="alice", password="StrongPass123"),
                db=object(),
            )

        self.assertEqual(response["code"], 200)
        self.assertEqual(response["data"]["accessToken"], "token-123")
        self.assertEqual(response["data"]["user"]["username"], "alice")

    async def test_login_returns_503_when_redis_unavailable(self):
        user = SimpleNamespace(
            id=1,
            username="alice",
            email="alice@example.com",
            role="USER",
            status=1,
        )

        with patch("routers.auth.crud_auth.authenticate_user", new=AsyncMock(return_value=user)), patch(
            "routers.auth.crud_auth.generate_access_token",
            new=AsyncMock(side_effect=RuntimeError("redis down")),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await auth_router.login(
                    UserLogin(username="alice", password="StrongPass123"),
                    db=object(),
                )

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.detail, "登录服务暂不可用，请稍后再试")

    async def test_verify_token_returns_valid_true(self):
        with patch(
            "routers.auth.crud_auth.verify_session_token",
            new=AsyncMock(return_value={"id": 1, "username": "alice", "role": "USER"}),
        ), patch("routers.auth.crud_auth.get_current_timestamp", return_value="2026-04-20T00:00:00Z"):
            response = await auth_router.verify_token(authorization="Bearer token-123")

        self.assertEqual(response["code"], 200)
        self.assertTrue(response["data"]["valid"])
        self.assertEqual(response["data"]["user"]["username"], "alice")

    async def test_verify_token_returns_valid_false_when_missing(self):
        with patch("routers.auth.crud_auth.get_current_timestamp", return_value="2026-04-20T00:00:00Z"):
            response = await auth_router.verify_token(authorization=None)

        self.assertEqual(response["code"], 200)
        self.assertFalse(response["data"]["valid"])

    async def test_logout_returns_success(self):
        with patch("routers.auth.crud_auth.delete_session_token", new=AsyncMock(return_value=True)), patch(
            "routers.auth.crud_auth.get_current_timestamp", return_value="2026-04-20T00:00:00Z"
        ):
            response = await auth_router.logout(authorization="Bearer token-123")

        self.assertEqual(response["code"], 200)
        self.assertTrue(response["data"]["success"])
        self.assertTrue(response["data"]["revoked"])


if __name__ == "__main__":
    unittest.main()
