"""OpenAI Vision 协议：文本 + 图片拼进同一条 user 消息。"""
from app.llm.factory import chat, get_model


def build_vision_messages(query: str, images: list[str], system: str = "") -> list[dict]:
    content: list[dict] = [{"type": "text", "text": query or "请描述图片中的渔具并给出选购建议"}]
    for img in images:
        # base64 传 data:image/...;base64,xxx；也可直接传 http(s) URL
        content.append({"type": "image_url", "image_url": {"url": img, "detail": "low"}})
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": content})
    return msgs


async def describe_images(query: str, images: list[str]) -> tuple[str | None, str]:
    """返回 (识别文本, 引擎名)；无多模态模型返回 (None, 引擎名)。"""
    if not images:
        return None, ""
    model = await get_model("chat", prefer_multimodal=True) or await get_model("vision")
    if not model:
        return None, "offline-vision"
    result = await chat(
        build_vision_messages(query, images,
                              "你是渔具鉴定助手，识别图片中的装备品类、特征与适用场景，简明输出。"),
        model,
        max_tokens=400,
    )
    return result, model.model_name
