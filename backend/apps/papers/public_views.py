from django.db.models import Prefetch, Q
from apps.documents.models import Document
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.core.query import apply_safe_ordering

from .models import RecommendedPaper
from .public_serializers import PublicRecommendedPaperSerializer


class PublicRecommendedPaperViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicRecommendedPaperSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = RecommendedPaper.objects.filter(publicly_visible=True).prefetch_related("tags", Prefetch("notes", queryset=Document.objects.filter(trashed_at__isnull=True).defer("content").prefetch_related("tags").order_by("-published_at", "-updated_at", "-id"), to_attr="public_note_summaries"))
        query = self.request.query_params.get("search", "").strip()
        paper_status = self.request.query_params.get("status", "").strip()
        tag = self.request.query_params.get("tag", "").strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(authors__icontains=query) | Q(abstract__icontains=query) | Q(reason__icontains=query))
        if paper_status:
            queryset = queryset.filter(status=paper_status)
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        return apply_safe_ordering(
            queryset.distinct(),
            self.request.query_params.get("ordering"),
            {"recommended_at", "created_at", "updated_at", "title", "id"},
            ("-recommended_at", "-id"),
        )
