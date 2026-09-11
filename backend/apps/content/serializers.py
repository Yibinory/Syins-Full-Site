from rest_framework import serializers

from apps.core.models import MediaAsset

from .models import CurrentResearchItem, ResearchProject, SiteProfile


class SiteProfileSerializer(serializers.ModelSerializer):
    researchDirections = serializers.CharField(source="research_directions")
    featuredResearchIntro = serializers.CharField(source="featured_research_intro")
    currentResearchHeading = serializers.CharField(source="current_research_heading")
    featuredResearchHeading = serializers.CharField(source="featured_research_heading")
    publicationsHeading = serializers.CharField(source="publications_heading")
    publicationsDescription = serializers.CharField(source="publications_description")
    notesHeading = serializers.CharField(source="notes_heading")
    notesDescription = serializers.CharField(source="notes_description")
    scholarUrl = serializers.URLField(source="scholar_url", allow_blank=True)
    githubUrl = serializers.URLField(source="github_url", allow_blank=True)
    cvUrl = serializers.URLField(source="cv_url", allow_blank=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = SiteProfile
        fields = [
            "name", "title", "location", "email", "headline", "bio",
            "researchDirections", "featuredResearchIntro", "currentResearchHeading",
            "featuredResearchHeading", "publicationsHeading", "publicationsDescription",
            "notesHeading", "notesDescription", "scholarUrl", "githubUrl", "cvUrl", "updatedAt",
        ]


class ResearchProjectSerializer(serializers.ModelSerializer):
    mediaType = serializers.CharField(source="media_type")
    mediaAssetId = serializers.PrimaryKeyRelatedField(source="media_asset", queryset=MediaAsset.objects.all(), allow_null=True, required=False)
    mediaUrl = serializers.CharField(source="media_url", allow_blank=True)
    mediaAlt = serializers.CharField(source="media_alt", allow_blank=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = ResearchProject
        fields = ["id", "order", "title", "motivation", "approach", "status", "mediaType", "mediaAssetId", "mediaUrl", "mediaAlt", "caption", "links", "updatedAt"]


class CurrentResearchItemSerializer(serializers.ModelSerializer):
    updated = serializers.CharField(source="updated_label")

    class Meta:
        model = CurrentResearchItem
        fields = ["id", "number", "title", "text", "status", "question", "method", "updated", "order"]
