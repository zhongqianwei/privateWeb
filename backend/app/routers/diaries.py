"""随笔 / 日记 / 学习记录 / 说说 —— 轻量记录流（以 kind 区分）
普通用户可写自己的记录；管理员可管理全部记录。列表/详情带作者头像供个人空间使用。"""
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import query, execute
from ..models import DiaryIn
from ..security import get_current_user

router = APIRouter(prefix="/api/diaries", tags=["记录"])
_HAS_AVATAR = None
_INCLUDE_COLS = "d.id, d.title, d.content, d.kind, d.mood, d.weather, d.created_at, d.user_id"


def _author_fields():
    """返回作者 join 的 SELECT 片段，兼容未迁移 avatar 的库。"""
    global _HAS_AVATAR
    if _HAS_AVATAR is None:
        try:
            query("SELECT avatar FROM users LIMIT 1")
            _HAS_AVATAR = True
        except Exception:
            _HAS_AVATAR = False
    return (
        "u.nickname AS author, u.id AS author_id, "
        + ("u.avatar AS author_avatar" if _HAS_AVATAR else "NULL AS author_avatar")
    )


def _query_diaries(sql_template: str, args: tuple, one: bool = False):
    sql = sql_template.replace("__AUTHOR__", _author_fields())
    return query(sql, args, one=one)


@router.get("")
def list_diaries(
    keyword: str = Query(default=None, max_length=50),
    kind: str = Query(default=None, description="diary/essay/note/saying，留空为全部"),
    user_id: int = Query(default=None, description="只看某用户的记录（个人空间用）"),
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
    if user_id:
        where += " AND d.user_id = %s"
        args.append(user_id)

    total = query(f"SELECT COUNT(*) AS c FROM diaries d {where}", tuple(args), one=True)["c"]
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    rows = _query_diaries(
        f"""SELECT {_INCLUDE_COLS}, __AUTHOR__
            FROM diaries d LEFT JOIN users u ON u.id = d.user_id
            {where}
            ORDER BY d.created_at DESC LIMIT %s OFFSET %s""",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    return {"items": rows, "total": total, "page": page, "page_size": page_size, "pages": pages}


@router.get("/{diary_id}")
def get_diary(diary_id: int):
    row = _query_diaries(
        f"""SELECT {_INCLUDE_COLS}, __AUTHOR__
            FROM diaries d LEFT JOIN users u ON u.id = d.user_id
            WHERE d.id = %s""",
        (diary_id,),
        one=True,
    )
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
    row = query("SELECT user_id FROM diaries WHERE id = %s", (diary_id,), one=True)
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    if row.get("user_id") != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="只能修改自己的记录")
    execute(
        "UPDATE diaries SET title=%s, content=%s, kind=%s, mood=%s, weather=%s WHERE id=%s",
        (data.title, data.content, data.kind, data.mood, data.weather, diary_id),
    )
    return {"message": "已保存"}


@router.delete("/{diary_id}")
def delete_diary(diary_id: int, user: dict = Depends(get_current_user)):
    row = query("SELECT user_id FROM diaries WHERE id = %s", (diary_id,), one=True)
    if row is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    if row.get("user_id") != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="只能删除自己的记录")
    execute("DELETE FROM diaries WHERE id = %s", (diary_id,))
    return {"message": "已删除"}
