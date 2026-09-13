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

## 引导安装（Linux / macOS / Windows）

需要 Git、**Python 3.9+**、已启动的 Docker Engine/Desktop 和 Compose v2。
Windows 使用 Docker Desktop 的 **Linux 容器模式**；macOS 先启动 Docker Desktop。
安装器会检查依赖，不会静默修改系统来安装 Docker；Docker 首次安装可能需要管理员权限或重启。

Linux / macOS 一行克隆并启动向导：

```bash
git clone https://github.com/Yibinory/Syins-Full-Site.git && cd Syins-Full-Site && sh scripts/install.sh
```

Windows PowerShell：

```powershell
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

向导设置站点名称、默认语言、管理员用户名、可选邮箱、密码（至少 12 位）和可选公开主机名/IP。
数据库密码及应用密钥自动随机生成，保存在已忽略的 `.env` 中，不在终端输出密码。
请妥善保护此文件；Windows 的文件访问权限由所在目录的 ACL 控制。

**使用向导前不要复制 `.env.example`**：检测到已有 `.env` 时会保留它并跳过初始化提问。
也可手动准备 `.env`，但必须自行替换全部占位密码。重复运行及升级均保留账户、内容与数据卷，
不会重设密码或自动导入示例。

新安装只有管理员、通用双语首页和自动登记的部署主机。发表论文、推荐论文、笔记、研究项目、外部页面等业务记录为空。
首次登录后在 **Dashboard → 站点内容** 编辑首页。默认语言用于首次访问；用户在浏览器中明确选择过的语言优先。

### 端口选择与启动检查

网站优先尝试 8080，被占用时向后搜索最多 99 个端口。首次安装实际绑定失败也会重新选择并重试。
最终端口及对应 CSRF 来源写入 `.env`。安装器通过 Nginx 检查后端公开 API 成功后，才输出就绪和访问地址。
请使用安装器输出的地址，不要默认认为一定是 8080。

```bash
sh scripts/install.sh --port 8090
# 可选：同时开放仅本机能连接的数据库端口
sh scripts/install.sh --port 8090 --database-port 5432
```

PowerShell 支持同样的参数。数据库默认不映射宿主机端口，网站端口映射到宿主机接口。
公开主机名/IP 会写入 Django 允许列表，但不会自动配置域名解析、防火墙、路由器转发或 HTTPS。
HTTPS 部署还需配置 `DJANGO_ALLOWED_HOSTS`、`DJANGO_CSRF_TRUSTED_ORIGINS` 和安全 Cookie。
该输入目前支持 DNS 主机名及 IPv4 地址。

自动选端口只用于**新安装**，已有安装保留原端口，避免地址意外改变。Dashboard 动态修改端口需要启动下文所述的宿主机管理进程。

### 源码构建与预构建镜像

默认从当前代码通过 Docker 在本机构建。轻负载运行可按约 2GB 内存规划；部署机器同时构建时建议留更多余量，4GB 更宽裕。

新增 `.github/workflows/images.yml`：推送 `v*` 标签或手动运行时，构建并发布 **linux/amd64 和 linux/arm64**
后端/前端镜像到 GHCR。**本次代码只提供发布流程，并不代表镜像已经发布。**
维护者需要先运行工作流，并将 GHCR 包设为公开，其他人才能匿名拉取。
Fork 项目需要修改 `docker-compose.images.yml` 中的镜像仓库地址。

实际发布标签后可免本机构建安装：

```bash
sh scripts/install.sh --version v1.0.0  # 示例，替换为真实已发布的标签
```

首次安装使用 `--source` 可明确选择源码构建。安装模式、Compose 文件组合及镜像版本保存在 `.env`，升级沿用。
固定版本升级时手动修改 `IMAGE_TAG`；`latest` 跟随最近一次工作流发布。

### 升级、示例内容与故障恢复

```bash
git pull
sh scripts/update.sh
sh scripts/backup.sh
```

Windows 升级使用 `powershell -ExecutionPolicy Bypass -File scripts/update.ps1`。
Windows 也可使用 Dashboard 的备份下载功能；Shell 备份存放在 `data/backups/`，建议另存到其他机器。

需要演示内容时主动执行：

```bash
docker compose exec backend python manage.py seed_demo
```

这会添加样例业务记录，不改变已有管理员凭据。默认 `SEED_DEMO=false`，保持关闭以免重启时重新补回删掉的示例。
账户初始化已独立为 `bootstrap`，发现已有用户就跳过，不覆盖现有站点。
若数据库已有用户但没有管理员，需明确执行 `manage.py createsuperuser`；安装器不会擅自提升已有用户权限。

失败后先执行 `docker compose ps`、`docker compose logs backend`，修正 `.env` 后可重新运行安装器。
改环境变量不会重设已存在的账户密码。需要保留数据时，不要用 `docker compose down -v` 排障。

物理主机采样是可选项：Linux/macOS 可运行 `sh scripts/monitor-host.sh start`，必要时设置 `PYTHON_BIN`。
未启用时会明确显示后端/容器运行环境指标，不将其称为物理主机数据。
Windows 原生硬件采样尚未实现，网站可以通过 Linux 容器正常运行，也支持远程 Linux SSH 监控。

## 在 Settings 中修改部署端口

部署管理员（Django 超级用户）可在 **Dashboard → 设置 → 部署端口** 调整网站访问端口，
以及是否开放仅本机能访问的 PostgreSQL 端口。容器内部端口保持固定。
该功能需要 **Docker Compose 2.24.4 或更新版本**。

安装器会在站点就绪后启动独立的宿主机管理进程。已有安装先更新 Compose 部署，以挂载
`data/deployment`，然后运行：

```bash
python3 scripts/deployment_manager.py start
python3 scripts/deployment_manager.py status
```

Windows 将 `python3` 替换为 `py -3`。管理进程需要操作当前项目的 Docker Compose 权限，
只接受经过校验的网站/数据库端口请求；不会将 Docker socket 或任意命令执行能力交给 Django。

点击应用会短暂重启相关服务。管理进程依次检查占用、更新 `.env` 与私有 Compose 覆盖配置、
应用映射，并通过新端口检查公开 API。失败会恢复原配置和端口。事务记录支持进程中断后的恢复，
整个流程不会删除数据库数据卷。

网站端口切换后，旧浏览器标签可能断开连接，点击**打开新的直连地址**，在新地址的设置页检查结果。
使用反向代理时继续使用原域名，并单独调整代理上游端口。
不会自动改变 DNS、TLS、防火墙或路由器转发，本机健康检查成功不等于公网已放行新端口。
保留原有网站监听地址，数据库仅绑定 `127.0.0.1`。自定义多端口映射会拒绝自动修改，
避免覆盖额外配置；两个已占用服务互换端口需要分步骤操作。

管理进程需要持续运行。安装和升级脚本会启动它，但**不会自动安装操作系统开机服务**。
主机重启后需要再次运行 `start`；无人值守场景可使用 systemd、launchd 或任务计划程序托管
`python3 scripts/deployment_manager.py run`，工作目录设为项目目录。
管理进程停止不影响网站运行，设置页会禁用端口变更。Windows 入口已提供，但仍需 Windows 实机验证。

在部署机器恢复未完成的变更：

```bash
python3 scripts/deployment_manager.py stop
python3 scripts/deployment_manager.py recover
python3 scripts/deployment_manager.py start
```

`stop` 会等待正在执行的变更结束；`recover` 只恢复**尚未完成的事务**，不会撤销已经成功的变更。
如果新地址无法从外部访问，可通过宿主机命令主动改回指定端口：

```bash
python3 scripts/deployment_manager.py stop
python3 scripts/deployment_manager.py set-ports --app-port 8080
# 如需本机数据库客户端访问，再加 --database-port 5432
python3 scripts/deployment_manager.py start
```

`.deployment/` 中可能有 `.env` 的临时恢复快照，应保持私密，不提交或放入对外共享的备份。
管理进程日志位于 `.deployment/controller.log`；`data/deployment/` 只存请求与状态，不存数据库密码。
事务执行期间不要手动修改受管理的端口配置。自定义项目名需将 `COMPOSE_PROJECT_NAME` 写入 `.env`，
不能只在一次命令中使用 `-p`。

## 本地开发

在项目根目录执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
../.venv/bin/python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='use-a-unique-12-character-password' ../.venv/bin/python manage.py bootstrap
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
