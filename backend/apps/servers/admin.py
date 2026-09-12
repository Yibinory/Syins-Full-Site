from django.contrib import admin

from .models import Server, ServerMetricSample


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "hostname", "status", "provider", "is_primary", "enabled", "updated_at")
    list_filter = ("status", "provider", "enabled")
    search_fields = ("name", "hostname", "ip", "description")


@admin.register(ServerMetricSample)
class ServerMetricSampleAdmin(admin.ModelAdmin):
    list_display = ("server", "recorded_at", "cpu_percent", "memory_used_bytes", "gpu_count", "containers")
    list_filter = ("server",)
    readonly_fields = ("recorded_at",)
