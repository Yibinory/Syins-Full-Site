from rest_framework import serializers

from apps.core.models import MediaAsset
from apps.core.serializers import TagNamesField, set_tag_names

from .models import Publication


class PublicationSerializer(serializers.ModelSerializer):
    venueShort = serializers.CharField(source="venue_short", allow_blank=True, required=False)
    paperUrl = serializers.URLField(source="paper_url", allow_blank=True, required=False)
    codeUrl = serializers.URLField(source="code_url", allow_blank=True, required=False)
    projectUrl = serializers.URLField(source="project_url", allow_blank=True, required=False)
    mediaType = serializers.CharField(source="media_type", required=False)
    mediaAssetId = serializers.PrimaryKeyRelatedField(source="media_asset", queryset=MediaAsset.objects.all(), allow_null=True, required=False)
    mediaUrl = serializers.CharField(source="media_url", allow_blank=True, required=False)
    mediaAlt = serializers.CharField(source="media_alt", allow_blank=True, required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    tags = TagNamesField(required=False)

    class Meta:
        model = Publication
        fields = [
            "id", "slug", "title", "authors", "venue", "venueShort", "year", "type",
            "motivation", "approach", "abstract", "paperUrl", "codeUrl", "projectUrl", "bibtex",
            "featured", "mediaType", "mediaAssetId", "mediaUrl", "mediaAlt", "caption", "tags",
            "createdAt", "updatedAt",
        ]
        read_only_fields = ["slug"]

    def create(self, validated_data):
        names = validated_data.pop("tags", [])
        instance = super().create(validated_data)
        set_tag_names(instance, names)
        return instance

    def update(self, instance, validated_data):
        names = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        if names is not None:
            set_tag_names(instance, names)
        return instance
