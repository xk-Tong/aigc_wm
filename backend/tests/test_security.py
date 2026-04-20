import unittest
from uuid import UUID
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from utils.security import create_session_token, get_password_hash, verify_password


class TestSecurity(unittest.TestCase):
    def test_password_hash_and_verify(self):
        password = "StrongPass123"

        hashed = get_password_hash(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPass", hashed))

    def test_create_session_token_is_valid_uuid_hex(self):
        token = create_session_token()

        self.assertEqual(len(token), 32)
        # 通过 UUID 校验 token 格式合法。
        UUID(hex=token)


if __name__ == "__main__":
    unittest.main()
