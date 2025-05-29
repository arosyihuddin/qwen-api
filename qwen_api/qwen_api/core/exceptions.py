class QwenAPIError(Exception):
    """Base exception untuk semua error API"""
    def __init__(self, message: str = "Qwen API Error"):
        super().__init__(message)

class AuthError(QwenAPIError):
    """Error autentikasi"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)

class RateLimitError(QwenAPIError):
    """Error rate limiting"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)