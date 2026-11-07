"""Agent 工具注册表。

工具描述写清楚「什么时候用、参数是什么」，模型才调得准。
这里用轻量注册表实现（等价于 LangChain Tool 的 name/description/coroutine 三要素），
如需换成 StructuredTool，只需把 TOOL_SPECS 映射到 langchain_core.tools.StructuredTool。
"""
import json
import re

from app.api.shop import product_dict
from app.models import CartItem, Order, Product

TOOL_SPECS = [
    {"name": "search_products", "description": "按关键词搜索在售商品，返回名称、价格、销量、库存",
     "when": ["找商品", "有没有", "多少钱", "查一下竿"]},
    {"name": "add_to_cart", "description": "把指定商品加入当前用户购物车",
     "when": ["加购", "加入购物车", "帮我买"]},
    {"name": "recommend_products", "description": "按预算/场景/鱼种推荐合适的商品",
     "when": ["推荐", "选竿", "新手", "预算"]},
    {"name": "query_orders", "description": "查询当前用户最近订单及状态",
     "when": ["订单", "物流", "发货", "买了什么"]},
]


async def search_products(keyword: str, limit: int = 5) -> tuple[str, list[dict]]:
    words = [w for w in re.split(r"[\s,，、/]+", keyword) if len(w) >= 2][:3]
    qs = Product.filter(status=True)
    rows = []
    if words:
        for w in words[:1]:
            rows = await qs.filter(title__icontains=w).order_by("-sales").limit(limit)
            if rows:
                break
    if not rows:
        rows = await Product.filter(status=True).order_by("-sales").limit(limit)
    data = [product_dict(p) for p in rows]
    text = json.dumps([{"title": d["title"], "price": d["price"], "sales": d["sales"]}
                       for d in data], ensure_ascii=False)
    return text, data


async def add_to_cart(product_id: int, user_id: int | None, quantity: int = 1) -> tuple[str, list[dict]]:
    if not user_id:
        return "用户未登录，无法加购，请提示用户先登录", []
    p = await Product.get_or_none(id=product_id, status=True)
    if not p:
        return "商品不存在或已下架", []
    c = await CartItem.get_or_none(user_id=user_id, product_id=product_id, spec="")
    if c:
        c.quantity += quantity
        await c.save()
    else:
        await CartItem.create(user_id=user_id, product_id=product_id, spec="", quantity=quantity)
    d = product_dict(p)
    return f"已把「{p.title}」加入购物车，单价 {p.price} 元", [d]


async def recommend_products(query: str, limit: int = 3) -> tuple[str, list[dict]]:
    budgets = re.findall(r"(\d{2,5})\s*[元块]", query)
    qs = Product.filter(status=True)
    if budgets:
        budget = float(budgets[0])
        qs = qs.filter(price__lte=budget * 1.15)
    rows = await qs.order_by("-sales").limit(limit)
    if not rows:
        rows = await Product.filter(status=True).order_by("-sales").limit(limit)
    data = [product_dict(p) for p in rows]
    text = json.dumps([{"title": d["title"], "price": d["price"], "subtitle": d["subtitle"]}
                       for d in data], ensure_ascii=False)
    return text, data


async def query_orders(user_id: int | None) -> tuple[str, list[dict]]:
    if not user_id:
        return "用户未登录，无法查询订单", []
    rows = await Order.filter(user_id=user_id).order_by("-id").limit(5)
    data = [{"order_no": o.order_no, "amount": o.total_amount, "status": o.status,
             "created_at": o.created_at.isoformat()} for o in rows]
    return json.dumps(data, ensure_ascii=False), data


async def dispatch(intent: str, query: str, user_id: int | None) -> tuple[str, str, list[dict]]:
    """返回 (tool_name, tool_result_text, structured_data)。"""
    if intent == "recommend":
        text, data = await recommend_products(query)
        return "recommend_products", text, data
    if intent == "tool":
        q = query.lower()
        if any(k in q for k in ("订单", "物流", "发货", "买了什么")):
            text, data = await query_orders(user_id)
            return "query_orders", text, data
        m = re.search(r"加购|加入购物车|帮我买", query)
        if m:
            # 演示：取热销第一款加购，生产应由 LLM 输出结构化参数
            hot = await Product.filter(status=True).order_by("-sales").first()
            if hot:
                text, data = await add_to_cart(hot.id, user_id)
                return "add_to_cart", text, data
        text, data = await search_products(query)
        return "search_products", text, data
    return "", "", []
