from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class Result:
    @staticmethod
    def success(data=None, msg: str = "success", **extra):
        body = {"code": 0, "msg": msg, "data": data}
        body.update(extra)
        return body

    @staticmethod
    def fail(msg: str = "fail", code: int = 1, data=None):
        return {"code": code, "msg": msg, "data": data}

    @staticmethod
    def page(items, total: int, page: int, size: int):
        return Result.success({"items": items, "total": total, "page": page, "size": size})


class BizError(Exception):
    def __init__(self, msg: str, status: int = 400):
        self.msg = msg
        self.status = status


def register_exception_handlers(app):
    @app.exception_handler(BizError)
    async def biz_handler(request: Request, exc: BizError):
        return JSONResponse(status_code=exc.status, content=Result.fail(exc.msg))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=Result.fail("参数校验失败", data=exc.errors()))

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content=Result.fail(str(exc.detail)))

    @app.exception_handler(Exception)
    async def unknown_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=Result.fail(f"服务内部错误: {exc}"))
