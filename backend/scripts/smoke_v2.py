"""全接口冒烟测试：读接口 + 写接口闭环，结束后清理测试数据。

用法：先启动 uvicorn，再执行
    ./venv/Scripts/python.exe scripts/smoke_v2.py
"""
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import execute, query  # noqa: E402

BASE = "http://127.0.0.1:8000"
results = []


def call(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            raw = res.read().decode()
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return e.code, json.loads(raw) if raw else {}


def check(label, cond, extra=""):
    results.append((label, bool(cond), extra))
    print(("  OK   " if cond else "  FAIL ") + label + (f"  {extra}" if extra and not cond else ""))


def main():
    print("[smoke] waiting for server...")
    for _ in range(20):
        try:
            call("GET", "/api/health")
            break
        except Exception:
            time.sleep(0.5)

    # --- 公共读接口 ---
    for path in [
        "/api/health", "/api/posts", "/api/posts?featured=true", "/api/posts/archives",
        "/api/diaries", "/api/photos", "/api/categories", "/api/tags",
        "/api/messages", "/api/friends", "/api/stats", "/api/settings",
    ]:
        code, body = call("GET", path)
        check(f"GET {path}", code == 200, f"status={code} {body}")

    code, detail = call("GET", "/api/posts/1")
    check("GET /api/posts/1", code in (200, 404), f"status={code}")
    if code == 200:
        check("post detail fields", all(k in detail["post"] for k in ("title", "content", "tags", "featured", "status")))

    # --- 鉴权保护 ---
    code, _ = call("PUT", "/api/settings", {"site_name": "X"})
    check("settings requires auth", code == 401, f"status={code}")

    # --- 注册临时账号 ---
    uname = "smoke_" + uuid.uuid4().hex[:8]
    code, auth = call("POST", "/api/auth/register", {"username": uname, "password": "Smoke@123456", "nickname": "冒烟"})
    check("register temp user", code == 200, f"status={code} {auth}")
    if code != 200:
        return report()
    token = auth["token"]
    uid = auth["user"]["id"]

    # --- 文章闭环 ---
    payload = {
        "title": "SMOKE 临时文章", "content": "## 测试标题\n\n这是一段冒烟测试正文。",
        "summary": "smoke", "cover": "", "featured": True, "status": "published",
        "category_id": None, "tag_ids": [],
    }
    code, created = call("POST", "/api/posts", payload, token)
    check("POST /api/posts", code == 200, f"status={code} {created}")
    pid = created.get("id")
    if pid:
        code, row = call("GET", f"/api/posts/{pid}")
        check("created post readable", code == 200 and row["post"]["featured"] == 1, f"status={code}")
        code, _ = call("PUT", f"/api/posts/{pid}", {**payload, "title": "SMOKE 已更新", "featured": False}, token)
        check("PUT /api/posts/{id}", code == 200, f"status={code}")
        code, row = call("GET", f"/api/posts/{pid}")
        check("update persisted", code == 200 and row["post"]["title"] == "SMOKE 已更新" and row["post"]["featured"] == 0)

    # --- 记录闭环 ---
    d = {"title": "SMOKE 记录", "content": "临时内容", "kind": "note", "mood": "", "weather": ""}
    code, dres = call("POST", "/api/diaries", d, token)
    check("POST /api/diaries", code == 200, f"status={code} {dres}")
    did = dres.get("id")
    if did:
        code, _ = call("PUT", f"/api/diaries/{did}", {**d, "title": "SMOKE 已更新"}, token)
        check("PUT /api/diaries/{id}", code == 200, f"status={code}")

    # --- 设置保存 / 还原 ---
    _, before = call("GET", "/api/settings")
    original = before["settings"]
    code, _ = call("PUT", "/api/settings", {**original, "site_name": "SMOKE TEMP"}, token)
    check("PUT /api/settings", code == 200, f"status={code}")
    call("PUT", "/api/settings", original, token)
    _, after = call("GET", "/api/settings")
    check("settings restored", after["settings"]["site_name"] == original["site_name"])

    # --- 删除闭环 ---
    if did:
        code, _ = call("DELETE", f"/api/diaries/{did}", token=token)
        check("DELETE /api/diaries/{id}", code == 200, f"status={code}")
    if pid:
        code, _ = call("DELETE", f"/api/posts/{pid}", token=token)
        check("DELETE /api/posts/{id}", code == 200, f"status={code}")
        code, _ = call("GET", f"/api/posts/{pid}")
        check("deleted post gone", code == 404, f"status={code}")

    # --- 数据库清理 ---
    execute("DELETE FROM diaries WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))
    check("temp user cleaned", query("SELECT id FROM users WHERE id=%s", (uid,), one=True) is None)
    print("\n[smoke] database rows: posts=%s diaries=%s photos=%s" % (
        query("SELECT COUNT(*) c FROM posts", one=True)["c"],
        query("SELECT COUNT(*) c FROM diaries", one=True)["c"],
        query("SELECT COUNT(*) c FROM photos", one=True)["c"],
    ))
    report()


def report():
    failed = [r for r in results if not r[1]]
    print(f"\n[smoke] {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("[smoke] FAILED:", ", ".join(r[0] for r in failed))
        sys.exit(1)


if __name__ == "__main__":
    main()
