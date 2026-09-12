# Syins Research OS

中文文档：[README.zh-CN.md](README.zh-CN.md)

Syins Research OS is a personal research portfolio and private research workspace for Syins Yibinory. The public site presents research directions, publications and public Notes; the private Dashboard manages the underlying records, recommended-paper memory, documents, media and server inventory.

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

## Quick start with Docker

Requirements: Docker Engine/Desktop with Compose v2.

```bash
cp .env.example .env
# Edit DJANGO_SECRET_KEY, POSTGRES_PASSWORD and DJANGO_SUPERUSER_PASSWORD.
# For a custom domain, also update DJANGO_ALLOWED_HOSTS and DJANGO_CSRF_TRUSTED_ORIGINS.
sh scripts/install.sh
```

Open <http://localhost:8080/>. The first startup runs migrations and creates the administrator plus missing demo records when `SEED_DEMO=true`. The seed command is non-destructive: existing content is not overwritten, so it is safe to leave enabled during upgrades. Set it to `false` when you no longer want new demo records to be added.

To update a deployed checkout:

```bash
git pull
sh scripts/update.sh
```

The update preserves the PostgreSQL and media volumes. Before a risky update, create a backup:

```bash
sh scripts/backup.sh
```

Backups are written to `data/backups/` and should be copied to a separate machine.

## Local development

```bash
pnpm install
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
../.venv/bin/python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='change-me' ../.venv/bin/python manage.py seed_demo
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
