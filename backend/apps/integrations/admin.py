from django.contrib import admin

from .models import EmbeddedPage


@admin.register(EmbeddedPage)
class EmbeddedPageAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "order", "enabled", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("title", "slug", "url")
