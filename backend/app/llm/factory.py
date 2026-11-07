"""模型适配层：**LangChain 为主链路**，所有厂商走 OpenAI 兼容协议。

- 对话/流式：langchain_openai.ChatOpenAI（ainvoke / astream）
- 向量：langchain_openai.OpenAIEmbeddings（aembed_query / aembed_documents）
- 多模态：langchain_core.messages.HumanMessage 直接承载 OpenAI Vision content 列表
- 工具：langchain_core.tools.StructuredTool（见 agent/tools.py）

LLM_FRAMEWORK=httpx 或 LangChain 调用异常时回退 httpx 直连，保证接口不崩。
"""
import json
import logging
from typing import AsyncIterator

import httpx

from app.config import settings
from app.models import AIModel

logger = logging.getLogger("youyu.llm")


def mask_key(key: str) -> str:
    if not key:
        return ""
    return key[:6] + "***" + key[-4:] if len(key) > 12 else "***"


async def get_model(model_type: str = "chat", prefer_multimodal: bool = False) -> AIModel | None:
    qs = AIModel.filter(model_type=model_type, enabled=True)
    if prefer_multimodal:
        qs = qs.filter(is_multimodal=True)
    model = await qs.filter(is_default=True).first()
    if not model:
        model = await qs.order_by("-id").first()
    if not model or model.provider == "offline" or not model.base_url or not model.model_name:
        return None
    return model


def base_url(model: AIModel) -> str:
    url = model.base_url.rstrip("/")
    if not url.endswith("/v1") and "/v1" not in url:
        url += "/v1"
    return url


def headers(model: AIModel) -> dict:
    return {"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"}


def use_langchain() -> bool:
    return settings.LLM_FRAMEWORK.lower() == "langchain"


def langchain_chat(model: AIModel, streaming: bool = False,
                   temperature: float = 0.3, max_tokens: int = 800):
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model.model_name,
        api_key=model.api_key,
        base_url=base_url(model),
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=settings.LLM_TIMEOUT,
        streaming=streaming,
        max_retries=1,
    )


def langchain_embeddings(model: AIModel):
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=model.model_name,
        api_key=model.api_key,
        base_url=base_url(model),
        check_embedding_ctx_length=False,
        timeout=settings.LLM_TIMEOUT,
        max_retries=1,
    )


def to_lc_messages(messages: list[dict]):
    """dict → LangChain Message；content 为 list 时保留 OpenAI Vision 多模态结构。"""
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    classes = {"system": SystemMessage, "assistant": AIMessage}
    return [classes.get(m["role"], HumanMessage)(content=m["content"]) for m in messages]


async def chat(messages: list[dict], model: AIModel | None = None,
               temperature: float = 0.3, max_tokens: int = 800) -> str | None:
    model = model or await get_model("chat")
    if not model:
        return None

    if use_langchain():
        try:
            result = await langchain_chat(model, False, temperature, max_tokens).ainvoke(
                to_lc_messages(messages))
            return result.content
        except ImportError as exc:
            logger.warning("langchain-openai 未安装，回退 httpx：%s", exc)
        except Exception as exc:
            logger.warning("LangChain 调用失败，回退 httpx：%s", exc)

    payload = {"model": model.model_name, "messages": messages,
               "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            r = await client.post(f"{base_url(model)}/chat/completions",
                                  headers=headers(model), json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


async def chat_stream(messages: list[dict], model: AIModel | None = None,
                      temperature: float = 0.3) -> AsyncIterator[str] | None:
    """返回逐块文本；不可用返回 None，由 Agent 走离线兜底。"""
    model = model or await get_model("chat")
    if not model:
        return None

    if use_langchain():
        try:
            llm = langchain_chat(model, streaming=True, temperature=temperature)
            lc_messages = to_lc_messages(messages)

            async def _lc_gen():
                async for chunk in llm.astream(lc_messages):
                    if chunk.content:
                        yield chunk.content

            return _lc_gen()
        except ImportError as exc:
            logger.warning("langchain-openai 未安装，回退 httpx 流式：%s", exc)
        except Exception as exc:
            logger.warning("LangChain 流式初始化失败，回退 httpx：%s", exc)

    payload = {"model": model.model_name, "messages": messages,
               "temperature": temperature, "stream": True}
    try:
        client = httpx.AsyncClient(timeout=settings.LLM_TIMEOUT)

        async def _gen():
            async with client:
                async with client.stream("POST", f"{base_url(model)}/chat/completions",
                                         headers=headers(model), json=payload) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if raw == "[DONE]":
                            break
                        try:
                            delta = json.loads(raw)["choices"][0]["delta"].get("content", "")
                        except (KeyError, IndexError, json.JSONDecodeError):
                            continue
                        if delta:
                            yield delta

        return _gen()
    except Exception:
        await client.aclose()
        return None


async def embed(texts: list[str], model: AIModel | None = None) -> list[list[float]]:
    model = model or await get_model("embedding")
    if not model or not texts:
        return []

    if use_langchain():
        try:
            emb = langchain_embeddings(model)
            if len(texts) == 1:
                return [await emb.aembed_query(texts[0])]
            return await emb.aembed_documents(texts)
        except ImportError as exc:
            logger.warning("langchain-openai 未安装，回退 httpx embedding：%s", exc)
        except Exception as exc:
            logger.warning("LangChain embedding 失败，回退 httpx：%s", exc)

    payload = {"model": model.model_name,
               "input": texts if len(texts) > 1 else texts[0]}
    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            r = await client.post(f"{base_url(model)}/embeddings",
                                  headers=headers(model), json=payload)
            r.raise_for_status()
            data = r.json()["data"]
            return [item["embedding"] for item in sorted(data, key=lambda x: x.get("index", 0))]
    except Exception:
        return []


async def test_connection(model: AIModel) -> tuple[bool, str]:
    if model.provider == "offline" or not model.base_url:
        return False, "未配置 base_url 或为离线模型"
    if model.model_type == "embedding":
        vec = await embed(["连接测试"], model)
        return (bool(vec), "连接成功" if vec else "embedding 调用失败")
    result = await chat([{"role": "user", "content": "只回复：OK"}], model, max_tokens=16)
    return (result is not None, "连接成功" if result is not None else "调用失败，请检查 key / 模型名 / 余额")
