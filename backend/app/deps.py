import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header

from app.config import settings
from app.models import User
from app.result import BizError
from app.schemas import Account


def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return hmac.compare_digest(calc, digest)


def create_token(account: Account) -> str:
    payload = {
        "sub": str(account.id),
        "username": account.username,
        "role": account.role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


async def current_user(authorization: str | None = Header(default=None)) -> Account:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise BizError("未登录", 401)
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise BizError("登录已过期，请重新登录", 401)

    # 边界：Account 是 Pydantic 登录态对象，查库必须用 id，而不是把 Account 传给 ORM
    user = await User.get_or_none(id=int(payload["sub"]), status=True)
    if not user:
        raise BizError("用户不存在或已禁用", 401)
    return Account(id=user.id, username=user.username, nickname=user.nickname,
                   avatar=user.avatar, role=user.role)


async def admin_user(account: Account = Depends(current_user)) -> Account:
    if account.role != "admin":
        raise BizError("无管理员权限", 403)
    return account
