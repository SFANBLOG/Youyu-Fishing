"""MinIO 对象存储封装。

上传返回后端代理路径 /api/files/{object_name}，前端无需直连 MinIO，
也不需要把桶设成公开读；读取统一走 api/cms.py 的 files 代理。
"""
import io
import logging
import uuid
from pathlib import Path

from app.config import settings

logger = logging.getLogger("youyu.minio")

CONTENT_TYPES = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}


class MinioStore:
    def __init__(self):
        self._client = None
        self._disabled = False

    @property
    def enabled(self) -> bool:
        return not self._disabled and settings.STORAGE_BACKEND.lower() == "minio"

    def disable(self) -> None:
        """连接失败后本次进程内降级为本地磁盘，避免每次上传都重试。"""
        self._disabled = True
        self._client = None

    def _connect(self):
        if self._client is not None:
            return self._client
        from minio import Minio  # 惰性导入
        self._client = Minio(settings.MINIO_ENDPOINT,
                             access_key=settings.MINIO_ACCESS_KEY,
                             secret_key=settings.MINIO_SECRET_KEY,
                             secure=settings.MINIO_SECURE)
        return self._client

    def ensure_bucket(self) -> bool:
        if not self.enabled:
            return False
        try:
            client = self._connect()
            if not client.bucket_exists(settings.MINIO_BUCKET):
                client.make_bucket(settings.MINIO_BUCKET)
            logger.info("MinIO bucket ready: %s", settings.MINIO_BUCKET)
            return True
        except Exception as exc:
            logger.warning("MinIO 不可用，已降级为本地磁盘：%s", exc)
            self.disable()
            return False

    def put(self, data: bytes, filename: str) -> str:
        """返回对象名，如 2026/11/07/ab12.png。"""
        ext = Path(filename or "x.png").suffix.lower() or ".png"
        from datetime import datetime
        name = datetime.now().strftime("%Y/%m/%d/") + uuid.uuid4().hex + ext
        client = self._connect()
        client.put_object(
            settings.MINIO_BUCKET, name, io.BytesIO(data), length=len(data),
            content_type=CONTENT_TYPES.get(ext, "application/octet-stream"),
        )
        return name

    def get(self, object_name: str) -> tuple[bytes, str]:
        client = self._connect()
        resp = client.get_object(settings.MINIO_BUCKET, object_name)
        try:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "application/octet-stream")
        finally:
            resp.close()
            resp.release_conn()
        ext = Path(object_name).suffix.lower()
        return data, CONTENT_TYPES.get(ext, ctype)

    def delete(self, object_name: str) -> None:
        try:
            self._connect().remove_object(settings.MINIO_BUCKET, object_name)
        except Exception as exc:
            logger.warning("MinIO 删除失败 %s: %s", object_name, exc)


minio_store = MinioStore()
