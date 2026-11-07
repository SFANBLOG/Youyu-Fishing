import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import seed
from app.config import settings
from app.database import close_db, init_db
from app.infra.milvus_client import milvus_store
from app.infra.minio_client import minio_store
from app.result import Result, register_exception_handlers
from app.api import admin, ai_config, auth, chat, cms, knowledge, shop, trade

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "static"
UPLOAD_DIR = BASE / settings.UPLOAD_DIR

_DEMO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect width="800" height="600" fill="url(#g)"/>
<circle cx="640" cy="130" r="86" fill="rgba(255,255,255,.16)"/>
<path d="M0 470 Q200 390 400 470 T800 450 V600 H0Z" fill="rgba(255,255,255,.12)"/>
<text x="50%" y="46%" text-anchor="middle" font-size="46" fill="#fff" font-family="sans-serif">{label}</text>
<text x="50%" y="56%" text-anchor="middle" font-size="22" fill="rgba(255,255,255,.8)" font-family="sans-serif">YOUYU FISHING</text>
</svg>"""


def ensure_assets():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    demo = STATIC_DIR / "demo"
    demo.mkdir(parents=True, exist_ok=True)
    palettes = [("#1d976c", "#0b3d2e"), ("#2b6cb0", "#12314f"), ("#b7791f", "#4a2f12"),
                ("#6b46c1", "#2d1b4e"), ("#c05621", "#4a2413"), ("#2c7a7b", "#123c3d")]
    for i in range(1, 7):
        f = demo / f"product_{i}.svg"
        if not f.exists():
            c1, c2 = palettes[(i - 1) % len(palettes)]
            f.write_text(_DEMO_SVG.format(c1=c1, c2=c2, label=f"渔具 {i}"), encoding="utf-8")
    for i in range(1, 4):
        f = demo / f"banner_{i}.svg"
        if not f.exists():
            f.write_text(_DEMO_SVG.format(c1="#0f766e", c2="#0b3d2e", label=f"秋季上新 {i}"),
                         encoding="utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.chdir(BASE)  # 本地降级上传等相对路径落在 backend/ 下
    ensure_assets()
    await init_db()
    # 基础设施初始化失败只告警：Milvus 降级纯 BM25，MinIO 降级本地磁盘
    await asyncio.to_thread(milvus_store.ensure_collection)
    await asyncio.to_thread(minio_store.ensure_bucket)
    await seed.seed()
    yield
    await close_db()


app = FastAPI(title=settings.APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)
# StaticFiles 在导入时就校验目录，必须先建好（完整资源由 lifespan 里的 ensure_assets 补齐）
ensure_assets()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

for module in (auth, shop, trade, cms, admin, ai_config, knowledge, chat):
    app.include_router(module.router, prefix="/api")


@app.get("/")
async def root():
    return Result.success({"app": settings.APP_NAME, "docs": "/docs"})
