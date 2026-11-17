"""友情链接管理"""
from fastapi import APIRouter, Depends, HTTPException

from ..database import query, execute
from ..models import FriendIn
from ..security import get_current_user

router = APIRouter(prefix="/api/friends", tags=["友链"])


@router.get("")
def list_friends():
    rows = query("SELECT id, name, url, avatar, description, created_at FROM friend_links ORDER BY id ASC")
    return {"items": rows}


@router.post("")
def create_friend(data: FriendIn, user: dict = Depends(get_current_user)):
    _, fid = execute(
        "INSERT INTO friend_links (name, url, avatar, description) VALUES (%s, %s, %s, %s)",
        (data.name, data.url, data.avatar, data.description),
    )
    return {"id": fid, "message": "友链已添加"}


@router.delete("/{friend_id}")
def delete_friend(friend_id: int, user: dict = Depends(get_current_user)):
    execute("DELETE FROM friend_links WHERE id = %s", (friend_id,))
    return {"message": "友链已删除"}
