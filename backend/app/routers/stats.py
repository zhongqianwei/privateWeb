"""站点统计：访问量 PV、内容数量、近 7 天活跃"""
from fastapi import APIRouter

from ..database import query, execute

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.post("/visit")
def visit():
    """访客进入站点时 PV +1（跨日自动重置今日计数）"""
    execute(
        """UPDATE site_stats
           SET today_pv = IF(last_date = CURDATE(), today_pv + 1, 1),
               total_pv = total_pv + 1,
               last_date = CURDATE()
           WHERE id = 1"""
    )
    return {"message": "ok"}


@router.get("")
def stats():
    """汇总数据一次拿全"""
    posts = query("SELECT COUNT(*) AS c FROM posts", one=True)["c"]
    diaries = query("SELECT COUNT(*) AS c FROM diaries", one=True)["c"]
    photos = query("SELECT COUNT(*) AS c FROM photos", one=True)["c"]
    messages = query("SELECT COUNT(*) AS c FROM messages", one=True)["c"]
    friends = query("SELECT COUNT(*) AS c FROM friend_links", one=True)["c"]
    users = query("SELECT COUNT(*) AS c FROM users", one=True)["c"]
    views = query("SELECT COALESCE(SUM(views),0) AS c FROM posts", one=True)["c"]
    pv = query("SELECT total_pv FROM site_stats WHERE id = 1", one=True)["total_pv"]
    today_pv = query("SELECT today_pv FROM site_stats WHERE id = 1", one=True)["today_pv"]
    categories = query("SELECT COUNT(*) AS c FROM categories", one=True)["c"]
    tags_count = query("SELECT COUNT(*) AS c FROM tags", one=True)["c"]
    words = query(
        "SELECT COALESCE(SUM(CHAR_LENGTH(content)),0) AS c FROM posts", one=True
    )["c"] + query(
        "SELECT COALESCE(SUM(CHAR_LENGTH(content)),0) AS c FROM diaries", one=True
    )["c"]
    first = query("SELECT MIN(created_at) AS d FROM posts", one=True)["d"]

    # 近 7 天每日新增（文章 + 日记）
    recent = query(
        """SELECT DATE_FORMAT(d.date, '%m-%d') AS date,
                  (SELECT COUNT(*) FROM posts p WHERE DATE(p.created_at) = d.date)
                + (SELECT COUNT(*) FROM diaries x WHERE DATE(x.created_at) = d.date) AS count
           FROM (
               SELECT CURDATE() AS date UNION ALL SELECT CURDATE() - INTERVAL 1 DAY UNION ALL
               SELECT CURDATE() - INTERVAL 2 DAY UNION ALL SELECT CURDATE() - INTERVAL 3 DAY UNION ALL
               SELECT CURDATE() - INTERVAL 4 DAY UNION ALL SELECT CURDATE() - INTERVAL 5 DAY UNION ALL
               SELECT CURDATE() - INTERVAL 6 DAY
           ) d ORDER BY d.date ASC"""
    )
    import hashlib, datetime
    create_date = None
    if first is not None:
        create_date = str(first)[:10]
    days = 0
    if create_date:
        d1 = datetime.date.fromisoformat(create_date)
        days = (datetime.date.today() - d1).days + 1

    return {
        "posts": posts,
        "diaries": diaries,
        "photos": photos,
        "messages": messages,
        "friends": friends,
        "users": users,
        "post_views": views,
        "total_pv": pv,
        "today_pv": today_pv,
        "categories": categories,
        "tags": tags_count,
        "words": words,
        "days": days,
        "since": create_date,
        "recent7": recent,
    }
