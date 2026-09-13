#!/usr/bin/env python3
"""Cross-platform, idempotent Docker Compose installer (Python 3.9+)."""
import argparse
import getpass
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, text=True, check=True, **kwargs)


def read_env(path):
    result = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip().strip("'\"")
    return result


def free_port(preferred, host='0.0.0.0', excluded=()):
    if not 1024 <= preferred <= 65535:
        raise ValueError('Choose a port between 1024 and 65535.')
    for port in range(preferred, min(65536, preferred + 100)):
        if port in excluded:
            continue
        try:
            with socket.socket() as sock:
                sock.bind((host, port))
            return port
        except OSError:
            continue
    raise ValueError('No free port in the next 100 ports; choose another starting port.')


def quote(value):
    # Compose single-quoted values are literal; reject multiline configuration.
    if any(c in value for c in '\r\n\0'):
        raise ValueError('Configuration values must be single-line.')
    return "'" + value.replace('\\', '\\\\').replace("'", "\\'") + "'"


def write_env(path, values):
    temporary = path.with_suffix('.tmp')
    with open(temporary, 'w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        stream.write(''.join(f'{key}={quote(str(value))}\n' for key, value in values.items()))
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--database-port', type=int, help='Optional localhost-only PostgreSQL port')
    parser.add_argument('--source', action='store_true', help='Build this checkout rather than pull a released image')
    parser.add_argument('--version', default=None, help='Published image tag (or use --source)')
    args = parser.parse_args()
    if not shutil.which('docker'):
        raise ValueError('Install and start Docker Engine/Desktop with Compose v2, then rerun this command.')
    run(['docker', 'compose', 'version'], stdout=subprocess.DEVNULL)
    run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    env_path = ROOT / '.env'
    existing = env_path.exists()
    if existing:
        print('Existing .env detected: preserving credentials, ports and data. Use the update command for upgrades.')
        values = read_env(env_path)
        # Existing installations keep their compose files, image choice and published ports.
        compose = ['docker', 'compose']
    else:
        if (ROOT / 'docker-compose.override.yml').exists():
            raise ValueError('Existing Compose override found. Review it before initializing a new installation.')
        name = input('Site name [Research Space]: ').strip() or 'Research Space'
        language = input('Default language [en/zh, en]: ').strip() or 'en'
        if language not in ('en', 'zh'):
            raise ValueError('Language must be en or zh.')
        username = input('Administrator username [admin]: ').strip() or 'admin'
        if not re.fullmatch(r'[\w.@+-]{1,150}', username):
            raise ValueError('Invalid administrator username.')
        email = input('Administrator email (optional): ').strip()
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise ValueError('Invalid email address.')
        password = getpass.getpass('Administrator password (12+ characters): ')
        if len(password) < 12 or password.isdigit() or password.startswith(('replace-with', 'change-this')):
            raise ValueError('Use a unique password of at least 12 characters, not only digits.')
        if password != getpass.getpass('Confirm password: '):
            raise ValueError('Passwords do not match.')
        address = input('Public hostname or IP (optional; no scheme or port): ').strip()
        if address and not re.fullmatch(r'[A-Za-z0-9.-]+', address):
            raise ValueError('Enter an IPv4 address or hostname without scheme/port.')
        port = free_port(args.port)
        db_port = free_port(args.database_port, '127.0.0.1', (port,)) if args.database_port else None
        hosts = ['localhost', '127.0.0.1'] + ([address] if address else [])
        values = {
            'APP_PORT': port, 'SITE_NAME': name, 'SITE_LANGUAGE': language,
            'DJANGO_SECRET_KEY': secrets.token_hex(48), 'DJANGO_DEBUG': 'false',
            'DJANGO_ALLOWED_HOSTS': ','.join(hosts),
            'DJANGO_CSRF_TRUSTED_ORIGINS': ','.join(f'http://{host}:{port}' for host in hosts),
            'POSTGRES_DB': 'research_os', 'POSTGRES_USER': 'research_os',
            'POSTGRES_PASSWORD': secrets.token_hex(24),
            'DJANGO_SUPERUSER_USERNAME': username, 'DJANGO_SUPERUSER_EMAIL': email,
            'DJANGO_SUPERUSER_PASSWORD': password, 'SEED_DEMO': 'false',
            'GUNICORN_WORKERS': '2', 'SESSION_COOKIE_SECURE': 'false', 'CSRF_COOKIE_SECURE': 'false',
        }
        if args.version and not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}', args.version):
            raise ValueError('Invalid image tag.')
        files = ['docker-compose.yml']
        if args.version and not args.source:
            files.append('docker-compose.images.yml')
            values['IMAGE_TAG'] = args.version
        if db_port:
            files.append('docker-compose.database.yml')
            values['DB_PORT'] = db_port
        values['COMPOSE_PATH_SEPARATOR'] = ';'
        values['COMPOSE_FILE'] = ';'.join(files)
        write_env(env_path, values)
        compose = ['docker', 'compose']
        print(f'Configuration saved to {env_path}. Website port: {port}. Database publishing: {db_port or "disabled"}.')
    (ROOT / 'data/deployment').mkdir(parents=True, exist_ok=True)
    try:
        from deployment_manager import stop
        stop(ROOT)
    except ImportError:
        pass
    use_images = 'docker-compose.images.yml' in values.get('COMPOSE_FILE', '')
    if use_images:
        run(compose + ['pull'])
    else:
        run(compose + ['build'])
    # Detect binding races after preflight; only fresh installations change ports automatically.
    for attempt in range(3):
        result = subprocess.run(compose + ['up', '-d', '--no-build'], cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0:
            break
        if existing or not any(word in result.stderr.lower() for word in ('port is already allocated', 'address already in use')) or attempt == 2:
            print(result.stderr, file=sys.stderr)
            raise ValueError('Startup failed. Configuration/data are kept. Inspect docker compose logs and rerun.')
        old_port = int(values['APP_PORT'])
        port = free_port(old_port + 1)
        values['APP_PORT'] = port
        if values.get('DB_PORT'):
            values['DB_PORT'] = free_port(int(values['DB_PORT']) + 1, '127.0.0.1', (port,))
        values['DJANGO_CSRF_TRUSTED_ORIGINS'] = values['DJANGO_CSRF_TRUSTED_ORIGINS'].replace(f':{old_port}', f':{port}')
        write_env(env_path, values)
    port = values.get('APP_PORT', '8080')
    # Probe the full nginx -> Django -> database path, not merely an open socket.
    from urllib.request import urlopen
    for _ in range(60):
        try:
            with urlopen(f'http://127.0.0.1:{port}/api/v1/site/content/', timeout=3) as response:
                if response.status == 200:
                    print(f'Ready: http://localhost:{port}/\nDashboard: http://localhost:{port}/dashboard')
                    try:
                        from deployment_manager import start
                        start(ROOT)
                    except (ImportError, OSError, RuntimeError):
                        print('Start the deployment manager manually to enable dashboard port changes.')
                    print('Credentials: .env. Existing data is retained on reruns. Host hardware monitoring is optional; see README.')
                    return
        except Exception:
            time.sleep(2)
    raise ValueError('Services started but readiness check timed out. Run docker compose logs backend; no data was removed.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, KeyboardInterrupt, EOFError) as exc:
        print(f'Installation stopped: {exc}', file=sys.stderr)
        sys.exit(1)
