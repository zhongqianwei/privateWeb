"""图片落盘工具：校验格式/大小并保存到 UPLOAD_DIR 指定子目录，返回可访问的 URL。"""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .config import settings


def save_image(file: UploadFile, subdir: str = "photos") -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext or '(无后缀)'}")
    data = _read_sync(file)
    if len(data) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片超过 10MB 限制")
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = settings.UPLOAD_DIR / subdir / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return f"/uploads/{subdir}/{filename}"


def _read_sync(file: UploadFile) -> bytes:
    """兼容同步读取 UploadFile 的内容。"""
    fn = getattr(file, "file", None)
    if fn is not None:
        fn.seek(0)
        return fn.read()
    raise HTTPException(status_code=400, detail="无法读取上传的文件")
