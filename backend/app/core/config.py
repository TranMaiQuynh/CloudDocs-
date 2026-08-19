# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb+srv://tranmaiquynhds_db_user:9002TranMaiquynhhh@clouddocs.ytdffuo.mongodb.net/?retryWrites=true&w=majority&appName=CloudDocs"
    DATABASE_NAME: str = "clouddocs"
    JWT_SECRET_KEY: str = "10dmdtdmqtxdqthg2009"
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