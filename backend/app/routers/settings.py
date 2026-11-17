"""站点设置：前台读取「关于我 / 站点信息」，管理员在后台维护"""
from fastapi import APIRouter, Depends, HTTPException

from ..database import execute, query
from ..models import SiteSettingsIn
from ..security import get_current_user

router = APIRouter(prefix="/api/settings", tags=["站点设置"])

_COLS = (
    "id, site_name, site_desc, author_name, author_title, author_bio, "
    "location, email, github, footer_text"
)
DEFAULTS = {
    "id": 1,
    "site_name": "我的小窝",
    "site_desc": None,
    "author_name": None,
    "author_title": None,
    "author_bio": None,
    "location": None,
    "email": None,
    "github": None,
    "footer_text": None,
}


def _row():
    row = query(f"SELECT {_COLS} FROM site_settings WHERE id = 1", one=True)
    return {**DEFAULTS, **(row or {})}


@router.get("")
def get_settings():
    return {"settings": _row()}


@router.put("")
def update_settings(data: SiteSettingsIn, user: dict = Depends(get_current_user)):
    values = data.model_dump()
    execute(
        """UPDATE site_settings SET site_name=%s, site_desc=%s, author_name=%s,
           author_title=%s, author_bio=%s, location=%s, email=%s, github=%s, footer_text=%s
           WHERE id=1""",
        tuple(values[k] for k in (
            "site_name", "site_desc", "author_name", "author_title", "author_bio",
            "location", "email", "github", "footer_text",
        )),
    )
    return {"settings": _row(), "message": "已保存"}
