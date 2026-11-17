"""Pydantic 请求模型定义"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- 用户 ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=20, description="用户名")
    password: str = Field(min_length=6, max_length=64, description="密码")
    nickname: Optional[str] = Field(default=None, max_length=30)


class LoginIn(BaseModel):
    username: str
    password: str


# ---------- 文章 ----------
class PostIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    summary: Optional[str] = None
    cover: Optional[str] = Field(default=None, max_length=300)
    featured: bool = False
    status: str = Field(default="published", pattern="^(published|draft)$")
    category_id: Optional[int] = None
    tag_ids: List[int] = []


# ---------- 日记 ----------
class DiaryIn(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    content: str = Field(min_length=1)
    kind: str = Field(default="diary", pattern="^(diary|journal|essay|note)$")
    mood: Optional[str] = Field(default=None, max_length=20)
    weather: Optional[str] = Field(default=None, max_length=20)


# ---------- 留言 ----------
class MessageIn(BaseModel):
    nickname: str = Field(min_length=1, max_length=30)
    content: str = Field(min_length=1, max_length=500)


# ---------- 友链 ----------
class FriendIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    url: str = Field(min_length=1, max_length=200)
    avatar: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=200)


# ---------- 分类 ----------
class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=30)


# ---------- 标签 ----------
class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=30)


# ---------- 内容优化体验官 ----------
class AuditIn(BaseModel):
    """一次体检快照：分数由前端规则引擎算出，原始明细整段存下来"""
    post_id: int
    score: int = Field(ge=0, le=100)
    grade: str = Field(default="C", max_length=8)
    detail: Optional[dict] = None


class CitationIn(BaseModel):
    post_id: Optional[int] = None
    ai_name: str = Field(min_length=1, max_length=40)
    question: Optional[str] = Field(default=None, max_length=255)
    quoted_text: Optional[str] = None
    url: Optional[str] = Field(default=None, max_length=500)
    cited: bool = True
    found_at: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=255)


# ---------- 站点设置 ----------
class SiteSettingsIn(BaseModel):
    site_name: str = Field(default="我的小窝", min_length=1, max_length=60)
    site_desc: Optional[str] = Field(default=None, max_length=200)
    author_name: Optional[str] = Field(default=None, max_length=30)
    author_title: Optional[str] = Field(default=None, max_length=60)
    author_bio: Optional[str] = Field(default=None, max_length=5000)
    location: Optional[str] = Field(default=None, max_length=60)
    email: Optional[str] = Field(default=None, max_length=120)
    github: Optional[str] = Field(default=None, max_length=200)
    footer_text: Optional[str] = Field(default=None, max_length=200)
