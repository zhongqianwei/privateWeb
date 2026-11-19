"""相册：图片上传 / 列表 / 删除"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..config import settings
from ..database import query, execute
from ..security import get_current_user, get_admin_user

router = APIRouter(prefix="/api/photos", tags=["相册"])


@router.post("")
async def upload_photo(
    file: UploadFile,
    title: str = "",
    description: str = "",
    user: dict = Depends(get_current_user),
):
    """multipart 上传，保存到 backend/uploads/photos/"""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext or '(无后缀)'}")

    data = await file.read()
    if len(data) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片超过 10MB 限制")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = settings.UPLOAD_DIR / "photos" / filename
    dest.write_bytes(data)

    _, pid = execute(
        "INSERT INTO photos (title, filename, description, user_id) VALUES (%s, %s, %s, %s)",
        (title or file.filename or filename, f"/uploads/photos/{filename}", description, user["id"]),
    )
    return {"id": pid, "url": f"/uploads/photos/{filename}", "message": "照片已放进来 📷"}


@router.get("")
def list_photos():
    rows = query(
        "SELECT id, title, description, filename AS url, created_at FROM photos ORDER BY created_at DESC"
    )
    return {"items": rows}


@router.delete("/{photo_id}")
def delete_photo(photo_id: int, user: dict = Depends(get_admin_user)):
    row = query("SELECT filename FROM photos WHERE id = %s", (photo_id,), one=True)
    if row is None:
        raise HTTPException(status_code=404, detail="照片不存在")
    # 删磁盘文件（filename 以 /uploads/ 开头，映射到 UPLOAD_DIR）
    rel = row["filename"].replace("/uploads/", "", 1)
    local = settings.UPLOAD_DIR / rel
    try:
        local.unlink(missing_ok=True)
    except OSError:
        pass
    execute("DELETE FROM photos WHERE id = %s", (photo_id,))
    return {"message": "已删除"}
