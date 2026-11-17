"""幂等增量迁移：给已存在的 little_home 库补齐 v2 字段与站点设置表。

用法（在 backend 目录）：
    ./venv/Scripts/python.exe scripts/migrate_v2.py

设计原则：
    1. 先查 information_schema，只在列/表不存在时才执行，重复运行安全。
    2. 全部使用项目自己的连接池，不需要额外安装 mysql 客户端。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import execute, query  # noqa: E402

DB = "little_home"

COLUMNS = [
    ("users", "is_admin", "TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否管理员'"),
    (
        "posts",
        "cover",
        "VARCHAR(300) DEFAULT NULL COMMENT '封面图访问路径'",
    ),
    (
        "posts",
        "featured",
        "TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否精选'",
    ),
    (
        "posts",
        "status",
        "VARCHAR(10) NOT NULL DEFAULT 'published' COMMENT '状态: published/draft'",
    ),
    (
        "diaries",
        "kind",
        "VARCHAR(20) NOT NULL DEFAULT 'diary' COMMENT '类型: diary/journal/essay/note'",
    ),
]

INDEXES = [
    ("posts", "idx_featured", "featured"),
    ("posts", "idx_status", "status"),
    ("diaries", "idx_kind", "kind"),
]

SITE_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS site_settings (
  id           TINYINT UNSIGNED PRIMARY KEY COMMENT '固定为 1',
  site_name    VARCHAR(60)  DEFAULT '我的小窝' COMMENT '站点名称',
  site_desc    VARCHAR(200) DEFAULT NULL COMMENT '站点描述',
  author_name  VARCHAR(30)  DEFAULT NULL COMMENT '作者名',
  author_title VARCHAR(60)  DEFAULT NULL COMMENT '一句话身份',
  author_bio   TEXT         DEFAULT NULL COMMENT '个人简介（支持 Markdown）',
  location     VARCHAR(60)  DEFAULT NULL COMMENT '所在地',
  email        VARCHAR(120) DEFAULT NULL COMMENT '邮箱',
  github       VARCHAR(200) DEFAULT NULL COMMENT 'GitHub 主页',
  footer_text  VARCHAR(200) DEFAULT NULL COMMENT '页脚文字',
  updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '站点设置'
"""


def has_column(table, column):
    return bool(
        query(
            "SELECT 1 FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s LIMIT 1",
            (DB, table, column),
            one=True,
        )
    )


def has_index(table, index):
    return bool(
        query(
            "SELECT 1 FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s LIMIT 1",
            (DB, table, index),
            one=True,
        )
    )


def has_table(table):
    return bool(
        query(
            "SELECT 1 FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s LIMIT 1",
            (DB, table),
            one=True,
        )
    )


def main():
    print(f"[migrate] database={DB}")
    for table, column, ddl in COLUMNS:
        if not has_table(table):
            print(f"  skip  {table}.{column} (table missing, run init.sql first)")
            continue
        if has_column(table, column):
            print(f"  keep  {table}.{column}")
        else:
            execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}")
            print(f"  add   {table}.{column}")

    for table, index, column in INDEXES:
        if has_table(table) and not has_index(table, index):
            execute(f"ALTER TABLE `{table}` ADD INDEX `{index}` (`{column}`)")
            print(f"  add   INDEX {table}.{index}")
        else:
            print(f"  keep  INDEX {table}.{index}")

    if has_table("site_settings"):
        print("  keep  table site_settings")
    else:
        execute(SITE_SETTINGS_SQL)
        print("  add   table site_settings")

    execute(
        "INSERT INTO site_settings (id) SELECT 1 "
        "WHERE NOT EXISTS (SELECT 1 FROM site_settings WHERE id = 1)"
    )
    print("[migrate] done.")


if __name__ == "__main__":
    main()
