# ☁️ 上传 GitHub & 部署 Pages 教程（保姆级）

> 目标：把「我的小窝」前端（`frontend/dist`）发布到 GitHub Pages，任何人都能通过
> `https://你的用户名.github.io/仓库名/` 访问。后端 + 数据库跑在自己电脑上。

---

## 第 0 步：准备 GitHub 账号

没有的话去 https://github.com/signup 注册，用户名下面记作 `<你的用户名>`。

---

## 方式一：Git 推送 + Actions 自动构建（推荐）

本项目已内置工作流 `.github/workflows/deploy.yml`——你只管推代码，构建发布全自动。

### 1. 在 GitHub 建一个空仓库

登录 GitHub → 右上角 `+` → **New repository** →
名字随意（例 `my-home`）→ 选 **Public**（Pages 免费版要求）→ **不要**勾选 README → Create。

### 2. 本地初始化并推送

在项目根目录（privatWebe）打开终端：

```bash
git init
git add .
git commit -m "feat: 我的小窝 v1.0"
git branch -M main
git remote add origin https://github.com/<你的用户名>/my-home.git
git push -u origin main
```

> Windows 第一次推送会弹 GitHub 登录窗，授权即可。
> `.gitignore` 已排除 `node_modules / venv / dist / .env`，放心 add。

### 3. 开启 Pages（只设一次）

GitHub 仓库页面 → **Settings** → 左侧 **Pages** →
**Build and deployment → Source** 选 **GitHub Actions** → 保存。

### 4. 触发部署

刚才的 `git push` 已经触发。等 2~3 分钟 → 仓库 **Actions** 标签页看到绿勾 →
打开 **Settings → Pages** 顶部显示的网址：

```
https://<你的用户名>.github.io/my-home/
```

以后每次 `git push`，页面自动更新。✅

---

## 方式二：手动上传 dist（不想配 Git 时）

1. 本地 `cd frontend && npm run build`，得到 `dist/`；
2. GitHub 建仓库后，仓库首页点 **uploading an existing file**；
3. 把 `dist` 文件夹里的**所有文件**（不是文件夹本身）拖进去，Commit；
4. Settings → Pages → Source 选 **Deploy from a branch** → 选 `main` / `/ (root)` → Save；
5. 等 1 分钟访问上面的网址。

---

## ⚠️ 关键：前端在 Pages、后端在哪？

Pages 只是静态托管的网页，**数据（文章/日记/图片）全靠后端接口**。因此：

### 场景 A：只有自己电脑访问（学习用，最简单）

1. 保持后端在本地跑：`cd backend && venv\Scripts\python.exe run.py`
2. 修改 `frontend/src/api/index.js`：`export const API_BASE = 'http://127.0.0.1:8000'`
3. 重新 `npm run build`，把新 dist 推上去；
4. 网页即可调你本机的后端（127.0.0.1 在你电脑浏览器里始终指向你自己的机器）。

> ⚠️ 127.0.0.1 只在你自己电脑有效；换设备/手机访问页面时接口会失效（属正常现象）。

### 场景 B：想让全世界访问（可选进阶）

需要一台公网服务器或免费云平台跑后端 + MySQL（如 Render、Railway、阿里云 ECS），

1. 后端部署后在云平台得到公网地址，如 `https://api.xxx.com`；
2. `API_BASE` 改成该地址 → 重新构建 → 推 GitHub；
3. `backend/.env` 的 CORS 不用改（默认全放行），生产建议填前端域名。

> 考虑到本机开发体验，**演示推荐方式 A**；答辩展示时用 `http://127.0.0.1:8000` 一体化模式即可。

---

## 常见问题

| 现象 | 原因 / 处理 |
| --- | --- |
| Pages 显示 404 | Pages 没开（第 3 步）/ Actions 构建失败（看 Actions 红叉日志） |
| 页面白屏 | F12 看 Console：接口地址不对 → 检查 `API_BASE` |
| push 被拒 `rejected` | 远端已有 README 提交：`git pull origin main --allow-unrelated-histories` 再推 |
| 想换仓库名 | Settings → General → Rename，之后本地 `git remote set-url origin <新地址>` |
