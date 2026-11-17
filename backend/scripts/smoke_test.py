"""全接口冒烟测试（联调用，不属于运行时依赖）

先启动后端: venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
再运行:    venv/Scripts/python.exe scripts/smoke_test.py
"""
import io
import struct
import zlib
import uuid

import requests

BASE = "http://127.0.0.1:8000"
PASS, FAIL = 0, []


def check(name, cond, extra=""):
    global PASS
    if cond:
        PASS += 1
        print(f"  ✔ {name}")
    else:
        FAIL.append(name)
        print(f"  ✘ {name}  {extra}")


def make_png():
    """生成一张 64x64 的纯色 PNG 用于上传测试"""
    w = h = 64
    raw = b"".join(b"\x00" + b"\x9a\xcd\x32" * w for _ in range(h))
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


s = requests.Session()
print("== 健康 ==")
r = s.get(f"{BASE}/api/health"); check("health 200", r.status_code == 200 and r.json()["database"] == "ok", r.text)

print("== 用户 ==")
uname = f"t{uuid.uuid4().hex[:6]}"
r = s.post(f"{BASE}/api/auth/register", json={"username": uname, "password": "123456", "nickname": "测试员"})
check("注册", r.status_code == 200 and r.json().get("token"), r.text)
token = r.json().get("token", "")
H = {"Authorization": f"Bearer {token}"}
r = s.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "123456"})
check("admin 登录", r.status_code == 200 and r.json().get("token"), r.text)
admin_token = r.json().get("token", "")
r = s.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": "wrong"})
check("错误密码 401", r.status_code == 401, r.text)
r = s.get(f"{BASE}/api/auth/me", headers=H)
check("me", r.status_code == 200 and r.json()["user"]["username"] == uname, r.text)

print("== 分类 / 标签 ==")
r = s.get(f"{BASE}/api/categories"); cats = r.json()["items"]
check("分类列表", r.status_code == 200 and len(cats) >= 2, r.text)
cat_id = cats[0]["id"]
r = s.post(f"{BASE}/api/categories", json={"name": f"测试分类{uuid.uuid4().hex[:4]}"}, headers=H)
check("新建分类", r.status_code == 200 and r.json().get("id"), r.text)
test_cat = r.json().get("id")
r = s.delete(f"{BASE}/api/categories/{test_cat}", headers=H)
check("删除分类", r.status_code == 200, r.text)
r = s.get(f"{BASE}/api/tags"); tags = r.json()["items"]
check("标签列表", r.status_code == 200 and len(tags) >= 1, r.text)
tag_id = tags[0]["id"]

print("== 文章 ==")
apikey_word = f"zqx{uuid.uuid4().hex[:8]}"  # 每轮唯一关键词，避免历史数据干扰
r = s.post(f"{BASE}/api/posts", json={"title": "冒烟测试文章", "content": f"这是冒烟测试内容，包含关键词 {apikey_word}。", "summary": "测试摘要", "category_id": cat_id, "tag_ids": [tag_id]}, headers=H)
check("发布文章", r.status_code == 200 and r.json().get("id"), r.text)
pid = r.json().get("id")
r = s.get(f"{BASE}/api/posts")
check("文章列表(含seed)", r.status_code == 200 and r.json()["total"] >= 3, r.text)
r = s.get(f"{BASE}/api/posts", params={"keyword": apikey_word})
check("关键词搜索", r.status_code == 200 and r.json()["total"] == 1, r.text)
r = s.get(f"{BASE}/api/posts", params={"tag_id": tag_id})
check("按标签筛选", r.status_code == 200 and r.json()["total"] >= 1, r.text)
r = s.get(f"{BASE}/api/posts/{pid}")
check("文章详情", r.status_code == 200 and r.json()["post"]["title"] == "冒烟测试文章" and r.json()["post"]["tags"], r.text)
r = s.get(f"{BASE}/api/posts/{pid}")
check("浏览量+1", r.json()["post"]["views"] >= 1, r.text)
r = s.put(f"{BASE}/api/posts/{pid}", json={"title": "冒烟测试文章(改)", "content": "修改后内容", "category_id": cat_id, "tag_ids": []}, headers=H)
check("更新文章", r.status_code == 200, r.text)
r = s.get(f"{BASE}/api/posts/archives")
check("归档接口", r.status_code == 200 and len(r.json()["items"]) >= 1, r.text)
r = s.post(f"{BASE}/api/posts", json={"title": "未登录发文", "content": "x"})
check("未登录发布 401", r.status_code == 401, r.text)

print("== 日记 ==")
r = s.post(f"{BASE}/api/diaries", json={"title": "冒烟日记", "content": "今天天气很好。", "mood": "开心", "weather": "晴"}, headers=H)
check("写日记", r.status_code == 200 and r.json().get("id"), r.text)
did = r.json().get("id")
r = s.get(f"{BASE}/api/diaries", params={"keyword": "天气"})
check("日记列表+搜索", r.status_code == 200 and r.json()["total"] >= 1, r.text)
r = s.get(f"{BASE}/api/diaries/{did}")
check("日记详情", r.status_code == 200 and r.json()["diary"]["mood"] == "开心", r.text)
r = s.put(f"{BASE}/api/diaries/{did}", json={"title": "冒烟日记(改)", "content": "改了改", "mood": "平静", "weather": "多云"}, headers=H)
check("改日记", r.status_code == 200, r.text)
r = s.get(f"{BASE}/api/diaries/{did}")
check("日记已更新", r.json()["diary"]["mood"] == "平静", r.text)

print("== 相册 ==")
png = make_png()
r = s.post(f"{BASE}/api/photos", files={"file": ("smoke.png", io.BytesIO(png), "image/png")}, data={"title": "冒烟照片"}, headers=H)
check("上传照片", r.status_code == 200 and r.json().get("url"), r.text)
photo_url = r.json().get("url", "")
r = s.get(f"{BASE}/api/photos")
check("照片列表", r.status_code == 200 and len(r.json()["items"]) >= 1, r.text)
if photo_url:
    r = s.get(f"{BASE}{photo_url}")
    check("照片可访问", r.status_code == 200 and r.headers.get("content-type", "").startswith("image"), r.status_code)
photo_id = s.get(f"{BASE}/api/photos").json()["items"][0]["id"]
r = s.delete(f"{BASE}/api/photos/{photo_id}", headers=H)
check("删除照片", r.status_code == 200, r.text)
r = s.post(f"{BASE}/api/photos", files={"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")}, headers=H)
check("拒绝非图片", r.status_code == 400, r.text)

print("== 留言 / 友链 / 统计 ==")
r = s.post(f"{BASE}/api/messages", json={"nickname": "冒烟机", "content": "测试留言"})
check("留言(免登录)", r.status_code == 200, r.text)
r = s.get(f"{BASE}/api/messages")
check("留言列表", r.status_code == 200 and r.json()["items"], r.text)
mid = r.json()["items"][0]["id"]
r = s.delete(f"{BASE}/api/messages/{mid}", headers=H)
check("登录删留言", r.status_code == 200, r.text)
r = s.post(f"{BASE}/api/friends", json={"name": "冒烟站", "url": "https://example.com", "description": "测试"}, headers=H)
check("添加友链", r.status_code == 200, r.text)
fid = r.json().get("id")
r = s.get(f"{BASE}/api/friends")
check("友链列表", r.status_code == 200 and r.json()["items"], r.text)
if fid:
    r = s.delete(f"{BASE}/api/friends/{fid}", headers=H)
    check("删除友链", r.status_code == 200, r.text)
r = s.post(f"{BASE}/api/stats/visit")
check("PV+1", r.status_code == 200, r.text)
r = s.get(f"{BASE}/api/stats")
check("统计汇总", r.status_code == 200 and "total_pv" in r.json() and r.json()["recent7"], r.text)

print("== 前端页面 (SPA 路由) ==")
for path in ("/", "/posts", "/diary", "/gallery", "/stats", "/about", "/login", "/no-such-page"):
    r = s.get(f"{BASE}{path}")
    check(f"GET {path} -> index.html", r.status_code == 200 and "div" in r.text, r.status_code)

print(f"\n通过 {PASS} 项，失败 {len(FAIL)} 项" + (f": {FAIL}" if FAIL else "  🎉 全部通过"))
