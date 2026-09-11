# Syins Research OS 架构说明

## 运行边界

前端是 Vue 3 + TypeScript SPA，后端是 Django 4.2 + Django REST Framework。生产环境由 Nginx 提供前端静态文件，并把 `/api/`、`/admin/` 和 `/static/` 反向代理到 Django；上传的 `/media/` 由共享 volume 提供。浏览器和 API 使用同源 Session + CSRF，不在前端保存长期 API token。

## 数据库边界

每个 Django app 负责一类稳定的数据，不把所有内容塞进一个 JSON 文档：

- `content`：单例 `SiteProfile`、排序后的 `CurrentResearchItem`、`ResearchProject`。
- `publications`：正式发表成果、链接、BibTeX、精选标记、标签和媒体引用。
- `documents`：Markdown 文档、公开性、精选标记、标签和可恢复 Trash。
- `papers`：推荐论文、阅读状态、DOI/arXiv 去重、标签，以及与文档的多对多关系。
- `servers`：机器清单、资源快照、能力标签、连接器配置和启用状态。
- `core`：`MediaAsset`、`Tag`、`WorkspaceSettings`、审计事件和服务器动作日志。

记录之间通过外键或多对多关系关联；媒体文件不直接嵌入业务表，只保存 `MediaAsset` 引用。所有 schema 变化必须通过 Django migration 提交。

## API 约定

API 固定在 `/api/v1/` 下，并返回前端使用的 camelCase 字段。公开读取和私有编辑在权限层明确分开：公开站点只读取公开内容；推荐论文、设置、媒体管理、服务器清单和所有写操作需要登录。`unlisted` 文档可以通过精确 slug 访问，但不会出现在公开列表中； Trash 通过显式 `?trash=1` 读取。

服务器动作不是任意命令接口，而是固定动作集合。当前 `mock` connector 只更新快照；SSH、Docker Remote 和 3x-ui 应作为独立 provider 接入，并在有凭据、权限和测试后再开放远程写操作。

## 媒体与交互内容

上传大小上限为 25 MB，按扩展名归类为图片、视频或 interactive。原始文件保存在 Django media volume；interactive 内容只在浏览器 sandbox iframe 中编译和运行，不执行 npm 安装、构建脚本或网络请求。删除前检查业务引用，避免留下悬空媒体。

## 发布、备份与升级

1. `docker compose up -d --build` 启动时先执行 `migrate`，再收集 Django static，最后启动 Gunicorn。
2. `seed_demo` 只补齐缺失的首个管理员和示例记录，不覆盖已经编辑过的内容。
3. 数据库和媒体分别使用持久化 volume；`scripts/backup.sh` 导出 PostgreSQL dump 和媒体快照。
4. 升级流程是备份、拉取代码、执行 `scripts/update.sh`。迁移是增量的，应用容器可替换，数据 volume 不替换。
5. 当前保存即发布，没有独立草稿/审核版本；如果以后需要，可在 `content` 和各业务模型上增加 revision/status，而不改变公开 API 的基础实体。

本地开发默认使用 SQLite，生产 Docker 使用 PostgreSQL；两者都通过同一套 migration 和测试运行。
