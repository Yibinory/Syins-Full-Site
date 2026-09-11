from datetime import datetime, timezone

from apps.core.models import ServerActionLog

from .models import Server

ALLOWED_ACTIONS = {"refresh_status", "start_container", "stop_container", "restart_container", "fetch_logs"}


def run_server_action(server, action, actor=None, payload=None):
    if action not in ALLOWED_ACTIONS:
        return False, "This server action is not allowed."
    payload = payload or {}
    if action == "refresh_status" and server.provider == "mock":
        server.last_seen = datetime.now(timezone.utc)
        server.save(update_fields=["last_seen", "updated_at"])
        message = "Mock status refreshed. Configure an SSH connector for live metrics."
        accepted = True
    elif server.provider != "mock":
        message = "This connector is reserved for the integration phase and has not been enabled."
        accepted = False
    else:
        message = "The mock connector does not execute container actions."
        accepted = False
    ServerActionLog.objects.create(server_id=server.id, action=action, accepted=accepted, message=message, actor=actor)
    return accepted, message
