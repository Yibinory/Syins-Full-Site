# Syins Research OS 功能模块设计说明

> 文档状态：开发协作版 v0.1  
> 适用范围：当前仓库中的 Vue 3 前端、Django REST Framework 后端、PostgreSQL/SQLite 数据层和 Docker 部署方案。  
> 用途：作为后续逐模块讨论、修改接口、调整数据库和验收功能的基线。

这份文档描述的是当前代码已经具备的结构，同时把尚未实现但已经预留的边界单独标记出来。后续如果某个模块的目标发生变化，应同步更新：

1. 本文档中的模块目标、接口和数据模型；
2. Django model、serializer、view/service 和 migration；
3. Vue 页面、Pinia store 和 API 调用；
4. 后端测试、前端交互测试和 README；
5. Docker 启动、备份和升级说明（如果影响部署）。

## 1. 系统总览

### 1.1 产品边界

Syins Research OS 由两部分组成：

- 公开研究主页：展示个人资料、研究方向、精选研究、论文和公开 Notes。
- 私人研究工作台：管理推荐论文、研究文档、标签、媒体资源、服务器清单和工作台设置。

当前定位是单用户、单工作区、单实例部署。设计上保留了未来扩展多人协作、外部客户端和真实基础设施连接器的空间，但当前不提前引入多租户、微服务、消息队列或独立搜索集群。

### 1.2 运行链路

    浏览器 Vue SPA
        -> Nginx 静态文件与反向代理
        -> Django + DRF + Gunicorn
        -> PostgreSQL（Docker）或 SQLite（本地开发）
        -> media volume（上传媒体）

Nginx 负责：

- 提供构建后的前端静态文件；
- 将 /api/ 和 /admin/ 转发给 Django；
- 提供 /media/ 下的上传资源；
- 保持浏览器与 API 同源，便于使用 Session + CSRF。

### 1.3 前端路由地图

| 路由 | 页面 | 访问边界 | 主要模块 |
| --- | --- | --- | --- |
| / | HomePage | 公开 | 个人资料、研究、精选项目 |
| /research | 重定向到首页研究区块 | 公开 | 兼容入口 |
| /publications | PublicationsPage | 公开 | 论文列表与筛选 |
| /notes | NotesPage | 公开 | 公开 Notes 列表 |
| /notes/:slug | NoteDetailPage | 公开/按可见性 | Note 阅读页 |
| /papers | PublicPapersPage | 公开 | 推荐论文公开记忆与关联 Note |
| /login | LoginPage | 未登录用户 | 登录 |
| /dashboard | OverviewPage | 登录 | 工作台总览 |
| /dashboard/content | SiteContentPage | 登录 | 公开站点内容管理 |
| /dashboard/papers | PapersPage | 登录 | 推荐论文管理 |
| /dashboard/publications | PublicationManagerPage | 登录 | 已发表论文管理 |
| /dashboard/docs | DocumentsPage | 登录 | 文档与 Trash |
| /dashboard/servers | ServersPage | 登录 | 服务器清单与动作 |
| /dashboard/integrations | IntegrationsPage | 登录 | 可嵌入的外部 Dashboard 页面 |
| /dashboard/integrations/:slug | EmbeddedPageView | 登录 | 查看嵌入页面 |
| /dashboard/tags | TagsPage | 登录 | 标签颜色、描述和层级 |
| /dashboard/settings | SettingsPage | 登录 | 设置、标签、媒体、备份 |
| /dashboard/vpn | ModulePlaceholderPage | 登录 | 3x-ui/VPN 预留模块 |

## 2. 通用设计约定

### 2.1 API 约定

- 业务 API 前缀统一为 /api/v1/。
- 数据库字段使用 snake_case，JSON 输出使用 camelCase。
- 列表默认使用 DRF 分页；前端同时兼容分页对象和数组响应。
- 列表接口统一支持 `page`、`page_size`，并对 `ordering` 做白名单校验；“近期/最新”不作为独立数据表或固定状态，页面通过状态过滤和时间字段排序得到结果。
- 公开读取与登录写入在权限层分离，不能只依赖前端隐藏按钮。
- 业务对象优先使用稳定 slug、UUID、DOI 或 arXiv ID 做外部定位，不让页面依赖自增 ID 连续性。
- 结构化内容由数据库字段保存，不把任意 HTML/CSS 作为业务数据直接执行。

常见状态码：

| 状态码 | 含义 |
| --- | --- |
| 200 | 查询、更新或动作成功 |
| 201 | 创建成功 |
| 204 | 删除成功且无响应体 |
| 401 | 未登录 |
| 403 | 已登录但无权限 |
| 404 | 资源不存在，或私有资源对匿名用户不可见 |
| 409 | 资源仍被引用、重复或发生冲突 |
| 501 | 动作已进入接口，但对应 connector 尚未实现 |

### 2.2 认证和写请求

当前使用 Django SessionAuthentication：

1. 前端访问 /api/v1/auth/session/，获取当前会话状态和 CSRF cookie；
2. 登录后由 Django 设置 HttpOnly Session cookie；
3. http.ts 从 csrftoken cookie 读取值，并在写请求中发送 X-CSRFToken；
4. 所有请求使用 credentials: include；
5. 前端不保存 JWT，也不保存长期 API token。

这套方式适合当前同源 Docker 部署。若未来增加移动端或第三方客户端，应另行设计 token/OAuth，不直接复用浏览器 Session 契约。

### 2.3 数据库约定

- 所有 schema 变化必须通过 Django migration。
- Docker 使用 PostgreSQL 16，本地未设置 DATABASE_URL 时使用 SQLite。
- 时间以带时区时间保存，展示层按配置转换。
- 单例配置表使用固定主键 1，例如 SiteProfile 和 WorkspaceSettings。
- 业务数据不直接存放在前端 localStorage；localStorage 只作为 API 暂时不可用时的回退和迁移缓存。
- 外部媒体文件保存到 media volume，业务表只保存 MediaAsset 引用和展示元数据。

### 2.4 权限分类

| 分类 | 典型内容 | 匿名用户 |
| --- | --- | --- |
| Public read | 首页、公开论文、公开文档 | 可读 |
| Authenticated read/write | 推荐论文、私有文档、设置、服务器 | 不可读 |
| Public read + authenticated write | 站点内容、论文、文档、媒体 | 可读部分数据 |
| Reserved | VPN/3x-ui 远程控制 | 当前不开放；可通过 Dashboard 外部页面嵌入 |

## 3. 模块一：账户、登录与会话

### 3.1 主要想做什么

提供一个足够安全且适合单人部署的登录入口，保护 Dashboard、私有论文、私有文档、媒体管理、设置和服务器动作。

当前不做注册、找回密码、多用户组织和复杂角色系统。Django Admin 可以使用 staff/superuser 作为运维入口，但业务前端只有当前工作区用户。

### 3.2 当前实现

- 前端页面：src/modules/accounts/pages/LoginPage.vue。
- 前端状态：src/stores/auth.ts。
- 后端 app：backend/apps/accounts。
- 登录方式：email 或 username + password。
- 认证方式：Django Session。
- 路由守卫：/dashboard 及其子路由要求已登录；/login 对已登录用户重定向到 Dashboard。
- 登录后 workspace store 才会加载推荐论文、全部文档、Trash、服务器和设置。

### 3.3 接口

| 方法 | 路径 | 作用 | 权限 |
| --- | --- | --- | --- |
| GET | /api/v1/auth/session/ | 返回当前 authenticated、user，并设置/刷新 CSRF | 公开 |
| POST | /api/v1/auth/login/ | 接收 email 或 username、password，创建 Session | 公开 |
| POST | /api/v1/auth/logout/ | 注销当前 Session | 登录 |

登录成功的核心响应：

    {
      "authenticated": true,
      "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "isStaff": true,
        "displayName": "Syins Yibinory"
      }
    }

### 3.4 数据库设计

依赖 Django 内置表：

| 表 | 作用 |
| --- | --- |
| auth_user | 用户、密码哈希、staff/superuser 标记 |
| auth_group、auth_permission | Django 权限元数据 |
| django_session | Session 登录状态 |
| django_migrations | 已应用 migration |
| django_admin_log | Admin 操作记录 |

业务模块通过 actor 外键关联 auth_user，但不在当前单用户版本中给每条业务记录增加 owner 字段。

### 3.5 后续可扩展

- 密码修改和管理员重置密码；
- 登录失败限流、设备会话管理；
- Workspace、成员和角色；
- API token/OAuth；
- 将所有重要写操作统一写入 AuditEvent。

## 4. 模块二：公开站点内容与 CMS

### 4.1 主要想做什么

让个人主页上的文字、链接、研究方向、研究区块标题、精选研究项目和当前研究问题可以通过 Dashboard 编辑，并立即反映到公开站点。

当前设计是保存即发布，没有独立草稿、审核和预览版本。

### 4.2 当前实现

- 公开页面：HomePage.vue、PublicationsPage.vue、NotesPage.vue。
- 管理页面：src/modules/dashboard/pages/SiteContentPage.vue。
- Pinia 状态：src/stores/siteContent.ts。
- 后端 app：backend/apps/content。
- 聚合接口把 SiteProfile、ResearchProject、CurrentResearchItem 合并成一个页面内容对象。
- PUT/PATCH 使用 transaction.atomic()，站点资料、精选项目和当前研究项要么整体成功，要么整体回滚。

### 4.3 接口

| 方法 | 路径 | 作用 | 权限 |
| --- | --- | --- | --- |
| GET | /api/v1/site/content/ | 返回完整公开站点内容 | 公开 |
| PUT/PATCH | /api/v1/site/content/ | 更新资料和嵌套项目/研究列表 | 登录 |
| GET | /api/v1/research/projects/ | 独立读取精选研究项目 | 公开 |
| GET | /api/v1/research/current/ | 独立读取启用的当前研究项 | 公开 |

聚合响应的主要结构：

    {
      "name": "...",
      "title": "...",
      "researchDirections": "...",
      "selectedProjects": [],
      "currentResearch": [],
      "publicationsHeading": "...",
      "notesHeading": "..."
    }

### 4.4 数据库设计

#### content_siteprofile

单例表，固定 id=1。

| 关键字段 | 作用 |
| --- | --- |
| name、title、location、email | 身份资料 |
| headline、bio | 首屏和关于区域文字 |
| research_directions | 研究方向条 |
| featured_research_intro | 精选研究总引导 |
| current_research_heading、featured_research_heading | 研究区块标题 |
| publications_heading、publications_description | 论文区块标题/说明 |
| notes_heading、notes_description | Notes 区块标题/说明 |
| scholar_url、github_url、cv_url | 外部链接 |
| updated_at | 最后更新时间 |

#### content_researchproject

精选研究项目表，UUID 主键。

| 关键字段 | 作用 |
| --- | --- |
| order、title | 排序和标题 |
| motivation、approach | 动机和方法 |
| status | Active、Ongoing 等展示状态 |
| media_type | image、video、interactive |
| media_asset_id | 可选的 MediaAsset 外键，SET NULL |
| media_url、media_alt、caption | 外链、替代文本、图注 |
| links | JSON 数组，保存项目/论文/代码链接 |

#### content_currentresearchitem

当前研究问题列表，自增主键。

| 关键字段 | 作用 |
| --- | --- |
| order、number | 展示顺序和编号 |
| title、text | 标题和摘要 |
| question、method | 研究问题和方法 |
| status、updated_label | 展示状态和更新时间文案 |
| enabled | 是否公开显示 |

SiteProfile 与两个列表模型当前没有数据库外键，而是由聚合接口统一返回。这种设计方便主页整体保存，但后续如果需要单独复用或权限细分，可以拆成独立管理接口。

### 4.5 当前边界和后续方向

- 当前保存即发布；
- 当前没有内容版本、草稿、审核和回滚；
- mediaAssetId 已预留，媒体文件本身由媒体模块管理；
- 后续可增加 draft/published 状态、预览 token、revision 表和发布记录。

## 5. 模块三：当前研究与精选研究展示

### 5.1 主要想做什么

把“我现在在研究什么”和“哪些研究项目值得展示”分开管理：

- Current Research 更像持续更新的研究问题清单；
- Selected Research 更像可对外展示的项目卡片，包含动机、方法、媒体和外部链接。

### 5.2 前端行为

- 首页读取 currentResearch 和 selectedProjects；
- Dashboard Content 页面可以新增、删除、上下移动和批量保存；
- 当前研究编号由前端按顺序补齐，例如 01、02、03；
- 精选研究媒体通过 MediaEditor 选择 URL、上传资源或交互式文件；
- 空链接允许保存，但前端不应把空链接渲染成无意义跳转。

### 5.3 接口和保存规则

主要写入统一走：

    PUT /api/v1/site/content/

请求中可同时包含：

- SiteProfile 字段；
- selectedProjects 数组；
- currentResearch 数组。

后端按数组顺序重写 order，并删除本次请求中没有保留的项目/研究项。因此该接口属于“集合替换”语义，前端提交前必须保证数组完整。

### 5.4 数据和关系

ResearchProject.media_asset_id -> core_mediaasset.id：

- 允许为空；
- 删除媒体时不会删除项目；
- 媒体被清空后，项目仍可使用 mediaUrl；
- 真实媒体删除前必须先解除项目引用。

CurrentResearchItem 不直接引用 Publication、Document 或 ResearchProject。若未来需要“当前研究关联论文/项目”，应新增显式多对多关系，不建议把 ID 列表塞进现有 text 字段。

### 5.5 后续可扩展

- 研究项目独立 CRUD；
- 项目状态、开始/结束日期；
- 项目关联论文、代码仓库、Note；
- 研究项目 revision 和公开预览；
- 研究方向标签化，而不是只保存一段展示文本。

## 6. 模块四：正式论文与公开 Publications

### 6.1 主要想做什么

管理已经发表的论文、会议/期刊信息、预印本、摘要、BibTeX、代码/项目地址和首页精选状态。公开列表和 Dashboard 管理页面使用同一批数据库记录，避免前后台各存一份。

### 6.2 当前实现

- 公开页面：src/modules/publications/pages/PublicationsPage.vue。
- 管理页面：src/modules/publications/pages/PublicationManagerPage.vue。
- 前端 API：src/modules/publications/api.ts。
- 后端 app：backend/apps/publications。
- 访问按 slug 定位，不按标题直接拼 URL。
- 默认排序：year DESC、id DESC。
- 支持按 title、authors、abstract 搜索，按 type、tag 过滤。

### 6.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/publications/ | 列表，公开 |
| POST | /api/v1/publications/ | 创建，登录 |
| GET | /api/v1/publications/{slug}/ | 详情，公开 |
| PUT/PATCH | /api/v1/publications/{slug}/ | 更新，登录 |
| DELETE | /api/v1/publications/{slug}/ | 删除，登录 |

查询参数：

| 参数 | 作用 |
| --- | --- |
| search | 搜索标题、作者、摘要 |
| type | Conference、Journal、Preprint |
| tag | 按标签名称过滤 |
| page_size | 前端批量读取时调整分页大小 |

### 6.4 数据库设计

表：publications_publication。

| 关键字段 | 作用 |
| --- | --- |
| id | BigAutoField 主键 |
| slug | 唯一 URL 标识，保存时自动生成并处理冲突 |
| title、authors | 标题和作者展示文本 |
| venue、venue_short、year、type | 出版信息 |
| motivation、approach、abstract | 研究说明 |
| paper_url、code_url、project_url | 外部资源 |
| bibtex | BibTeX 原文 |
| featured | 是否出现在首页精选 |
| media_type、media_asset_id、media_url、media_alt、caption | 论文展示媒体 |
| created_at、updated_at | 生命周期 |

关系：

- Publication <-> Tag：多对多，连接表由 Django 自动生成；
- Publication -> MediaAsset：可空外键，删除媒体时 SET NULL；
- Publication 与 Documents 当前没有直接关系；如需要论文阅读笔记，应通过 RecommendedPaper.noteIds 或后续新增关联。

### 6.5 后续可扩展

- DOI、arXiv ID 的规范字段和唯一校验；
- 作者拆分为结构化作者表；
- 论文状态和正式发表日期；
- 公开/私有可见性；
- 论文与研究项目、Notes 的显式关系；
- BibTeX 自动生成和导入。

## 7. 模块五：Documents、Markdown Notes 与 Trash

### 7.1 主要想做什么

用同一个文档实体同时支持：

- 对外公开的研究 Notes、Essay、Guide、Reference；
- 工作台中的私有研究笔记；
- unlisted 链接分享；
- 可恢复的 Trash；
- 与推荐论文的可选关联。

### 7.2 当前实现

- 公开列表：src/modules/documents/pages/NotesPage.vue。
- 公开详情：src/modules/documents/pages/NoteDetailPage.vue。
- 管理页面：src/modules/documents/pages/DocumentsPage.vue。
- Markdown 预览：MarkdownBody.vue。
- 文档状态和保存逻辑：workspace store。
- 后端 app：backend/apps/documents。
- 前端编辑器使用表单草稿，点击 Save 后才提交 API。
- 正文以 Markdown 保存，预览只允许受控渲染，不把任意脚本作为文章内容执行。
- 支持在工作台直接上传 UTF-8 `.md`/`.markdown` 文件；服务端从首个 H1 或文件名推导标题，从首段推导摘要，单文件限制为 10 MB。
- Markdown 使用 GFM 解析，并采用自包含的研究编辑风格：衬线标题、引用块、表格、代码块、任务列表、暗色模式和移动端适配。HTML 经过 DOMPurify 清洗，禁止脚本、表单和 iframe。

### 7.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/docs/ | 文档列表，匿名只返回 public |
| POST | /api/v1/docs/ | 新建文档，登录 |
| POST | /api/v1/docs/upload/ | multipart 上传 `.md`/`.markdown`，登录 |
| GET | /api/v1/docs/{slug}/ | 精确读取；匿名允许 public/unlisted |
| PUT/PATCH | /api/v1/docs/{slug}/ | 更新，登录 |
| DELETE | /api/v1/docs/{slug}/ | 当前为 ModelViewSet 删除入口，使用前应优先 Trash |
| POST | /api/v1/docs/{slug}/trash/ | 软删除到 Trash |
| POST | /api/v1/docs/{slug}/restore/ | 从 Trash 恢复 |

查询参数：

| 参数 | 作用 |
| --- | --- |
| visibility | private、public、unlisted |
| kind | Research Note、Essay、Guide、Reference |
| tag | 标签过滤 |
| search | 搜索标题、摘要、正文 |
| trash=1 | 只读取 Trash |
| trash=all | 登录用户读取包含 Trash 的全部数据 |

### 7.4 可见性规则

- public：出现在匿名列表，可通过 slug 访问；
- unlisted：不出现在匿名列表，但知道精确 slug 的用户可以访问；
- private：匿名列表和匿名详情均不可见，返回 404；
- trashed_at 非空：不参与正常列表，也不出现在公开站点；
- 登录用户默认读取未归档文档，Trash 必须通过显式参数读取。

### 7.5 数据库设计

表：documents_document。

| 关键字段 | 作用 |
| --- | --- |
| id | BigAutoField 主键 |
| slug | 唯一访问标识 |
| title、summary、excerpt | 标题、摘要、列表摘要 |
| kind | 文档类型 |
| content | Markdown 正文 |
| published_at | 可空发布日期，空值展示为 Draft |
| reading_time | 展示用阅读时长 |
| visibility | private、public、unlisted |
| featured | 是否出现在首页 Notes |
| trashed_at | 软删除时间 |
| tags | 与 Tag 多对多 |
| created_at、updated_at | 生命周期 |

Document.save() 会在缺少 excerpt 或 reading_time 时根据正文自动补齐。Trash 不删除正文或标签关系，因此恢复后可以保留论文关联。

### 7.6 后续可扩展

- 文档版本和自动保存；
- Markdown 附件、目录和版本历史；
- 文章目录、引用和反向链接；
- 草稿/审核/发布时间；
- 文档与 Publication、ResearchProject 的关系；
- 真正的批量导入/导出。

## 8. 模块六：Recommended Papers 文献记忆

### 8.1 主要想做什么

管理“推荐给自己阅读”的论文，而不是公开发表成果。重点是记录为什么收藏、读到哪一步、打了什么标签，以及是否关联了研究笔记。

### 8.2 当前实现

- 页面：src/modules/papers/pages/PapersPage.vue。
- 详情编辑：PaperDrawer.vue。
- 后端 app：backend/apps/papers。
- 管理接口需要登录；`/api/v1/public/papers/` 只读取显式开启 `publicly_visible` 的论文。
- 支持 search、status、tag 过滤。
- 支持 DOI、arXiv ID 和标题的重复检查。
- 支持将推荐论文发布到公开的 `/papers` 页面；公开详情会返回关联 Note 的可见性和内容，私有 Note 对匿名用户只返回“需要登录”状态。
- 支持 JSON 和 Markdown 导出。
- noteIds 是论文到 Document 的多对多关系；一篇论文可以关联多篇 Note，一篇 Note 也可以关联多篇论文。

### 8.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/papers/ | 推荐论文列表 |
| POST | /api/v1/papers/ | 新建论文 |
| GET | /api/v1/papers/{id}/ | 论文详情 |
| PUT/PATCH | /api/v1/papers/{id}/ | 更新状态、标签、关联文档等 |
| DELETE | /api/v1/papers/{id}/ | 删除 |
| POST | /api/v1/papers/check/ | DOI、arXiv ID、标题重复检查 |
| GET | /api/v1/papers/export/?format=json | JSON 导出 |
| GET | /api/v1/papers/export/?format=markdown | Markdown 导出 |
| GET | /api/v1/public/papers/ | 公开推荐论文列表，按 `recommended_at DESC, id DESC` 分页 |
| GET | /api/v1/public/papers/{id}/ | 公开推荐论文详情及关联 Note |

### 8.4 数据库设计

表：papers_recommendedpaper。

| 关键字段 | 作用 |
| --- | --- |
| id | BigAutoField 主键 |
| title、authors、venue、year、topic | 论文基本信息 |
| status | recommended、to_read、reading、read、ignored、important |
| recommended_at | 加入推荐列表日期 |
| publicly_visible | 是否显示在公开推荐论文页面 |
| reason、abstract | 推荐理由和摘要 |
| rating | 可空个人评分 |
| doi、arxiv_id | 可选外部唯一标识 |
| paper_url | 论文链接 |
| tags | 与 Tag 多对多 |
| notes | 与 Document 多对多 |
| created_at、updated_at | 生命周期 |

约束：

- doi 不为空时唯一；
- arxiv_id 不为空时唯一；
- 新建和更新先按规范化 DOI、arXiv ID、标题执行重复检查；冲突返回 HTTP 409 和 `code=duplicate_paper`；
- 空 DOI 或空 arXiv ID 允许重复；
- 删除 Note 不会自动删除 Paper；
- Trash 中的 Note 仍保留关系，便于恢复。

### 8.5 后续可扩展

- 从 DOI/arXiv 自动抓取元数据；
- 阅读进度、评分维度、引用次数；
- 与 Publication 的去重提示；
- 论文集合、阅读计划和提醒；
- 全文 PDF 文件与媒体库关联；
- 后台任务队列用于导入和 metadata enrichment。

## 9. 模块七：媒体库与交互式内容

### 9.1 主要想做什么

统一管理研究项目、论文和未来模块使用的上传资源，避免业务表直接保存文件路径。当前支持图片、视频和 interactive 三类内容。

### 9.2 当前实现

- 前端公共组件：MediaEditor.vue、ResearchMedia.vue。
- 媒体 API 封装：src/services/mediaLibrary.ts。
- 设置页可以列出、刷新和删除未被引用的资源。
- 后端模型：core.MediaAsset。
- 上传文件保存在 Django media volume。
- 业务模型只保存 mediaAssetId、mediaType 和展示元数据。

### 9.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/media/ | 媒体列表，登录管理 |
| POST | /api/v1/media/ | multipart 上传，字段 upload |
| GET | /api/v1/media/{id}/ | 媒体元数据和 URL |
| PATCH/PUT | /api/v1/media/{id}/ | 更新媒体元数据 |
| DELETE | /api/v1/media/{id}/ | 删除未被引用的媒体 |

删除约束：

- ResearchProject 或 Publication 仍引用资源时，返回冲突；
- 先清空业务记录中的 mediaAssetId，再删除文件；
- 删除应同时处理数据库记录和 storage 文件；
- 删除前建议先导出备份。

### 9.4 数据库设计

表：core_mediaasset。

| 关键字段 | 作用 |
| --- | --- |
| id | UUID 主键 |
| original_name | 原始文件名 |
| kind | image、video、interactive |
| content_type | MIME 类型 |
| size | 文件大小 |
| checksum | SHA-256 |
| source_file | assets/UUID/filename 下的 FileField |
| created_at、updated_at | 生命周期 |

上限和安全边界：

- 最大上传大小 25 MB；
- 图片、mp4、webm、html、htm、vue、zip 在白名单内；
- ZIP 解压后限制 40 MB、最多 300 个文件；
- 拒绝目录穿越路径；
- 不执行 npm install、构建脚本或上传包内的网络请求。

### 9.5 Interactive 内容契约

支持：

- 单个 HTML；
- Vue SFC；
- ZIP 包。

ZIP 需要恰好包含一个 index.html，或者在没有 HTML 入口时恰好包含一个 App.vue。Vue 支持普通 script/setup、TypeScript、本地 Vue 组件、JS/TS/JSON、普通 CSS 和导入图片；其他 npm 依赖需要在上传前打包成自包含内容。

运行时：

- 已准备好的 HTML/Vue 内容在浏览器 sandbox iframe 中显示；
- 不允许父页面访问、表单提交、顶层导航、worker、import map、CSS @import、srcset 和网络请求；
- 编译器和 WASM 只在导入 interactive 内容时加载；
- 替换失败时保留原来的视觉内容。

### 9.6 后续可扩展

- 视频缩略图和媒体处理任务；
- 媒体版本、替换历史和引用图；
- 对图片增加 width/height/alt 校验；
- 对 interactive 内容增加预览截图；
- 外部对象存储和 CDN；
- S3/MinIO 兼容存储。

## 10. 模块八：标签与跨模块分类

### 10.1 主要想做什么

让 Publications、Documents 和 Recommended Papers 共用一套标签，支持搜索、筛选、重命名、合并和全局删除，避免每个模块维护孤立的标签字符串。

### 10.2 当前实现

- 前端公共组件：TagEditor.vue。
- 设置页面提供标签重命名、合并和移除。
- Tags 页面可以编辑颜色、描述和父标签；父标签关系禁止自环和循环。
- 后端 TagNamesField 负责字符串数组与多对多关系之间的转换。
- 写入时会去除首尾空格、压缩空字符串，并按大小写不敏感规则去重。

### 10.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/tags/ | 获取标签列表 |
| POST | /api/v1/tags/ | 创建标签 |
| PATCH/PUT | /api/v1/tags/{id}/ | 更新名称、颜色、描述和父标签 |
| DELETE | /api/v1/tags/{id}/ | 删除标签并清理多对多连接 |
| POST | /api/v1/tags/rename/ | 将 from 重命名/合并到 to |

请求示例：

    {
      "from": "domain-generalization",
      "to": "Domain Generalization"
    }

to 为空时表示从所有记录移除该标签。

### 10.4 数据库设计

表：core_tag。

| 字段 | 作用 |
| --- | --- |
| id | BigAutoField 主键 |
| name | 唯一展示名称 |
| slug | 唯一 slug |
| color | 六位十六进制颜色，例如 `#5C7891` |
| description | 标签定义或使用说明 |
| parent_id | 可空父标签，构成树状层级 |
| created_at | 创建时间 |
| updated_at | 最近一次元数据更新时间 |

连接表：

- publications_publication_tags；
- documents_document_tags；
- papers_recommendedpaper_tags。

重命名/合并必须在事务中处理：

1. 找到源标签和目标标签；
2. 将三类业务记录的关系迁移到目标标签；
3. 删除重复连接；
4. 删除源标签；
5. 返回统一结果。

### 10.5 后续可扩展

- 标签统计接口；
- 预设标签和自动补全；
- 标签别名和迁移历史；
- PostgreSQL trigram/全文索引。

## 11. 模块九：服务器清单与基础设施状态

### 11.1 主要想做什么

记录研究环境中的机器、资源、GPU、容器和在线状态。部署主机可以标记为 primary，工作台通过 SSH 连接读取受控的主机指标，并将每次轮询保存为历史样本。

当前重点是“清单和状态展示”，不是任意远程命令执行。

### 11.2 当前实现

- 页面：src/modules/servers/pages/ServersPage.vue。
- 后端 app：backend/apps/servers。
- 所有接口需要登录。
- provider 支持 mock、ssh、xui；mock 用于演示，ssh 支持主机指纹确认、密码加密存储和 Linux 资源读取，xui 作为外部 Dashboard 嵌入场景保留。
- 页面支持输入主机 IP/域名、端口、用户名、密码和连接方式，设置 10/30/60 秒或关闭自动刷新。
- SSH 只执行固定的指标采集脚本，不接受页面传入的任意 shell 命令。
- 每次成功采集都会写入 ServerMetricSample，页面可以读取最近 24 小时的 CPU、内存和磁盘历史曲线。
- 动作必须来自白名单，未实现的真实动作返回 501。
- 每次动作都会写 ServerActionLog。

### 11.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/servers/ | 服务器列表 |
| POST | /api/v1/servers/ | 新建服务器 |
| GET/PATCH/PUT/DELETE | /api/v1/servers/{id}/ | 服务器 CRUD |
| GET | /api/v1/servers/{id}/status/ | 获取当前状态快照 |
| POST | /api/v1/servers/{id}/actions/ | 执行一个白名单动作 |
| POST | /api/v1/servers/{id}/test-connection/ | 测试 SSH/Mock 连接 |
| POST | /api/v1/servers/{id}/trust-host/ | 显式信任首次发现的 SSH 主机指纹 |
| GET | /api/v1/servers/{id}/metrics/?hours=24&limit=500 | 获取历史资源样本 |
| POST | /api/v1/servers/refresh/ | 刷新所有 enabled 服务器 |

当前允许的动作：

- refresh_status；
- start_container；
- stop_container；
- restart_container；
- fetch_logs。

mock provider 当前只接受 refresh_status 类状态更新；ssh 只读取指标，容器和日志动作仍未开放。

### 11.4 数据库设计

表：servers_server。

| 关键字段 | 作用 |
| --- | --- |
| id、name | 标识和显示名称 |
| hostname、ip、location、os | 机器地址和环境 |
| port、username | SSH 连接参数；端口范围 1–65535，密码不以明文返回 |
| description | 备注 |
| status | online、offline、warning |
| provider | mock、ssh、xui |
| is_primary | 是否为部署主机；同一时间仅保留一个 primary |
| last_seen、uptime | 在线时间信息 |
| capabilities | JSON 数组，如 SSH、Docker、NVIDIA_GPU |
| cpu | CPU 展示值 |
| memory、disk | JSON 资源快照 |
| gpus | JSON GPU 快照 |
| containers | 容器数量 |
| connector_config | 旧版 connector 兼容字段；当前不通过 serializer 返回，也不存放敏感凭据 |
| encrypted_password、host_key_fingerprint | 加密后的 SSH 密码和已确认主机指纹 |
| last_error | 最近一次连接/采集错误 |
| enabled | 是否参与批量刷新 |
| created_at、updated_at | 生命周期 |

表：core_serveractionlog。

| 字段 | 作用 |
| --- | --- |
| server_id | 逻辑引用，服务器删除后仍保留历史 |
| action | 请求动作 |
| accepted | 是否接受 |
| message | 结果消息 |
| actor_id | 操作者 |
| created_at | 动作时间 |

表：servers_servermetricsample。

| 关键字段 | 作用 |
| --- | --- |
| server_id、recorded_at | 样本归属主机和采集时间 |
| cpu_percent、load_average | CPU 使用率和系统负载 |
| memory_used_bytes、memory_total_bytes | 内存使用量/总量 |
| disk_used_bytes、disk_total_bytes | 根分区使用量/总量 |
| gpu_utilization_percent、gpu_memory_*、gpu_count | GPU 资源概览 |
| containers | Docker 运行容器数量 |
| payload | 受控的 GPU 明细和 connector 来源 |

### 11.5 安全边界

- 不提供任意 shell、command 或脚本参数接口；
- connector 只能收到固定动作；
- SSH 密码使用由 `DJANGO_SECRET_KEY` 派生的 Fernet 密钥加密，serializer 只接受 write-only password；生产环境必须使用高熵且长期稳定的 `DJANGO_SECRET_KEY`。
- 首次 SSH 握手只展示指纹，不自动信任；主机指纹变化会阻断连接，必须显式重新信任。
- SSH connector 有连接和命令超时，并且不接受任意命令；容器/日志写操作仍未开放。
- 远程动作默认应该是显式确认，而不是页面加载时自动触发。

## 12. 模块十：Dashboard 外部页面嵌入

### 12.1 主要想做什么

让用户在工作台中配置 3x-ui 或其他内部工具的 URL，生成一个独立的 Dashboard 页面。服务端只保存 URL 和展示元数据，不主动抓取或执行外部页面；浏览器使用受限 iframe 加载，必要时提供新标签页回退。

### 12.2 接口和数据

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/integrations/pages/ | 登录用户的嵌入页面列表，支持分页和排序 |
| POST | /api/v1/integrations/pages/ | 创建页面 |
| GET | /api/v1/integrations/pages/{slug}/ | 读取页面配置 |
| PATCH/PUT | /api/v1/integrations/pages/{slug}/ | 更新页面 |
| DELETE | /api/v1/integrations/pages/{slug}/ | 删除页面 |

数据表：integrations_embeddedpage，包含 `slug`、`title`、`description`、`url`、`icon`、`order`、`enabled`、`open_in_new_tab` 和生命周期时间。URL 只允许 `http`/`https`，后端不做代理请求，因此不会把外部服务凭据带入 Django。

### 12.3 安全和兼容边界

- iframe 设置 sandbox、`referrerpolicy=no-referrer`，但外部站点是否允许被嵌入仍由其 X-Frame-Options/CSP 决定；
- 不在站点数据库保存 3x-ui 密码，不尝试绕过第三方登录或安全策略；
- 如果外部页面禁止 iframe，用户可以直接打开新标签页；
- 后续若要做真正的 3x-ui API 集成，应新增独立 connector、凭据轮换、权限范围和审计设计。

## 13. 模块十一：工作台设置、媒体清理与备份

### 13.1 主要想做什么

提供不属于某一业务实体的工作台级配置，并保证用户可以把数据库记录和媒体文件一起导出。

### 13.2 当前实现

- 页面：src/modules/dashboard/pages/SettingsPage.vue。
- 设置包括新建文档默认可见性、新建文档默认类型、分页大小和工作台标题。
- 设置页提供共享标签操作和媒体清理。
- 页面通过浏览器下载 ZIP 备份。
- scripts/backup.sh 负责 Docker 主机上的 PostgreSQL dump 和 media volume 快照。

### 13.3 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | /api/v1/settings/ | 获取工作台设置 |
| PATCH/PUT | /api/v1/settings/ | 更新设置 |
| GET | /api/v1/settings/backup/ | 生成完整 ZIP 备份 |

### 13.4 数据库设计

表：core_workspacesettings，单例 id=1。

| 字段 | 作用 |
| --- | --- |
| default_note_visibility | 新建文档默认 private/public/unlisted |
| default_note_kind | 新建文档默认类型 |
| page_size | 工作台分页大小 |
| site_title | 工作台标题 |
| updated_at | 更新时间 |

### 13.5 备份内容

API ZIP 包包含：

- research-os.json；
- SiteProfile；
- CurrentResearchItem；
- ResearchProject；
- Publication；
- Document；
- RecommendedPaper；
- Server；
- ServerMetricSample（服务器资源历史）；
- Tag（含颜色、描述和父标签）；
- EmbeddedPage（Dashboard 外部页面配置）；
- WorkspaceSettings；
- media/UUID/filename 下的原始媒体文件。

宿主机备份脚本另外生成：

- PostgreSQL pg_dump；
- media volume tar.gz。

数据库和媒体必须成对保存。当前提供导出，不提供自动导入 API；恢复应在临时环境校验后再切换到生产环境。

### 13.6 后续可扩展

- 备份保留周期和校验和；
- 自动定时备份；
- 加密备份；
- 导入前预览与冲突处理；
- 从备份恢复单个模块而不是覆盖整个工作区；
- 对备份文件增加版本迁移器。

## 14. 模块十二：Dashboard 总览

### 14.1 主要想做什么

把多个模块的关键状态集中到一个入口，让用户打开工作台后能快速看到：

- 当前研究问题；
- 推荐论文数量和待阅读数量；
- 在线服务器和 GPU 数量；
- 文档总量和私有文档数量；
- 按推荐日期、更新时间排序的论文、文档和服务器状态。

### 14.2 当前实现

- 页面：src/modules/dashboard/pages/OverviewPage.vue。
- 当前没有单独的 DashboardSummary 数据表。
- Overview 直接读取 workspace store 和 site-content store 的已加载数据。
- 跳转到具体模块进行编辑，不在总览中复制编辑逻辑。

### 14.3 数据来源

| 总览指标 | 来源 |
| --- | --- |
| 当前研究 | site content API |
| 推荐论文和待阅读数 | papers API |
| 服务器在线数、GPU 数 | servers API |
| 文档总量、私有数 | docs API |
| 排序后的记录 | 前端按 updatedAt/recommendedAt 排序 |

### 14.4 后续可扩展

当前规模不需要额外聚合接口。数据量明显扩大或需要复杂统计后，可以增加：

- GET /api/v1/dashboard/summary/；
- 后端聚合查询；
- 按时间范围的研究活动统计；
- 最近编辑、审计事件和系统告警；
- 缓存和权限过滤。

## 15. 模块十三：前端 API、状态和离线回退

### 15.1 主要想做什么

把页面与具体 HTTP 细节隔离，并在后端暂时不可用时保留可用的本地编辑体验。

### 15.2 当前实现

- HTTP 封装：src/services/http.ts；
- 通用解析：src/services/api.ts；
- 认证状态：src/stores/auth.ts；
- 站点内容：src/stores/siteContent.ts；
- 工作台数据：src/stores/workspace.ts；
- 媒体 API：src/services/mediaLibrary.ts。

http.ts 负责：

- 组装 VITE_API_BASE_URL 或 /api/v1；
- 自动带 credentials；
- 自动添加 CSRF header；
- JSON、FormData、Blob 和文本响应解析；
- 将非 2xx 响应包装成带 status 和 data 的错误。

### 15.3 Hydrate 顺序

1. auth store 查询 session；
2. site content store 读取公开站点内容；
3. workspace store 读取公开 publications 和 public docs；
4. 登录状态有效时，再读取 papers、全部 docs、Trash、servers、settings；
5. API 失败时保留 localStorage 里的旧数据，并标记 offline。

### 15.4 回退策略

当前 localStorage 仍保存：

- research-os:site-content；
- research-os:papers；
- research-os:publications；
- research-os:documents；
- research-os:preferences。

回退数据的作用是开发和临时断网，不是正式数据库。恢复网络后，保存操作应优先以 API 返回值覆盖本地临时记录。

### 15.5 当前风险和后续建议

- 浏览器缓存可能落后于数据库；
- 多标签页同时编辑时没有冲突检测；
- 失败保存会回退到本地，用户需要看到明确的离线提示；
- 后续可以加入 revision、updatedAt 比较、乐观锁和“重新加载远程版本”。

## 16. 模块十四：部署、迁移和升级

### 16.1 主要想做什么

保证模块代码和数据库能够被替换升级，同时不丢失 PostgreSQL 数据和媒体 volume。

### 16.2 当前启动顺序

docker/entrypoint.sh 执行：

1. python manage.py migrate --noinput；
2. python manage.py collectstatic --noinput；
3. SEED_DEMO=true 时执行幂等 seed_demo；
4. 使用 Gunicorn 启动 Django。

### 16.3 升级原则

升级顺序：

    备份数据库和媒体
        -> 拉取代码
        -> docker compose build --pull
        -> docker compose up -d
        -> 自动执行增量 migration
        -> 检查 API、前端和日志

数据库 migration 必须兼容现有数据。字段重命名或删除建议采用：

1. 新增字段；
2. 数据迁移；
3. 应用切换读取/写入；
4. 经过一个版本后再删除旧字段。

### 16.4 验收命令

    cd backend
    python manage.py check
    python manage.py makemigrations --check --dry-run
    python manage.py test

    cd ..
    docker compose ps
    docker compose logs --tail=100 backend
    curl -I http://localhost:8080/
    curl http://localhost:8080/api/v1/site/content/

## 17. 当前模块状态总表

| 模块 | 前端状态 | 后端状态 | 数据库状态 | 当前限制 |
| --- | --- | --- | --- | --- |
| 账户与会话 | 已实现 | 已实现 | 使用 Django 内置表 | 无注册和密码找回 |
| 公开站点内容 | 已实现 | 已实现 | SiteProfile 单例 | 保存即发布 |
| 当前研究 | 已实现 | 已实现 | CurrentResearchItem | 独立管理接口较少 |
| 精选研究 | 已实现 | 已实现 | ResearchProject + MediaAsset | 关系扩展待定 |
| Publications | 已实现 | 已实现 | Publication、Tag、MediaAsset | 无 DOI 标准化 |
| Documents/Notes | 已实现 | 已实现 | Document、Tag | 无版本和审核；支持 Markdown 上传 |
| Recommended Papers | 已实现 | 已实现 | RecommendedPaper、Tag、Document | 无自动元数据抓取；公开发布需显式开启 |
| Media Library | 已实现 | 已实现 | MediaAsset | 本地/Docker volume，暂无对象存储 |
| Tags | 已实现 | 已实现 | Tag + 三类连接表 | 统计和别名待扩展 |
| Servers | 已实现 | mock/SSH 读取已实现 | Server、ServerMetricSample、ServerActionLog | 容器/日志远程写操作未开放 |
| Dashboard 外部页面 | 已实现 | 已实现 | EmbeddedPage | 受第三方 iframe 策略限制 |
| Settings/Backup | 已实现 | 已实现 | WorkspaceSettings | 只有导出，没有导入 |
| Dashboard Overview | 已实现 | 复用现有 API | 无独立表 | 无后端聚合统计 |
| VPN/3x-ui | 占位页面 | 未实现 | 未建表 | 需要单独确认需求 |

## 18. 后续模块修改的讨论格式

你可以按下面格式逐模块告诉我修改要求，我会据此同步更新代码、数据库、接口、测试和文档：

    模块：
    当前问题：
    希望达到的效果：
    页面/交互变化：
    新增或删除字段：
    接口变化：
    权限变化：
    是否需要保留旧数据：
    是否需要兼容旧接口：
    验收标准：

如果某次修改会改变数据库语义，我会优先给出 migration 方案和兼容策略，再实施代码调整。若只是页面文案、排序、展示字段或前端交互变化，则尽量不改变数据库和公开 API。

## 19. 相关文档

- BACKEND_DATABASE_DESIGN.md：后端分层、完整字段、关系、权限、安全、备份和升级原则；
- ARCHITECTURE.md：运行边界、服务边界和部署架构；
- CONTENT_DESIGN.md：页面内容、媒体和 interactive 内容约定；
- README.zh-CN.md：安装、启动、测试和 Docker 使用说明。
