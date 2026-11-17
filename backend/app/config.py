"""「我的小窝」后端配置 —— 全部配置从 backend/.env 读取，改配置只需改 .env"""
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# backend 目录（config.py 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env
load_dotenv(BASE_DIR / ".env")


class Settings:
    """环境变量 -> 配置项"""

    # ---------- 数据库 ----------
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "little_home")

    # ---------- 鉴权 ----------
    # 未配置时每次启动生成随机密钥：生产环境请务必在 .env 显式设置，否则重启后旧 token 失效
    JWT_SECRET: str = os.getenv("JWT_SECRET") or secrets.token_urlsafe(48)
    TOKEN_EXPIRE_HOURS: int = int(os.getenv("TOKEN_EXPIRE_HOURS", "72"))

    # ---------- 文件上传 ----------
    UPLOAD_DIR: Path = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads")))

    # ---------- 服务 ----------
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # 跨域白名单：逗号分隔；默认 * 方便本地开发，生产建议填具体域名
    CORS_ORIGINS: list = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]

    # 上传白名单与大小限制
    ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


settings = Settings()
# 确保上传目录存在
(settings.UPLOAD_DIR / "photos").mkdir(parents=True, exist_ok=True)
