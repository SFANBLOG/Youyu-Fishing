import asyncio
import json

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from app.agent.graph import run as run_graph
from app.deps import admin_user, current_user
from app.models import ChatMessage, ChatSession
from app.result import BizError, Result
from app.schemas import Account, ChatIn

router = APIRouter(tags=["AI 对话"])


async def optional_user(authorization: str | None) -> Account | None:
    if not authorization:
        return None
    try:
        return await current_user(authorization)
    except Exception:
        return None


def sse(payload: dict) -> str:
    return "data: " + json.dumps(payload, ensure_ascii=False) + "\n\n"


@router.post("/chat/stream")
async def chat_stream(body: ChatIn, authorization: str | None = Header(default=None)):
    if not body.message.strip() and not body.images:
        raise BizError("问题不能为空")
    account = await optional_user(authorization)
    user_id = account.id if account else None

    if body.session_id:
        session = await ChatSession.get_or_none(id=body.session_id)
        if not session:
            raise BizError("会话不存在", 404)
    else:
        title = (body.message or "图片咨询")[:40]
        session = await ChatSession.create(user_id=user_id, title=title)

    queue: asyncio.Queue[str] = asyncio.Queue()

    async def emit(delta: str):
        await queue.put(delta)

    state = {
        "query": body.message, "images": body.images, "user_id": user_id,
        "session_id": session.id, "emit": emit,
        "trace": [], "sources": [], "recommendations": [], "hits": [],
        "degraded": False,
    }
    task = asyncio.create_task(run_graph(state))

    async def generator():
        yield sse({"type": "meta", "session_id": session.id})
        try:
            while True:
                try:
                    delta = await asyncio.wait_for(queue.get(), timeout=0.15)
                    yield sse({"type": "delta", "text": delta})
                except asyncio.TimeoutError:
                    if task.done():
                        break
            result = task.result()
            yield sse({
                "type": "done",
                "answer": result.get("answer", ""),
                "intent": result.get("intent", ""),
                "tool": result.get("tool", ""),
                "engine": result.get("engine", ""),
                "degraded": result.get("degraded", False),
                "trace": result.get("trace", []),
                "sources": result.get("sources", []),
                "recommendations": result.get("recommendations", []),
            })
        except Exception as exc:
            yield sse({"type": "error", "message": f"Agent 执行失败: {exc}"})
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"},
    )


@router.get("/chat/sessions")
async def list_sessions(account: Account = Depends(current_user)):
    rows = await ChatSession.filter(user_id=account.id).order_by("-id").limit(50)
    return Result.success([{"id": s.id, "title": s.title,
                            "created_at": s.created_at.isoformat()} for s in rows])


def message_dict(m: ChatMessage) -> dict:
    return {
        "id": m.id, "role": m.role, "content": m.content, "avatar": m.avatar,
        "images": m.images, "intent": m.intent, "tool": m.tool, "engine": m.engine,
        "trace": m.trace, "sources": m.sources, "recommendations": m.recommendations,
        "degraded": m.degraded, "created_at": m.created_at.isoformat(),
    }


@router.get("/chat/sessions/{sid}/messages")
async def session_messages(sid: int, account: Account = Depends(current_user)):
    s = await ChatSession.get_or_none(id=sid, user_id=account.id)
    if not s:
        raise BizError("会话不存在", 404)
    rows = await ChatMessage.filter(session_id=sid).order_by("id")
    return Result.success([message_dict(m) for m in rows])


@router.delete("/chat/sessions/{sid}")
async def delete_session(sid: int, account: Account = Depends(current_user)):
    await ChatSession.filter(id=sid, user_id=account.id).delete()
    return Result.success()


@router.get("/admin/chat/records")
async def chat_records(page: int = 1, size: int = 20, keyword: str = "",
                       _: Account = Depends(admin_user)):
    qs = ChatMessage.all()
    if keyword:
        qs = qs.filter(content__icontains=keyword)
    total = await qs.count()
    rows = await qs.order_by("-id").offset((page - 1) * size).limit(size)
    return Result.page([{**message_dict(m), "session_id": m.session_id} for m in rows],
                       total, page, size)
