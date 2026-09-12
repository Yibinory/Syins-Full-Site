from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Server(models.Model):
    STATUS_CHOICES = (("online", "Online"), ("offline", "Offline"), ("warning", "Warning"))
    PROVIDER_CHOICES = (("local", "Deployment host"), ("mock", "Mock"), ("ssh", "SSH"), ("xui", "3x-ui"))

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120)
    hostname = models.CharField(max_length=180, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(default=22, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    username = models.CharField(max_length=120, blank=True)
    encrypted_password = models.TextField(blank=True)
    host_key_fingerprint = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    os = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="offline")
    provider = models.CharField(max_length=12, choices=PROVIDER_CHOICES, default="mock")
    is_primary = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    uptime = models.CharField(max_length=80, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    cpu = models.FloatField(default=0)
    memory = models.JSONField(default=dict, blank=True)
    disk = models.JSONField(default=dict, blank=True)
    gpus = models.JSONField(default=list, blank=True)
    containers = models.PositiveIntegerField(default=0)
    connector_config = models.JSONField(default=dict, blank=True)
    last_error = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["enabled", "provider", "status"]),
            models.Index(fields=["is_primary"]),
        ]

    def save(self, *args, **kwargs):
        if self.is_primary:
            Server.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServerMetricSample(models.Model):
    server = models.ForeignKey(Server, related_name="metric_samples", on_delete=models.CASCADE)
    recorded_at = models.DateTimeField(default=timezone.now)
    cpu_percent = models.FloatField(default=0)
    memory_used_bytes = models.PositiveBigIntegerField(default=0)
    memory_total_bytes = models.PositiveBigIntegerField(default=0)
    disk_used_bytes = models.PositiveBigIntegerField(default=0)
    disk_total_bytes = models.PositiveBigIntegerField(default=0)
    gpu_utilization_percent = models.FloatField(null=True, blank=True)
    gpu_memory_used_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    gpu_memory_total_bytes = models.PositiveBigIntegerField(null=True, blank=True)
    gpu_count = models.PositiveIntegerField(default=0)
    containers = models.PositiveIntegerField(default=0)
    load_average = models.FloatField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-recorded_at", "-id"]
        indexes = [models.Index(fields=["server", "-recorded_at"])]
