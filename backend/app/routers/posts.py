"""文章（博客 / 学习总结）增删改查 + 搜索 + 分类/标签筛选 + 归档 + 精选"""
import math

from fastapi import APIRouter, Depends, HTTPException, Query

from ..database import query, execute, call_in_transaction
from ..models import PostIn
from ..security import get_current_user, get_admin_user, get_optional_user

router = APIRouter(prefix="/api/posts", tags=["文章"])

_EXCERPT_LEN = 200  # 列表页摘要长度
_HAS_AVATAR = None   # users.avatar 列是否存在的缓存（兼容未迁移的库）


def _query_posts_with_author(sql_template: str, args: tuple):
    """把 __AVATAR__ 占位符替换为安全的列表达式，兼容未迁移 avatar 的库。"""
    global _HAS_AVATAR
    if _HAS_AVATAR is None:
        try:
            query("SELECT avatar FROM users LIMIT 1")
            _HAS_AVATAR = True
        except Exception:
            _HAS_AVATAR = False
    avatar_expr = "u.avatar AS author_avatar" if _HAS_AVATAR else "NULL AS author_avatar"
    return query(sql_template.replace("__AVATAR__", avatar_expr), args)


def _brief(row: dict) -> dict:
    """列表页不返回完整正文，用 summary 或截断内容做摘要"""
    row = dict(row)
    content = row.pop("content", "") or ""
    row["excerpt"] = row.get("summary") or content[:_EXCERPT_LEN] + (
        "…" if len(content) > _EXCERPT_LEN else ""
    )
    return row


def _attach_tags(row: dict) -> dict:
    tags = query(
        "SELECT t.id, t.name FROM tags t JOIN post_tags pt ON pt.tag_id = t.id "
        "WHERE pt.post_id = %s ORDER BY t.id",
        (row["id"],),
    )
    row["tags"] = tags
    return row


def _save_tags_with_cur(cur, post_id: int, tag_ids):
    """在事务连接里重写文章-标签关联"""
    cur.execute("DELETE FROM post_tags WHERE post_id = %s", (post_id,))
    if tag_ids:
        cur.executemany(
            "INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s)",
            [(post_id, tid) for tid in tag_ids],
        )


@router.get("/archives")
def archives():
    """按年月归档统计，如 2026-11 共 5 篇"""
    rows = query(
        """SELECT DATE_FORMAT(created_at, '%Y') AS year, DATE_FORMAT(created_at, '%m') AS month,
                  COUNT(*) AS count
           FROM posts WHERE status='published'
           GROUP BY year, month ORDER BY year DESC, month DESC"""
    )
    return {"items": rows}


@router.get("")
def list_posts(
    keyword: str = Query(default=None, max_length=50, description="标题/内容搜索"),
    category_id: int = Query(default=None),
    tag_id: int = Query(default=None),
    year: int = Query(default=None, description="归档筛选: 年"),
    month: int = Query(default=None, ge=1, le=12, description="归档筛选: 月"),
    featured: bool = Query(default=None, description="只看精选"),
    status: str = Query(default="published", description="published/draft/all，后两者需登录"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    viewer: dict = Depends(get_optional_user),
):
    # 草稿 / 全部需要登录后才能看
    if status in ("draft", "all") and not viewer:
        raise HTTPException(status_code=401, detail="查看草稿需要先登录")

    where, args = "WHERE 1=1", []
    if status == "published":
        where += " AND p.status = 'published'"
    elif status == "draft":
        where += " AND p.status = 'draft'"
    if keyword:
        where += " AND (p.title LIKE %s OR p.content LIKE %s)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    if category_id:
        where += " AND p.category_id = %s"
        args.append(category_id)
    if tag_id:
        where += (
            " AND EXISTS (SELECT 1 FROM post_tags pt "
            "WHERE pt.post_id = p.id AND pt.tag_id = %s)"
        )
        args.append(tag_id)
    if year:
        where += " AND YEAR(p.created_at) = %s"
        args.append(year)
    if month:
        where += " AND MONTH(p.created_at) = %s"
        args.append(month)
    if featured is not None:
        where += " AND p.featured = %s"
        args.append(1 if featured else 0)

    total = query(f"SELECT COUNT(*) AS c FROM posts p {where}", tuple(args), one=True)["c"]
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    rows = _query_posts_with_author(
        f"""SELECT p.id, p.title, p.summary, p.content, p.cover, p.featured, p.status,
                   p.views, p.created_at, p.updated_at,
                   c.name AS category_name, c.id AS category_id,
                   u.nickname AS author, u.id AS author_id, __AVATAR__
            FROM posts p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN users u ON u.id = p.user_id
            {where}
            ORDER BY p.featured DESC, p.created_at DESC
            LIMIT %s OFFSET %s""",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    return {
        "items": [_brief(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get("/{post_id}")
def get_post(post_id: int):
    rows = _query_posts_with_author(
        """SELECT p.*, c.name AS category_name,
                  u.nickname AS author, u.id AS author_id, __AVATAR__
           FROM posts p
           LEFT JOIN categories c ON c.id = p.category_id
           LEFT JOIN users u ON u.id = p.user_id
           WHERE p.id = %s""",
        (post_id,),
    )
    row = rows[0] if rows else None
    if row is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    execute("UPDATE posts SET views = views + 1 WHERE id = %s", (post_id,))
    row = _attach_tags(row)
    # 最近一次体检（post_audits 为增量表，未迁移时降级为 None，不打断阅读）
    try:
        import json as _json

        audit = query(
            "SELECT score, grade, detail, created_at FROM post_audits "
            "WHERE post_id = %s ORDER BY id DESC LIMIT 1",
            (post_id,),
            one=True,
        )
        if audit:
            raw = audit.get("detail")
            if isinstance(raw, str) and raw:
                try:
                    audit["detail"] = _json.loads(raw)
                except ValueError:
                    audit["detail"] = None
        row["audit"] = audit
    except Exception:
        row["audit"] = None
    prev = query(
        "SELECT id, title FROM posts WHERE id < %s AND status='published' "
        "ORDER BY id DESC LIMIT 1",
        (post_id,),
        one=True,
    )
    nxt = query(
        "SELECT id, title FROM posts WHERE id > %s AND status='published' "
        "ORDER BY id ASC LIMIT 1",
        (post_id,),
        one=True,
    )
    return {"post": {**row, "prev": prev, "next": nxt}}


@router.post("")
def create_post(data: PostIn, user: dict = Depends(get_admin_user)):
    def _tx(conn):
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO posts
                   (title, content, summary, cover, featured, status, category_id, user_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    data.title,
                    data.content,
                    data.summary,
                    data.cover,
                    1 if data.featured else 0,
                    data.status,
                    data.category_id,
                    user["id"],
                ),
            )
            post_id = cur.lastrowid
            _save_tags_with_cur(cur, post_id, data.tag_ids)
        return post_id

    pid = call_in_transaction(_tx)
    return {"id": pid, "message": "保存成功"}


@router.put("/{post_id}")
def update_post(post_id: int, data: PostIn, user: dict = Depends(get_admin_user)):
    exists = query("SELECT id FROM posts WHERE id = %s", (post_id,), one=True)
    if not exists:
        raise HTTPException(status_code=404, detail="文章不存在")

    def _tx(conn):
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE posts SET title=%s, content=%s, summary=%s, cover=%s,
                   featured=%s, status=%s, category_id=%s WHERE id=%s""",
                (
                    data.title,
                    data.content,
                    data.summary,
                    data.cover,
                    1 if data.featured else 0,
                    data.status,
                    data.category_id,
                    post_id,
                ),
            )
            _save_tags_with_cur(cur, post_id, data.tag_ids)
        return post_id

    call_in_transaction(_tx)
    return {"message": "更新成功"}


@router.delete("/{post_id}")
def delete_post(post_id: int, user: dict = Depends(get_admin_user)):
    execute("DELETE FROM post_tags WHERE post_id = %s", (post_id,))
    execute("DELETE FROM posts WHERE id = %s", (post_id,))
    return {"message": "已删除"}
