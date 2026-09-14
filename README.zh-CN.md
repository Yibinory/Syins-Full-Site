# Syins Research OS

[English](README.md)

一个可自行部署的个人研究主页与私有研究工作台。对外展示研究成果，在同一个 Dashboard 中管理论文、笔记、工具和服务器，内容保存在你自己的部署环境中。

## 功能

- **个人主页**：中英文资料、共用人像、研究项目、发表论文和公开笔记。
- **研究工作台**：推荐论文、阅读状态、自定义标签，以及一篇论文关联多篇笔记。
- **内容编辑**：Markdown 上传、笔记可见性管理，支持图片、视频、HTML、Vue 组件和 ZIP 项目展示包。
- **工具与服务器**：嵌入外部工具，按需公开工具入口，管理服务器连接和资源监控。
- **部署管理**：引导安装、空闲端口检查、后台修改端口及失败回滚、备份工具。

技术栈：Vue 3、TypeScript、Django REST Framework、PostgreSQL。

## 安装

需要 Git、**Python 3.9+**、已启动的 Docker，以及 **Docker Compose 2.24.4+**。轻负载运行可按约 **2 GB 内存**规划；在同一台机器构建时建议 **4 GB**，预留更多余量。

**Linux / macOS**（macOS 请先启动 Docker Desktop）：

```sh
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
sh scripts/install.sh
```

**Windows PowerShell**（Docker Desktop 使用 Linux 容器模式）：

```powershell
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

已提供 Windows 脚本，但尚未在原生 Windows 主机上完成验证。

向导会询问站点名称、默认语言、管理员账户、密码及可选的公开主机名，自动生成数据库密码和应用密钥并保存在 `.env`。**运行向导前不要复制 `.env.example`**：已有 `.env` 时会保留配置并跳过初始化提问。

安装会在本机构建应用，从 **8080** 开始寻找可用网站端口。完成后打开终端输出的地址，在 `/login` 登录。新安装包含通用首页与部署主机条目，论文、笔记和研究项目等业务数据为空。

需要指定起始端口时：

```sh
sh scripts/install.sh --port 8090
```

如需公网访问，请另行配置域名、防火墙和 HTTPS 反向代理。允许主机名及 CSRF 配置见[部署指南](docs/deployment.zh-CN.md)。

## 开始使用

| Dashboard 页面 | 用途 |
| --- | --- |
| 站点内容 | 修改个人资料，上传首页人像，编辑研究项目和各页面介绍；点击保存更改后发布。 |
| 发表论文 | 添加论文、年份、链接、配图和 BibTeX。可勾选多篇在首页展示，公开论文列表按年份从新到旧排列。 |
| 推荐论文 | 管理阅读状态和标签，每篇可关联零到多篇笔记。 |
| 文档 | 编写或上传 Markdown，设置可见性，从回收站恢复内容。 |
| 外部页面 | 添加工具网址，按需公开到工具页面。部分网站禁止嵌入，可使用浏览器打开链接。 |
| 服务器 | 配置 SSH 主机，核对并信任指纹后查看监控信息。 |
| 设置 | 管理部署端口、文件和备份。 |

**中 / EN** 按钮切换界面语言。在站点内容中选择编辑语言，分别填写中文和英文。某种语言未填写时显示另一种，都未填写则显示 `-`；人像、邮箱和链接共用。

## 更新与备份

更新前先备份。Linux / macOS：

```sh
sh scripts/backup.sh
git pull
sh scripts/update.sh
```

备份存放在 `data/backups/`，建议另存一份到其他设备。Windows 可在 Dashboard 下载备份，再执行 `git pull` 和 `powershell -ExecutionPolicy Bypass -File scripts/update.ps1`。

升级保留数据库和媒体数据卷。**需要保留数据时不要运行 `docker compose down -v`。** 请单独妥善备份 `.env`，不要公开其中的密码和密钥。

## 常用操作

- **修改端口**：进入 Dashboard → 设置 → 部署端口。应用时服务会短暂重启，失败自动回滚。主机重启后运行 `python3 scripts/deployment_manager.py start`，重新启用端口管理；Windows 使用 `py -3` 替换 `python3`。
- **连接数据库客户端**：在设置中启用仅本机访问的数据库端口，主机填 `127.0.0.1`，端口填配置值。数据库名、用户名和密码分别查看 `.env` 的 `POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`；远程访问使用 SSH 隧道。
- **排查启动问题**：执行 `docker compose ps` 和 `docker compose logs --tail=100 backend`。
- **监控物理部署主机**：Linux/macOS 执行 `sh scripts/monitor-host.sh start`；未启用时界面会区分显示容器或运行环境指标。

## 更多资料

- [部署、恢复与本地开发](docs/deployment.zh-CN.md)
- [架构说明](ARCHITECTURE.md) · [后端与数据库](BACKEND_DATABASE_DESIGN.md)
- API 交互文档：运行站点的 `/api/docs/`
