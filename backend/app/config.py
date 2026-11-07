from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "有渔渔具 AI Agent"

    # ---- MySQL ----
    DATABASE_URL: str = "mysql://root:youyu123@127.0.0.1:3306/youyu"
    DB_RETRY: int = 20
    DB_RETRY_DELAY: float = 2.0

    # ---- Milvus ----
    VECTOR_BACKEND: str = "milvus"          # milvus | off（off 时纯 BM25，便于无 Docker 开发）
    MILVUS_HOST: str = "127.0.0.1"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "yy_knowledge_chunks"
    EMBED_DIM: int = 1024
    MILVUS_TOPK: int = 30

    # ---- MinIO ----
    STORAGE_BACKEND: str = "minio"          # minio | local
    MINIO_ENDPOINT: str = "127.0.0.1:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "youyu-uploads"
    MINIO_SECURE: bool = False
    UPLOAD_DIR: str = "uploads"            # STORAGE_BACKEND=local / MinIO 降级时使用
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    # ---- LangChain / LLM ----
    LLM_FRAMEWORK: str = "langchain"        # langchain | httpx
    LLM_TIMEOUT: float = 30.0

    # ---- 通用 ----
    SECRET_KEY: str = "change-this-secret-in-production"
    TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 60

    @property
    def cors_list(self) -> list[str]:
        return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]

    @property
    def milvus_uri(self) -> str:
        return f"http://{self.MILVUS_HOST}:{self.MILVUS_PORT}"


settings = Settings()
