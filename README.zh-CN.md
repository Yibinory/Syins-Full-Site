# Syins Research OS

Syins Research OS 是一个面向个人研究者的研究主页和私有研究工作台。公开站点展示研究方向、论文和公开 Notes；私有 Dashboard 用于管理研究记录、推荐论文、文档、媒体资源和服务器清单。

项目遵循的原则是：

> 现在保持简单，未来易于扩展。

English version: [README.md](README.md)

## 当前已实现

- Vue 3 + Vite + TypeScript 公共站点和 Dashboard
- Django 4.2 + Django REST Framework API
- Docker 中使用 PostgreSQL，本地开发支持 SQLite
- 基于 Session 和 CSRF 的认证
- 个人资料、研究方向和精选研究项目 CMS
- 带标签、链接、BibTeX 和媒体引用的论文管理
- 带阅读状态、标签、导出和文档关联的推荐论文管理
- 支持 Markdown、公开/私有/不公开可见性和可恢复 Trash 的文档管理
- 带能力快照和审计动作的服务器清单
- 支持图片、视频、HTML、Vue 和 ZIP 的服务端媒体存储
- OpenAPI Schema 和 Django Admin
- 数据库 migration、幂等示例数据和自动化 API 测试
- 使用 Nginx、PostgreSQL、媒体持久化卷的 Docker Compose 部署
- 一键安装、更新和备份脚本

## Docker 快速启动

要求：Docker Engine 或 Docker Desktop，以及 Compose v2。

```bash
cp .env.example .env
# 修改 DJANGO_SECRET_KEY、POSTGRES_PASSWORD 和 DJANGO_SUPERUSER_PASSWORD。
# 如果使用自定义域名，还需要修改 DJANGO_ALLOWED_HOSTS 和 DJANGO_CSRF_TRUSTED_ORIGINS。
sh scripts/install.sh
```

启动后访问：<http://localhost:8080/>。

首次启动会执行数据库 migration 和静态文件收集；当 `SEED_DEMO=true` 时，还会创建管理员和缺失的示例记录。示例数据初始化是非破坏性的，不会覆盖已有内容，因此升级时可以暂时保持开启。确定不再需要示例数据后，可将其改为 `false`。

如果当前终端找不到 Docker Desktop CLI，可以先加入 Docker 的命令路径：

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:/Applications/Docker.app/Contents/Resources/cli-plugins:$PATH"
```

### 更新已部署项目

```bash
git pull
sh scripts/update.sh
```

更新会保留 PostgreSQL 和媒体 volume。进行风险较高的升级前，建议先备份：

```bash
sh scripts/backup.sh
```

备份写入 `data/backups/`，并应复制到独立机器或其他存储位置。

## 本地开发

在项目根目录执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
../.venv/bin/python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='change-me' ../.venv/bin/python manage.py seed_demo
../.venv/bin/python manage.py runserver 127.0.0.1:8000
```

另开一个终端运行前端：

```bash
pnpm install
pnpm dev
```

Vite 会把 `/api`、`/admin`、`/media` 和 `/static` 代理到本地 Django 服务。未设置 `DATABASE_URL` 时，后端默认使用 `data/database/research-os.sqlite3`。

## 项目结构

```text
src/                         Vue 应用和 API-backed stores
backend/config/              Django 配置、URL、WSGI/ASGI
backend/apps/accounts/       登录认证
backend/apps/content/        公开站点内容
backend/apps/publications/   正式论文和预印本
backend/apps/documents/      Notes 和 Markdown 文档
backend/apps/papers/         推荐论文记忆
backend/apps/servers/        服务器清单和安全动作
backend/apps/core/           媒体、标签、设置和共享基础设施
Dockerfile.backend           Django/Gunicorn 镜像
Dockerfile.frontend          Vite/Nginx 镜像
docker-compose.yml           PostgreSQL + 后端 + 前端部署
nginx/default.conf            SPA fallback 和反向代理
scripts/                     安装、更新和备份命令
```

## API

- 认证：`/api/v1/auth/session/`、`/api/v1/auth/login/`、`/api/v1/auth/logout/`
- 公开内容：`/api/v1/site/content/`、`/api/v1/publications/`、`/api/v1/docs/`
- 私有工作台：`/api/v1/papers/`、`/api/v1/settings/`、`/api/v1/tags/`、`/api/v1/media/`
- 基础设施：`/api/v1/servers/`
- OpenAPI Schema：`/api/schema/`
- Swagger UI：`/api/docs/`

API 返回前端使用的 camelCase 字段。列表接口默认分页，前端的 `listData` helper 同时兼容分页和非分页响应。

后端和数据库的详细设计见 [BACKEND_DATABASE_DESIGN.md](BACKEND_DATABASE_DESIGN.md)，服务边界说明见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 数据和安全说明

- 公开 GET 接口不要求登录；Dashboard 写操作和私有记录需要 Django Session。
- 密码、Session 和 CSRF token 由 Django 管理，前端不会持久化 API token。
- 媒体上传限制为 25 MB；interactive 内容只会在浏览器 sandbox iframe 中加载。
- 服务器操作使用显式白名单，并记录到 `ServerActionLog`；当前不提供任意 shell 执行接口。
- 示例图片和示例论文是占位内容，正式公开前请通过 CMS 替换。
- 正式部署时应使用 HTTPS，启用安全 cookie，轮换 Django 和数据库密钥，并关闭 demo seed。
- `connector_config` 当前不会通过 API 返回；在启用真实 SSH、Docker Remote 或 3x-ui connector 前，不要保存明文私钥、密码或 token。

## 验证命令

前端：

```bash
pnpm test
pnpm build
```

后端：

```bash
cd backend
../.venv/bin/python manage.py check
../.venv/bin/python manage.py makemigrations --check --dry-run
../.venv/bin/python manage.py test
```

Docker：

```bash
docker compose ps
docker compose logs --tail=100 backend
curl -I http://localhost:8080/
curl http://localhost:8080/api/v1/site/content/
```

前端测试覆盖 interactive HTML/Vue/ZIP 导入、压缩包安全和工作台关系行为。后端测试覆盖公开/私有权限、认证、论文与文档关联、标签合并、媒体上传和安全服务器动作。

## 生产部署注意事项

`.env` 不应提交到 Git。正式部署前至少修改：

```text
DJANGO_SECRET_KEY
POSTGRES_PASSWORD
DATABASE_URL
DJANGO_SUPERUSER_PASSWORD
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
```

数据库和媒体文件使用独立 Docker volume。升级应用时只替换镜像并执行增量 migration，不要删除数据 volume。备份数据库时必须同时备份媒体文件，以避免数据库记录和文件资源不一致。
