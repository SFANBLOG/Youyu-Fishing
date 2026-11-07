from typing import Any

from pydantic import BaseModel, Field


class Account(BaseModel):
    """登录态对象（Pydantic），不是 ORM 模型，不能直接传给 get_or_none。"""

    id: int
    username: str
    nickname: str = ""
    avatar: str = ""
    role: str = "user"


class LoginIn(BaseModel):
    username: str
    password: str


class RegisterIn(BaseModel):
    username: str
    password: str
    nickname: str = ""
    phone: str = ""


class ProductIn(BaseModel):
    title: str
    subtitle: str = ""
    category_id: int | None = None
    price: float = 0
    original_price: float = 0
    stock: int = 0
    cover: str = ""
    images: list[str] = Field(default_factory=list)
    specs: list[dict] = Field(default_factory=list)
    detail: str = ""
    tags: list[str] = Field(default_factory=list)
    status: bool = True


class CartIn(BaseModel):
    product_id: int
    spec: str = ""
    quantity: int = 1
    checked: bool = True


class OrderIn(BaseModel):
    cart_ids: list[int]
    address: dict = Field(default_factory=dict)
    remark: str = ""


class ReviewIn(BaseModel):
    product_id: int
    order_id: int | None = None
    rating: int = 5
    content: str = ""
    images: list[str] = Field(default_factory=list)


class NewsIn(BaseModel):
    title: str
    cover: str = ""
    summary: str = ""
    content: str = ""
    status: bool = True


class BannerIn(BaseModel):
    title: str = ""
    image: str = ""
    link: str = ""
    sort: int = 0
    status: bool = True


class NoticeIn(BaseModel):
    title: str
    content: str = ""
    status: bool = True


class AIModelIn(BaseModel):
    name: str
    provider: str = "openai-compatible"
    base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    model_type: str = "chat"
    is_default: bool = False
    is_multimodal: bool = False
    enabled: bool = True


class PromptIn(BaseModel):
    key: str
    name: str = ""
    content: str = ""
    variables: list[str] = Field(default_factory=list)
    enabled: bool = True


class KnowledgeIn(BaseModel):
    title: str
    content: str
    filename: str = ""


class SearchTestIn(BaseModel):
    query: str
    top_k: int = 5


class ChatIn(BaseModel):
    message: str = ""
    session_id: int | None = None
    images: list[str] = Field(default_factory=list)  # data:image/...;base64,xxx 或 http(s) URL


class StatusIn(BaseModel):
    status: str


class IdsIn(BaseModel):
    ids: list[int]


class PreviewIn(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)
