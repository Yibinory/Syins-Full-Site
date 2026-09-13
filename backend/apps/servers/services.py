import base64
import hashlib
import json
import math
import os
import socket
import time
from pathlib import Path

from django.utils import timezone

from apps.core.models import ServerActionLog

from .credentials import CredentialUnavailable, decrypt_password
from .models import Server, ServerMetricSample
from .host_metrics import collect

ALLOWED_ACTIONS = {"refresh_status", "start_container", "stop_container", "restart_container", "fetch_logs"}
CONNECT_TIMEOUT_SECONDS = 10
COMMAND_TIMEOUT_SECONDS = 20


class ConnectorError(RuntimeError):
    pass


class HostKeyConfirmationRequired(ConnectorError):
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        super().__init__("Host key confirmation is required before connecting.")


SNAPSHOT_SCRIPT = r"""#!/bin/sh
test -r /proc/stat && test -r /proc/meminfo || { echo 'SSH monitoring requires a Linux host.' >&2; exit 1; }
cpu_sample() {
  awk '/^cpu / {print ($2+$3+$4+$5+$6+$7+$8+$9) " " ($5+$6); exit}' /proc/stat 2>/dev/null || printf '0 0\n'
}
before=$(cpu_sample)
sleep 0.4
after=$(cpu_sample)
bt=$(printf '%s' "$before" | awk '{print $1}')
bi=$(printf '%s' "$before" | awk '{print $2}')
at=$(printf '%s' "$after" | awk '{print $1}')
ai=$(printf '%s' "$after" | awk '{print $2}')
cpu=$(awk -v bt="$bt" -v bi="$bi" -v at="$at" -v ai="$ai" 'BEGIN { d=at-bt; b=(at-ai)-(bt-bi); if (d > 0) printf "%.2f", (b/d)*100; else print "0" }')
mem_total=$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null)
mem_available=$(awk '/^MemAvailable:/ {print $2; exit}' /proc/meminfo 2>/dev/null)
test -n "$mem_total" || mem_total=0
test -n "$mem_available" || mem_available=0
mem_used=$((mem_total - mem_available))
disk=$(df -Pk / 2>/dev/null | awk 'NR==2 {print $2 " " $3; exit}')
disk_total=$(printf '%s' "$disk" | awk '{print $1}')
disk_used=$(printf '%s' "$disk" | awk '{print $2}')
test -n "$disk_total" || disk_total=0
test -n "$disk_used" || disk_used=0
printf 'hostname=%s\n' "$(hostname 2>/dev/null || true)"
os_name=$(grep '^PRETTY_NAME=' /etc/os-release 2>/dev/null | cut -d= -f2- | tr -d '"' | head -n 1)
test -n "$os_name" || os_name=Linux
printf 'os=%s\n' "$os_name"
printf 'uptime_seconds=%s\n' "$(awk '{printf "%d", $1}' /proc/uptime 2>/dev/null || printf '0')"
printf 'cpu_model=%s\n' "$(awk -F ': ' '/^(model name|Hardware)[[:space:]]*:/ {print $2; exit}' /proc/cpuinfo 2>/dev/null)"
printf 'cpu_threads=%s\n' "$(getconf _NPROCESSORS_ONLN 2>/dev/null)"
printf 'cpu_cores=%s\n' "$(lscpu -p=SOCKET,CORE 2>/dev/null | awk -F, '!/^#/ && NF==2 {seen[$1 FS $2]=1} END {for (k in seen) n++; if(n) print n}')"
printf 'architecture=%s\n' "$(uname -m)"
if command -v timeout >/dev/null 2>&1 && command -v dmidecode >/dev/null 2>&1; then
  printf 'memory_speed=%s\n' "$(timeout 3 dmidecode --type 17 2>/dev/null | awk -F ': ' '/Configured (Memory |Clock )?Speed:/ && $2 ~ /^[0-9]/ {seen[$2]=1} END {for (s in seen) printf "%s ", s}')"
fi
printf 'cpu_percent=%s\n' "$cpu"
printf 'load_average=%s\n' "$(awk '{print $1}' /proc/loadavg 2>/dev/null || printf '0')"
printf 'memory_total_kb=%s\n' "$mem_total"
printf 'memory_used_kb=%s\n' "$mem_used"
printf 'disk_total_kb=%s\n' "$disk_total"
printf 'disk_used_kb=%s\n' "$disk_used"
if command -v docker >/dev/null 2>&1 && container_ids=$(docker ps -q 2>/dev/null); then
  printf 'containers=%s\n' "$(printf '%s\n' "$container_ids" | awk 'NF { n++ } END { print n+0 }')"
  printf 'containers_available=true\n'
else
  printf 'containers=0\ncontainers_available=false\n'
fi
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null | while IFS=',' read -r gpu_name gpu_util gpu_memory_used gpu_memory_total gpu_temperature; do
    gpu_name=$(printf '%s' "$gpu_name" | sed 's/^ *//;s/ *$//')
    gpu_util=$(printf '%s' "$gpu_util" | tr -cd '0-9.')
    gpu_memory_used=$(printf '%s' "$gpu_memory_used" | tr -cd '0-9.')
    gpu_memory_total=$(printf '%s' "$gpu_memory_total" | tr -cd '0-9.')
    gpu_temperature=$(printf '%s' "$gpu_temperature" | tr -cd '0-9.')
    printf 'gpu=%s|%s|%s|%s|%s\n' "$gpu_name" "$gpu_util" "$gpu_memory_used" "$gpu_memory_total" "$gpu_temperature"
  done
fi
"""


def _paramiko():
    try:
        import paramiko
    except ImportError as exc:
        raise ConnectorError("The SSH connector is unavailable. Install the paramiko dependency.") from exc
    return paramiko


def _host(server):
    value = (str(server.ip or "") or server.hostname).strip()
    if not value:
        raise ConnectorError("A hostname or IP address is required.")
    return value


def host_key_fingerprint(key):
    encoded = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode("ascii").rstrip("=")
    return "SHA256:" + encoded


def _transport(server):
    sock = socket.create_connection((_host(server), int(server.port or 22)), timeout=CONNECT_TIMEOUT_SECONDS)
    try:
        transport = _paramiko().Transport(sock)
        transport.banner_timeout = CONNECT_TIMEOUT_SECONDS
        transport.auth_timeout = CONNECT_TIMEOUT_SECONDS
        return transport
    except Exception:
        sock.close()
        raise


def _probe_host_key(server):
    paramiko = _paramiko()
    transport = _transport(server)
    try:
        transport.start_client(timeout=CONNECT_TIMEOUT_SECONDS)
        key = transport.get_remote_server_key()
        if key is None:
            raise ConnectorError("The SSH server did not present a host key.")
        return host_key_fingerprint(key)
    except Exception as exc:
        if isinstance(exc, ConnectorError):
            raise
        raise ConnectorError("SSH handshake failed: {}".format(str(exc)[:240])) from exc
    finally:
        transport.close()


def _open_authenticated_transport(server):
    paramiko = _paramiko()
    try:
        password = decrypt_password(server.encrypted_password)
    except CredentialUnavailable as exc:
        raise ConnectorError(str(exc)) from exc
    if not server.username or not password:
        raise ConnectorError("SSH username and password must be configured.")
    transport = _transport(server)
    try:
        transport.start_client(timeout=CONNECT_TIMEOUT_SECONDS)
        key = transport.get_remote_server_key()
        if key is None:
            raise ConnectorError("The SSH server did not present a host key.")
        fingerprint = host_key_fingerprint(key)
        if not server.host_key_fingerprint:
            raise HostKeyConfirmationRequired(fingerprint)
        if fingerprint != server.host_key_fingerprint:
            raise ConnectorError("SSH host key fingerprint does not match the trusted fingerprint.")
        transport.auth_password(server.username, password)
        if not transport.is_authenticated():
            raise ConnectorError("SSH authentication failed.")
        return transport
    except HostKeyConfirmationRequired:
        transport.close()
        raise
    except Exception as exc:
        transport.close()
        if isinstance(exc, ConnectorError):
            raise
        raise ConnectorError("SSH connection failed: {}".format(str(exc)[:240])) from exc


def _execute_snapshot(transport):
    channel = transport.open_session(timeout=COMMAND_TIMEOUT_SECONDS)
    try:
        channel.settimeout(COMMAND_TIMEOUT_SECONDS)
        channel.exec_command("sh -s")
        channel.sendall(SNAPSHOT_SCRIPT.encode("utf-8"))
        channel.shutdown_write()
        output = channel.makefile("rb").read().decode("utf-8", "replace")
        error = channel.makefile_stderr("rb").read().decode("utf-8", "replace")
        if channel.recv_exit_status() != 0:
            raise ConnectorError("Metrics command failed: {}".format(error.strip()[:240]))
        return output
    finally:
        channel.close()


def _number(value, default=0.0):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError, OverflowError):
        return default


def _integer(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def parse_snapshot(raw):
    values = {}
    gpus = []
    for line in raw.splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        if key == "gpu":
            parts = (value.split("|", 4) + [""] * 5)[:5]
            name, utilization, memory_used, memory_total, temperature = parts
            gpus.append({
                "name": name.strip() or "NVIDIA GPU",
                "utilization": round(_number(utilization), 1),
                "memoryUsed": round(_number(memory_used), 1),
                "memoryTotal": round(_number(memory_total), 1),
                "temperature": round(_number(temperature), 1),
            })
        else:
            values[key] = value.strip()
    values["gpus"] = gpus
    return values


def _uptime_label(seconds):
    seconds = max(0, int(seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return "{}d {}h".format(days, hours)
    if hours:
        return "{}h {}m".format(hours, minutes)
    return "{}m".format(minutes)


def normalized_snapshot(raw_values):
    memory_total = _integer(raw_values.get("memory_total_kb")) * 1024
    memory_used = max(0, _integer(raw_values.get("memory_used_kb")) * 1024)
    disk_total = _integer(raw_values.get("disk_total_kb")) * 1024
    disk_used = max(0, _integer(raw_values.get("disk_used_kb")) * 1024)
    if memory_total <= 0 or disk_total <= 0:
        raise ConnectorError("Incomplete host metrics: memory or disk capacity is unavailable.")
    gpus = raw_values.get("gpus", [])
    formatted_gpus = []
    for gpu in gpus:
        used_gb = gpu["memoryUsed"] / 1024
        total_gb = gpu["memoryTotal"] / 1024
        formatted_gpus.append({
            "name": gpu["name"],
            "utilization": gpu["utilization"],
            "memory": "{:.1f} / {:.1f} GB".format(used_gb, total_gb),
            "memoryUsed": round(used_gb, 2),
            "memoryTotal": round(total_gb, 2),
            "temperature": gpu["temperature"],
        })
    return {
        "hardware": {key: raw_values.get(key, "") for key in ("cpu_model", "cpu_threads", "cpu_cores", "architecture", "machine_model", "memory_speed")},
        "hostname": raw_values.get("hostname", ""),
        "os": raw_values.get("os", "Linux"),
        "uptime": _uptime_label(_integer(raw_values.get("uptime_seconds"))),
        "cpu": round(min(100, max(0, _number(raw_values.get("cpu_percent")))), 1),
        "load_average": _number(raw_values.get("load_average"), None),
        "memory": {"usedBytes": memory_used, "totalBytes": memory_total, "used": round(memory_used / (1024 ** 3), 2), "total": round(memory_total / (1024 ** 3), 2)},
        "disk": {"usedBytes": disk_used, "totalBytes": disk_total, "used": round(disk_used / (1024 ** 4), 2), "total": round(disk_total / (1024 ** 4), 2)},
        "memory_used_bytes": memory_used,
        "memory_total_bytes": memory_total,
        "disk_used_bytes": disk_used,
        "disk_total_bytes": disk_total,
        "gpus": formatted_gpus,
        "containers": max(0, _integer(raw_values.get("containers"))),
        "containers_available": raw_values.get("containers_available") in (True, "true"),
    }


def _save_snapshot(server, snapshot):
    server.status = "online"
    server.last_seen = timezone.now()
    server.last_error = snapshot.get("notice", "")
    if snapshot.get("os"):
        server.os = snapshot["os"][:120]
    server.uptime = snapshot["uptime"]
    server.cpu = snapshot["cpu"]
    server.memory = snapshot["memory"]
    server.disk = snapshot["disk"]
    server.gpus = snapshot["gpus"]
    server.containers = snapshot["containers"]
    server.save(update_fields=["status", "last_seen", "last_error", "os", "uptime", "cpu", "memory", "disk", "gpus", "containers", "updated_at"])
    first_gpu = snapshot["gpus"][0] if snapshot["gpus"] else None
    ServerMetricSample.objects.create(
        server=server,
        recorded_at=server.last_seen,
        cpu_percent=snapshot["cpu"],
        memory_used_bytes=snapshot["memory_used_bytes"],
        memory_total_bytes=snapshot["memory_total_bytes"],
        disk_used_bytes=snapshot["disk_used_bytes"],
        disk_total_bytes=snapshot["disk_total_bytes"],
        gpu_utilization_percent=first_gpu.get("utilization") if first_gpu else None,
        gpu_memory_used_bytes=int(first_gpu.get("memoryUsed", 0) * 1024 ** 3) if first_gpu else None,
        gpu_memory_total_bytes=int(first_gpu.get("memoryTotal", 0) * 1024 ** 3) if first_gpu else None,
        gpu_count=len(snapshot["gpus"]),
        containers=snapshot["containers"],
        load_average=snapshot.get("load_average"),
        payload={"hardware": snapshot.get("hardware", {}), "gpus": snapshot["gpus"], "provider": server.provider, "hostname": snapshot.get("hostname", ""), "scope": snapshot.get("scope", "ssh_host"), "containersAvailable": snapshot.get("containers_available", True)},
    )
    return server


def local_snapshot():
    source = Path(os.environ.get("HOST_METRICS_FILE", "/app/data/host-metrics/snapshot.json"))
    if source.exists():
        data = json.loads(source.read_text())
        age = time.time() - float(data["collectedAt"])
        if not 0 <= age <= 120:
            raise ConnectorError("Host sampler is stale. Restart the host sampler to resume live deployment metrics.")
        snapshot = normalized_snapshot(data["values"])
        snapshot["scope"] = "deployment_host"
        snapshot["containers_available"] = data["values"].get("containers_available", False)
        return snapshot
    values = collect()
    snapshot = normalized_snapshot(values)
    container = Path("/.dockerenv").exists()
    snapshot["scope"] = "container_runtime" if container else "deployment_host"
    snapshot["containers_available"] = values.get("containers_available", False)
    if container:
        snapshot["notice"] = "Host sampler is not connected. These are backend runtime / Docker VM metrics, not the physical deployment host."
    return snapshot


def refresh_server(server):
    if server.provider == "mock":
        return True, "Demo snapshot; no live connection was made.", server
    if server.provider == "local":
        try:
            return True, "Deployment metrics refreshed.", _save_snapshot(server, local_snapshot())
        except Exception as exc:
            server.status = "warning"
            server.last_error = str(exc)[:500]
            server.save(update_fields=["status", "last_error", "updated_at"])
            return False, server.last_error, server
    if server.provider != "ssh":
        message = "This connector does not provide host metrics yet. Add an SSH server for live monitoring."
        server.status = "warning"
        server.last_error = message
        server.save(update_fields=["status", "last_error", "updated_at"])
        return False, message, server
    try:
        transport = _open_authenticated_transport(server)
        try:
            snapshot = normalized_snapshot(parse_snapshot(_execute_snapshot(transport)))
        finally:
            transport.close()
        return True, "SSH status refreshed.", _save_snapshot(server, snapshot)
    except HostKeyConfirmationRequired as exc:
        message = "Host key confirmation required before connecting ({})".format(exc.fingerprint)
    except Exception as exc:
        message = str(exc)[:500]
    server.status = "warning"
    server.last_error = message
    server.save(update_fields=["status", "last_error", "updated_at"])
    return False, message, server


def test_server_connection(server):
    if server.provider == "local":
        accepted, message, _ = refresh_server(server)
        return {"status": "connected" if accepted else "failed", "message": message}
    if server.provider == "mock":
        return {"status": "connected", "message": "Mock connector is ready."}
    if server.provider != "ssh":
        return {"status": "unsupported", "message": "Only SSH and mock connectors support host connection tests."}
    try:
        fingerprint = _probe_host_key(server)
        if not server.host_key_fingerprint:
            return {"status": "host_key_required", "fingerprint": fingerprint, "message": "Trust this host key before the first SSH connection."}
        if server.host_key_fingerprint != fingerprint:
            return {"status": "host_key_mismatch", "fingerprint": fingerprint, "message": "The host key changed and was not trusted."}
        transport = _open_authenticated_transport(server)
        transport.close()
        return {"status": "connected", "fingerprint": fingerprint, "message": "SSH connection authenticated."}
    except HostKeyConfirmationRequired as exc:
        return {"status": "host_key_required", "fingerprint": exc.fingerprint, "message": str(exc)}
    except Exception as exc:
        return {"status": "failed", "message": str(exc)[:500]}


def trust_server_host(server, expected_fingerprint):
    if server.provider != "ssh":
        return False, "Only SSH servers have a host key to trust."
    try:
        fingerprint = _probe_host_key(server)
    except Exception as exc:
        return False, str(exc)[:500]
    if not expected_fingerprint or fingerprint != expected_fingerprint:
        return False, "The host key changed since the connection test. Test again before trusting it."
    server.host_key_fingerprint = fingerprint
    server.last_error = ""
    server.save(update_fields=["host_key_fingerprint", "last_error", "updated_at"])
    return True, "Host key trusted: {}".format(fingerprint)


def run_server_action(server, action, actor=None, payload=None):
    if action not in ALLOWED_ACTIONS:
        accepted, message = False, "This server action is not allowed."
    elif action == "refresh_status":
        accepted, message, _ = refresh_server(server)
    elif server.provider in {"mock", "ssh"}:
        accepted, message = False, "Container and log actions are not enabled in this release."
    else:
        accepted, message = False, "This connector does not support remote actions."
    ServerActionLog.objects.create(server_id=server.id, action=action, accepted=accepted, message=message, actor=actor)
    return accepted, message
