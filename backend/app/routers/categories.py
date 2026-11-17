"""分类管理（带文章计数）"""
from fastapi import APIRouter, Depends, HTTPException, Body

from ..database import query, execute
from ..models import CategoryIn
from ..security import get_current_user

router = APIRouter(prefix="/api/categories", tags=["分类"])


@router.get("")
def list_categories():
    rows = query(
        """SELECT c.id, c.name, COUNT(p.id) AS post_count
           FROM categories c
           LEFT JOIN posts p ON p.category_id = c.id
           GROUP BY c.id, c.name ORDER BY c.id ASC"""
    )
    return {"items": rows}


@router.post("")
def create_category(data: CategoryIn, user: dict = Depends(get_current_user)):
    exists = query("SELECT id FROM categories WHERE name = %s", (data.name,), one=True)
    if exists:
        raise HTTPException(status_code=400, detail="分类已存在")
    _, cid = execute("INSERT INTO categories (name) VALUES (%s)", (data.name,))
    return {"id": cid, "message": "分类已创建"}


@router.delete("/{category_id}")
def delete_category(category_id: int, user: dict = Depends(get_current_user)):
    _, affected = execute("UPDATE posts SET category_id=NULL WHERE category_id=%s", (category_id,))
    execute("DELETE FROM categories WHERE id = %s", (category_id,))
    return {"message": "分类已删除"}


@router.put("/{category_id}")
def rename_category(category_id: int, name: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="分类名不能为空")
    row = query("SELECT id FROM categories WHERE id = %s", (category_id,), one=True)
    if not row:
        raise HTTPException(status_code=404, detail="分类不存在")
    clash = query("SELECT id FROM categories WHERE name = %s AND id != %s", (name, category_id), one=True)
    if clash:
        raise HTTPException(status_code=400, detail="已有同名分类")
    execute("UPDATE categories SET name = %s WHERE id = %s", (name, category_id))
    return {"message": "分类已更新"}
