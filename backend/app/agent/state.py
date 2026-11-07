from typing import Awaitable, Callable, TypedDict


class AgentState(TypedDict, total=False):
    # 输入
    query: str
    images: list[str]
    user_id: int | None
    session_id: int
    emit: Callable[[str], Awaitable[None]] | None
    # 中间状态
    intent: str
    vision_result: str
    hits: list[dict]
    sources: list[dict]
    tool: str
    tool_result: str
    tool_data: list[dict]
    recommendations: list[dict]
    context: str
    messages: list[dict]
    answer: str
    # 观测
    trace: list[dict]
    engine: str
    degraded: bool
