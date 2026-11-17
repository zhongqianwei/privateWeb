# 部署文档 · 我的小窝

本站点支持两种部署方式：

1. **一体化部署（推荐）**：FastAPI 同时提供 API 与前端静态文件，单进程即可运行。
2. **前后端分离**：Vite 构建产物交给 Nginx，API 反代到 FastAPI。

---

## 1. 环境依赖

| 软件 | 版本要求 | 用途 |
| --- | --- | --- |
| Node.js | ≥ 18（推荐 20 LTS） | 前端构建 |
| npm | ≥ 9 | 前端依赖管理 |
| Python | ≥ 3.10（推荐 3.11/3.12） | 后端运行时 |
| MySQL | ≥ 8.0（需支持 ngram 全文解析器） | 数据存储 |
| 可选：Nginx | 任意稳定版 | 生产反代 / HTTPS |
| 可选：Docker + Docker Compose | 任意稳定版 | 容器化部署 |

验证：

```bash
node -v && npm -v
python --version
mysql --version
```

---

## 2. 数据库初始化

### 2.1 建库建表

```bash
mysql -u root -p < backend/init.sql
```

脚本会创建 `little_home` 库以及 `users / categories / tags / posts / post_tags / diaries / photos / messages / friend_links / site_stats / site_settings` 共 11 张表，并初始化统计行与站点设置行。

### 2.2 配置账号（可选但推荐）

```sql
CREATE USER 'littlehome'@'localhost' IDENTIFIED BY '换成强密码';
GRANT ALL PRIVILEGES ON little_home.* TO 'littlehome'@'localhost';
FLUSH PRIVILEGES;
```

### 2.3 老库升级

如果你是旧版本升级，先备份再执行幂等迁移（可重复运行）：

```bash
cd backend
./venv/Scripts/python.exe scripts/migrate_v2.py
```

该脚本只补齐缺失字段与表：`users.is_admin`、`posts.cover/featured/status`、`diaries.kind`、`site_settings`，不会覆盖已有数据。

---

## 3. 后端配置与启动

### 3.1 配置文件

```bash
cd backend
cp .env.example .env
```

编辑 `.env`：

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=littlehome
DB_PASSWORD=你的数据库密码
DB_NAME=little_home

JWT_SECRET=一段足够长的随机字符串
TOKEN_EXPIRE_HOURS=72

HOST=0.0.0.0
PORT=8000
```

生成随机密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> **安全提示**：生产环境不要使用默认 `JWT_SECRET`；不要提交 `.env` 到 Git。

### 3.2 安装依赖

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3.3 开发启动

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

健康检查：<http://127.0.0.1:8000/api/health>，应返回 `{"status":"ok","database":"ok"}`。

接口文档：<http://127.0.0.1:8000/docs>。

---

## 4. 前端构建与启动

### 4.1 开发模式

```bash
cd frontend
npm install
npm run dev
```

访问 <http://localhost:5173>。Vite 已配置代理，`/api` 与 `/uploads` 自动转发到 `127.0.0.1:8000`。

### 4.2 生产构建

```bash
cd frontend
npm run build
```

产物在 `frontend/dist`。后端启动时会自动检测该目录并托管：

- 静态资源走 `/assets/*`
- API 走 `/api/*`
- SPA 路由回退到 `index.html`

因此一体化部署只需启动后端：<http://服务器IP:8000>。

---

## 5. 生产部署

### 5.1 一体化 + systemd（Linux）

创建 `/etc/systemd/system/little-home.service`：

```ini
[Unit]
Description=Little Home Blog
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/privatWebe/backend
ExecStart=/opt/privatWebe/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-fail

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now little-home
sudo systemctl status little-home
```

### 5.2 Nginx 反代 + HTTPS

```nginx
server {
    listen 80;
    server_name blog.example.com;

    client_max_body_size 12m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

申请证书后改为 `listen 443 ssl` 并加上 80 → 443 跳转。

> 上传目录由后端 `/uploads` 提供，Nginx 反代时无需额外配置；若想让 Nginx 直接服务图片，可加 `location /uploads/ { alias /opt/privatWebe/backend/uploads/; }`。

### 5.3 前后端分离部署

把 `frontend/dist` 放到任意静态托管（Nginx / GitHub Pages / Vercel）。此时需要：

1. 修改 `frontend/src/api/index.js` 的 `API_BASE` 为后端完整地址；
2. 后端 `.env` 设置 `CORS_ORIGINS`（当前实现默认 `allow_origins=["*"]`，分离部署可按域名收紧）；
3. 注意浏览器不会在跨域请求中自动共享本地存储，登录态仍在前端域名下保存。

---

## 6. 首次使用

1. 打开站点，点击右上角「登录」→ 切换到「注册」。
2. **第一个注册的账号用于管理站点**。密码使用 PBKDF2 加盐存储。
3. 进入 `#/manage` →「站点设置」填写站点名、作者名、简介、邮箱与 GitHub。
4. 在「分类标签」建立常用分类与标签。
5. 在 `#/posts/new` 写第一篇文章；开启「设为精选」后会出现在首页。
6. 在「后台 → 文章」可切换草稿、编辑与删除。

---

## 7. 自检脚本

```bash
# 后端：读接口 + 写闭环（自动清理测试数据）
cd backend && ./venv/Scripts/python.exe scripts/smoke_v2.py

# 前端：构建 + 12 个页面 × 桌面/移动端截图 + 溢出与控制台检查
cd frontend && npm run check:ui

# 前端：真实交互流程（注册、写作、后台切换、写记录）
cd frontend && npm run check:e2e
```

截图输出到 `frontend/qa/`。`check:e2e` 会创建临时账号与内容，测试后请按用户名前缀 `e2e_` 清理：

```bash
cd backend && ./venv/Scripts/python.exe -c "
from app.database import execute, query
rows = query(\"SELECT id FROM users WHERE username LIKE 'e2e_%'\")
for r in rows:
    uid=r['id']
    execute('DELETE FROM post_tags WHERE post_id IN (SELECT id FROM posts WHERE user_id=%s)',(uid,))
    execute('DELETE FROM posts WHERE user_id=%s',(uid,))
    execute('DELETE FROM diaries WHERE user_id=%s',(uid,))
    execute('DELETE FROM users WHERE id=%s',(uid,))
print('cleaned', len(rows))
"
```

---

## 8. 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `/api/health` 返回 `database: error` | MySQL 未启动或 `.env` 账号密码错误；用 `mysql -u 用户 -p` 验证 |
| 启动报 `Unknown column 'featured'` | 老库未迁移；执行 `scripts/migrate_v2.py` |
| 上传图片 400 | 格式不在白名单或超过 10MB；检查 `config.py` 的 `ALLOWED_EXTS` / `MAX_FILE_SIZE` |
| 上传后图片不显示 | 后端未托管 `/uploads`，或 Nginx 反代丢失该路径 |
| 刷新带 token 的页面被踢到登录 | 路由守卫会等待会话恢复；若仍发生，检查浏览器是否禁用了 localStorage |
| 中文搜索命中率低 | 确认 `posts` 表含 `FULLTEXT ... WITH PARSER ngram`；当前列表搜索使用 LIKE，短关键词更稳 |
| 浅色主题下对比度异常 | 主题写在 `localStorage.lh_theme`，清除后默认深色 |
| 前端改完没生效 | 生产模式需 `npm run build` 并重启/刷新后端 |

---

## 9. 备份建议

```bash
# 数据库
mysqldump -u root -p little_home > backup-$(date +%F).sql

# 上传图片
tar czf uploads-$(date +%F).tar.gz backend/uploads
```

升级前先备份，再执行迁移脚本。

---

## 10. 目录与端口速查

| 项 | 默认 |
| --- | --- |
| 后端 API | `http://127.0.0.1:8000/api` |
| 静态上传 | `http://127.0.0.1:8000/uploads` |
| 前端开发 | `http://localhost:5173` |
| 数据库 | `127.0.0.1:3306 / little_home` |
| 前端构建产物 | `frontend/dist` |
