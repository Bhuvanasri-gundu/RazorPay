from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Operational Modes: "auto" (default), "real", or "mock"
    ai_mode: str = "auto"
    database_mode: str = "auto"
    payment_mode: str = "auto"

    # Gemini AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_mode: str = "test"

    @property
    def is_gemini_active(self) -> bool:
        if self.ai_mode in ("mock", "fallback"):
            return False
        val = self.gemini_api_key.strip()
        has_key = bool(val and not val.startswith("your_") and not val.startswith("YOUR_") and len(val) > 15)
        if self.ai_mode in ("real", "gemini"):
            return has_key
        # Auto mode: detect if key is provided and not a placeholder
        return has_key

    @property
    def is_supabase_active(self) -> bool:
        if self.database_mode in ("mock", "local"):
            return False
        url = self.supabase_url.strip()
        key = self.supabase_service_role_key.strip()
        url_valid = bool(url and url.startswith("https://") and "your-project" not in url.lower())
        key_valid = bool(key and not key.startswith("your_") and not key.startswith("YOUR_") and len(key) > 20)
        if self.database_mode in ("real", "supabase"):
            return url_valid and key_valid
        # Auto mode
        return url_valid and key_valid

    @property
    def is_razorpay_active(self) -> bool:
        if self.payment_mode in ("mock", "simulated"):
            return False
        key_id = self.razorpay_key_id.strip()
        secret = self.razorpay_key_secret.strip()
        key_valid = bool(key_id and key_id.startswith("rzp_") and not key_id.lower().startswith("rzp_test_your") and len(key_id) > 10)
        secret_valid = bool(secret and not secret.startswith("your_") and not secret.startswith("YOUR_") and len(secret) > 8)
        if self.payment_mode in ("real", "razorpay"):
            return key_valid and secret_valid
        # Auto mode
        return key_valid and secret_valid

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
