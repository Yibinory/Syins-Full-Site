from rest_framework import serializers

from apps.core.models import MediaAsset

from .models import CurrentResearchItem, ResearchProject, SiteProfile


class SiteProfileSerializer(serializers.ModelSerializer):
    papersHeading = serializers.CharField(source="papers_heading", allow_blank=True, required=False)
    papersDescription = serializers.CharField(source="papers_description", allow_blank=True, required=False)
    toolsHeading = serializers.CharField(source="tools_heading", allow_blank=True, required=False)
    toolsDescription = serializers.CharField(source="tools_description", allow_blank=True, required=False)
    researchDirections = serializers.CharField(source="research_directions", allow_blank=True)
    featuredResearchIntro = serializers.CharField(source="featured_research_intro", allow_blank=True)
    currentResearchHeading = serializers.CharField(source="current_research_heading", allow_blank=True)
    featuredResearchHeading = serializers.CharField(source="featured_research_heading", allow_blank=True)
    publicationsHeading = serializers.CharField(source="publications_heading", allow_blank=True)
    publicationsDescription = serializers.CharField(source="publications_description", allow_blank=True)
    notesHeading = serializers.CharField(source="notes_heading", allow_blank=True)
    notesDescription = serializers.CharField(source="notes_description", allow_blank=True)
    scholarUrl = serializers.URLField(source="scholar_url", allow_blank=True)
    githubUrl = serializers.URLField(source="github_url", allow_blank=True)
    cvUrl = serializers.URLField(source="cv_url", allow_blank=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        extra_kwargs = {key: {"allow_blank": True} for key in ("name", "title")}
        model = SiteProfile
        fields = [
            "translations", "papersHeading", "papersDescription", "toolsHeading", "toolsDescription", "name", "title", "location", "email", "headline", "bio",
            "researchDirections", "featuredResearchIntro", "currentResearchHeading",
            "featuredResearchHeading", "publicationsHeading", "publicationsDescription",
            "notesHeading", "notesDescription", "scholarUrl", "githubUrl", "cvUrl", "updatedAt",
        ]


class ResearchProjectSerializer(serializers.ModelSerializer):
    mediaType = serializers.CharField(source="media_type", allow_blank=True)
    mediaAssetId = serializers.PrimaryKeyRelatedField(source="media_asset", queryset=MediaAsset.objects.all(), allow_null=True, required=False)
    mediaUrl = serializers.CharField(source="media_url", allow_blank=True)
    mediaAlt = serializers.CharField(source="media_alt", allow_blank=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        extra_kwargs = {key: {"allow_blank": True} for key in ("title", "status")}
        model = ResearchProject
        fields = ["translations", "id", "order", "title", "motivation", "approach", "status", "mediaType", "mediaAssetId", "mediaUrl", "mediaAlt", "caption", "links", "updatedAt"]


class CurrentResearchItemSerializer(serializers.ModelSerializer):
    updated = serializers.CharField(source="updated_label", allow_blank=True)

    class Meta:
        extra_kwargs = {key: {"allow_blank": True} for key in ("title", "text", "status", "question", "method")}
        model = CurrentResearchItem
        fields = ["translations", "id", "number", "title", "text", "status", "question", "method", "updated", "order"]
