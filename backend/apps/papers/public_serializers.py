from rest_framework import serializers

from apps.core.serializers import TagNamesField
from apps.documents.models import Document

from .models import RecommendedPaper


class PublicPaperNoteSerializer(serializers.ModelSerializer):
    publishedAt = serializers.DateField(source="published_at", allow_null=True)
    readingTime = serializers.CharField(source="reading_time")
    requiresAuth = serializers.SerializerMethodField()
    tags = TagNamesField()

    class Meta:
        model = Document
        fields = ["id", "slug", "title", "summary", "excerpt", "kind", "publishedAt", "readingTime", "visibility", "tags", "requiresAuth"]

    def _is_authenticated(self):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated)

    def get_requiresAuth(self, obj):
        return obj.visibility == Document.VISIBILITY_PRIVATE and not self._is_authenticated()



class PublicRecommendedPaperSerializer(serializers.ModelSerializer):
    recommendedAt = serializers.DateField(source="recommended_at")
    arxivId = serializers.CharField(source="arxiv_id", allow_blank=True)
    paperUrl = serializers.URLField(source="paper_url", allow_blank=True)
    publiclyVisible = serializers.BooleanField(source="publicly_visible")
    tags = TagNamesField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = RecommendedPaper
        fields = ["id", "title", "authors", "venue", "year", "topic", "tags", "status", "recommendedAt", "reason", "abstract", "rating", "doi", "arxivId", "paperUrl", "publiclyVisible", "notes"]

    def get_notes(self, obj):
        notes = obj.public_note_summaries
        return PublicPaperNoteSerializer(notes, many=True, context=self.context).data
