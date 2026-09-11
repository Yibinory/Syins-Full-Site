from django.contrib import admin

from .models import RecommendedPaper


@admin.register(RecommendedPaper)
class RecommendedPaperAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "venue", "year", "recommended_at", "rating")
    list_filter = ("status", "year")
    search_fields = ("title", "authors", "reason", "abstract", "doi", "arxiv_id")
    filter_horizontal = ("tags", "notes")
