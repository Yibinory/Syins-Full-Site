from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.query import apply_safe_ordering

from .models import EmbeddedPage
from .serializers import EmbeddedPageSerializer


class EmbeddedPageViewSet(viewsets.ModelViewSet):
    serializer_class = EmbeddedPageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        return apply_safe_ordering(
            EmbeddedPage.objects.all(),
            self.request.query_params.get("ordering"),
            {"order", "title", "created_at", "updated_at", "id"},
            ("order", "title", "id"),
        )


class PublicEmbeddedPageViewSet(viewsets.ReadOnlyModelViewSet):
    from rest_framework.permissions import AllowAny
    from .serializers import PublicEmbeddedPageSerializer
    serializer_class = PublicEmbeddedPageSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    queryset = EmbeddedPage.objects.filter(publicly_visible=True)
