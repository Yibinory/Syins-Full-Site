from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "visibility", "featured", "published_at", "trashed_at")
    list_filter = ("kind", "visibility", "featured")
    search_fields = ("title", "summary", "content")
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
