import uuid

from django.db import models

from apps.core.models import MediaAsset


class SiteProfile(models.Model):
    portrait_asset = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="portraits")
    translations = models.JSONField(default=dict, blank=True)
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField(max_length=120, default="Research Space")
    title = models.CharField(max_length=180, default="Independent researcher")
    location = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    headline = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    research_directions = models.TextField(blank=True)
    featured_research_intro = models.TextField(blank=True)
    current_research_heading = models.CharField(max_length=240, blank=True)
    featured_research_heading = models.CharField(max_length=240, blank=True)
    publications_heading = models.CharField(max_length=240, blank=True)
    publications_description = models.TextField(blank=True)
    notes_heading = models.CharField(max_length=240, blank=True)
    notes_description = models.TextField(blank=True)
    papers_heading = models.TextField(blank=True, default="Papers worth returning to.")
    papers_description = models.TextField(blank=True, default="A reading collection on medical imaging, generalization and generation. Recommendations, context and linked notes, newest first.")
    tools_heading = models.TextField(blank=True, default="Tools & resources.")
    tools_description = models.TextField(blank=True, default="A collection of useful external pages and research tools.")
    scholar_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    cv_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance


class ResearchProject(models.Model):
    translations = models.JSONField(default=dict, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=240)
    motivation = models.TextField(blank=True)
    approach = models.TextField(blank=True)
    status = models.CharField(max_length=80, default="Active")
    media_type = models.CharField(max_length=20, default="image")
    media_asset = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="research_projects")
    media_url = models.TextField(blank=True)
    media_alt = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    links = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]


class CurrentResearchItem(models.Model):
    translations = models.JSONField(default=dict, blank=True)
    id = models.BigAutoField(primary_key=True)
    order = models.PositiveIntegerField(default=0)
    number = models.CharField(max_length=12)
    title = models.CharField(max_length=240)
    text = models.TextField(blank=True)
    status = models.CharField(max_length=80, default="Active")
    question = models.TextField(blank=True)
    method = models.TextField(blank=True)
    updated_label = models.CharField(max_length=120, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
