from app.deps import hash_password
from app.models import (AIModel, Banner, Category, KnowledgeChunk, KnowledgeDoc,
                        News, Notice, Product, Prompt, User)
from app.rag.chunker import split_text

DEFAULT_PROMPTS = [
    ("agent_system", "AI 助手系统提示词",
     "你是「有渔」渔具商城的专业选竿助手。回答准确、简洁、口语化，只依据给定资料与工具结果回答；资料里没有的内容不要编造。涉及推荐时说明依据。", ["shop_name"]),
    ("intent", "意图路由提示词",
     "判断用户意图，只输出一个词：rag / tool / recommend / chitchat / vision。\n"
     "rag=询问商品知识、保养、钓法、材质等专业知识；tool=要搜商品、加购物车、查订单；"
     "recommend=求推荐、选竿、预算搭配；vision=主要围绕上传图片提问；其余为 chitchat。\n用户问题：{query}", ["query"]),
    ("rag", "RAG 回答提示词",
     "依据以下知识库片段回答用户问题，必须贴合片段内容，无法回答时明确说明。\n\n资料：\n{context}\n\n问题：{query}", ["context", "query"]),
    ("tool_answer", "工具结果回答提示词",
     "根据工具返回的真实结果，用自然语言总结回答，不得虚构不存在的商品或订单。\n\n工具：{tool}\n结果：{tool_result}\n\n问题：{query}", ["tool", "tool_result", "query"]),
    ("chitchat", "闲聊提示词", "友好简短地回应用户，并适时引导到选竿、商品或知识咨询。\n用户：{query}", ["query"]),
    ("vision", "图片理解提示词",
     "识别图片中的渔具/钓场信息：品类、特征、可能的使用场景，并给出选购建议。内容：{vision_result}\n用户问题：{query}", ["vision_result", "query"]),
    ("recommend", "商品推荐提示词",
     "根据用户需求与下列候选商品，推荐最合适的 2-3 款并说明理由，不要推荐列表之外的商品。\n候选：{products}\n需求：{query}", ["products", "query"]),
]

CATEGORIES = ["手竿/台钓竿", "路亚竿", "鱼线轮", "鱼线", "浮漂", "饵料/配件"]

PRODUCTS = [
    ("轻羽 4.5m 超轻碳素台钓竿", "28 调，鲫鲤通用", "手竿/台钓竿", 399, 499, 120, 860),
    ("轻羽 5.4m 高碳竞技竿", "轻量持握，久钓不累", "手竿/台钓竿", 529, 659, 80, 512),
    ("逐浪 6.3m 大物竿", "腰力足，适合水库守大鱼", "手竿/台钓竿", 699, 899, 45, 330),
    ("溪流 3.6m 短节便携竿", "收纳仅 58cm，出行友好", "手竿/台钓竿", 219, 279, 200, 970),
    ("猎鲈 ML 直柄路亚竿 2.1m", "快调，感度清晰", "路亚竿", 459, 559, 90, 610),
    ("猎鲈 M 枪柄路亚竿 2.28m", "泛用翘嘴鲈鱼", "路亚竿", 489, 599, 75, 420),
    ("远投 MH 路亚竿 2.4m", "远投打黑，强腰", "路亚竿", 619, 759, 40, 210),
    ("疾风 2000 型纺车轮", "5.2:1，顺滑防缠线", "鱼线轮", 259, 329, 150, 780),
    ("疾风 3000 型深线杯轮", "大水体远投适用", "鱼线轮", 299, 379, 110, 460),
    ("拉力王 尼龙主线 100m", "低延展，耐磨抗卷", "鱼线", 39, 59, 500, 2100),
    ("纳米浮漂 3 支套装", "高灵敏，醒目尾", "浮漂", 69, 89, 260, 1320),
    ("综合腥香饵 500g", "鲫鲤通杀，状态稳定", "饵料/配件", 25, 35, 800, 3400),
]

DOCS = [
    ("选竿与调性入门", "选竿.md",
     "选竿首先看目标鱼种和水域。鲫鱼、白条等小型鱼适合 37 调或 28 调的软竿，手感轻、护线；鲤鱼、草鱼等中大型鱼建议 28 调或 19 调硬竿，腰力足、起鱼快。"
     "长度常见 3.6 米、4.5 米、5.4 米、6.3 米。野钓小水面 4.5 米最通用，水库或大水面守大鱼用 5.4 米以上。新手优先 4.5 米 28 调，兼顾手感与控鱼。"
     "碳素竿含碳量越高越轻越硬，但也更脆，磕碰和踩踏容易断裂。收纳与运输要用竿袋，竿稍最细，抽竿时从竿稍开始逐节抽出，收竿反向从大把节收回。"
     "调性不是越硬越好：竿太硬遇到细线容易切线，太软刺鱼无力、回鱼慢。搭配线组时，主线号数应与目标鱼体重和竿子调性匹配，一般钓鲫 0.8-1.2 号主线即可。"),
    ("路亚装备与拟饵搭配", "路亚.md",
     "路亚竿按硬度分 UL、L、ML、M、MH、H。翘嘴、鲈鱼泛用选 ML 或 M，打黑、雷强选 MH 以上。直柄竿配纺车轮，操作简单不易炸线；枪柄竿配水滴轮，抛投精准但需要练习刹车。"
     "拟饵分硬饵与软饵：米诺适合搜索中上层，亮片远投搜索范围大，VIB 适合深水快速搜索，软虫配铅头钩适合底层慢速磨鱼。"
     "季节影响作钓策略：春季鱼靠岸产卵，浅滩软饵效果好；夏季高温鱼躲深水与阴影，早晚窗口期用亮片远投；秋季饵鱼丰富，米诺抽停容易激发追咬。"
     "线组方面，PE 线感度高、无延展，建议主线 PE 0.8-1.2 号加前导碳线 2-3 号；前导长度 1-1.5 米，既能防磨又能降低鱼的警觉。"),
]


async def seed() -> None:
    if not await User.exists():
        await User.create(username="admin", password_hash=hash_password("123456"),
                          nickname="超级管理员", role="admin")
        await User.create(username="user", password_hash=hash_password("123456"),
                          nickname="钓友小明", role="user")

    cat_map: dict[str, Category] = {}
    for i, name in enumerate(CATEGORIES):
        obj, _ = await Category.get_or_create(name=name, defaults={"sort": i})
        cat_map[name] = obj

    if not await Product.exists():
        for i, (title, subtitle, cat, price, origin, stock, sales) in enumerate(PRODUCTS):
            await Product.create(
                title=title, subtitle=subtitle, category=cat_map[cat],
                price=price, original_price=origin, stock=stock, sales=sales,
                cover=f"/static/demo/product_{(i % 6) + 1}.svg",
                images=[f"/static/demo/product_{(i % 6) + 1}.svg"],
                specs=[{"name": "规格", "options": ["标准版", "套装版"]}],
                detail=f"<h3>{title}</h3><p>{subtitle}。适合休闲野钓与进阶作钓，出厂逐支检测。</p>",
                tags=["热销", "新品"] if i < 4 else ["热销"],
            )

    if not await News.exists():
        await News.create(title="秋季野钓选竿指南：调性、长度与线组怎么配", cover="",
                          summary="从目标鱼种出发，三步选到合适的手竿。",
                          content="<h2>先看鱼，再看竿</h2><p>钓鲫与守鲤完全是两套思路……</p>")
        await News.create(title="路亚新手常踩的 5 个坑", cover="",
                          summary="炸线、挂底、拟饵选错，一次讲清。",
                          content="<h2>从纺车轮开始</h2><p>直柄竿 + 纺车轮是最省心的入门组合……</p>")
        await News.create(title="钓竿保养：延长碳素竿寿命的 4 个习惯", cover="",
                          summary="用完擦干、避免暴晒、逐节收纳。",
                          content="<h2>别小看擦竿</h2><p>泥沙与盐分会侵蚀竿节接口……</p>")

    if not await Banner.exists():
        for i in range(1, 4):
            await Banner.create(title=f"秋季上新 {i}", image=f"/static/demo/banner_{i}.svg",
                                link="/products", sort=i)

    if not await Notice.exists():
        await Notice.create(title="国庆假期发货安排", content="10 月 1 日 - 3 日订单顺延至 4 日发出。")
        await Notice.create(title="新用户注册即送 20 元选竿券", content="券在结算页自动可用。")

    for key, name, content, variables in DEFAULT_PROMPTS:
        if not await Prompt.exists(key=key):
            await Prompt.create(key=key, name=name, content=content, variables=variables)

    if not await AIModel.exists():
        await AIModel.create(name="未配置（离线兜底）", provider="offline", model_type="chat",
                             model_name="offline", is_default=True, enabled=True)

    if not await KnowledgeDoc.exists():
        for title, filename, content in DOCS:
            doc = await KnowledgeDoc.create(title=title, filename=filename, content=content)
            chunks = split_text(content)
            for c in chunks:
                await KnowledgeChunk.create(doc=doc, idx=c["idx"], content=c["content"],
                                            start_char=c["start"], end_char=c["end"])
            doc.chunk_count = len(chunks)
            await doc.save()
