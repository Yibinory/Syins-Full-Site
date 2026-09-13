"""Read-only host sampler. Can run on the host without Django or third-party packages."""
import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
from pathlib import Path


def command(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=15, env={**os.environ, 'LC_ALL': 'C'})


def hardware_info():
    result = {'architecture': platform.machine(), 'cpu_threads': os.cpu_count() or ''}
    try:
        if platform.system() == 'Linux':
            cpu = Path('/proc/cpuinfo').read_text()
            match = re.search(r'^(?:model name|Hardware)\s*:\s*(.+)', cpu, re.M)
            result['cpu_model'] = match.group(1).strip() if match else ''
            pairs = re.findall(r'physical id\s*:\s*(\d+).*?core id\s*:\s*(\d+)', cpu, re.S)
            result['cpu_cores'] = len(set(pairs)) if pairs else ''
            try:
                dmi = command('dmidecode', '--type', '17')
                speeds = re.findall(r'^\s*Configured (?:Memory |Clock )?Speed:\s*(\d+\s*\S+)', dmi, re.M)
                result['memory_speed'] = ', '.join(sorted(set(speeds)))
            except (OSError, subprocess.SubprocessError):
                pass
        elif platform.system() == 'Darwin':
            result['cpu_model'] = command('/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string').strip()
            result['cpu_cores'] = command('/usr/sbin/sysctl', '-n', 'hw.physicalcpu').strip()
            result['machine_model'] = command('/usr/sbin/sysctl', '-n', 'hw.model').strip()
            try:
                memory = command('/usr/sbin/system_profiler', 'SPMemoryDataType')
                speeds = re.findall(r'Speed:\s*([^\n]+)', memory)
                result['memory_speed'] = ', '.join(sorted(set(speeds)))
            except (OSError, subprocess.SubprocessError):
                pass
    except (OSError, subprocess.SubprocessError):
        pass
    return result


def collect():
    system = platform.system()
    if system == 'Linux':
        def cpu():
            values = [int(v) for v in Path('/proc/stat').read_text().splitlines()[0].split()[1:9]]
            return sum(values), values[3] + values[4]
        total1, idle1 = cpu()
        time.sleep(.4)
        total2, idle2 = cpu()
        usage = 100 * (1 - (idle2-idle1) / max(1, total2-total1))
        mem = {line.split(':')[0]: int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines()}
        total = mem['MemTotal'] * 1024
        available = mem.get('MemAvailable', mem.get('MemFree', 0)) * 1024
        uptime = float(Path('/proc/uptime').read_text().split()[0])
        os_name = platform.freedesktop_os_release().get('PRETTY_NAME', 'Linux')
    elif system == 'Darwin':
        top = command('/usr/bin/top', '-l', '2', '-s', '1', '-n', '0')
        idle = re.findall(r'CPU usage:.*?([\d.]+)% idle', top)
        if not idle:
            raise RuntimeError('macOS CPU sample unavailable')
        usage = 100 - float(idle[-1])
        total = int(command('/usr/sbin/sysctl', '-n', 'hw.memsize'))
        vm = command('/usr/bin/vm_stat')
        page_size = int(re.search(r'page size of (\d+) bytes', vm).group(1))
        pages = {key.strip(): int(value) for key, value in re.findall(r'^([^:\n]+):\s+(\d+)\.', vm, re.M)}
        available = sum(pages.get(key, 0) for key in ('Pages free', 'Pages inactive', 'Pages speculative')) * page_size
        boot = int(re.search(r'sec = (\d+)', command('/usr/sbin/sysctl', '-n', 'kern.boottime')).group(1))
        uptime = time.time() - boot
        os_name = 'macOS ' + platform.mac_ver()[0]
    else:
        raise RuntimeError('Host metrics currently support Linux and macOS')
    disk = shutil.disk_usage('/')
    result = {
        **hardware_info(),
        'hostname': socket.gethostname(), 'os': os_name, 'uptime_seconds': int(uptime),
        'cpu_percent': round(max(0, min(100, usage)), 2), 'load_average': os.getloadavg()[0],
        'memory_total_kb': total // 1024, 'memory_used_kb': max(0, total-available) // 1024,
        'disk_total_kb': disk.total // 1024, 'disk_used_kb': disk.used // 1024,
        'containers': 0, 'containers_available': False, 'gpus': [],
    }
    try:
        result['containers'] = len(command('docker', 'ps', '-q').splitlines())
        result['containers_available'] = True
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        for line in command('nvidia-smi', '--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu', '--format=csv,noheader,nounits').splitlines():
            name, util, used, capacity, temp = [v.strip() for v in line.split(',')]
            result['gpus'].append({'name': name, 'utilization': float(util), 'memoryUsed': float(used), 'memoryTotal': float(capacity), 'temperature': float(temp)})
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    target = Path(args.output).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            data = {'collectedAt': time.time(), 'scope': 'deployment_host', 'values': collect()}
            temporary = target.with_suffix('.tmp')
            temporary.write_text(json.dumps(data))
            temporary.chmod(0o644)
            temporary.replace(target)
        except Exception as exc:
            print('Host sampling failed: ' + str(exc), flush=True)
            if args.once:
                raise
        if args.once:
            return
        time.sleep(max(5, args.interval))


if __name__ == '__main__':
    main()
