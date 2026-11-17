"""一键重置数据库到干净种子态（危险操作：会清掉全部内容后重建）。

用法:  在 backend 目录下  venv/Scripts/python reset.py
流程:  DROP DATABASE -> CREATE -> 执行 init.sql 建表 -> 执行 seed.py 写入种子数据
说明:  管理员账号固定为 admin / 123456（与 seed.py 一致）
"""
import os
import re
import sys

import pymysql

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover
    dotenv_values = None


def db_conf() -> dict:
    """从 .env 读取连接配置（与 app/config.py 同源）。"""
    conf = dict(host="127.0.0.1", port=3306, user="root", password="123456", charset="utf8mb4")
    if dotenv_values:
        env = dotenv_values(".env")
        conf.update(
            host=env.get("DB_HOST", conf["host"]),
            port=int(env.get("DB_PORT", 3306)),
            user=env.get("DB_USER", "root"),
            password=env.get("DB_PASSWORD", conf["password"]),
        )
    return conf


def exec_sql_file(cursor, path: str, db_name: str) -> int:
    """逐条执行 SQL 文件（跳过 -- 注释与空白，兼容中文内容）。"""
    sql = open(path, encoding="utf-8").read()
    n = 0
    for block in re.split(r";\s*\n", sql):
        lines = [l for l in block.splitlines() if l.strip() and not l.strip().startswith("--")]
        if lines:
            cursor.execute("\n".join(lines))
            n += 1
    return n


def main() -> None:
    conf = db_conf()
    conn = pymysql.connect(autocommit=True, **conf)
    cur = conn.cursor()

    print("= DROP DATABASE little_home")
    cur.execute("DROP DATABASE IF EXISTS little_home")
    cur.execute("CREATE DATABASE little_home CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute("USE little_home")

    here = os.path.dirname(os.path.abspath(__file__))
    stmts = exec_sql_file(cur, os.path.join(here, "init.sql"), "little_home")
    print(f"= init.sql 建表完成（{stmts} 条语句）")

    import seed  # 复用同一套种子数据

    seed.main()
    print("✅ 数据库已重置为干净种子态：admin / 123456")


if __name__ == "__main__":
    main()
