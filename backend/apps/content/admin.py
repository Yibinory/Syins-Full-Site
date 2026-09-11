from django.contrib import admin

from .models import CurrentResearchItem, ResearchProject, SiteProfile


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Identity", {"fields": ("name", "title", "location", "email", "headline", "bio")}),
        ("Research", {"fields": ("research_directions", "featured_research_intro", "current_research_heading", "featured_research_heading")}),
        ("Public pages", {"fields": ("publications_heading", "publications_description", "notes_heading", "notes_description")}),
        ("Links", {"fields": ("scholar_url", "github_url", "cv_url")}),
    )


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "order", "updated_at")
    list_editable = ("order",)
    search_fields = ("title", "motivation", "approach")


@admin.register(CurrentResearchItem)
class CurrentResearchItemAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "status", "order", "enabled")
    list_editable = ("order", "enabled")
