"""留言板：访客留言，登录后可删除"""
from fastapi import APIRouter, Depends, HTTPException

from ..database import query, execute
from ..models import MessageIn
from ..security import get_current_user, get_optional_user

router = APIRouter(prefix="/api/messages", tags=["留言板"])


@router.get("")
def list_messages():
    rows = query("SELECT id, nickname, content, created_at FROM messages ORDER BY created_at DESC LIMIT 200")
    return {"items": rows}


@router.post("")
def create_message(data: MessageIn, user: dict = Depends(get_optional_user)):
    _, mid = execute("INSERT INTO messages (nickname, content, user_id) VALUES (%s, %s, %s)", (data.nickname, data.content, user["id"] if user else None))
    return {"id": mid, "message": "留言成功 🍀"}


@router.delete("/{message_id}")
def delete_message(message_id: int, user: dict = Depends(get_current_user)):
    execute("DELETE FROM messages WHERE id = %s", (message_id,))
    return {"message": "已删除留言"}
