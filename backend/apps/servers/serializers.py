from rest_framework import serializers

from .models import Server


class ServerSerializer(serializers.ModelSerializer):
    lastSeen = serializers.DateTimeField(source="last_seen", allow_null=True, read_only=True)
    connectorStatus = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Server
        fields = [
            "id", "name", "hostname", "ip", "description", "location", "os", "status", "provider",
            "lastSeen", "uptime", "capabilities", "cpu", "memory", "disk", "gpus", "containers",
            "connectorStatus", "enabled", "createdAt", "updatedAt",
        ]
        read_only_fields = ["lastSeen", "connectorStatus"]

    def get_connectorStatus(self, obj):
        if obj.provider == "mock":
            return "demo"
        if obj.connector_config:
            return "configured"
        return "not_configured"
