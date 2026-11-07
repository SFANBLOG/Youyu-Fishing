from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "有渔渔具 AI Agent"
    DATABASE_URL: str = "sqlite://db.sqlite3"
    SECRET_KEY: str = "change-this-secret-in-production"
    TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    UPLOAD_DIR: str = "uploads"
    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 60
    LLM_TIMEOUT: float = 30.0

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_list(self) -> list[str]:
        return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]


settings = Settings()
