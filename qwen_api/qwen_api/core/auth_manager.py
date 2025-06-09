import os
from typing import Optional
from dotenv import load_dotenv
from qwen_api.core.exceptions import AuthError


class AuthManager:
    def __init__(self, token: Optional[str] = None, cookie: Optional[str] = None):
        load_dotenv()
        self._token = token or os.getenv("QWEN_AUTH_TOKEN")
        self._cookie = cookie or os.getenv("QWEN_COOKIE")

    def get_token(self) -> str:
        if not self._token:
            raise AuthError("Authentication token not found in .env")
        return f"Bearer {self._token}"

    def get_cookie(self) -> str:
        if not self._cookie:
            raise AuthError("Cookie not found in .env")
        return self._cookie

    def get_bx_ua(self) -> str:
        if not self._bx_ua:
            raise AuthError("BX-UA not found in .env")
        return self._bx_ua

    def refresh(self):
        """Untuk implementasi token refresh jika diperlukan"""
        pass
