from fastapi import APIRouter, Depends, Query

from app.deps import admin_user, current_user
from app.models import Category, Favorite, Product
from app.result import BizError, Result
from app.schemas import Account, ProductIn

router = APIRouter(tags=["商城"])


def product_dict(p: Product) -> dict:
    return {
        "id": p.id, "title": p.title, "subtitle": p.subtitle,
        "category_id": p.category_id, "price": p.price,
        "original_price": p.original_price, "stock": p.stock, "sales": p.sales,
        "cover": p.cover, "images": p.images or [], "specs": p.specs or [],
        "detail": p.detail, "tags": p.tags or [], "status": p.status,
    }


@router.get("/categories")
async def list_categories():
    rows = await Category.all().order_by("sort")
    return Result.success([{"id": c.id, "name": c.name, "icon": c.icon, "sort": c.sort} for c in rows])


@router.post("/categories")
async def create_category(name: str, icon: str = "", sort: int = 0, _: Account = Depends(admin_user)):
    if await Category.exists(name=name):
        raise BizError("分类已存在")
    c = await Category.create(name=name, icon=icon, sort=sort)
    return Result.success({"id": c.id, "name": c.name})


@router.put("/categories/{cid}")
async def update_category(cid: int, name: str, icon: str = "", sort: int = 0,
                          _: Account = Depends(admin_user)):
    c = await Category.get_or_none(id=cid)
    if not c:
        raise BizError("分类不存在", 404)
    c.name, c.icon, c.sort = name, icon, sort
    await c.save()
    return Result.success({"id": c.id})


@router.delete("/categories/{cid}")
async def delete_category(cid: int, _: Account = Depends(admin_user)):
    await Product.filter(category_id=cid).update(category_id=None)
    await Category.filter(id=cid).delete()
    return Result.success()


@router.get("/products")
async def list_products(
    page: int = 1, size: int = 12, keyword: str = "", category_id: int | None = None,
    sort: str = Query("default", pattern="^(default|price_asc|price_desc|sales|new)$"),
    only_online: bool = True,
):
    qs = Product.all()
    if only_online:
        qs = qs.filter(status=True)
    if keyword:
        qs = qs.filter(title__icontains=keyword)
    if category_id:
        qs = qs.filter(category_id=category_id)
    order = {"default": "-id", "price_asc": "price", "price_desc": "-price",
             "sales": "-sales", "new": "-created_at"}[sort]
    total = await qs.count()
    rows = await qs.order_by(order).offset((page - 1) * size).limit(size)
    return Result.page([product_dict(p) for p in rows], total, page, size)


@router.get("/products/{pid}")
async def get_product(pid: int):
    p = await Product.get_or_none(id=pid)
    if not p:
        raise BizError("商品不存在", 404)
    return Result.success(product_dict(p))


@router.get("/products/{pid}/similar")
async def similar_products(pid: int, limit: int = 4):
    p = await Product.get_or_none(id=pid)
    if not p:
        raise BizError("商品不存在", 404)
    rows = await Product.filter(category_id=p.category_id, status=True).exclude(id=pid).order_by("-sales").limit(limit)
    if len(rows) < limit:
        extra = await Product.filter(status=True).exclude(id=pid).exclude(
            id__in=[r.id for r in rows]).order_by("-sales").limit(limit - len(rows))
        rows = list(rows) + list(extra)
    return Result.success([product_dict(x) for x in rows])


@router.post("/products")
async def create_product(body: ProductIn, _: Account = Depends(admin_user)):
    p = await Product.create(**body.model_dump(exclude={"category_id"}), category_id=body.category_id)
    return Result.success({"id": p.id})


@router.put("/products/{pid}")
async def update_product(pid: int, body: ProductIn, _: Account = Depends(admin_user)):
    p = await Product.get_or_none(id=pid)
    if not p:
        raise BizError("商品不存在", 404)
    for k, v in body.model_dump(exclude={"category_id"}).items():
        setattr(p, k, v)
    p.category_id = body.category_id
    await p.save()
    return Result.success(product_dict(p))


@router.delete("/products/{pid}")
async def delete_product(pid: int, _: Account = Depends(admin_user)):
    await Product.filter(id=pid).delete()
    return Result.success()


@router.get("/favorites")
async def list_favorites(account: Account = Depends(current_user)):
    rows = await Favorite.filter(user_id=account.id).prefetch_related("product")
    return Result.success([product_dict(r.product) for r in rows])


@router.post("/favorites")
async def add_favorite(product_id: int, account: Account = Depends(current_user)):
    if not await Product.exists(id=product_id):
        raise BizError("商品不存在", 404)
    await Favorite.get_or_create(user_id=account.id, product_id=product_id)
    return Result.success()


@router.delete("/favorites/{product_id}")
async def remove_favorite(product_id: int, account: Account = Depends(current_user)):
    await Favorite.filter(user_id=account.id, product_id=product_id).delete()
    return Result.success()
