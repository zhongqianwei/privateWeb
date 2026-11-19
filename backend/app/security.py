"""鉴权工具：密码哈希（PBKDF2）+ JWT Token + FastAPI 依赖"""
import hashlib
import time
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .database import query

# ---------------- 密码 ----------------


def hash_password(password: str, salt: str | None = None) -> str:
    """PBKDF2-SHA256，存储格式: salt$hash"""
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return calc == digest


# ---------------- JWT ----------------


def create_token(user_id: int, username: str) -> str:
    payload = {
        "uid": user_id,
        "sub": username,
        "exp": int(time.time()) + settings.TOKEN_EXPIRE_HOURS * 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------- FastAPI 依赖 ----------------

_bearer = HTTPBearer(auto_error=False)


def _row_to_user(row: dict | None) -> dict | None:
    """把 users 表的一行整理成对外的用户对象，统一带上 is_admin / avatar。

    兼容尚未迁移 avatar 字段的库：用 try 降级，绝不因为缺列而 500。
    管理员判定取两个来源的并集：
      1) .env 里 ADMIN_USERNAME 命中用户名（不依赖数据库改动）
      2) 库里的 is_admin 字段为 1（老数据仍然生效）
    """
    if row is None:
        return None
    is_admin = bool(row.get("is_admin")) or row.get("username") == settings.ADMIN_USERNAME
    return {
        "id": row.get("id"),
        "username": row.get("username"),
        "nickname": row.get("nickname") or row.get("username"),
        "avatar": row.get("avatar") or "",
        "is_admin": is_admin,
    }


def _fetch_user_row(user_id):
    """读取用户行；若 avatar 列尚未迁移，自动降级为不含 avatar 的查询。"""
    try:
        return query(
            "SELECT id, username, nickname, is_admin, avatar FROM users WHERE id = %s",
            (user_id,), one=True,
        )
    except Exception:
        return query(
            "SELECT id, username, nickname, is_admin FROM users WHERE id = %s",
            (user_id,), one=True,
        )


def _parse_user(cred: HTTPAuthorizationCredentials | None):
    if cred is None or cred.credentials is None:
        return None
    payload = decode_token(cred.credentials)
    if payload is None:
        return None
    return _row_to_user(_fetch_user_row(payload.get("uid")))


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """必须登录，否则 401"""
    user = _parse_user(cred)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_admin_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    """必须是管理员，否则 403。用于文章增删改、后台管理等写操作。"""
    user = _parse_user(cred)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_optional_user(cred: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict | None:
    """可选登录"""
    return _parse_user(cred)
