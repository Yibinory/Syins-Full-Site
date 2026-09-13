from rest_framework import serializers

from .credentials import CredentialUnavailable, encrypt_password
from .models import Server, ServerMetricSample


class ServerSerializer(serializers.ModelSerializer):
    hardware = serializers.SerializerMethodField()
    metricScope = serializers.SerializerMethodField()
    detectedHostname = serializers.SerializerMethodField()
    containersAvailable = serializers.SerializerMethodField()
    lastSeen = serializers.DateTimeField(source="last_seen", allow_null=True, read_only=True)
    connectorStatus = serializers.SerializerMethodField()
    isPrimary = serializers.BooleanField(source="is_primary", required=False)
    hostKeyFingerprint = serializers.CharField(source="host_key_fingerprint", read_only=True)
    lastError = serializers.CharField(source="last_error", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Server
        fields = [
            "id", "hardware", "metricScope", "detectedHostname", "containersAvailable", "name", "hostname", "ip", "port", "username", "password", "description", "location", "os", "status", "provider",
            "isPrimary", "lastSeen", "uptime", "capabilities", "cpu", "memory", "disk", "gpus", "containers",
            "connectorStatus", "hostKeyFingerprint", "lastError", "enabled", "createdAt", "updatedAt",
        ]
        read_only_fields = ["lastSeen", "connectorStatus", "hostKeyFingerprint", "lastError"]

    def _latest_sample(self, obj):
        if not hasattr(obj, "_latest_metric"):
            obj._latest_metric = obj.metric_samples.first()
        return obj._latest_metric

    def get_hardware(self, obj):
        sample = self._latest_sample(obj)
        return sample.payload.get("hardware", {}) if sample else {}

    def get_metricScope(self, obj):
        if obj.provider == "mock":
            return "demo"
        sample = self._latest_sample(obj)
        return sample.payload.get("scope", "ssh_host") if sample else "not_sampled"

    def get_detectedHostname(self, obj):
        sample = self._latest_sample(obj)
        return sample.payload.get("hostname", "") if sample else ""

    def get_containersAvailable(self, obj):
        sample = self._latest_sample(obj)
        return bool(sample and sample.payload.get("containersAvailable", True))

    def validate(self, attrs):
        current = self.instance
        provider = attrs.get("provider", current.provider if current else "mock")
        if provider == "local" and (not current or current.provider != "local"):
            raise serializers.ValidationError({"provider": "The deployment host is managed automatically."})
        if current and current.provider == "local" and provider != "local":
            raise serializers.ValidationError({"provider": "The deployment host connection method cannot be changed."})
        if provider == "ssh":
            host = attrs.get("hostname", current.hostname if current else "").strip()
            ip = attrs.get("ip", current.ip if current else None)
            username = attrs.get("username", current.username if current else "").strip()
            password = attrs.get("password", None)
            if not host and not ip:
                raise serializers.ValidationError({"hostname": "A hostname or IP address is required."})
            if "://" in host or "/" in host or any(ch.isspace() for ch in host):
                raise serializers.ValidationError({"hostname": "Enter a hostname or IP without a URL scheme or path."})
            if not username or password == "" or (password is None and not (current and current.encrypted_password)):
                raise serializers.ValidationError({"password": "SSH requires a username and password."})
        return attrs

    def _encrypted_password(self, validated_data):
        if "password" not in self.initial_data:
            return None
        password = validated_data.pop("password", "")
        try:
            return encrypt_password(password)
        except CredentialUnavailable as exc:
            raise serializers.ValidationError({"password": str(exc)}) from exc

    def create(self, validated_data):
        encrypted_password = self._encrypted_password(validated_data)
        if encrypted_password is not None:
            validated_data["encrypted_password"] = encrypted_password
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if any(key in validated_data and validated_data[key] != getattr(instance, key) for key in ("hostname", "ip", "port", "provider")):
            validated_data["host_key_fingerprint"] = ""
        encrypted_password = self._encrypted_password(validated_data)
        if encrypted_password is not None:
            validated_data["encrypted_password"] = encrypted_password
        return super().update(instance, validated_data)

    def get_connectorStatus(self, obj):
        if obj.provider == "local":
            return "local"
        if obj.provider == "mock":
            return "demo"
        if obj.provider == "ssh" and obj.username and obj.encrypted_password:
            return "configured" if obj.host_key_fingerprint else "host_key_pending"
        if obj.connector_config:
            return "configured"
        return "not_configured"


class ServerMetricSampleSerializer(serializers.ModelSerializer):
    recordedAt = serializers.DateTimeField(source="recorded_at")
    cpu = serializers.FloatField(source="cpu_percent")
    memory = serializers.SerializerMethodField()
    disk = serializers.SerializerMethodField()
    gpuUtilization = serializers.FloatField(source="gpu_utilization_percent", allow_null=True)
    gpuCount = serializers.IntegerField(source="gpu_count")
    loadAverage = serializers.FloatField(source="load_average", allow_null=True)

    class Meta:
        model = ServerMetricSample
        fields = ["id", "recordedAt", "cpu", "memory", "disk", "gpuUtilization", "gpuCount", "containers", "loadAverage"]

    def get_memory(self, obj):
        return {"used": obj.memory_used_bytes, "total": obj.memory_total_bytes}

    def get_disk(self, obj):
        return {"used": obj.disk_used_bytes, "total": obj.disk_total_bytes}
