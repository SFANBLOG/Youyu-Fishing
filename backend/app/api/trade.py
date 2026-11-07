import uuid
from datetime import datetime

from fastapi import APIRouter, Depends

from app.deps import admin_user, current_user
from app.models import CartItem, Order, OrderItem, Product, Review
from app.result import BizError, Result
from app.schemas import Account, CartIn, IdsIn, OrderIn, ReviewIn, StatusIn

router = APIRouter(tags=["交易"])

ALLOWED_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"shipped", "cancelled"},
    "shipped": {"completed"},
    "completed": set(),
    "cancelled": set(),
}


async def cart_dict(c: CartItem) -> dict:
    p = await Product.get_or_none(id=c.product_id)
    return {
        "id": c.id, "product_id": c.product_id, "spec": c.spec,
        "quantity": c.quantity, "checked": c.checked,
        "title": p.title if p else "商品已下架",
        "cover": p.cover if p else "",
        "price": p.price if p else 0,
        "stock": p.stock if p else 0,
        "status": p.status if p else False,
    }


@router.get("/cart")
async def list_cart(account: Account = Depends(current_user)):
    rows = await CartItem.filter(user_id=account.id).order_by("-id")
    items = [await cart_dict(c) for c in rows]
    total = sum(i["price"] * i["quantity"] for i in items if i["checked"])
    return Result.success({"items": items, "total_amount": round(total, 2),
                           "count": sum(i["quantity"] for i in items)})


@router.post("/cart")
async def add_cart(body: CartIn, account: Account = Depends(current_user)):
    p = await Product.get_or_none(id=body.product_id)
    if not p:
        raise BizError("商品不存在", 404)
    existing = await CartItem.get_or_none(user_id=account.id, product_id=body.product_id, spec=body.spec)
    if existing:
        existing.quantity += body.quantity
        await existing.save()
        return Result.success({"id": existing.id})
    c = await CartItem.create(user_id=account.id, **body.model_dump())
    return Result.success({"id": c.id})


@router.put("/cart/{cid}")
async def update_cart(cid: int, quantity: int | None = None, checked: bool | None = None,
                      account: Account = Depends(current_user)):
    c = await CartItem.get_or_none(id=cid, user_id=account.id)
    if not c:
        raise BizError("购物车项不存在", 404)
    if quantity is not None:
        c.quantity = max(1, quantity)
    if checked is not None:
        c.checked = checked
    await c.save()
    return Result.success()


@router.post("/cart/check-all")
async def check_all(checked: bool, account: Account = Depends(current_user)):
    await CartItem.filter(user_id=account.id).update(checked=checked)
    return Result.success()


@router.post("/cart/batch-delete")
async def batch_delete(body: IdsIn, account: Account = Depends(current_user)):
    await CartItem.filter(user_id=account.id, id__in=body.ids).delete()
    return Result.success()


@router.delete("/cart")
async def clear_cart(account: Account = Depends(current_user)):
    await CartItem.filter(user_id=account.id).delete()
    return Result.success()


async def order_dict(o: Order) -> dict:
    items = await OrderItem.filter(order_id=o.id)
    return {
        "id": o.id, "order_no": o.order_no, "total_amount": o.total_amount,
        "status": o.status, "address": o.address, "remark": o.remark,
        "created_at": o.created_at.isoformat(),
        "items": [{"id": i.id, "product_id": i.product_id, "title": i.title,
                   "cover": i.cover, "spec": i.spec, "price": i.price,
                   "quantity": i.quantity} for i in items],
        "can_review": o.status == "completed",
    }


@router.post("/orders")
async def create_order(body: OrderIn, account: Account = Depends(current_user)):
    rows = await CartItem.filter(user_id=account.id, id__in=body.cart_ids, checked=True)
    if not rows:
        raise BizError("没有勾选任何商品")
    total = 0.0
    snapshots = []
    for c in rows:
        p = await Product.get_or_none(id=c.product_id)
        if not p or not p.status or p.stock < c.quantity:
            raise BizError(f"「{p.title if p else '商品'}」库存不足或已下架")
        total += p.price * c.quantity
        snapshots.append((p, c))
    order_no = datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6]
    order = await Order.create(order_no=order_no, user_id=account.id,
                               total_amount=round(total, 2), address=body.address,
                               remark=body.remark)
    for p, c in snapshots:
        await OrderItem.create(order_id=order.id, product_id=p.id, title=p.title,
                               cover=p.cover, spec=c.spec, price=p.price, quantity=c.quantity)
        p.stock -= c.quantity
        p.sales += c.quantity
        await p.save()
    await CartItem.filter(id__in=[c.id for _, c in snapshots]).delete()
    return Result.success(await order_dict(order))


@router.get("/orders")
async def list_orders(page: int = 1, size: int = 10, status: str = "",
                      account: Account = Depends(current_user)):
    qs = Order.filter(user_id=account.id)
    if status:
        qs = qs.filter(status=status)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size)
    return Result.page([await order_dict(o) for o in rows], total, page, size)


@router.put("/orders/{oid}/status")
async def change_status(oid: int, body: StatusIn, account: Account = Depends(current_user)):
    o = await Order.get_or_none(id=oid, user_id=account.id)
    if not o:
        raise BizError("订单不存在", 404)
    if body.status not in ALLOWED_TRANSITIONS.get(o.status, set()):
        raise BizError(f"不允许从 {o.status} 变更为 {body.status}")
    o.status = body.status
    await o.save()
    return Result.success(await order_dict(o))


@router.get("/reviews")
async def list_reviews(product_id: int | None = None, page: int = 1, size: int = 10):
    qs = Review.all()
    if product_id:
        qs = qs.filter(product_id=product_id)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size).prefetch_related("user")
    return Result.page([{
        "id": r.id, "product_id": r.product_id, "rating": r.rating,
        "content": r.content, "images": r.images,
        "user": r.user.nickname if r.user else "匿名",
        "created_at": r.created_at.isoformat(),
    } for r in rows], total, page, size)


@router.post("/reviews")
async def create_review(body: ReviewIn, account: Account = Depends(current_user)):
    r = await Review.create(user_id=account.id, **body.model_dump())
    return Result.success({"id": r.id})


@router.delete("/reviews/{rid}")
async def delete_review(rid: int, _: Account = Depends(admin_user)):
    await Review.filter(id=rid).delete()
    return Result.success()
