from django.db import models


class Server(models.Model):
    STATUS_CHOICES = (("online", "Online"), ("offline", "Offline"), ("warning", "Warning"))
    PROVIDER_CHOICES = (("mock", "Mock"), ("ssh", "SSH"), ("xui", "3x-ui"))

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=120)
    hostname = models.CharField(max_length=180, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=120, blank=True)
    os = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="offline")
    provider = models.CharField(max_length=12, choices=PROVIDER_CHOICES, default="mock")
    last_seen = models.DateTimeField(null=True, blank=True)
    uptime = models.CharField(max_length=80, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    cpu = models.FloatField(default=0)
    memory = models.JSONField(default=dict, blank=True)
    disk = models.JSONField(default=dict, blank=True)
    gpus = models.JSONField(default=list, blank=True)
    containers = models.PositiveIntegerField(default=0)
    connector_config = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]

    def __str__(self):
        return self.name
