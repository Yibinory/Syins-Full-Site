from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Server
from .serializers import ServerSerializer
from .services import run_server_action


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated]

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

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        updated = []
        for server in self.get_queryset().filter(enabled=True):
            if server.provider == "mock":
                server.last_seen = timezone.now()
                server.save(update_fields=["last_seen", "updated_at"])
            updated.append(server)
        return Response(self.get_serializer(updated, many=True).data)
