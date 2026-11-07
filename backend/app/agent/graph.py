"""LangGraph StateGraph：感知 → 意图路由 → 分支 → 生成 → 持久化。

若当前环境的 langgraph 版本不兼容，自动回退到等价的顺序流水线，保证接口永远可用。
"""
from app.agent.nodes import (chitchat_node, generate_node, perceive, persist_node,
                             rag_node, recommend_node, route_intent, tool_node, vision_node)
from app.agent.state import AgentState

BRANCHES = {
    "rag": rag_node,
    "tool": tool_node,
    "recommend": recommend_node,
    "vision": vision_node,
    "chitchat": chitchat_node,
}


def build_graph():
    from langgraph.graph import END, StateGraph

    g = StateGraph(AgentState)
    g.add_node("perceive", perceive)
    g.add_node("intent", route_intent)
    for name, fn in BRANCHES.items():
        g.add_node(name, fn)
    g.add_node("generate", generate_node)
    g.add_node("persist", persist_node)

    g.set_entry_point("perceive")
    g.add_edge("perceive", "intent")
    g.add_conditional_edges("intent", lambda s: s.get("intent", "chitchat"),
                            {name: name for name in BRANCHES})
    for name in BRANCHES:
        g.add_edge(name, "generate")
    g.add_edge("generate", "persist")
    g.add_edge("persist", END)
    return g.compile()


async def _sequential(state: dict) -> dict:
    state = dict(state)
    for fn in (perceive, route_intent):
        state.update(await fn(state))
    state.update(await BRANCHES.get(state.get("intent", "chitchat"), chitchat_node)(state))
    state.update(await generate_node(state))
    state.update(await persist_node(state))
    return state


async def run(state: dict) -> dict:
    try:
        graph = build_graph()
        return await graph.ainvoke(state)
    except Exception as exc:
        state = dict(state)
        state["trace"] = list(state.get("trace", [])) + [
            {"node": "graph", "detail": f"LangGraph 不可用({exc})，使用顺序流水线", "ts": 0}]
        return await _sequential(state)
