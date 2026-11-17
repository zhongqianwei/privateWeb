"""MySQL 连接池封装 —— 简单、可靠的线程池式连接管理"""
import queue

import pymysql
from pymysql.cursors import DictCursor

from .config import settings

_pool: "queue.Queue[pymysql.connections.Connection]" = queue.Queue(maxsize=10)


def _new_conn():
    """新建一个数据库连接"""
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=DictCursor,
        connect_timeout=5,
    )


def get_conn():
    """从池里取连接，失效则重建"""
    try:
        conn = _pool.get_nowait()
        conn.ping(reconnect=True)
        return conn
    except queue.Empty:
        return _new_conn()
    except Exception:
        return _new_conn()


def _release(conn):
    try:
        if conn.open:
            if conn.in_transaction:
                conn.rollback()
            _pool.put_nowait(conn)
            return
    except Exception:
        pass
    try:
        conn.close()
    except Exception:
        pass


def _run(cur, sql, args):
    """args 为空时不交给 pymysql 转义，避免 SQL 中的字面 % 报错"""
    if args:
        cur.execute(sql, args)
    else:
        cur.execute(sql)


def query(sql: str, args: tuple = None, *, one: bool = False):
    """查询：返回 list[dict] 或单个 dict/None"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            _run(cur, sql, args)
            rows = cur.fetchone() if one else cur.fetchall()
            return rows
    finally:
        _release(conn)


def execute(sql: str, args: tuple = None) -> tuple:
    """增删改：返回 (受影响行数, 自增ID)"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            _run(cur, sql, args)
            affected, last_id = cur.rowcount, cur.lastrowid
        conn.commit()
        return affected, last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        _release(conn)


def execute_many(sql: str, seq_of_args) -> int:
    """批量执行：返回受影响行数"""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            affected = cur.executemany(sql, seq_of_args)
        conn.commit()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        _release(conn)


def call_in_transaction(fn):
    """在一个连接的事务里执行 fn(conn)，用于需要多表一致性的写入"""
    conn = get_conn()
    try:
        result = fn(conn)
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        _release(conn)
