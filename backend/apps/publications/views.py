from django.db.models import Q
from rest_framework import viewsets

from apps.core.query import apply_safe_ordering
from apps.core.permissions import ReadOnlyOrAuthenticated

from .models import Publication
from .serializers import PublicationSerializer


class PublicationViewSet(viewsets.ModelViewSet):
    serializer_class = PublicationSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Publication.objects.prefetch_related("tags", "media_asset").all()
        query = self.request.query_params.get("search", "").strip()
        publication_type = self.request.query_params.get("type", "").strip()
        tag = self.request.query_params.get("tag", "").strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(authors__icontains=query) | Q(abstract__icontains=query))
        if publication_type:
            queryset = queryset.filter(type=publication_type)
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        return apply_safe_ordering(
            queryset.distinct(),
            self.request.query_params.get("ordering"),
            {"year", "id", "created_at", "updated_at", "title"},
            ("-year", "-id"),
        )
