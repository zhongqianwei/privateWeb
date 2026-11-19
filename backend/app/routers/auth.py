"""用户注册 / 登录 / 获取当前用户 / 个人资料"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..config import settings
from ..database import query, execute
from ..models import LoginIn, RegisterIn
from ..security import (
    create_token, get_current_user, hash_password, verify_password,
    _row_to_user, _fetch_user_row,
)
from ..utils_upload import save_image

router = APIRouter(prefix="/api/auth", tags=["用户"])


@router.post("/register")
def register(data: RegisterIn):
    exists = query("SELECT id FROM users WHERE username = %s", (data.username,), one=True)
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    nickname = data.nickname or data.username
    # 配置的管理员用户名注册时自动赋予管理员权限
    is_admin = 1 if data.username == settings.ADMIN_USERNAME else 0
    try:
        _, uid = execute(
            "INSERT INTO users (username, password_hash, nickname, is_admin) VALUES (%s, %s, %s, %s)",
            (data.username, hash_password(data.password), nickname, is_admin),
        )
    except Exception:
        # 兼容 is_admin 列尚未迁移的库
        _, uid = execute(
            "INSERT INTO users (username, password_hash, nickname) VALUES (%s, %s, %s)",
            (data.username, hash_password(data.password), nickname),
        )
    token = create_token(uid, data.username)
    user = _row_to_user(_fetch_user_row(uid)) or {
        "id": uid, "username": data.username, "nickname": nickname,
        "avatar": "", "is_admin": bool(is_admin),
    }
    return {"token": token, "user": user}


@router.post("/login")
def login(data: LoginIn):
    row = query("SELECT id, password_hash FROM users WHERE username = %s", (data.username,), one=True)
    if row is None or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user = _row_to_user(_fetch_user_row(row["id"]))
    token = create_token(row["id"], data.username)
    return {"token": token, "user": user}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}


@router.put("/profile")
def update_profile(data: dict, user: dict = Depends(get_current_user)):
    """更新自己的昵称；头像走 /avatar 上传接口。"""
    nickname = (data.get("nickname") or "").strip()
    if not nickname or len(nickname) > 30:
        raise HTTPException(status_code=400, detail="昵称需为 1-30 个字符")
    execute("UPDATE users SET nickname = %s WHERE id = %s", (nickname, user["id"]))
    return {"user": _row_to_user(_fetch_user_row(user["id"]))}


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """上传自己的头像，返回新的 avatar URL。"""
    url = save_image(file, subdir="avatars")
    try:
        execute("UPDATE users SET avatar = %s WHERE id = %s", (url, user["id"]))
    except Exception:
        # avatar 列未迁移时仍返回 URL，前端可临时用；迁移后即可持久化
        pass
    return {"avatar": url, "user": _row_to_user(_fetch_user_row(user["id"]))}
