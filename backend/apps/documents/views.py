from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import ReadOnlyOrAuthenticated

from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [ReadOnlyOrAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Document.objects.prefetch_related("tags").all()
        if not self.request.user.is_authenticated:
            visible = [Document.VISIBILITY_PUBLIC, Document.VISIBILITY_UNLISTED] if self.action == "retrieve" else [Document.VISIBILITY_PUBLIC]
            queryset = queryset.filter(visibility__in=visible, trashed_at__isnull=True)
        elif self.action == "restore":
            pass
        else:
            trash_filter = self.request.query_params.get("trash", "").lower()
            if trash_filter in {"1", "true"}:
                queryset = queryset.filter(trashed_at__isnull=False)
            elif trash_filter != "all":
                queryset = queryset.filter(trashed_at__isnull=True)
        visibility = self.request.query_params.get("visibility", "").strip()
        kind = self.request.query_params.get("kind", "").strip()
        tag = self.request.query_params.get("tag", "").strip()
        search = self.request.query_params.get("search", "").strip()
        if visibility:
            queryset = queryset.filter(visibility=visibility)
        if kind:
            queryset = queryset.filter(kind=kind)
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(summary__icontains=search) | Q(content__icontains=search))
        return queryset.distinct()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated and instance.visibility == Document.VISIBILITY_PRIVATE:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"])
    def trash(self, request, **kwargs):
        document = self.get_object()
        document.trashed_at = timezone.now()
        document.save(update_fields=["trashed_at", "updated_at"])
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, **kwargs):
        document = self.get_object()
        document.trashed_at = None
        document.save(update_fields=["trashed_at", "updated_at"])
        return Response(self.get_serializer(document).data)
