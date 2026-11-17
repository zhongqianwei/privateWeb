"""
一键重置数据库：删除 little_home → 重新执行 init.sql（建表+基础种子）
用法： venv\\Scripts\\python.exe scripts\\reset_db.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymysql  # noqa: E402

from app.config import settings  # noqa: E402

SQL_FILE = Path(__file__).resolve().parents[1] / "init.sql"


def main() -> None:
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        charset="utf8mb4",
    )
    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS `{settings.DB_NAME}`")
        cur.execute(f"CREATE DATABASE `{settings.DB_NAME}` DEFAULT CHARSET utf8mb4")
        cur.execute(f"USE `{settings.DB_NAME}`")
        statements = []
        for block in SQL_FILE.read_text(encoding="utf-8").split(";"):
            # 去掉注释行后若仍有实质 SQL 才执行
            body = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--")).strip()
            if body:
                statements.append(body)
        for s in statements:
            cur.execute(s)
    conn.commit()
    conn.close()
    print(f"✅ 数据库 {settings.DB_NAME} 已重置（表结构 + 基础种子）")
    print("👉 接着运行 seed.py 生成管理员与示例内容：venv\\Scripts\\python.exe seed.py")


if __name__ == "__main__":
    main()
