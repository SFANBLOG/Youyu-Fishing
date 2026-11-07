from tortoise import fields, models


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class User(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(64, unique=True)
    password_hash = fields.CharField(255)
    nickname = fields.CharField(64, default="")
    avatar = fields.CharField(255, default="")
    phone = fields.CharField(32, default="")
    role = fields.CharField(16, default="user")  # user | admin
    status = fields.BooleanField(default=True)

    class Meta:
        table = "yy_user"


class Category(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(64, unique=True)
    icon = fields.CharField(255, default="")
    sort = fields.IntField(default=0)

    class Meta:
        table = "yy_category"


class Product(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(200)
    subtitle = fields.CharField(255, default="")
    category: fields.ForeignKeyRelation["Category"] = fields.ForeignKeyField(
        "models.Category", related_name="products", null=True, on_delete=fields.SET_NULL
    )
    price = fields.FloatField(default=0)
    original_price = fields.FloatField(default=0)
    stock = fields.IntField(default=0)
    sales = fields.IntField(default=0)
    cover = fields.CharField(255, default="")
    images = fields.JSONField(default=list)       # 多图
    specs = fields.JSONField(default=list)        # [{name, options:[...]}]
    detail = fields.TextField(default="")         # 富文本图文详情
    tags = fields.JSONField(default=list)
    status = fields.BooleanField(default=True)    # 上下架

    class Meta:
        table = "yy_product"


class Favorite(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="favorites", on_delete=fields.CASCADE
    )
    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product", related_name="favorites", on_delete=fields.CASCADE
    )

    class Meta:
        table = "yy_favorite"
        unique_together = (("user", "product"),)


class CartItem(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="cart_items", on_delete=fields.CASCADE
    )
    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product", related_name="cart_items", on_delete=fields.CASCADE
    )
    spec = fields.CharField(255, default="")
    quantity = fields.IntField(default=1)
    checked = fields.BooleanField(default=True)

    class Meta:
        table = "yy_cart"


class Order(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    order_no = fields.CharField(64, unique=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="orders", on_delete=fields.CASCADE
    )
    total_amount = fields.FloatField(default=0)
    status = fields.CharField(24, default="pending")  # pending/paid/shipped/completed/cancelled
    address = fields.JSONField(default=dict)
    remark = fields.CharField(500, default="")

    class Meta:
        table = "yy_order"


class OrderItem(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    order: fields.ForeignKeyRelation["Order"] = fields.ForeignKeyField(
        "models.Order", related_name="items", on_delete=fields.CASCADE
    )
    product_id = fields.IntField()
    title = fields.CharField(200)
    cover = fields.CharField(255, default="")
    spec = fields.CharField(255, default="")
    price = fields.FloatField(default=0)
    quantity = fields.IntField(default=1)

    class Meta:
        table = "yy_order_item"


class Review(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="reviews", on_delete=fields.CASCADE
    )
    product: fields.ForeignKeyRelation["Product"] = fields.ForeignKeyField(
        "models.Product", related_name="reviews", on_delete=fields.CASCADE
    )
    order_id = fields.IntField(null=True)
    rating = fields.IntField(default=5)
    content = fields.TextField(default="")
    images = fields.JSONField(default=list)

    class Meta:
        table = "yy_review"


class News(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(200)
    cover = fields.CharField(255, default="")
    summary = fields.CharField(500, default="")
    content = fields.TextField(default="")   # 富文本，带图带视频
    views = fields.IntField(default=0)
    status = fields.BooleanField(default=True)

    class Meta:
        table = "yy_news"


class Banner(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(200, default="")
    image = fields.CharField(255, default="")
    link = fields.CharField(255, default="")
    sort = fields.IntField(default=0)
    status = fields.BooleanField(default=True)

    class Meta:
        table = "yy_banner"


class Notice(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(200)
    content = fields.TextField(default="")
    status = fields.BooleanField(default=True)

    class Meta:
        table = "yy_notice"


class AIModel(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(100)
    provider = fields.CharField(64, default="openai-compatible")
    base_url = fields.CharField(255, default="")
    api_key = fields.CharField(500, default="")
    model_name = fields.CharField(128, default="")
    model_type = fields.CharField(24, default="chat")  # chat | embedding | vision
    is_default = fields.BooleanField(default=False)
    is_multimodal = fields.BooleanField(default=False)
    enabled = fields.BooleanField(default=True)

    class Meta:
        table = "yy_ai_model"


class Prompt(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    key = fields.CharField(64, unique=True)
    name = fields.CharField(100, default="")
    content = fields.TextField(default="")
    variables = fields.JSONField(default=list)
    enabled = fields.BooleanField(default=True)

    class Meta:
        table = "yy_prompt"


class KnowledgeDoc(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(200)
    filename = fields.CharField(255, default="")
    content = fields.TextField(default="")
    chunk_count = fields.IntField(default=0)
    status = fields.CharField(24, default="ready")  # ready | indexing | error

    class Meta:
        table = "yy_knowledge_doc"


class KnowledgeChunk(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    doc: fields.ForeignKeyRelation["KnowledgeDoc"] = fields.ForeignKeyField(
        "models.KnowledgeDoc", related_name="chunks", on_delete=fields.CASCADE
    )
    idx = fields.IntField(default=0)
    content = fields.TextField(default="")
    start_char = fields.IntField(default=0)
    end_char = fields.IntField(default=0)
    embedding = fields.JSONField(default=list)  # 兼容旧版占位；向量统一存 Milvus，此处恒为空

    class Meta:
        table = "yy_knowledge_chunk"


class ChatSession(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField(
        "models.User", related_name="chat_sessions", null=True, on_delete=fields.SET_NULL
    )
    title = fields.CharField(200, default="新会话")

    class Meta:
        table = "yy_chat_session"


class ChatMessage(TimestampMixin, models.Model):
    id = fields.IntField(pk=True)
    session: fields.ForeignKeyRelation["ChatSession"] = fields.ForeignKeyField(
        "models.ChatSession", related_name="messages", on_delete=fields.CASCADE
    )
    role = fields.CharField(16, default="user")  # user | assistant
    content = fields.TextField(default="")
    avatar = fields.CharField(255, default="")
    images = fields.JSONField(default=list)
    intent = fields.CharField(32, default="")
    tool = fields.CharField(64, default="")
    engine = fields.CharField(64, default="")
    trace = fields.JSONField(default=list)            # [{node, detail, ts}]
    sources = fields.JSONField(default=list)          # [{doc_id, idx, content, score}]
    recommendations = fields.JSONField(default=list)  # 商品卡片
    degraded = fields.BooleanField(default=False)

    class Meta:
        table = "yy_chat_message"
