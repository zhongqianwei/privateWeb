"""首次初始化种子数据：默认管理员账号 admin/123456 + 示例内容（重复运行安全）

用法:  在 backend 目录下  venv/Scripts/python seed.py
"""
from app.database import query, execute
from app.security import hash_password
from app.main import check_db


def main():
    if not check_db():
        return

    # 1. 默认管理员
    admin = query("SELECT id FROM users WHERE username='admin'", one=True)
    if not admin:
        _, uid = execute(
            "INSERT INTO users (username, password_hash, nickname) VALUES (%s, %s, %s)",
            ("admin", hash_password("123456"), "窝主"),
        )
        print("+ 默认账号 admin / 123456 创建成功")
    else:
        uid = admin["id"]
        print("= 账号 admin 已存在，密码仍为初始 123456（如改过请用新密码）")

    # 2. 分类
    for name in ("学习总结", "生活随笔"):
        if not query("SELECT id FROM categories WHERE name=%s", (name,), one=True):
            execute("INSERT INTO categories (name) VALUES (%s)", (name,))
            print(f"+ 分类 {name}")

    # 3. 标签
    for name in ("Vue", "FastAPI", "记录"):
        if not query("SELECT id FROM tags WHERE name=%s", (name,), one=True):
            execute("INSERT INTO tags (name) VALUES (%s)", (name,))
            print(f"+ 标签 {name}")

    # 4. 示例文章
    if not query("SELECT id FROM posts LIMIT 1", one=True):
        cat1 = query("SELECT id FROM categories WHERE name='学习总结'", one=True)["id"]
        cat2 = query("SELECT id FROM categories WHERE name='生活随笔'", one=True)["id"]
        tag1 = query("SELECT id FROM tags WHERE name='Vue'", one=True)["id"]
        execute(
            "INSERT INTO posts (title, content, summary, category_id, user_id) VALUES (%s, %s, %s, %s, %s)",
            (
                "欢迎来到我的小窝",
                "这里是「我的小窝」的第一篇文章。\n\n"
                "以后会在这里记录学习总结、生活随笔，偶尔也会写下一些碎片化的想法。\n\n"
                "**小窝目前的板块：**\n\n"
                "- 📝 博文：正式的学习总结与文章\n"
                "- 🌙 随笔（日记）：随手记录心情\n"
                "- 📷 相册：照片墙\n"
                "- 💬 留言板：欢迎来找我玩\n\n"
                "写下第一篇，就是好的开始。",
                "小窝的第一篇文章，记录建站的心情与板块介绍。",
                cat1, uid,
            ),
        )
        execute(
            "INSERT INTO posts (title, content, summary, category_id, user_id) VALUES (%s, %s, %s, %s, %s)",
            (
                "Vue3 + FastAPI 学习小结",
                "这一篇记录一下搭建小窝用到的技术：\n\n"
                "> 前端：Vue3 + Vite，毛玻璃风格 UI\n"
                "> 后端：FastAPI + MySQL，RESTful 接口\n"
                "> 鉴权：JWT Token\n\n"
                "前后端分离最大的好处是职责清晰：前端管好看，后端管可靠。",
                "记录 Vue3 + Vite 前端与 FastAPI + MySQL 后端的学习要点。",
                cat2, uid,
            ),
        )
        p1 = query("SELECT id FROM posts ORDER BY id LIMIT 1", one=True)["id"]
        execute("INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s)", (p1, tag1))
        print("+ 示例文章 2 篇")

    # 5. 示例日记
    if not query("SELECT id FROM diaries LIMIT 1", one=True):
        execute(
            "INSERT INTO diaries (title, content, mood, weather, user_id) VALUES (%s, %s, %s, %s, %s)",
            ("开张日记", "今晚把小窝搭好了，灯是这个颜色，桌是这个颜色。\n心情像刚铺好的床单一样平整。", "开心", "晴", uid),
        )
        print("+ 示例日记 1 篇")

    # 6. 站点统计行（统计页依赖，幂等）
    execute(
        "INSERT INTO site_stats (id, total_pv) SELECT 1, 0 WHERE NOT EXISTS "
        "(SELECT 1 FROM site_stats WHERE id = 1)"
    )

    # 7. 示例留言 + 友链
    if not query("SELECT id FROM messages LIMIT 1", one=True):
        execute(
            "INSERT INTO messages (nickname, content) VALUES (%s, %s)",
            ("路过的小猫", "小窝真温馨呀，常来坐坐 🐾"),
        )
        print("+ 示例留言 1 条")

    if not query("SELECT id FROM friend_links LIMIT 1", one=True):
        for name, url, desc in (
            ("Vue 官方文档", "https://cn.vuejs.org", "我的前端老师在上学"),
            ("FastAPI 文档", "https://fastapi.tiangolo.com/zh/", "现代、快速的 Python Web 框架"),
        ):
            execute(
                "INSERT INTO friend_links (name, url, description) VALUES (%s, %s, %s)",
                (name, url, desc),
            )
        print("+ 示例友链 2 条")

    print("✅ 种子数据就绪")


if __name__ == "__main__":
    main()
