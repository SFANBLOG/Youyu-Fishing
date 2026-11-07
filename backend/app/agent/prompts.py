"""提示词全部落库，改完即时生效；未配置时用内置默认值兜底。"""
from app.models import Prompt
from app.seed import DEFAULT_PROMPTS

_FALLBACK = {key: content for key, _, content, _ in DEFAULT_PROMPTS}


async def get_prompt(key: str) -> str:
    p = await Prompt.get_or_none(key=key, enabled=True)
    return p.content if p else _FALLBACK.get(key, "")


def render(template: str, **kwargs) -> str:
    out = template
    for k, v in kwargs.items():
        out = out.replace("{" + k + "}", str(v))
    return out


async def build(key: str, **kwargs) -> str:
    return render(await get_prompt(key), **kwargs)
