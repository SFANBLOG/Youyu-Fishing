"""Agent 工具注册表：**LangChain StructuredTool**。

每个工具都是可被 `llm.bind_tools(LANGCHAIN_TOOLS)` 或 LangGraph `ToolNode` 直接使用的
标准 BaseTool；当前状态图里由 dispatch 显式调用底层函数以保留结构化数据（商品卡片），
工具描述与参数 schema 的唯一真相源是这里的 StructuredTool。
"""
import json
import re

from langchain_core.tools import StructuredTool

from app.api.shop import product_dict
from app.models import CartItem, Order, Product


async def _lc_search_products(keyword: str) -> str:
    text, _ = await search_products(keyword)
    return text


async def _lc_add_to_cart(product_id: int, user_id: int) -> str:
    text, _ = await add_to_cart(product_id, user_id)
    return text


async def _lc_recommend_products(query: str) -> str:
    text, _ = await recommend_products(query)
    return text


async def _lc_query_orders(user_id: int) -> str:
    text, _ = await query_orders(user_id)
    return text


LANGCHAIN_TOOLS = [
    StructuredTool.from_function(
        coroutine=_lc_search_products, name="search_products",
        description="按关键词搜索在售渔具商品，返回名称、价格、销量。参数 keyword 为商品名关键词。"),
    StructuredTool.from_function(
        coroutine=_lc_add_to_cart, name="add_to_cart",
        description="把指定商品加入购物车。参数 product_id 为商品 ID，user_id 为当前用户 ID。"),
    StructuredTool.from_function(
        coroutine=_lc_recommend_products, name="recommend_products",
        description="按预算、鱼种、场景推荐合适商品。参数 query 为用户的原始需求。"),
    StructuredTool.from_function(
        coroutine=_lc_query_orders, name="query_orders",
        description="查询指定用户最近订单及状态。参数 user_id 为当前用户 ID。"),
]
TOOL_MAP = {t.name: t for t in LANGCHAIN_TOOLS}
TOOL_SPECS = [
    {"name": t.name, "description": t.description,
     "when": {"search_products": ["找商品", "有没有", "多少钱"],
              "add_to_cart": ["加购", "加入购物车"],
              "recommend_products": ["推荐", "选竿", "预算"],
              "query_orders": ["订单", "物流", "发货"]}[t.name]}
    for t in LANGCHAIN_TOOLS
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
