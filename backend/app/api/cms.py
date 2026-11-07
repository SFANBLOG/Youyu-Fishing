import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import settings
from app.deps import admin_user
from app.models import Banner, News, Notice
from app.result import BizError, Result
from app.schemas import Account, BannerIn, NewsIn, NoticeIn

router = APIRouter(tags=["内容"])


@router.get("/news")
async def list_news(page: int = 1, size: int = 10):
    qs = News.filter(status=True)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size)
    return Result.page([{"id": n.id, "title": n.title, "cover": n.cover,
                         "summary": n.summary, "views": n.views,
                         "created_at": n.created_at.isoformat()} for n in rows],
                       total, page, size)


@router.get("/news/{nid}")
async def get_news(nid: int):
    n = await News.get_or_none(id=nid)
    if not n:
        raise BizError("资讯不存在", 404)
    n.views += 1
    await n.save()
    return Result.success({"id": n.id, "title": n.title, "cover": n.cover,
                           "summary": n.summary, "content": n.content, "views": n.views})


@router.post("/news")
async def create_news(body: NewsIn, _: Account = Depends(admin_user)):
    n = await News.create(**body.model_dump())
    return Result.success({"id": n.id})


@router.put("/news/{nid}")
async def update_news(nid: int, body: NewsIn, _: Account = Depends(admin_user)):
    n = await News.get_or_none(id=nid)
    if not n:
        raise BizError("资讯不存在", 404)
    for k, v in body.model_dump().items():
        setattr(n, k, v)
    await n.save()
    return Result.success()


@router.delete("/news/{nid}")
async def delete_news(nid: int, _: Account = Depends(admin_user)):
    await News.filter(id=nid).delete()
    return Result.success()


@router.get("/banners")
async def list_banners():
    rows = await Banner.filter(status=True).order_by("sort")
    return Result.success([{"id": b.id, "title": b.title, "image": b.image,
                            "link": b.link, "sort": b.sort} for b in rows])


@router.post("/banners")
async def create_banner(body: BannerIn, _: Account = Depends(admin_user)):
    b = await Banner.create(**body.model_dump())
    return Result.success({"id": b.id})


@router.put("/banners/{bid}")
async def update_banner(bid: int, body: BannerIn, _: Account = Depends(admin_user)):
    b = await Banner.get_or_none(id=bid)
    if not b:
        raise BizError("轮播不存在", 404)
    for k, v in body.model_dump().items():
        setattr(b, k, v)
    await b.save()
    return Result.success()


@router.delete("/banners/{bid}")
async def delete_banner(bid: int, _: Account = Depends(admin_user)):
    await Banner.filter(id=bid).delete()
    return Result.success()


@router.get("/notices")
async def list_notices():
    rows = await Notice.filter(status=True).order_by("-id")
    return Result.success([{"id": n.id, "title": n.title, "content": n.content} for n in rows])


@router.post("/notices")
async def create_notice(body: NoticeIn, _: Account = Depends(admin_user)):
    n = await Notice.create(**body.model_dump())
    return Result.success({"id": n.id})


@router.put("/notices/{nid}")
async def update_notice(nid: int, body: NoticeIn, _: Account = Depends(admin_user)):
    n = await Notice.get_or_none(id=nid)
    if not n:
        raise BizError("公告不存在", 404)
    for k, v in body.model_dump().items():
        setattr(n, k, v)
    await n.save()
    return Result.success()


@router.delete("/notices/{nid}")
async def delete_notice(nid: int, _: Account = Depends(admin_user)):
    await Notice.filter(id=nid).delete()
    return Result.success()


@router.post("/upload")
async def upload(file: UploadFile = File(...), _: Account = Depends(admin_user)):
    """wangEditor 要求返回 {errno, data:[{url}]}。"""
    ext = Path(file.filename or "x.png").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
        raise BizError("不支持的图片格式")
    folder = Path(__file__).resolve().parent.parent.parent / settings.UPLOAD_DIR
    folder.mkdir(parents=True, exist_ok=True)
    name = uuid.uuid4().hex + ext
    content = await file.read()
    (folder / name).write_bytes(content)
    url = f"/uploads/{name}"
    return {"errno": 0, "data": [{"url": url, "alt": file.filename, "href": url}],
            "url": url}
