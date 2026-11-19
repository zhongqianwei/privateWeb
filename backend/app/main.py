"""「我的小窝」FastAPI 后端入口

启动：uvicorn app.main:app --reload   （在 backend 目录下，或使用 venv）
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings

# ---------- 启动前检查数据库可达 ----------
from .database import query


def check_db():
    try:
        query("SELECT 1", one=True)
        return True
    except Exception as e:  # 数据库未启动时给出友好提示
        print("=" * 50)
        print(f"[!] 无法连接 MySQL ({settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME})")
        print(f"    原因: {e}")
        print("    请先运行 init.sql 建库建表，并确认 backend/.env 数据库配置正确")
        print("=" * 50)
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_db()
    yield


app = FastAPI(title="我的小窝 API", version="1.0.0", lifespan=lifespan)

# 允许跨域（本地 vite 开发端口 5173 / 部署后的域名都放行）
app.add_middleware(
    CORSMiddleware,
    # 分离部署时可在 .env 用 CORS_ORIGINS 收紧；默认放开方便本地学习调试
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 注册 API 路由 ----------
from .routers import (  # noqa: E402
    auth, categories, diaries, friends, messages, photos, posts,
    settings as settings_router, stats, studio, tags, users,
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(diaries.router)
app.include_router(photos.router)
app.include_router(messages.router)
app.include_router(friends.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(stats.router)
app.include_router(settings_router.router)
app.include_router(studio.router)
app.include_router(users.router)


@app.get("/api/health")
def health():
    db_ok = check_db()
    return {"status": "ok", "database": "ok" if db_ok else "error"}


# ---------- 统一异常响应格式 ----------
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    head = exc.errors()[0]
    msg = head.get("msg", "参数错误")
    loc = ".".join(str(x) for x in head.get("loc", []) if str(x) not in ("body",))
    return JSONResponse(status_code=422, content={"detail": f"{loc}: {msg}" if loc else msg})


# ---------- 上传目录静态托管 ----------
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# ---------- 若存在前端打包产物 dist，则由后端直接托管（一体化部署用） ----------
# SPA：非 /api、/uploads 的 GET 一律回退 index.html，前端 hash/history 路由都能跑
from fastapi.responses import FileResponse  # noqa: E402

_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _dist.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        candidate = (_dist / full_path).resolve()
        # 防目录穿越：只允许 dist 内的文件
        if (
            full_path
            and str(candidate).startswith(str(_dist.resolve()))
            and candidate.is_file()
        ):
            return FileResponse(candidate)
        return FileResponse(_dist / "index.html")
