# Syins Research OS

[中文](README.zh-CN.md)

A self-hosted research portfolio with a private workspace. Present your work publicly and manage your papers, notes, resources, and servers from one Dashboard.

## Features

- **Personal website:** bilingual profile, shared portrait, research projects, publications, and public notes.
- **Research workspace:** recommended papers with reading status, custom tags, and links to multiple notes.
- **Content editing:** Markdown uploads, public/private notes, and project visuals including images, videos, HTML, Vue components, and ZIP packages.
- **Tools and infrastructure:** optional public external pages, embedded tools, server inventory, and resource monitoring.
- **Deployment management:** guided setup, port availability checks, Dashboard port changes with rollback, and backup tools.

Built with Vue 3, TypeScript, Django REST Framework, and PostgreSQL. Your content stays in your deployment.

## Install

Requires Git, Python **3.9+**, and running Docker with Compose **2.24.4+**. Allow around **2 GB RAM** for light use; **4 GB** is more comfortable when building on the same machine.

**Linux / macOS** (start Docker Desktop first on macOS):

```sh
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
sh scripts/install.sh
```

**Windows PowerShell** (Docker Desktop in Linux container mode):

```powershell
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

Windows scripts are provided but have not yet been validated on a native Windows host.

The wizard asks for your site name, default language, administrator account, password, and optional public hostname. It generates application/database secrets and saves them in `.env`. **Do not copy `.env.example` before running the wizard:** an existing `.env` skips initial setup questions.

Installation builds the application locally and chooses an available website port, starting at **8080**. Open the address printed when installation finishes, then sign in at `/login`. A new installation includes a generic homepage and deployment-host entry; papers, notes, and projects start empty.

To request a different port:

```sh
sh scripts/install.sh --port 8090
```

For access over the internet, configure your domain, firewall, and HTTPS reverse proxy separately. See the [deployment guide](docs/deployment.md) for host and CSRF settings.

## Make it yours

| Dashboard page | What to do |
| --- | --- |
| Site content | Edit profile text, upload your homepage portrait, and configure research projects and page introductions. Save changes to publish. |
| Publications | Add authored papers, year, links, media, and BibTeX. Select any number to feature on the homepage. Public listings show newest years first. |
| Recommended papers | Track reading status and tags; link zero or more notes to each paper. |
| Documents | Write or upload Markdown, manage visibility, and restore items from Trash. |
| Dashboard pages | Add external tools and optionally make them visible on the public Tools page. Some websites prevent embedding; use the browser link instead. |
| Servers | Configure SSH hosts and confirm their fingerprints before monitoring. |
| Settings | Manage deployment ports, files, and backups. |

Use **中 / EN** to change interface language. In Site content, choose the content language to edit each translation. Empty translated text falls back to the other language, then `-`; portrait, email, and links are shared.

## Update and back up

Back up before updating. On Linux / macOS:

```sh
sh scripts/backup.sh
git pull
sh scripts/update.sh
```

Backups are written to `data/backups/`; store a copy elsewhere. On Windows, use Dashboard backup downloads, then `git pull` and `powershell -ExecutionPolicy Bypass -File scripts/update.ps1`.

Updates preserve database and media volumes. **Do not run `docker compose down -v` if you need to keep your data.** Keep `.env` private and backed up separately.

## Common tasks

- **Change ports:** Dashboard → Settings → Deployment ports. Applying changes briefly restarts services; failures roll back. After a host reboot, run `python3 scripts/deployment_manager.py start` (`py -3` on Windows) to re-enable port management.
- **Connect a database client:** enable the localhost-only database port in Settings. Use host `127.0.0.1`, the configured port, and `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` from `.env`. For remote clients, use an SSH tunnel.
- **Inspect startup problems:** run `docker compose ps` and `docker compose logs --tail=100 backend`.
- **Monitor the physical deployment host:** on Linux/macOS, run `sh scripts/monitor-host.sh start`. Without it, the UI identifies container/runtime metrics separately.

## More information

- [Deployment, recovery, and local development](docs/deployment.md)
- [Architecture](ARCHITECTURE.md) · [Backend and database](BACKEND_DATABASE_DESIGN.md)
- Interactive API documentation: `/api/docs/` on your running site
