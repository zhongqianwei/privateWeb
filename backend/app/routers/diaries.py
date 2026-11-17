"""随笔 / 日记 / 学习记录 —— 轻量记录流（以 kind 区分）"""
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import query, execute
from ..models import DiaryIn
from ..security import get_current_user

router = APIRouter(prefix="/api/diaries", tags=["记录"])
_COLS = "id, title, content, kind, mood, weather, created_at"


@router.get("")
def list_diaries(
    keyword: str = Query(default=None, max_length=50),
    kind: str = Query(default=None, description="diary/essay/note，留空为全部"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
):
    where, args = "WHERE 1=1", []
    if keyword:
        where += " AND (d.title LIKE %s OR d.content LIKE %s)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    if kind:
        where += " AND d.kind = %s"
        args.append(kind)

    total = query(f"SELECT COUNT(*) AS c FROM diaries d {where}", tuple(args), one=True)["c"]
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    rows = query(
        f"SELECT {_COLS} FROM diaries d {where} "
        f"ORDER BY d.created_at DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    return {"items": rows, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/{diary_id}")
def get_diary(diary_id: int):
    row = query(f"SELECT {_COLS} FROM diaries WHERE id = %s", (diary_id,), one=True)
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"diary": row}


@router.post("")
def create_diary(data: DiaryIn, user: dict = Depends(get_current_user)):
    _, did = execute(
        "INSERT INTO diaries (title, content, kind, mood, weather, user_id) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (data.title, data.content, data.kind, data.mood, data.weather, user["id"]),
    )
    return {"id": did, "message": "已保存这一页"}


@router.put("/{diary_id}")
def update_diary(diary_id: int, data: DiaryIn, user: dict = Depends(get_current_user)):
    affected, _ = execute(
        "UPDATE diaries SET title=%s, content=%s, kind=%s, mood=%s, weather=%s WHERE id=%s",
        (data.title, data.content, data.kind, data.mood, data.weather, diary_id),
    )
    if not affected:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"message": "已保存"}


@router.delete("/{diary_id}")
def delete_diary(diary_id: int, user: dict = Depends(get_current_user)):
    execute("DELETE FROM diaries WHERE id = %s", (diary_id,))
    return {"message": "已删除"}
