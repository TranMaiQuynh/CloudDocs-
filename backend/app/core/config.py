# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URI: str
    DATABASE_NAME: str = "clouddocs"
    JWT_SECRET_KEY: str = "clouddocs_default_jwt_secret_key_2026_super_secure"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15 # access token có thời hạn 15 phút
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # Hết hạn sau 7 ngày

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()