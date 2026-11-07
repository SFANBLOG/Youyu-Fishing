import json
import time

from app.agent.prompts import build, get_prompt
from app.agent.state import AgentState
from app.agent.tools import dispatch
from app.llm.factory import chat, chat_stream, get_model
from app.llm.vision import describe_images
from app.models import ChatMessage
from app.rag.retriever import hybrid_search


def _trace(state: dict, node: str, detail: str) -> list[dict]:
    trace = list(state.get("trace", []))
    trace.append({"node": node, "detail": detail[:300], "ts": int(time.time() * 1000)})
    return trace


async def perceive(state: AgentState) -> dict:
    state = dict(state)
    images = state.get("images") or []
    if not images:
        return {"trace": _trace(state, "perceive", "纯文本输入"), "vision_result": ""}
    result, engine = await describe_images(state.get("query", ""), images)
    degraded = result is None
    return {
        "vision_result": result or "（未配置多模态模型，仅按文字问题处理）",
        "engine": engine,
        "degraded": degraded or state.get("degraded", False),
        "trace": _trace(state, "perceive", f"Vision 引擎={engine}, 识别成功={not degraded}"),
    }


def _keyword_intent(query: str, has_images: bool) -> str:
    q = (query or "").lower()
    if has_images and any(k in q for k in ("这", "图", "识别", "什么装备", "看看")):
        return "vision"
    if any(k in q for k in ("订单", "物流", "发货", "买了什么", "购物车", "加购", "搜索", "多少钱")):
        return "tool"
    if any(k in q for k in ("推荐", "选竿", "新手", "预算", "买哪", "搭配")):
        return "recommend"
    if any(k in q for k in ("调性", "保养", "钓法", "怎么选", "为什么", "区别", "知识", "教程", "原理", "PE线", "拟饵")):
        return "rag"
    return "chitchat"


async def route_intent(state: AgentState) -> dict:
    state = dict(state)
    query = state.get("query", "")
    has_images = bool(state.get("images"))
    fallback = _keyword_intent(query, has_images)
    model = await get_model("chat")
    intent = None
    engine = model.model_name if model else "keyword-rule"
    if model:
        prompt = await build("intent", query=query)
        answer = await chat([{"role": "user", "content": prompt}], model, max_tokens=16)
        if answer:
            for candidate in ("rag", "tool", "recommend", "chitchat", "vision"):
                if candidate in answer.strip().lower():
                    intent = candidate
                    break
    if not intent:
        intent = fallback
        engine = "keyword-rule (LLM 降级)"
    if has_images and intent == "chitchat":
        intent = "vision"
    return {"intent": intent, "engine": engine,
            "trace": _trace(state, "intent", f"意图={intent}, 路由引擎={engine}")}


async def rag_node(state: AgentState) -> dict:
    state = dict(state)
    result = await hybrid_search(state.get("query", ""), top_k=4)
    hits = result["hits"]
    context = "\n\n".join(f"[{i + 1}] {h['doc_title']}：{h['content']}" for i, h in enumerate(hits))
    return {
        "hits": hits, "sources": hits, "context": context,
        "degraded": state.get("degraded", False) or result["degraded"],
        "trace": _trace(state, "rag", f"{result['engine']}, 命中 {len(hits)} 块, 向量块 {result['vector_count']}"),
    }


async def tool_node(state: AgentState) -> dict:
    state = dict(state)
    name, text, data = await dispatch(state.get("intent", "tool"), state.get("query", ""),
                                      state.get("user_id"))
    return {"tool": name, "tool_result": text, "tool_data": data,
            "recommendations": data if state.get("intent") == "recommend" else [],
            "context": text,
            "trace": _trace(state, "tool", f"调用 {name}, 返回 {len(data)} 条")}


async def recommend_node(state: AgentState) -> dict:
    return await tool_node(state)


async def vision_node(state: AgentState) -> dict:
    state = dict(state)
    text, data = await dispatch("tool", state.get("query", ""), state.get("user_id"))
    return {"tool": "search_products", "tool_result": text, "tool_data": data,
            "recommendations": data[:3],
            "context": f"图片识别：{state.get('vision_result', '')}\n候选商品：{text}",
            "trace": _trace(state, "vision", "图片理解 + 商品匹配")}


async def chitchat_node(state: AgentState) -> dict:
    state = dict(state)
    return {"context": "", "trace": _trace(state, "chitchat", "无需检索与工具")}


def _offline_answer(state: dict) -> str:
    lines = ["（当前未配置可用大模型，已切换离线兜底回复，以下为工具与检索的真实结果）"]
    if state.get("vision_result"):
        lines.append(f"\n图片理解：{state['vision_result']}")
    if state.get("hits"):
        lines.append("\n知识库命中：")
        for i, h in enumerate(state["hits"][:3], 1):
            lines.append(f"{i}. {h['doc_title']}：{h['content'][:160]}")
    if state.get("tool_result"):
        lines.append(f"\n工具 {state.get('tool')} 返回：{state['tool_result'][:400]}")
    if not (state.get("hits") or state.get("tool_result") or state.get("vision_result")):
        lines.append("\n暂无可用资料，请在后台配置模型或添加知识库文档。")
    return "\n".join(lines)


async def generate_node(state: AgentState) -> dict:
    state = dict(state)
    intent = state.get("intent", "chitchat")
    query = state.get("query", "")
    context = state.get("context", "")

    key_map = {"rag": "rag", "tool": "tool_answer", "recommend": "recommend",
               "vision": "vision", "chitchat": "chitchat"}
    user_prompt = await build(key_map.get(intent, "chitchat"),
                              query=query, context=context,
                              tool=state.get("tool", ""), tool_result=state.get("tool_result", ""),
                              products=state.get("tool_result", ""),
                              vision_result=state.get("vision_result", ""))
    system = await get_prompt("agent_system")
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user_prompt}]
    model = await get_model("chat", prefer_multimodal=bool(state.get("images")))
    emit = state.get("emit")

    collected = ""
    used_engine = model.model_name if model else "offline-fallback"
    if model:
        try:
            stream = await chat_stream(messages, model)
            if stream:
                async for delta in stream:
                    collected += delta
                    if emit:
                        await emit(delta)
        except Exception as exc:
            state["trace"] = _trace(state, "generate", f"流式异常 {exc}，转离线兜底")
    if not collected.strip():
        collected = _offline_answer(state)
        used_engine = "offline-fallback"
        if emit:
            for i in range(0, len(collected), 12):
                await emit(collected[i:i + 12])
    return {
        "answer": collected, "messages": messages, "engine": used_engine,
        "degraded": state.get("degraded", False) or used_engine == "offline-fallback",
        "trace": _trace(state, "generate", f"引擎={used_engine}, 输出 {len(collected)} 字"),
    }


async def persist_node(state: AgentState) -> dict:
    state = dict(state)
    sid = state.get("session_id")
    if not sid:
        return {"trace": _trace(state, "persist", "无会话，跳过持久化")}
    await ChatMessage.create(
        session_id=sid, role="user", content=state.get("query", ""),
        images=state.get("images") or [], intent=state.get("intent", ""),
    )
    await ChatMessage.create(
        session_id=sid, role="assistant", content=state.get("answer", ""),
        intent=state.get("intent", ""), tool=state.get("tool", ""),
        engine=state.get("engine", ""), trace=state.get("trace", []),
        sources=state.get("sources", []), recommendations=state.get("recommendations", []),
        degraded=state.get("degraded", False),
    )
    return {"trace": _trace(state, "persist", "消息 / 轨迹 / 引用 / 推荐已落库")}
