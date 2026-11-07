import asyncio
import logging

from tortoise import Tortoise

from app.config import settings

logger = logging.getLogger("youyu.database")


async def init_db() -> None:
    """MySQL 容器冷启动较慢，做带退避的重连。"""
    last: Exception | None = None
    for attempt in range(1, settings.DB_RETRY + 1):
        try:
            await Tortoise.init(
                db_url=settings.DATABASE_URL,
                modules={"models": ["app.models"]},
                timezone="Asia/Shanghai",
            )
            await Tortoise.generate_schemas(safe=True)
            logger.info("MySQL connected: %s", settings.DATABASE_URL.split("@")[-1])
            return
        except Exception as exc:
            last = exc
            try:
                await Tortoise.close_connections()
            except Exception:
                pass
            logger.warning("MySQL not ready (%s/%s): %s", attempt, settings.DB_RETRY, exc)
            await asyncio.sleep(settings.DB_RETRY_DELAY)
    raise RuntimeError(f"MySQL 连接失败，已重试 {settings.DB_RETRY} 次：{last}")


async def close_db() -> None:
    await Tortoise.close_connections()
