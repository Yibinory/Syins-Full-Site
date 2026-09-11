from django.contrib import admin

from .models import Server


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "hostname", "status", "provider", "enabled", "updated_at")
    list_filter = ("status", "provider", "enabled")
    search_fields = ("name", "hostname", "ip", "description")
