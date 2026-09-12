from rest_framework import serializers

from apps.core.serializers import TagNamesField, set_tag_names
from apps.documents.models import Document

from .models import RecommendedPaper
from .services import normalize_arxiv_id, normalize_doi


class RecommendedPaperSerializer(serializers.ModelSerializer):
    recommendedAt = serializers.DateField(source="recommended_at")
    arxivId = serializers.CharField(source="arxiv_id", allow_blank=True, required=False)
    paperUrl = serializers.URLField(source="paper_url", allow_blank=True, required=False)
    publiclyVisible = serializers.BooleanField(source="publicly_visible", required=False)
    noteIds = serializers.PrimaryKeyRelatedField(source="notes", many=True, queryset=Document.objects.all(), required=False)
    tags = TagNamesField(required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = RecommendedPaper
        fields = [
            "id", "title", "authors", "venue", "year", "topic", "tags", "status", "recommendedAt",
            "reason", "abstract", "rating", "doi", "arxivId", "paperUrl", "publiclyVisible", "noteIds", "createdAt", "updatedAt",
        ]

    def validate_doi(self, value):
        return normalize_doi(value)

    def validate_arxivId(self, value):
        return normalize_arxiv_id(value)

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
