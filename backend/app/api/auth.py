from fastapi import APIRouter, Depends

from app.deps import create_token, current_user, hash_password, verify_password
from app.models import User
from app.result import BizError, Result
from app.schemas import Account, LoginIn, RegisterIn

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register(body: RegisterIn):
    if await User.exists(username=body.username):
        raise BizError("用户名已存在")
    user = await User.create(
        username=body.username,
        password_hash=hash_password(body.password),
        nickname=body.nickname or body.username,
        phone=body.phone,
    )
    account = Account(id=user.id, username=user.username, nickname=user.nickname, role=user.role)
    return Result.success({"token": create_token(account), "user": account.model_dump()})


@router.post("/login")
async def login(body: LoginIn):
    user = await User.get_or_none(username=body.username)
    if not user or not verify_password(body.password, user.password_hash):
        raise BizError("用户名或密码错误")
    if not user.status:
        raise BizError("账号已被禁用", 403)
    account = Account(id=user.id, username=user.username, nickname=user.nickname,
                      avatar=user.avatar, role=user.role)
    return Result.success({"token": create_token(account), "user": account.model_dump()})


@router.get("/me")
async def me(account: Account = Depends(current_user)):
    return Result.success(account.model_dump())
