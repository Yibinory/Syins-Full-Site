from django.contrib import admin

from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "venue_short", "year", "type", "featured")
    list_filter = ("type", "featured", "year")
    search_fields = ("title", "authors", "venue", "abstract")
    filter_horizontal = ("tags",)
    prepopulated_fields = {"slug": ("title",)}
