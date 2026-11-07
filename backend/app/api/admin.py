from tortoise.functions import Count, Sum

from fastapi import APIRouter, Depends

from app.api.trade import order_dict
from app.deps import admin_user, hash_password
from app.models import Category, ChatMessage, KnowledgeDoc, Order, Product, Review, User
from app.result import BizError, Result
from app.schemas import Account

router = APIRouter(prefix="/admin", tags=["后台"])


def user_dict(u: User) -> dict:
    return {"id": u.id, "username": u.username, "nickname": u.nickname,
            "avatar": u.avatar, "phone": u.phone, "role": u.role,
            "status": u.status, "created_at": u.created_at.isoformat()}


@router.get("/admins")
async def list_admins(_: Account = Depends(admin_user)):
    rows = await User.filter(role="admin").order_by("id")
    return Result.success([user_dict(u) for u in rows])


@router.post("/admins")
async def create_admin(username: str, password: str, nickname: str = "",
                       _: Account = Depends(admin_user)):
    if await User.exists(username=username):
        raise BizError("用户名已存在")
    u = await User.create(username=username, password_hash=hash_password(password),
                          nickname=nickname or username, role="admin")
    return Result.success(user_dict(u))


@router.put("/admins/{uid}/status")
async def toggle_admin(uid: int, status: bool, _: Account = Depends(admin_user)):
    u = await User.get_or_none(id=uid, role="admin")
    if not u:
        raise BizError("管理员不存在", 404)
    u.status = status
    await u.save()
    return Result.success()


@router.get("/members")
async def list_members(page: int = 1, size: int = 10, keyword: str = "",
                       _: Account = Depends(admin_user)):
    qs = User.filter(role="user")
    if keyword:
        qs = qs.filter(username__icontains=keyword)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size)
    return Result.page([user_dict(u) for u in rows], total, page, size)


@router.put("/members/{uid}/status")
async def toggle_member(uid: int, status: bool, _: Account = Depends(admin_user)):
    u = await User.get_or_none(id=uid, role="user")
    if not u:
        raise BizError("会员不存在", 404)
    u.status = status
    await u.save()
    return Result.success()


@router.get("/dashboard")
async def dashboard(_: Account = Depends(admin_user)):
    order_rows = await Order.all().group_by("status").annotate(cnt=Count("id")).values("status", "cnt")
    status_map = {"pending": "待支付", "paid": "已支付", "shipped": "已发货",
                  "completed": "已完成", "cancelled": "已取消"}
    order_status = [{"name": status_map.get(r["status"], r["status"]), "value": r["cnt"]}
                    for r in order_rows]

    cats = await Category.all().order_by("sort")
    cat_rows = await Product.all().group_by("category_id").annotate(cnt=Count("id")).values("category_id", "cnt")
    name_by_id = {c.id: c.name for c in cats}
    category_bar = {"categories": [name_by_id.get(r["category_id"], "未分类") for r in cat_rows],
                    "values": [r["cnt"] for r in cat_rows]}

    hot = await Product.filter(status=True).order_by("-sales").limit(10)
    hot_bar = {"names": [p.title[:10] for p in hot], "values": [p.sales for p in hot]}

    revenue = await Order.filter(status__in=["paid", "shipped", "completed"]).annotate(
        total=Sum("total_amount")).values("total")
    amount = float(revenue[0].get("total") or 0) if revenue else 0.0

    return Result.success({
        "cards": {
            "products": await Product.all().count(),
            "orders": await Order.all().count(),
            "members": await User.filter(role="user").count(),
            "reviews": await Review.all().count(),
            "knowledge_docs": await KnowledgeDoc.all().count(),
            "chat_messages": await ChatMessage.all().count(),
            "revenue": round(amount, 2),
        },
        "order_status": order_status,
        "category_bar": category_bar,
        "hot_bar": hot_bar,
    })


@router.get("/orders")
async def all_orders(page: int = 1, size: int = 10, status: str = "",
                     _: Account = Depends(admin_user)):
    qs = Order.all()
    if status:
        qs = qs.filter(status=status)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size)
    return Result.page([await order_dict(o) for o in rows], total, page, size)


@router.put("/orders/{oid}/status")
async def admin_order_status(oid: int, status: str, _: Account = Depends(admin_user)):
    o = await Order.get_or_none(id=oid)
    if not o:
        raise BizError("订单不存在", 404)
    o.status = status
    await o.save()
    return Result.success(await order_dict(o))


@router.get("/reviews")
async def all_reviews(page: int = 1, size: int = 10, _: Account = Depends(admin_user)):
    total = await Review.all().count()
    rows = await Review.all().order_by("-id").offset((page - 1) * size).limit(size).prefetch_related("user")
    return Result.page([{
        "id": r.id, "user": r.user.nickname if r.user else "匿名",
        "product_id": r.product_id, "rating": r.rating, "content": r.content,
        "created_at": r.created_at.isoformat(),
    } for r in rows], total, page, size)
