from django.contrib import admin

from .models import AuditEvent, MediaAsset, ServerActionLog, Tag, WorkspaceSettings


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("original_name", "kind", "size", "created_at")
    search_fields = ("original_name", "checksum")
    readonly_fields = ("checksum", "size", "created_at", "updated_at")


@admin.register(WorkspaceSettings)
class WorkspaceSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_title", "default_note_visibility", "updated_at")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "resource_type", "resource_id", "actor", "created_at")
    readonly_fields = ("created_at",)


@admin.register(ServerActionLog)
class ServerActionLogAdmin(admin.ModelAdmin):
    list_display = ("server_id", "action", "accepted", "actor", "created_at")
    readonly_fields = ("created_at",)
