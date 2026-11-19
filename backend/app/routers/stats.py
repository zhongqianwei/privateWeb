"""站点统计：访问量 PV、内容数量、近 7 天活跃

性能：首页首屏会调用本接口，原来的 14 次串行查询曾导致 ~930ms 延迟。
这里合并为 2 次查询（总量用 1 条多子查询 SQL，近 7 天用 1 条 GROUP BY）。
"""
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
    """汇总数据一次拿全：2 次查询替代原来的 14 次。"""
    # 1) 所有标量统计合并成一条 SQL，并行子查询一次性返回
    row = query(
        """SELECT
             (SELECT COUNT(*) FROM posts)                       AS posts,
             (SELECT COUNT(*) FROM diaries)                     AS diaries,
             (SELECT COUNT(*) FROM photos)                      AS photos,
             (SELECT COUNT(*) FROM messages)                    AS messages,
             (SELECT COUNT(*) FROM friend_links)                AS friends,
             (SELECT COUNT(*) FROM users)                       AS users,
             (SELECT COALESCE(SUM(views),0) FROM posts)         AS post_views,
             (SELECT COUNT(*) FROM categories)                  AS categories,
             (SELECT COUNT(*) FROM tags)                        AS tags,
             (SELECT COALESCE(SUM(CHAR_LENGTH(content)),0) FROM posts)
               + (SELECT COALESCE(SUM(CHAR_LENGTH(content)),0) FROM diaries) AS words,
             (SELECT MIN(created_at) FROM posts)                AS since,
             (SELECT total_pv FROM site_stats WHERE id = 1)     AS total_pv,
             (SELECT today_pv FROM site_stats WHERE id = 1)     AS today_pv""",
        one=True,
    ) or {}

    # 2) 近 7 天：用日期表 LEFT JOIN 聚合，避免相关子查询逐行扫描
    recent = query(
        """SELECT DATE_FORMAT(d.date, '%m-%d') AS date,
                  COALESCE(a.c, 0) + COALESCE(b.c, 0) AS count
           FROM (
             SELECT CURDATE() AS date UNION ALL SELECT CURDATE()-INTERVAL 1 DAY
             UNION ALL SELECT CURDATE()-INTERVAL 2 DAY UNION ALL SELECT CURDATE()-INTERVAL 3 DAY
             UNION ALL SELECT CURDATE()-INTERVAL 4 DAY UNION ALL SELECT CURDATE()-INTERVAL 5 DAY
             UNION ALL SELECT CURDATE()-INTERVAL 6 DAY
           ) d
           LEFT JOIN (SELECT DATE(created_at) dt, COUNT(*) c FROM posts GROUP BY dt) a ON a.dt = d.date
           LEFT JOIN (SELECT DATE(created_at) dt, COUNT(*) c FROM diaries GROUP BY dt) b ON b.dt = d.date
           ORDER BY d.date ASC"""
    )

    import datetime
    since = str(row.get("since"))[:10] if row.get("since") else None
    days = 0
    if since:
        try:
            days = (datetime.date.today() - datetime.date.fromisoformat(since)).days + 1
        except ValueError:
            days = 0

    return {
        "posts": row.get("posts", 0),
        "diaries": row.get("diaries", 0),
        "photos": row.get("photos", 0),
        "messages": row.get("messages", 0),
        "friends": row.get("friends", 0),
        "users": row.get("users", 0),
        "post_views": row.get("post_views", 0),
        "total_pv": row.get("total_pv", 0),
        "today_pv": row.get("today_pv", 0),
        "categories": row.get("categories", 0),
        "tags": row.get("tags", 0),
        "words": row.get("words", 0),
        "days": days,
        "since": since,
        "recent7": recent,
    }
