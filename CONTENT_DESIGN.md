# 页面内容与展示约定

基本原则：常规内容通过结构化字段编辑；展示组件负责字体、留白、响应式和深色模式。不要让每条内容携带任意 HTML 或独立 CSS。

| 页面 / 模块 | 配置内容 | 展示方式 | 当前边界 |
| --- | --- | --- | --- |
| 首页身份介绍 | 姓名、身份、地点、简介、外部链接；后续增加头像和主图上传 | 固定首屏布局 | 文本和链接已接入 Site content；人像仍为固定素材 |
| 研究方向条 | 英文研究方向，以 × 分隔 | 桌面横排、窄屏纵排 | 已接入 Site content |
| Current research | 标题、摘要、状态、研究问题、方法、更新时间 | 列表与详情 | 已由 Django 内容接口管理 |
| Selected research | 标题、动机一句、做法一句、状态、两个链接、素材类型、素材地址、替代文本、图注、顺序 | 图文交错；完整显示图片；视频由访客控制播放 | Django 已持久化配置；媒体上传使用独立 MediaAsset |
| Publications | 标题、作者、年份、会议/期刊、摘要、缩略图、论文/代码链接、BibTeX、精选标记 | 年份分组与类型筛选；首页引用精选记录 | 页面介绍由 Site content 管理；条目由 Publications API 管理 |
| Notes | 标题、摘要、Markdown 正文、内容类型、标签、可见性、发布时间、精选标记 | 列表索引与统一阅读页；首页引用精选记录 | Documents API 管理；公开读取与私有编辑权限分开 |
| Dashboard overview | 从论文、Current Research、文档、服务器模块聚合真实数据 | 统一栅格和常用操作 | 研究进度不单独虚构；当前显示状态和更新时间 |
| Recommended papers | 论文元数据、推荐理由、阅读状态、标签、笔记 | 高密度列表与抽屉 | Django 持久化；DOI/arXiv 去重约束与 JSON/Markdown 导出已提供 |
| Servers / VPN | 服务器名称、分组、能力、连接信息、集成设置 | 按能力显示状态与操作 | Servers 已接入后端快照；VPN 保留 3x-ui 集成占位 |
| Settings | 写作默认值、共享标签、媒体库、备份 | 分组表单 | 已接入 Django workspace；公共内容继续由 Site content 管理 |

## 科研配图选型

- 方法、流程和概念关系：SVG，或导出的 PNG/WebP。作为图片加载，统一适配容器。
- MRI、分割、生成结果：真实结果拼图，保留图例和标注；避免裁切或滤镜改变科学含义。
- 时间序列、生成过程：MP4/WebM 视频，提供控件，不自动播放；图注补充摘要。
- 对照拖动、多条件切换：后续有真实数据和明确交互需求时新增受控 Vue 展示组件，以组件类型和参数配置，不粘贴任意 HTML。
- 示例必须标明概念图或占位素材。空链接显示待提供，不跳回页面顶部。

当前 Site content 通过 Django API 保存到数据库，前端仍保留 localStorage 作为后端暂时不可用时的迁移/回退缓存。当前没有独立草稿和正式发布工作流；保存即发布，后续可以在同一模型上增加草稿状态、审核和预览版本。

## Dashboard update — current implementation

The Django backend is now the normal source of truth. The browser cache is only a fallback for local development or temporary API outages.

- Publications now has a separate manager for authored papers: metadata, motivation, approach, abstract, tags, media, links, BibTeX and homepage selection. Public listings and homepage selections share these records.
- Recommended papers preserve their detail information and add editable tags, reading status, paper URL and zero-to-many note links. A note can be linked from multiple papers. Unlinking does not delete it, and Trash retains links for restoration.
- Documents now supports create/edit/save, Markdown with sanitized preview, unique slugs, public/private/unlisted visibility, public reading pages, homepage selection and recoverable Trash. Homepage note content now comes from Documents.
- Settings now provides new-note defaults, global tag rename/merge, media cleanup and deployment backup scripts. Account security is handled by Django sessions and CSRF.
- Records are stored in Django/PostgreSQL (or SQLite for local development). Uploaded media is stored under the configured media volume. Publication and Document edits use form drafts and explicit saves; Site content and recommended-paper changes are sent to the API immediately.

### Interactive package contract

Accept `.html`, `.vue` and `.zip`. A ZIP needs exactly one `index.html`, or, if there is no HTML entry, exactly one `App.vue`. Nested wrapper directories are supported. Maximum upload size: 25 MB; archive limits: 40 MB unpacked and 300 entries. Traversal paths are rejected. The original upload is stored by Django; the browser performs the same safe compilation before displaying it.

Vue supports ordinary/setup scripts, TypeScript, local Vue components, JS/TS/JSON, plain CSS and imported images. The Vue runtime is bundled. Other npm dependencies and CSS preprocessors must be built into a self-contained HTML package first. The importer never executes package installation or archive build scripts.

HTML supports packaged scripts, styles, images and videos. Runtime fetch/network requests, workers, import maps, CSS @import and srcset are outside this version's contract. The iframe allows scripts but has an opaque origin; no parent-page access, forms, top navigation or network connections are granted. The compiler and WASM load only when importing interactive content, not when displaying already prepared media.

Replacement failure keeps the previous visual. Clearing removes the record reference; Settings only permits deleting unused files, with confirmation. `scripts/backup.sh` exports a PostgreSQL dump and a compressed media-volume snapshot; restore remains an operator command rather than a public UI action.

Examples: `public/examples/interactive-demo.html`, `ResearchDemo.vue`, `vue-demo.zip`.

Implementation reference: [Vue SFC compilation](https://vuejs.org/guide/scaling-up/sfc).
