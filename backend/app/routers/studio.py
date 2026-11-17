"""内容优化体验官 · 工作台接口

三块数据：
1) 体检快照 post_audits —— 前端把逐段评分整段存进来，用来画分数走势、给阅读页挂徽章
2) 引用追踪 citations  —— 哪一天、问的什么问题、哪个助手真的提了我们（含"问了但没提"）
3) AI 可见性 geo       —— 现算 robots.txt / sitemap.xml / llms.txt，附公开爬虫清单

约定：读取全开放（文章页与创作台不用登录也能看），写入必须登录。
"""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from ..database import execute, query
from ..models import AuditIn, CitationIn
from ..security import get_current_user

router = APIRouter(prefix="/api/studio", tags=["内容优化体验官"])

# 公开的抓取方 User-agent（各家在自己文档里公布，这里只做收录与检测，不解释规则）
BOTS = [
    {"ua": "GPTBot", "owner": "OpenAI", "kind": "训练", "note": "用于模型训练抓取"},
    {"ua": "OAI-SearchBot", "owner": "OpenAI", "kind": "检索", "note": "供搜索式回答建索引"},
    {"ua": "ChatGPT-User", "owner": "OpenAI", "kind": "用户触发", "note": "用户当场提问时来抓"},
    {"ua": "ClaudeBot", "owner": "Anthropic", "kind": "训练", "note": "用于模型训练抓取"},
    {"ua": "Claude-User", "owner": "Anthropic", "kind": "用户触发", "note": "用户当场提问时来抓"},
    {"ua": "PerplexityBot", "owner": "Perplexity", "kind": "检索", "note": "检索索引并附来源"},
    {"ua": "Google-Extended", "owner": "Google", "kind": "训练", "note": "控制 Gemini 侧的使用"},
    {"ua": "Bytespider", "owner": "字节跳动", "kind": "训练", "note": "头条/豆包侧抓取"},
]

_LATEST = """SELECT a.post_id, a.score, a.grade, a.detail, a.created_at
             FROM post_audits a
             JOIN (SELECT post_id, MAX(id) AS mid FROM post_audits GROUP BY post_id) m
               ON m.mid = a.id"""


def _loads(raw):
    if not raw:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None


# ---------------------------------------------------------------- 体检台

@router.get("/board")
def board():
    """所有文章 + 最近一次体检结果，体检台首屏就用这个"""
    posts = query(
        """SELECT p.id, p.title, p.summary, p.views, p.created_at, p.updated_at,
                  c.name AS category_name
           FROM posts p LEFT JOIN categories c ON c.id = p.category_id
           ORDER BY p.updated_at DESC, p.id DESC"""
    )
    latest = {r["post_id"]: r for r in query(_LATEST)}
    items = []
    for p in posts:
        a = latest.get(p["id"])
        items.append({
            **p,
            "score": a["score"] if a else None,
            "grade": a["grade"] if a else None,
            "audited_at": a["created_at"] if a else None,
        })
    scored = [i["score"] for i in items if i["score"] is not None]
    total_audits = query("SELECT COUNT(*) AS c FROM post_audits", one=True)["c"]
    return {
        "items": items,
        "summary": {
            "posts": len(items),
            "scored": len(scored),
            "avg": round(sum(scored) / len(scored)) if scored else None,
            "total_audits": total_audits,
            "stale": len([i for i in items if i["score"] is None]),
        },
    }


@router.post("/audit")
def save_audit(data: AuditIn, user: dict = Depends(get_current_user)):
    """存一次体检快照。detail 里放逐段结果、锚问句、四幕字数占比"""
    exists = query("SELECT id FROM posts WHERE id = %s", (data.post_id,), one=True)
    if not exists:
        raise HTTPException(status_code=404, detail="文章不存在")
    detail = json.dumps(data.detail, ensure_ascii=False) if data.detail else None
    execute(
        "INSERT INTO post_audits (post_id, score, grade, detail) VALUES (%s, %s, %s, %s)",
        (data.post_id, data.score, data.grade, detail),
    )
    row = query("SELECT id, created_at FROM post_audits ORDER BY id DESC LIMIT 1", one=True)
    return {"id": row["id"], "created_at": row["created_at"], "message": "体检结果已存档"}


@router.get("/audit/{post_id}")
def latest_audit(post_id: int):
    row = query(
        "SELECT id, score, grade, detail, created_at FROM post_audits "
        "WHERE post_id = %s ORDER BY id DESC LIMIT 1",
        (post_id,),
        one=True,
    )
    if not row:
        return {"audit": None}
    row["detail"] = _loads(row["detail"])
    return {"audit": row}


@router.get("/audit/{post_id}/history")
def audit_history(post_id: int):
    rows = query(
        "SELECT id, score, grade, created_at FROM post_audits "
        "WHERE post_id = %s ORDER BY id DESC LIMIT 30",
        (post_id,),
    )
    return {"items": rows}


# ---------------------------------------------------------------- 引用追踪

@router.get("/citations")
def list_citations():
    rows = query(
        """SELECT c.*, p.title AS post_title, DATE_FORMAT(c.found_at, '%Y-%m-%d') AS found
           FROM citations c LEFT JOIN posts p ON p.id = c.post_id
           ORDER BY (c.found_at IS NULL), c.found_at DESC, c.id DESC
           LIMIT 100"""
    )
    hit = len([r for r in rows if r["cited"]])
    miss = len(rows) - hit
    return {
        "items": rows,
        "summary": {
            "total": len(rows),
            "hit": hit,
            "miss": miss,
            "rate": round(hit / len(rows) * 100) if rows else None,
        },
    }


@router.post("/citations")
def add_citation(data: CitationIn, user: dict = Depends(get_current_user)):
    if data.post_id is not None:
        if not query("SELECT id FROM posts WHERE id = %s", (data.post_id,), one=True):
            raise HTTPException(status_code=404, detail="文章不存在")
    execute(
        """INSERT INTO citations (post_id, ai_name, question, quoted_text, url, cited, found_at, note)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            data.post_id,
            data.ai_name,
            data.question,
            data.quoted_text,
            data.url,
            1 if data.cited else 0,
            data.found_at or date.today().isoformat(),
            data.note,
        ),
    )
    row = query("SELECT id FROM citations ORDER BY id DESC LIMIT 1", one=True)
    return {"id": row["id"], "message": "记下了"}


@router.delete("/citations/{cid}")
def remove_citation(cid: int, user: dict = Depends(get_current_user)):
    execute("DELETE FROM citations WHERE id = %s", (cid,))
    return {"message": "已删除"}


# ---------------------------------------------------------------- AI 可见性

def _base_url(request: Request, override: str | None) -> str:
    if override:
        return override.rstrip("/")
    return str(request.base_url).rstrip("/")


@router.get("/geo")
def geo(request: Request, base: str | None = None):
    """现算三份"给机器看的文件"，并给出爬虫清单。

    robots.txt 与 sitemap.xml 是正经协议；llms.txt 目前只是社区提案
    （由 Answer.AI 在 2024 年提出），不是标准，别当成保证。
    """
    root = _base_url(request, base)
    posts = query(
        "SELECT id, title, updated_at, DATE_FORMAT(updated_at, '%Y-%m-%d') AS d "
        "FROM posts ORDER BY updated_at DESC"
    )

    allow = "\n".join(f"User-agent: {b['ua']}\nAllow: /\n" for b in BOTS)
    robots = (
        "# 我们欢迎检索，但请别把整站打包去训练后就当没来过\n"
        f"{allow}\nSitemap: {root}/sitemap.xml\n"
    )

    urls = "\n".join(
        f"  <url><loc>{root}/#/posts/{p['id']}</loc>"
        f"<lastmod>{p['d']}</lastmod></url>"
        for p in posts
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n</urlset>\n"
    )

    lines = [
        "# 我的小窝",
        "",
        "> 一个写技术踩坑与内容实验的地方。欢迎引用，请带上日期与链接。",
        "",
        "## 文章",
    ]
    lines += [f"- [{p['title']}]({root}/#/posts/{p['id']}) — 更新于 {p['d']}" for p in posts]
    llms = "\n".join(lines) + "\n"

    return {
        "base": root,
        "robots": robots,
        "sitemap": sitemap,
        "llms": llms,
        "bots": BOTS,
        "counts": {"posts": len(posts)},
        "notes": {
            "robots": "协议，真生效",
            "sitemap": "协议，真生效",
            "llms": "社区提案，不是标准，只能算递名片",
        },
    }
