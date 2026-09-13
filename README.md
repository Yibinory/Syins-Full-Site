# Syins Research OS

中文文档：[README.zh-CN.md](README.zh-CN.md)

Syins Research OS is a personal research portfolio and private research workspace for researchers. The public site presents research directions, publications and public Notes; the private Dashboard manages the underlying records, recommended-paper memory, documents, media and server inventory.

The project follows the principle:

> Simple now. Easy to extend later.

## What is implemented

- Vue 3 + Vite + TypeScript public site and Dashboard UI
- Django 4.2 + Django REST Framework API
- PostgreSQL in Docker, with SQLite available for local development
- Session authentication with CSRF protection
- Public profile and selected-research CMS
- Authored publications with tags, links, BibTeX and media references
- Recommended papers with reading status, tags, export and zero-to-many Notes links, plus a public date-ordered reading list
- Markdown Documents with direct `.md`/`.markdown` upload, public/private/unlisted visibility and recoverable Trash
- Server inventory with a primary-host view, SSH credential encryption, host-key trust and historical resource metrics
- Dashboard-managed external pages, such as a 3x-ui panel, embedded through a controlled iframe
- Tag metadata with color, description and cycle-safe parent hierarchy
- Server-side media storage for images, video, HTML, Vue and ZIP uploads
- OpenAPI schema and Django admin
- Database migrations, idempotent demo seed data and automated API tests
- Docker Compose deployment with Nginx, persistent PostgreSQL/media volumes, update and backup scripts

## Guided installation (Linux, macOS, Windows)

Requirements: Git, Python **3.9+**, and a running Docker Engine/Desktop with
Compose v2. On Windows use Docker Desktop in **Linux containers** mode. On
macOS Docker Desktop must be started before running the installer. Docker
installation itself may require administrator privileges or a restart; this
installer checks prerequisites rather than silently changing the host system.

Linux / macOS — clone and start the wizard:

```bash
git clone https://github.com/Yibinory/Syins-Full-Site.git && cd Syins-Full-Site && sh scripts/install.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/Yibinory/Syins-Full-Site.git
cd Syins-Full-Site
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

The wizard asks for site name, default language, administrator username,
optional email, a password (12+ characters), and optional public hostname/IP.
Database credentials and application secrets are randomly generated. They are
stored in the ignored `.env` file; passwords are not printed. Protect this
file, particularly on Windows where local access depends on directory ACLs.

Do **not** copy `.env.example` before using the wizard: an existing `.env` is
intentionally preserved and skips all prompts. If preparing configuration
manually, replace every placeholder yourself and run the same installer.
Repeated installation and upgrades preserve accounts, content and data volumes;
they do not reset passwords or automatically import examples.

New workspaces contain an administrator, a generic bilingual homepage and an
automatically registered deployment host. Publications, recommended papers,
notes, research projects and integrations start empty. Configure the homepage
in **Dashboard → Site content**. The default language is applied to first-time
visitors; an explicitly selected browser language takes precedence.

### Ports and readiness

The website tries port 8080, then searches the next 99 ports if occupied.
An actual bind failure during first installation is retried with a new port.
The chosen port and CSRF origins are persisted in `.env`. Completion is reported
only after the public API responds through Nginx. Use the exact URL printed by
the installer, not a presumed 8080 URL.

```bash
sh scripts/install.sh --port 8090
# Optionally publish PostgreSQL to this machine only:
sh scripts/install.sh --port 8090 --database-port 5432
```

PowerShell accepts the same arguments. The database is **not published by
default**; the frontend is published to host interfaces. A configured public
hostname/IP permits that host in Django but does not configure HTTPS, DNS,
firewalls, or router forwarding. For production HTTPS set the appropriate
`DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, and secure cookie options.
The installer currently accepts DNS hostnames and IPv4 addresses for this prompt.

The installer searches ports only for a **new installation**. An existing
installation keeps its port to avoid unexpectedly changing its address.
Dashboard port editing is available through the optional host deployment manager described below.

### Source builds and prebuilt images

The default installs from this checkout with local Docker builds. Plan for
roughly 2 GB RAM for light operation and additional headroom during builds;
4 GB is more comfortable when building on the deployment machine.

The release workflow `.github/workflows/images.yml` publishes backend/frontend
images for **linux/amd64 and linux/arm64** to GitHub Container Registry on `v*`
tags or manual dispatch. This code change supplies the workflow; it does not
itself publish a release or guarantee that an image tag already exists. The
maintainer must run the workflow and make the GHCR packages public before
anonymous image installation works. Forks should update the image repository
names in `docker-compose.images.yml`.

Once a tag has been published, install without building locally:

```bash
sh scripts/install.sh --version v1.0.0  # example: use an actually published tag
```

Use `--source` to select local builds on first installation. The selected
Compose files and image tag are saved in `.env`; updates use the same mode.
For existing installations change `IMAGE_TAG` explicitly when upgrading to a
new version. `latest` follows the last workflow publication.

### Updates, demo data, and recovery

```bash
git pull
sh scripts/update.sh
sh scripts/backup.sh
```

On Windows use `powershell -ExecutionPolicy Bypass -File scripts/update.ps1`.
The Dashboard backup download is also available on Windows. Shell backups are
written to `data/backups/`; keep another copy on a separate machine.

Demo records are an explicit opt-in:

```bash
docker compose exec backend python manage.py seed_demo
```

This adds sample business records without changing existing administrator
credentials. `SEED_DEMO=false` is the default; keep it false to avoid filling
in deleted demo records on restarts. Initialization uses the separate
`bootstrap` command and skips existing workspaces. An installation with users
but no administrator needs an explicit `manage.py createsuperuser` action;
the installer does not promote an existing account.

For a failed installation run `docker compose ps` and `docker compose logs
backend`. Fix `.env` if needed and rerun the installer. Existing credentials
are not reset by changing environment variables. Never run `docker compose
down -v` to troubleshoot an installation whose data you want to retain.

Optional physical-host metrics: on Linux/macOS run `sh scripts/monitor-host.sh
start` (or set `PYTHON_BIN` to a Python executable). Without the sampler,
monitoring identifies backend/container runtime metrics rather than claiming
they describe the physical host. Native Windows hardware sampling is not
implemented; the application still runs through Linux containers, and remote
Linux SSH monitoring remains available.

## Deployment ports in Settings

The deployment owner (Django superuser) can change the **website port** and
**optional localhost-only PostgreSQL port** in Dashboard → Settings → Deployment
ports. Backend/container internal ports remain fixed. Docker Compose **2.24.4+**
is required for this feature.

The installer starts a separate host process after the site is ready. Existing
installations should update their Compose deployment to mount `data/deployment`,
then run:

```bash
python3 scripts/deployment_manager.py start
python3 scripts/deployment_manager.py status
```

On Windows replace `python3` with `py -3`. The host process requires access to
this installation's Docker Compose project. It accepts only validated website
and database port changes through a shared request directory; Django is **not**
given the Docker socket or an arbitrary command execution endpoint.

Applying changes briefly restarts the affected services. The controller checks
port availability, updates `.env` and a private Compose override, applies the
mapping, and checks the public API through the new port. Failures restore the
previous files and ports. A private transaction journal also enables recovery
when the controller is interrupted. Database volumes are never deleted.

After changing the website port, the old browser tab can lose its connection.
Use **Open new direct address** and check the result in Settings. For a reverse
proxy, keep using the original domain and update the proxy's upstream separately.
DNS, TLS, firewall rules, and router forwarding are not changed. A successful
local health check does not prove that a new port is reachable from the Internet.
Existing website bind addresses are preserved; database publishing binds only
`127.0.0.1`. Multiple/custom port mappings are rejected rather than silently
replaced. Port swaps between occupied services should be made in separate steps.

The controller must remain running. Installer/update scripts start it, but no
OS login/startup service is installed automatically. After reboot, run `start`
again, or use your OS supervisor to run `python3 scripts/deployment_manager.py run`
with the project directory as its working directory. If it stops, the website
keeps running and Settings disables port changes. Use the foreground `run` mode
with systemd/launchd/Task Scheduler when unattended host restarts are required.
Windows wrappers are provided; Windows host execution still needs platform testing.

Recovery on the deployment host:

```bash
python3 scripts/deployment_manager.py stop
python3 scripts/deployment_manager.py recover
python3 scripts/deployment_manager.py start
```

`stop` waits for any active change to finish. `recover` restores an **unfinished**
transaction; it does not undo an already successful change. To explicitly return
to another port even when the browser address is inaccessible:

```bash
python3 scripts/deployment_manager.py stop
python3 scripts/deployment_manager.py set-ports --app-port 8080
# Add --database-port 5432 if localhost database access is wanted.
python3 scripts/deployment_manager.py start
```

Keep `.deployment/` private and out of version control/backups shared with others:
it may contain a temporary snapshot of `.env`. Controller logs are in
`.deployment/controller.log`. The public bridge in `data/deployment/` contains
only requests/status, not database credentials. Do not hand-edit managed port
values while a transaction is active. For custom project names persist
`COMPOSE_PROJECT_NAME` in `.env`, rather than supplying it only through CLI `-p`.

## Local development

```bash
pnpm install
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
../.venv/bin/python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='use-a-unique-12-character-password' ../.venv/bin/python manage.py bootstrap
../.venv/bin/python manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```bash
pnpm dev
```

Vite proxies the API, admin, media and static paths to the local Django server. The backend can also run with a local SQLite database when `DATABASE_URL` is unset.

## Project structure

```text
src/                         Vue application and API-backed stores
backend/config/              Django settings, URLs, WSGI/ASGI
backend/apps/accounts/       Authentication
backend/apps/content/        Public site content
backend/apps/publications/   Authored papers
backend/apps/documents/      Notes and Markdown documents
backend/apps/papers/         Recommended-paper memory
backend/apps/servers/        Server inventory and safe actions
backend/apps/integrations/   Dashboard external-page embeds
backend/apps/core/           Media, tags, settings and shared infrastructure
Dockerfile.backend           Django/Gunicorn image
Dockerfile.frontend          Vite/Nginx image
docker-compose.yml           PostgreSQL + backend + frontend deployment
nginx/default.conf           SPA fallback and reverse proxy
scripts/                     Install, update and backup commands
```

For the database and service boundaries, see [ARCHITECTURE.md](ARCHITECTURE.md). For the detailed backend and database design, see [BACKEND_DATABASE_DESIGN.md](BACKEND_DATABASE_DESIGN.md). For the module-by-module product, API and database baseline, see [MODULE_DESIGN.zh-CN.md](MODULE_DESIGN.zh-CN.md).

## Data and security notes

- Public GET endpoints do not require login. Dashboard writes and private records require a Django session.
- Passwords, sessions and CSRF tokens are handled by Django; the frontend does not persist an API token.
- Media uploads are limited to 25 MB and interactive packages are executed only in a sandboxed browser frame with no network access.
- Server monitoring uses a fixed read-only SSH metrics script after an explicit host-key trust step; credentials are encrypted, actions are audited in `ServerActionLog`, and arbitrary shell execution is unavailable.
- External Dashboard pages are URL-validated and sandboxed in an iframe; a target site may still disallow framing through its own CSP or `X-Frame-Options` policy.
- Demo images and sample papers are placeholders. Replace them through the CMS before public deployment.
- Use HTTPS in front of the Compose stack, set secure cookies, rotate the Django and database secrets, and disable demo seeding for a public installation.

## Verification

```bash
pnpm test
pnpm build
cd backend && ../.venv/bin/python manage.py test
```

The frontend tests cover interactive HTML/Vue/ZIP import, archive safety and workspace relation behavior. Backend tests cover public/private permissions, authentication, paper–Note relations, tag metadata, Markdown upload, duplicate-paper conflicts, media upload and server monitoring actions.
