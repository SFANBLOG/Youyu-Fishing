from fastapi import APIRouter, Depends

from app.deps import admin_user
from app.llm.factory import mask_key, test_connection
from app.models import AIModel, Prompt
from app.result import BizError, Result
from app.schemas import Account, AIModelIn, PreviewIn, PromptIn

router = APIRouter(prefix="/ai", tags=["AI 能力中心"])


def model_dict(m: AIModel) -> dict:
    return {"id": m.id, "name": m.name, "provider": m.provider, "base_url": m.base_url,
            "api_key": mask_key(m.api_key), "has_key": bool(m.api_key),
            "model_name": m.model_name, "model_type": m.model_type,
            "is_default": m.is_default, "is_multimodal": m.is_multimodal,
            "enabled": m.enabled, "created_at": m.created_at.isoformat()}


def prompt_dict(p: Prompt) -> dict:
    return {"id": p.id, "key": p.key, "name": p.name, "content": p.content,
            "variables": p.variables, "enabled": p.enabled}


@router.get("/models")
async def list_models(_: Account = Depends(admin_user)):
    rows = await AIModel.all().order_by("model_type", "-is_default", "-id")
    return Result.success([model_dict(m) for m in rows])


@router.post("/models")
async def create_model(body: AIModelIn, _: Account = Depends(admin_user)):
    data = body.model_dump()
    if data["is_default"]:
        await AIModel.filter(model_type=data["model_type"]).update(is_default=False)
    m = await AIModel.create(**data)
    return Result.success(model_dict(m))


@router.put("/models/{mid}")
async def update_model(mid: int, body: AIModelIn, _: Account = Depends(admin_user)):
    m = await AIModel.get_or_none(id=mid)
    if not m:
        raise BizError("模型配置不存在", 404)
    data = body.model_dump()
    # 前端回传的是脱敏值，不覆盖真实 key
    if "api_key" in data and "***" in (data["api_key"] or ""):
        data.pop("api_key")
    if data.get("is_default"):
        await AIModel.filter(model_type=data["model_type"]).exclude(id=mid).update(is_default=False)
    for k, v in data.items():
        setattr(m, k, v)
    await m.save()
    return Result.success(model_dict(m))


@router.delete("/models/{mid}")
async def delete_model(mid: int, _: Account = Depends(admin_user)):
    await AIModel.filter(id=mid).delete()
    return Result.success()


@router.post("/models/{mid}/test")
async def test_model(mid: int, _: Account = Depends(admin_user)):
    m = await AIModel.get_or_none(id=mid)
    if not m:
        raise BizError("模型配置不存在", 404)
    ok, msg = await test_connection(m)
    return Result.success({"ok": ok, "message": msg})


@router.post("/models/{mid}/default")
async def set_default(mid: int, _: Account = Depends(admin_user)):
    m = await AIModel.get_or_none(id=mid)
    if not m:
        raise BizError("模型配置不存在", 404)
    await AIModel.filter(model_type=m.model_type).update(is_default=False)
    m.is_default = True
    await m.save()
    return Result.success()


@router.get("/prompts")
async def list_prompts(_: Account = Depends(admin_user)):
    rows = await Prompt.all().order_by("id")
    return Result.success([prompt_dict(p) for p in rows])


@router.post("/prompts")
async def create_prompt(body: PromptIn, _: Account = Depends(admin_user)):
    if await Prompt.exists(key=body.key):
        raise BizError("提示词 key 已存在")
    p = await Prompt.create(**body.model_dump())
    return Result.success(prompt_dict(p))


@router.put("/prompts/{pid}")
async def update_prompt(pid: int, body: PromptIn, _: Account = Depends(admin_user)):
    p = await Prompt.get_or_none(id=pid)
    if not p:
        raise BizError("提示词不存在", 404)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    await p.save()
    return Result.success(prompt_dict(p))


@router.delete("/prompts/{pid}")
async def delete_prompt(pid: int, _: Account = Depends(admin_user)):
    await Prompt.filter(id=pid).delete()
    return Result.success()


@router.post("/prompts/{pid}/preview")
async def preview_prompt(pid: int, body: PreviewIn, _: Account = Depends(admin_user)):
    p = await Prompt.get_or_none(id=pid)
    if not p:
        raise BizError("提示词不存在", 404)
    rendered = p.content
    for k, v in (body.variables or {}).items():
        rendered = rendered.replace("{" + k + "}", str(v))
    return Result.success({"rendered": rendered, "missing": [
        v for v in (p.variables or []) if "{" + v + "}" in rendered]})
