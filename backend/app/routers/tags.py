"""标签管理（带文章计数）"""
from fastapi import APIRouter, Depends, HTTPException, Body

from ..database import query, execute
from ..models import TagIn
from ..security import get_current_user

router = APIRouter(prefix="/api/tags", tags=["标签"])


@router.get("")
def list_tags():
    rows = query(
        """SELECT t.id, t.name, COUNT(pt.post_id) AS post_count
           FROM tags t
           LEFT JOIN post_tags pt ON pt.tag_id = t.id
           GROUP BY t.id, t.name ORDER BY post_count DESC, t.id ASC"""
    )
    return {"items": rows}


@router.post("")
def create_tag(data: TagIn, user: dict = Depends(get_current_user)):
    exists = query("SELECT id FROM tags WHERE name = %s", (data.name,), one=True)
    if exists:
        return {"id": exists["id"], "message": "标签已存在"}
    _, tid = execute("INSERT INTO tags (name) VALUES (%s)", (data.name,))
    return {"id": tid, "message": "标签已创建"}


@router.put("/{tag_id}")
def rename_tag(tag_id: int, name: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    name = (name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="标签名不能为空")
    row = query("SELECT id FROM tags WHERE id = %s", (tag_id,), one=True)
    if not row:
        raise HTTPException(status_code=404, detail="标签不存在")
    clash = query("SELECT id FROM tags WHERE name = %s AND id != %s", (name, tag_id), one=True)
    if clash:
        raise HTTPException(status_code=400, detail="已有同名标签")
    execute("UPDATE tags SET name = %s WHERE id = %s", (name, tag_id))
    return {"message": "标签已更新"}


@router.delete("/{tag_id}")
def delete_tag(tag_id: int, user: dict = Depends(get_current_user)):
    row = query("SELECT id FROM tags WHERE id = %s", (tag_id,), one=True)
    if not row:
        raise HTTPException(status_code=404, detail="标签不存在")
    # 关联表已配置级联删除（post_tags.tag_id ON DELETE CASCADE）
    execute("DELETE FROM tags WHERE id = %s", (tag_id,))
    return {"message": "标签已删除"}
