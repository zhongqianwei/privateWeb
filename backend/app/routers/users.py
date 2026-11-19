"""个人空间：用户公开资料 + 聚合内容（文章 / 日记 / 说说 / 图片）"""
import math

from fastapi import APIRouter, HTTPException, Query

from ..database import query

router = APIRouter(prefix="/api/users", tags=["个人空间"])
_HAS_AVATAR = None

_KINDS = {
    "diary": "日记", "journal": "日记", "essay": "随笔",
    "note": "笔记", "saying": "说说",
}


def _avatar_expr(alias: str = "u") -> str:
    global _HAS_AVATAR
    if _HAS_AVATAR is None:
        try:
            query("SELECT avatar FROM users LIMIT 1")
            _HAS_AVATAR = True
        except Exception:
            _HAS_AVATAR = False
    return f"{alias}.avatar" if _HAS_AVATAR else "NULL"


def _get_user(user_id: int) -> dict:
    global _HAS_AVATAR
    if _HAS_AVATAR is None:
        try:
            query("SELECT avatar FROM users LIMIT 1")
            _HAS_AVATAR = True
        except Exception:
            _HAS_AVATAR = False
    avatar_col = "avatar" if _HAS_AVATAR else "NULL"
    row = query(
        f"SELECT id, username, nickname, {avatar_col} AS avatar, is_admin, created_at "
        "FROM users WHERE id = %s",
        (user_id,), one=True,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return row


@router.get("/{user_id}/profile")
def profile(user_id: int):
    u = _get_user(user_id)
    counts = {
        "posts": query("SELECT COUNT(*) AS c FROM posts WHERE user_id=%s AND status='published'", (user_id,), one=True)["c"],
        "diaries": query("SELECT COUNT(*) AS c FROM diaries WHERE user_id=%s", (user_id,), one=True)["c"],
        "photos": query("SELECT COUNT(*) AS c FROM photos WHERE user_id=%s", (user_id,), one=True)["c"],
    }
    return {
        "user": {
            "id": u["id"], "username": u["username"],
            "nickname": u.get("nickname") or u["username"],
            "avatar": u.get("avatar") or "",
            "is_admin": bool(u.get("is_admin")),
            "joined_at": str(u.get("created_at") or ""),
        },
        "counts": counts,
    }


@router.get("/{user_id}/contents")
def contents(
    user_id: int,
    type: str = Query(default="all", description="all/posts/diaries/photos/saying"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
):
    """个人空间内容流：统一返回 {type,title,content,cover,created_at,ref} 的小窗口卡片数据。"""
    _get_user(user_id)
    items = []

    def _fetch(sql, args, kind):
        # diary 类内容按原始 kind 区分 type，前端 Tab 可直接精确筛选
        result = []
        for r in query(sql, args):
            raw = r.get("kind")
            row_type = raw if (kind == "diary" and raw in _KINDS) else kind
            if row_type == "journal":
                row_type = "diary"
            result.append({
                "type": row_type,
                "kind_label": _KINDS.get(raw, "记录") if kind == "diary" else kind,
                "title": r.get("title") or "",
                "content": r.get("content") or r.get("excerpt") or "",
                "cover": r.get("cover") or "",
                "created_at": str(r.get("created_at") or ""),
                "ref": f"/posts/{r['id']}" if kind == "post" else "/diary",
                "id": r["id"],
                "mood": r.get("mood"),
                "weather": r.get("weather"),
            })
        return result

    if type in ("all", "posts"):
        items += _fetch(
            "SELECT id, title, LEFT(content,200) AS excerpt, cover, created_at "
            "FROM posts WHERE user_id=%s AND status='published'",
            (user_id,), "post",
        )
    if type in ("all", "diaries"):
        items += _fetch(
            "SELECT id, title, content, kind, mood, weather, created_at "
            "FROM diaries WHERE user_id=%s",
            (user_id,), "diary",
        )
    if type in ("all", "photos"):
        items += _fetch(
            "SELECT id, title, filename AS cover, description AS content, created_at "
            "FROM photos WHERE user_id=%s",
            (user_id,), "photo",
        )

    # type=saying 只取说说（all 分支已在 _fetch 里把 saying 单独标记）
    if type == "saying":
        items = _fetch(
            "SELECT id, title, content, kind, mood, weather, created_at "
            "FROM diaries WHERE user_id=%s AND kind='saying'",
            (user_id,), "diary",
        )

    items.sort(key=lambda x: x["created_at"], reverse=True)
    total = len(items)
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "total": total, "page": page, "page_size": page_size, "pages": pages,
    }
