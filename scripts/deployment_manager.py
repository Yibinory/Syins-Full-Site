#!/usr/bin/env python3
"""Host-side controller for this checkout's web and loopback database ports only."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

from install import read_env, quote

ROOT = Path(__file__).resolve().parent.parent
ACTIVE = {'queued', 'checking', 'applying'}


def atomic_json(path, value, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    with open(temporary, 'w', encoding='utf-8') as stream:
        os.chmod(temporary, mode)
        json.dump(value, stream)
    temporary.replace(path)


def atomic_text(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with open(temporary, 'w', encoding='utf-8') as stream:
        os.chmod(temporary, 0o600)
        stream.write(value)
    temporary.replace(path)


def read_json(path):
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Invalid deployment request.')
    return json.loads(path.read_text(encoding='utf-8'))


def validate_ports(value):
    if set(value) != {'appPort', 'databasePort'}:
        raise ValueError('Only website and database ports can be changed.')
    app, db = value['appPort'], value['databasePort']
    for port in (app, db):
        if port is not None and (type(port) is not int or not 1024 <= port <= 65535):
            raise ValueError('Ports must be integers between 1024 and 65535.')
    if app is None or app == db:
        raise ValueError('Website and database ports must be different.')
    return {'appPort': app, 'databasePort': db}


def check_available(port, host):
    try:
        with socket.socket() as sock:
            sock.bind((host, port))
    except OSError as exc:
        raise ValueError(f'Port {port} is already in use.') from exc


def replace_env(text, updates):
    # Leave all existing secrets and unrelated settings byte-for-byte unchanged.
    lines = text.splitlines()
    for key, value in updates.items():
        replacement = f'{key}={quote(str(value))}'
        positions = [i for i, line in enumerate(lines) if line.split('=', 1)[0].strip() == key]
        if len(positions) > 1:
            raise ValueError('Duplicate deployment setting in .env: ' + key)
        if positions:
            lines[positions[0]] = replacement
        else:
            lines.append(replacement)
    return '\n'.join(lines) + '\n'


def update_origins(value, old_port, new_port):
    origins = []
    for origin in value.split(','):
        parsed = urlsplit(origin.strip())
        if parsed.port == old_port:
            host = parsed.hostname or ''
            host = '[' + host + ']' if ':' in host else host
            origin = urlunsplit((parsed.scheme, f'{host}:{new_port}', parsed.path, parsed.query, parsed.fragment))
        origins.append(origin)
    return ','.join(origins)


def controller_lock(path):
    guard = open(path, 'a+')
    try:
        if os.name == 'nt':
            import msvcrt
            guard.seek(0); guard.write('0'); guard.flush(); guard.seek(0)
            msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        guard.close()
        raise RuntimeError('Another deployment manager is running. Stop it before recovery.')
    return guard


class Manager:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.shared = self.root / 'data/deployment'
        self.private = self.root / '.deployment'
        self.shared.mkdir(parents=True, exist_ok=True)
        self.private.mkdir(mode=0o700, exist_ok=True)
        self.env = self.root / '.env'
        self.overlay = self.private / 'ports.compose.yml'
        self.journal = self.private / 'transaction.json'
        self.state = {'version': 1, 'current': None, 'job': None, 'error': ''}
        try:
            self.state['job'] = read_json(self.shared / 'status.json').get('job')
        except (OSError, ValueError):
            pass
        self.lock = threading.Lock()

    def compose(self, *args):
        environment = dict(os.environ)
        # Deployment settings come from this installation, never a shell's overrides.
        for key in ('APP_PORT', 'DB_PORT', 'COMPOSE_FILE', 'COMPOSE_PATH_SEPARATOR', 'COMPOSE_PROJECT_NAME', 'DJANGO_CSRF_TRUSTED_ORIGINS'):
            environment.pop(key, None)
        result = subprocess.run(['docker', 'compose', *args], cwd=self.root, env=environment,
                                text=True, capture_output=True, timeout=180)
        if result.returncode:
            # Do not expose resolved compose settings or credential-bearing stderr.
            raise RuntimeError('Docker operation failed. Check the host Docker service and deployment configuration.')
        return result.stdout

    def config(self):
        return json.loads(self.compose('config', '--format', 'json'))

    def configured_ports(self):
        services = self.config()['services']
        def published(service, target):
            mappings = services[service].get('ports', [])
            if any(int(p['target']) != target for p in mappings) or len(mappings) > 1:
                raise ValueError('Custom multi-port mappings require manual deployment configuration.')
            if not mappings:
                return None
            return int(mappings[0]['published'])
        return validate_ports({'appPort': published('frontend', 80), 'databasePort': published('db', 5432)})

    def available(self, desired, current):
        # Permit unchanged mappings; reject occupied ports, including cross-service swaps.
        for key, host in (('appPort', '0.0.0.0'), ('databasePort', '127.0.0.1')):
            port = desired[key]
            if port is not None and port != current[key]:
                check_available(port, host)

    def write_status(self):
        with self.lock:
            atomic_json(self.shared / 'status.json', {**self.state, 'heartbeat': time.time()}, 0o644)

    def job(self, **fields):
        with self.lock:
            self.state['job'] = {**(self.state['job'] or {}), **fields}
        self.write_status()

    def snapshot(self):
        return {'env': self.env.read_text(encoding='utf-8'),
                'overlay': self.overlay.read_text(encoding='utf-8') if self.overlay.exists() else None}

    def restore(self, snapshot):
        atomic_text(self.env, snapshot['env'])
        if snapshot['overlay'] is None:
            self.overlay.unlink(missing_ok=True)
        else:
            atomic_text(self.overlay, snapshot['overlay'])

    def prepare(self, desired, current):
        env = read_env(self.env)
        separator = env.get('COMPOSE_PATH_SEPARATOR', os.pathsep)
        if env.get('COMPOSE_FILE'):
            files = env['COMPOSE_FILE'].split(separator)
        else:
            files = ['docker-compose.yml']
            if (self.root / 'docker-compose.override.yml').exists():
                files.append('docker-compose.override.yml')
        relative = '.deployment/ports.compose.json'
        files = [f for f in files if f != relative]
        # JSON cannot express Compose !override. Use a small YAML override instead.
        relative = '.deployment/ports.compose.yml'
        files = [f for f in files if f != relative] + [relative]
        self.overlay = self.private / 'ports.compose.yml'
        db = desired['databasePort']
        bind = self.config()['services']['frontend'].get('ports', [{}])[0].get('host_ip', '0.0.0.0')
        if ':' in bind:
            bind = '[' + bind + ']'
        content = 'services:\n  frontend:\n    ports: !override\n      - "' + bind + ':' + str(desired['appPort']) + ':80"\n  db:\n'
        content += '    ports: !override []\n' if db is None else '    ports: !override\n      - "127.0.0.1:' + str(db) + ':5432"\n'
        atomic_text(self.overlay, content)
        updates = {'APP_PORT': desired['appPort'], 'DB_PORT': db or 5432,
                   'COMPOSE_FILE': ';'.join(files), 'COMPOSE_PATH_SEPARATOR': ';',
                   'DJANGO_CSRF_TRUSTED_ORIGINS': update_origins(env.get('DJANGO_CSRF_TRUSTED_ORIGINS', ''), current['appPort'], desired['appPort'])}
        atomic_text(self.env, replace_env(self.env.read_text(encoding='utf-8'), updates))

    def ready(self, port, seconds=120):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                with urlopen(f'http://127.0.0.1:{port}/api/v1/site/content/', timeout=3) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(2)
        raise RuntimeError('Health check failed.')

    def apply(self, request):
        snapshot = None
        self.state['job'] = None
        try:
            if set(request) != {'id', 'ports'} or not re.fullmatch(r'[0-9a-f-]{36}', request['id']):
                raise ValueError('Invalid deployment request.')
            desired = validate_ports(request['ports'])
            self.job(id=request['id'], status='checking', requested=desired, message='Checking ports.')
            current = self.configured_ports()
            self.available(desired, current)
            if desired == current:
                self.job(status='succeeded', message='Ports are unchanged.')
                return
            self.overlay = self.private / 'ports.compose.yml'
            snapshot = self.snapshot()
            atomic_json(self.journal, {'snapshot': snapshot, 'previous': current, 'id': request['id']})
            self.job(status='applying', previous=current, message='Applying ports. Services will restart briefly.')
            self.prepare(desired, current)
            self.compose('config', '--quiet')
            self.compose('up', '-d', '--no-build', '--pull', 'never', 'db', 'backend', 'frontend')
            self.ready(desired['appPort'])
            self.state['current'] = self.configured_ports()
            self.journal.unlink()
            self.job(status='succeeded', message='Ports applied successfully.')
        except Exception as exc:
            if snapshot is not None:
                try:
                    self.restore(snapshot)
                    self.compose('up', '-d', '--no-build', '--pull', 'never', 'db', 'backend', 'frontend')
                    self.ready(current['appPort'])
                    self.state['current'] = current
                    self.journal.unlink(missing_ok=True)
                    self.job(status='rolled_back', message='Change failed; previous ports restored.')
                except Exception:
                    self.job(status='recovery_required', message='Automatic recovery failed. Run the host recovery command.')
            else:
                self.job(status='failed', message=str(exc))
        finally:
            (self.shared / 'request.json').unlink(missing_ok=True)

    def recover(self):
        if not self.journal.exists():
            return
        transaction = read_json(self.journal)
        self.overlay = self.private / 'ports.compose.yml'
        self.restore(transaction['snapshot'])
        self.compose('up', '-d', '--no-build', '--pull', 'never', 'db', 'backend', 'frontend')
        self.ready(transaction['previous']['appPort'])
        self.journal.unlink()
        self.state['current'] = transaction['previous']
        self.job(id=transaction['id'], status='rolled_back', message='Interrupted change recovered to previous ports.')
        (self.shared / 'request.json').unlink(missing_ok=True)

    def run(self):
        guard = controller_lock(self.private / 'controller.lock')
        version = self.compose('version', '--short').strip().lstrip('v').split('-')[0]
        if tuple(map(int, version.split('.')[:3])) < (2, 24, 4):
            raise RuntimeError('Deployment manager requires Docker Compose 2.24.4 or newer.')
        try:
            self.recover()
            self.state['current'] = self.configured_ports()
        except Exception:
            self.state['error'] = 'Cannot read or recover deployment. Run the recovery command on the host.'
        worker = None
        while True:
            if (self.private / 'stop').exists() and (worker is None or not worker.is_alive()):
                atomic_json(self.shared / 'status.json', {**self.state, 'heartbeat': 0}, 0o644)
                guard.close()
                return
            self.write_status()
            request_path = self.shared / 'request.json'
            if request_path.exists() and (worker is None or not worker.is_alive()) and not self.state['error']:
                if self.journal.exists():
                    self.state['error'] = 'Recovery required before accepting another change.'
                else:
                    try:
                        request = read_json(request_path)
                        worker = threading.Thread(target=self.apply, args=(request,))
                        worker.start()
                    except Exception:
                        self.job(status='failed', message='Invalid deployment request.')
                        request_path.unlink(missing_ok=True)
            time.sleep(2)


def stop(root=ROOT):
    manager = Manager(root)
    try:
        guard = controller_lock(manager.private / 'controller.lock')
        guard.close()
        return
    except RuntimeError:
        pass
    try:
        state = read_json(manager.shared / 'status.json')
        if time.time() - state.get('heartbeat', 0) >= 15:
            return
    except (OSError, ValueError):
        return
    (manager.private / 'stop').touch()
    deadline = time.monotonic() + 660
    while time.monotonic() < deadline:
        state = read_json(manager.shared / 'status.json')
        if time.time() - state.get('heartbeat', 0) >= 15:
            print('Deployment manager stopped.')
            return
        time.sleep(1)
    raise RuntimeError('Active deployment is still running; do not update until it completes.')


def start(root=ROOT):
    manager = Manager(root)
    try:
        guard = controller_lock(manager.private / 'controller.lock')
    except RuntimeError:
        print('Deployment manager already running.')
        return
    guard.close()
    started_at = time.time()
    (manager.private / 'stop').unlink(missing_ok=True)
    with open(manager.private / 'controller.log', 'a') as log:
        kwargs = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'run', '--root', str(root)],
                         cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **kwargs)
    for _ in range(20):
        try:
            if read_json(manager.shared / 'status.json')['heartbeat'] >= started_at:
                print('Deployment manager is online.')
                return
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(.5)
    raise RuntimeError('Deployment manager did not start. Check .deployment/controller.log.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'start', 'stop', 'status', 'recover', 'set-ports'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--app-port', type=int)
    parser.add_argument('--database-port', type=int, help='Omit to disable host database publishing with set-ports')
    args = parser.parse_args()
    if args.command == 'start':
        start(args.root)
    else:
        manager = Manager(args.root)
        if args.command == 'run':
            manager.run()
        elif args.command == 'stop':
            stop(args.root)
        elif args.command == 'set-ports':
            import uuid
            desired = validate_ports({'appPort': args.app_port, 'databasePort': args.database_port})
            guard = controller_lock(manager.private / 'controller.lock')
            try:
                if manager.journal.exists():
                    raise RuntimeError('Recover the pending transaction first.')
                manager.apply({'id': str(uuid.uuid4()), 'ports': desired})
                print(json.dumps(manager.state['job']))
                if manager.state['job']['status'] != 'succeeded':
                    sys.exit(1)
            finally:
                guard.close()
        elif args.command == 'recover':
            try:
                state = read_json(manager.shared / 'status.json')
                if time.time() - state.get('heartbeat', 0) < 15:
                    raise RuntimeError('Stop the deployment manager first; wait until it reports offline, then recover.')
            except (FileNotFoundError, KeyError):
                pass
            guard = controller_lock(manager.private / 'controller.lock')
            try:
                manager.recover()
            finally:
                guard.close()
            print('Recovery completed (or no pending transaction).')
        else:
            print(json.dumps(read_json(manager.shared / 'status.json'), indent=2))
