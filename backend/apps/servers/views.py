from datetime import timedelta

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.query import apply_safe_ordering

from .models import Server, ServerMetricSample
from .serializers import ServerMetricSampleSerializer, ServerSerializer
from .services import run_server_action, test_server_connection, trust_server_host


class ServerViewSet(viewsets.ModelViewSet):
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return apply_safe_ordering(
            Server.objects.all(),
            self.request.query_params.get("ordering"),
            {"is_primary", "name", "status", "last_seen", "created_at", "updated_at", "id"},
            ("-is_primary", "name", "id"),
        )

    def perform_destroy(self, instance):
        if instance.provider == "local":
            raise ValidationError("The deployment host is managed automatically.")
        instance.delete()

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        server = self.get_object()
        return Response(self.get_serializer(server).data)

    @action(detail=True, methods=["post"], url_path="actions")
    def actions(self, request, pk=None):
        server = self.get_object()
        action_name = str(request.data.get("action", "")).strip()
        accepted, message = run_server_action(server, action_name, request.user, request.data)
        payload = {"accepted": accepted, "message": message, "server": self.get_serializer(server).data}
        return Response(payload, status=status.HTTP_200_OK if accepted else status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request, pk=None):
        server = self.get_object()
        return Response(test_server_connection(server))

    @action(detail=True, methods=["post"], url_path="trust-host")
    def trust_host(self, request, pk=None):
        server = self.get_object()
        accepted, message = trust_server_host(server, str(request.data.get("fingerprint", "")))
        payload = {"accepted": accepted, "message": message, "server": self.get_serializer(server).data}
        return Response(payload, status=status.HTTP_200_OK if accepted else status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="metrics")
    def metrics(self, request, pk=None):
        server = self.get_object()
        try:
            hours = min(720, max(1, float(request.query_params.get("hours", 24))))
        except (TypeError, ValueError):
            hours = 24
        try:
            limit = min(1000, max(1, int(request.query_params.get("limit", 500))))
        except (TypeError, ValueError):
            limit = 500
        since = timezone.now() - timedelta(hours=hours)
        samples = list(ServerMetricSample.objects.filter(server=server, recorded_at__gte=since).order_by("-recorded_at", "-id")[:limit])
        samples.reverse()
        return Response({"serverId": server.id, "hours": hours, "count": len(samples), "results": ServerMetricSampleSerializer(samples, many=True).data})

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        updated = []
        for server in self.get_queryset().filter(enabled=True):
            run_server_action(server, "refresh_status", request.user, request.data)
            updated.append(server)
        return Response(self.get_serializer(updated, many=True).data)
