import re
from pathlib import Path

from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import ReadOnlyOrAuthenticated
from apps.core.query import apply_safe_ordering

from .models import Document
from .serializers import DocumentSerializer


MAX_MARKDOWN_UPLOAD_BYTES = 10 * 1024 * 1024


def markdown_title(content, filename):
    match = re.search(r"^#\s+(.+?)\s*$", content, flags=re.MULTILINE)
    return match.group(1).strip() if match else Path(filename).stem.replace("-", " ").replace("_", " ").strip()


def markdown_summary(content):
    paragraphs = []
    for block in re.split(r"\n\s*\n", content):
        value = block.strip()
        if not value or re.match(r"^#{1,6}\s", value):
            continue
        value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
        value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
        value = re.sub(r"[*_~>#-]", "", value)
        value = " ".join(value.split())
        if value:
            paragraphs.append(value)
    return (paragraphs[0] if paragraphs else "").strip()[:500]


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
        return apply_safe_ordering(
            queryset.distinct(),
            self.request.query_params.get("ordering"),
            {"published_at", "updated_at", "created_at", "title", "id"},
            ("-published_at", "-updated_at", "-id"),
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated and instance.visibility == Document.VISIBILITY_PRIVATE:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(instance).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="upload",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload(self, request):
        uploaded = request.FILES.get("file") or request.FILES.get("upload")
        if uploaded is None:
            return Response({"detail": "A Markdown file is required.", "code": "missing_file"}, status=status.HTTP_400_BAD_REQUEST)
        suffix = Path(uploaded.name or "").suffix.lower()
        if suffix not in {".md", ".markdown"}:
            return Response({"detail": "Only .md and .markdown files are supported.", "code": "unsupported_extension"}, status=status.HTTP_400_BAD_REQUEST)
        if uploaded.size > MAX_MARKDOWN_UPLOAD_BYTES:
            return Response({"detail": "The Markdown file exceeds the 10 MB limit.", "code": "file_too_large"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            content = uploaded.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response({"detail": "Markdown files must use UTF-8 encoding.", "code": "invalid_encoding"}, status=status.HTTP_400_BAD_REQUEST)

        title = str(request.data.get("title", "")).strip() or markdown_title(content, uploaded.name)
        summary = str(request.data.get("summary", "")).strip() or markdown_summary(content)
        visibility = str(request.data.get("visibility", Document.VISIBILITY_PRIVATE)).strip() or Document.VISIBILITY_PRIVATE
        kind = str(request.data.get("kind", Document.KIND_RESEARCH)).strip() or Document.KIND_RESEARCH
        tags = request.data.get("tags", "")
        if isinstance(tags, str):
            tags = [value.strip() for value in re.split(r"[,，]", tags) if value.strip()]
        payload = {
            "title": title[:300],
            "summary": summary,
            "content": content,
            "kind": kind,
            "visibility": visibility,
            "featured": str(request.data.get("featured", "")).lower() in {"1", "true", "yes", "on"},
            "tags": tags or [],
        }
        if request.data.get("publishedAt"):
            payload["publishedAt"] = request.data.get("publishedAt")
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response(self.get_serializer(document).data, status=status.HTTP_201_CREATED)

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
