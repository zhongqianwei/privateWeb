# 我的小窝 · Little Home

一个极简、冷淡、可长期维护的全栈个人博客。基于 **Vue 3 + Vite + TailwindCSS** 与 **FastAPI + MySQL**，前台、后台与 API 同仓库交付。

> 没有动漫图、没有风景照、没有花哨动效。只有低饱和弥散光、磨砂玻璃、克制的排版与足够多的留白。

---

## 预览

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `#/home` | 问候、站点数据、精选内容、最近文章、生活切片 |
| 文章 | `#/posts` | 搜索、分类/标签筛选、归档筛选、分页 |
| 阅读 | `#/posts/:id` | Markdown、代码高亮、目录滚动高亮、阅读进度、上下篇 |
| 记录 | `#/diary` | 随笔 / 日记 / 学习记录三类时间线，支持增删改 |
| 相册 | `#/gallery` | 多图上传、瀑布流、灯箱预览 |
| 关于 | `#/about` | 个人简介、技术栈、联系方式（后台可配置） |
| 归档 / 友链 / 留言 / 统计 | `#/archive` 等 | 常规内容模块 |
| 后台 | `#/manage` | 概览、文章、分类标签、记录、相册、留言、友链、站点设置 |

---

## 功能清单

- **内容**：文章发布 / 编辑 / 删除、精选标记、草稿、摘要、封面、分类、标签、全文搜索、年月归档
- **记录**：随笔 / 日记 / 学习记录三类，时间线浏览，行内增删改
- **媒体**：图片上传（10MB 以内，白名单格式）、相册瀑布流、灯箱查看
- **互动**：游客留言、友链展示与管理
- **后台**：数据概览、内容管理、分类标签维护、站点信息配置
- **阅读体验**：Markdown 渲染、代码高亮、目录锚点与滚动高亮、全站阅读进度条、深浅主题切换
- **工程化**：JWT 鉴权、PBKDF2 加盐密码、统一错误格式、SQL 幂等迁移、自动化自检脚本

---

## 技术栈

| 层 | 选型 |
| --- | --- |
| 前端 | Vue 3 Composition API、Vite 5、Vue Router（hash）、TailwindCSS 3 |
| 内容渲染 | marked + highlight.js |
| 后端 | Python 3.10+、FastAPI、Uvicorn、PyMySQL、Pydantic v2、PyJWT |
| 数据库 | MySQL 8.x（utf8mb4，中文全文索引 ngram） |
| 部署 | 后端直接托管 `frontend/dist`，单进程一体化；可选 Nginx 反代 |

---

## 目录结构

```
privatWebe/
├── backend/
│   ├── app/
│   │   ├── main.py            # 应用入口 / 静态托管 / 异常处理
│   │   ├── config.py          # .env 配置
│   │   ├── database.py        # 连接池与事务封装
│   │   ├── models.py          # Pydantic 请求模型
│   │   ├── security.py        # 密码哈希 / JWT
│   │   └── routers/           # auth / posts / diaries / photos / messages
│   │                          # friends / categories / tags / stats / settings
│   ├── init.sql               # 全新库建表脚本
│   ├── scripts/migrate_v2.py  # 老库幂等增量迁移
│   ├── scripts/smoke_v2.py    # 全接口冒烟测试
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/               # fetch 封装与模块 API
│   │   ├── components/        # 导航 / 卡片 / 分页 / Markdown / 状态组件
│   │   ├── composables/       # toast
│   │   ├── router/            # 路由与登录守卫
│   │   ├── store/             # 用户态 / 站点设置
│   │   ├── utils/             # 日期与文本工具
│   │   ├── views/             # 14 个页面
│   │   ├── style.css          # Tailwind 入口 + 设计令牌 + 排版
│   │   └── App.vue            # 背景 / 进度条 / 布局外壳
│   ├── check-ui.mjs           # 桌面+移动端截图与溢出检查
│   ├── e2e-check.mjs          # 注册→写作→后台→记录交互检查
│   ├── tailwind.config.js
│   └── postcss.config.js
├── content/                   # 文章原稿归档
└── DEPLOYMENT.md              # 详细部署文档
```

---

## 快速开始

```bash
# 1) 数据库：创建库表
mysql -u root -p < backend/init.sql

# 2) 后端配置
cd backend
cp .env.example .env
# 编辑 .env：填 DB_PASSWORD、JWT_SECRET
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/migrate_v2.py       # 全新库可跳过，重复执行安全
uvicorn app.main:app --reload --port 8000

# 3) 前端（另开终端）
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

生产构建：`cd frontend && npm run build`，产物在 `frontend/dist`，重启后端即可由 FastAPI 直接托管在 `http://127.0.0.1:8000`。

完整步骤、生产部署与排错见 **[DEPLOYMENT.md](./DEPLOYMENT.md)**。

---

## 自检

```bash
# 后端接口（需先启动服务）
cd backend && ./venv/Scripts/python.exe scripts/smoke_v2.py

# 前端构建 + 24 组页面/视口截图检查
cd frontend && npm run build && npm run check:ui

# 真实交互流程（会创建临时数据，脚本结束后需手动清理）
cd frontend && npm run check:e2e
```

最近一次自检结果：接口 **28/28** 通过；页面 **24/24** 无控制台错误、无横向溢出；交互 **12/12** 通过。

---

## 设计参考

实现前调研了 GitHub 上若干高星个人博客 / 全栈博客项目，提取了以下共性并落地：

| 参考项目 | 借鉴的特点 | 本项目的落地方式 |
| --- | --- | --- |
| `sxchou/futuristic-blog` | 玻璃态、暗色模式、阅读进度、后台仪表盘、Markdown | 全站玻璃卡片、进度条、写作台与后台概览 |
| `AVIDS2/Astris-Blog` | 前台/后台双端适配、动态内容、本地搜索 | 响应式导航与后台八标签、即时筛选 |
| `phenol-cat/homepage` | CSS 变量主题、玻璃拟态、Zen 式克制 | 令牌化配色 + 深浅主题切换 |
| `kintong3000/kintong-blog` | GitHub 风格排版、代码高亮、目录跟随 | `prose-mini` 排版系统、highlight.js、TOC 滚动高亮 |
| `Kirie233/Kirie-Blog` | 组件化、标签系统、搜索 | 组件拆分、标签筛选、关键词搜索 |
| `Peerless-man/vue3-blog` | 前后台分离、完整管理视图 | `/manage` 统一管理入口 |

> 以上均为设计思路参考，本项目代码为独立实现，未复制其源码。

---

## 许可与说明

本项目用于个人学习与自建站点。生产环境请务必修改 `backend/.env` 中的 `JWT_SECRET` 与数据库密码，并按需收紧 CORS 配置。
