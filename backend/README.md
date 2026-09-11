# Django backend

The backend is a Django 4.2 + Django REST Framework service. It deliberately uses the same-origin session/CSRF model as the Vue application: the browser does not store an API token, and the private API is protected by the Django session.

## Apps

- `accounts` — session login, logout, CSRF bootstrap and email/username authentication
- `content` — singleton public profile, current research entries and selected research projects
- `publications` — authored publication metadata, links, tags and media references
- `documents` — Markdown notes, visibility, slugs, homepage selection and recoverable trash
- `papers` — recommended-paper memory, status, tags and many-to-many document links
- `servers` — server inventory, capability snapshots and explicit action logs
- `core` — media files, tags, workspace settings, pagination and audit primitives

## Local development

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cd backend
.venv/bin/python manage.py migrate
DJANGO_SUPERUSER_PASSWORD='change-me' .venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Run the Vue dev server in another terminal with `pnpm dev`. Vite proxies `/api`, `/admin`, `/media` and `/static` to port 8000.

## API

- Session: `/api/v1/auth/session/`, `/api/v1/auth/login/`, `/api/v1/auth/logout/`
- Public content: `/api/v1/site/content/`, `/api/v1/publications/`, `/api/v1/docs/`
- Private workspace: `/api/v1/papers/`, `/api/v1/settings/`, `/api/v1/tags/`, `/api/v1/media/`
- Infrastructure: `/api/v1/servers/`
- OpenAPI: `/api/schema/`; interactive docs: `/api/docs/`

The API returns the frontend's camelCase contract. List endpoints are paginated, and the frontend's `listData` helper accepts both paginated and non-paginated responses.

`seed_demo` is safe to run again: it creates missing demo records but does not replace records that already exist. This makes container restarts and version upgrades non-destructive.

## Production boundary

Server actions are a whitelist (`refresh_status`, `start_container`, `stop_container`, `restart_container`, `fetch_logs`). The current mock connector only refreshes mock snapshots; SSH, Docker Remote and 3x-ui connectors must be implemented as isolated providers before any remote write action is enabled. There is no arbitrary shell endpoint.

Interactive media is stored as an uploaded source file and compiled in the browser inside a sandboxed iframe. The importer never runs package installation or archive build scripts.
