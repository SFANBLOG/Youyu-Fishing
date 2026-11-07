from tortoise import Tortoise

from app.config import settings


async def init_db() -> None:
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
        timezone="Asia/Shanghai",
    )
    await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()
