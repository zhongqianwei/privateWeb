"""用户注册 / 登录 / 获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException

from ..database import query, execute
from ..models import LoginIn, RegisterIn
from ..security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["用户"])


def _public_user(row: dict) -> dict:
    return {"id": row["id"], "username": row["username"], "nickname": row["nickname"], "created_at": str(row.get("created_at", ""))}


@router.post("/register")
def register(data: RegisterIn):
    exists = query("SELECT id FROM users WHERE username = %s", (data.username,), one=True)
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    nickname = data.nickname or data.username
    _, uid = execute(
        "INSERT INTO users (username, password_hash, nickname) VALUES (%s, %s, %s)",
        (data.username, hash_password(data.password), nickname),
    )
    token = create_token(uid, data.username)
    return {"token": token, "user": {"id": uid, "username": data.username, "nickname": nickname}}


@router.post("/login")
def login(data: LoginIn):
    row = query("SELECT id, username, nickname, password_hash FROM users WHERE username = %s", (data.username,), one=True)
    if row is None or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(row["id"], row["username"])
    return {"token": token, "user": {"id": row["id"], "username": row["username"], "nickname": row["nickname"]}}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}
