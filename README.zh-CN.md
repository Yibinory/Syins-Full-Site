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
- 带阅读状态、标签、导出和文档关联的推荐论文管理，并提供按推荐时间排序的公开 Recommended Papers 页面
- 支持直接上传 `.md`/`.markdown`、公开/私有/不公开可见性和可恢复 Trash 的文档管理
- 带主机信息、SSH 凭据加密、主机指纹确认和资源历史曲线的服务器清单
- 可在 Dashboard 中配置 3x-ui 等外部 URL，并以受限 iframe 页面嵌入
- 支持标签颜色、描述和防循环的父子层级
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
- 公开内容：`/api/v1/site/content/`、`/api/v1/publications/`、`/api/v1/docs/`、`/api/v1/public/papers/`
- 私有工作台：`/api/v1/papers/`、`/api/v1/settings/`、`/api/v1/tags/`、`/api/v1/media/`
- 基础设施：`/api/v1/servers/`（包括 SSH 测试、主机指纹确认和 metrics 历史）
- Dashboard 外部页面：`/api/v1/integrations/pages/`
- OpenAPI Schema：`/api/schema/`
- Swagger UI：`/api/docs/`

API 返回前端使用的 camelCase 字段。列表接口默认返回 DRF 分页对象（`count`、`next`、`previous`、`results`），支持 `page`、`page_size` 和经过白名单校验的 `ordering`。页面用状态过滤和时间排序表达“近期”，不建立“近期”专用表或固定状态。

推荐论文新建和更新会先按 DOI、arXiv ID、规范化标题做重复检查；命中重复记录时返回 HTTP 409 和 `code=duplicate_paper`。公开推荐论文详情会同时返回已关联的 Notes：私有 Note 的元信息可见，但内容需要登录后才能读取。

后端和数据库的详细设计见 [BACKEND_DATABASE_DESIGN.md](BACKEND_DATABASE_DESIGN.md)，服务边界说明见 [ARCHITECTURE.md](ARCHITECTURE.md)。按功能模块拆分的目标、接口、数据库和后续扩展说明见 [MODULE_DESIGN.zh-CN.md](MODULE_DESIGN.zh-CN.md)。

## 数据和安全说明

- 公开 GET 接口不要求登录；Dashboard 写操作和私有记录需要 Django Session。
- 密码、Session 和 CSRF token 由 Django 管理，前端不会持久化 API token。
- 媒体上传限制为 25 MB；interactive 内容只会在浏览器 sandbox iframe 中加载。
- 服务器监控使用固定的只读 SSH 指标脚本；首次连接必须先核对并信任主机指纹。密码在服务端加密保存，不通过 API 返回；历史资源样本会随完整备份导出。服务器操作使用显式白名单，并记录到 `ServerActionLog`；当前不提供任意 shell 执行接口。
- Dashboard 外部页面只允许 `http/https` URL，并使用 sandbox iframe；如果目标站点通过 CSP 或 `X-Frame-Options` 禁止被嵌入，页面会由目标站点策略阻止加载。
- 示例图片和示例论文是占位内容，正式公开前请通过 CMS 替换。
- 正式部署时应使用 HTTPS，启用安全 cookie，轮换 Django 和数据库密钥，并关闭 demo seed。
- 旧版 `connector_config` 仅保留兼容字段，不用于保存密码、私钥或 token。SSH 密码写入加密字段；3x-ui 等面板建议使用 Dashboard 外部页面嵌入，并自行保护目标面板的登录会话。

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

前端测试覆盖 interactive HTML/Vue/ZIP 导入、压缩包安全和工作台关系行为。后端测试覆盖公开/私有权限、认证、论文与文档关联、标签元数据、Markdown 上传、推荐论文重复检查、媒体上传和服务器监控动作。

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

### 部署主机监控

服务器清单自动包含 `Deployment host`。Docker 无法直接读取 macOS 物理宿主机的指标，因此在宿主机启动只读采集器：

```bash
sh scripts/monitor-host.sh start
sh scripts/monitor-host.sh status
# 停止：sh scripts/monitor-host.sh stop
```

采集器只依赖 Python 3（Linux / macOS），每 30 秒把主机 CPU、内存、根磁盘、可访问的 Docker 容器数量和 NVIDIA GPU 写入 `data/host-metrics/snapshot.json`。Compose 将这个目录只读挂载给后端，不暴露 Docker socket。若 Python 不在 PATH 中，可用 `PYTHON_BIN=/path/to/python3 sh scripts/monitor-host.sh start`。宿主机重启后需重新启动采集器，或用自己的 systemd / launchd 管理该命令。

没有宿主机采集器时，页面明确标记 `Docker runtime / VM`，不会将容器信息冒充物理主机；已连接的采集器超过 120 秒未更新时显示过期错误并保留最后一次有效样本。内存和磁盘以 GiB / TiB 表示。macOS 内存采用总内存减去 free / inactive / speculative 页的估算口径，与活动监视器的应用内存口径不同。

示例服务器默认隐藏，不计入实时统计，也不会产生伪造的新样本。新增 SSH 主机后会立即测试连接并展示待确认的指纹；修改连接地址或端口会清除旧指纹，密码留空则保留已有密码。SSH 采集当前支持 Linux。

### 外部页面导航

嵌入窗口支持普通页内跳转、表单、下载和新窗口；用户点击触发的顶层跳转也可执行。切换侧栏的外部页面会正确加载新配置。地址栏仅用于输入要打开的 URL，不冒充跨域 iframe 的实时地址。第三方站点的嵌入限制、登录 cookie 限制仍由浏览器执行；需要完整浏览器环境时使用 `Open in browser`。

### 页面与语言（2026-09）

- 公开笔记列表点击后直接进入阅读页。推荐论文只返回关联笔记的基础信息，正文在笔记页按需读取。
- 编辑笔记时可使用“从 Markdown 文件替换正文”，仅替换当前草稿正文；标题、简介、独立摘要、标签和可见性不变，点击保存后生效。
- 首页会列出所有选中的发表论文，按年份从新到旧排序。
- 工作台统计来自 `/api/v1/overview/` 的数据库聚合结果，不使用浏览器中的示例计数；mock 服务器不计入统计。
- 外部页面新增 `publiclyVisible` 开关，默认关闭。公开入口为 `/tools` 和 `/tools/:slug`，只读接口为 `/api/v1/public/pages/`。取消公开后，直接访问该详情接口也会返回 404。VPN 旧入口跳转到外部页面管理。
- 中 / EN 按钮切换公开页面与工作台的固定界面文案，选择保存在当前浏览器。翻译集中在 `src/i18n/zh.ts`；用户输入的内容和数据库中的枚举值不会随语言切换改变。
- SSH 地址选择以填写的 IP 优先，未填写 IP 时使用主机名。已有远端主机可修改连接方式或删除（同时删除其采集历史）；系统部署主机由程序管理，不支持删除。
