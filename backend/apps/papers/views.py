from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.query import apply_safe_ordering

from .models import RecommendedPaper
from .serializers import RecommendedPaperSerializer
from .services import duplicate_payload, find_duplicate


class RecommendedPaperViewSet(viewsets.ModelViewSet):
    serializer_class = RecommendedPaperSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = RecommendedPaper.objects.prefetch_related("tags", "notes").all()
        query = self.request.query_params.get("search", "").strip()
        paper_status = self.request.query_params.get("status", "").strip()
        tag = self.request.query_params.get("tag", "").strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(authors__icontains=query) | Q(reason__icontains=query))
        if paper_status:
            queryset = queryset.filter(status=paper_status)
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)
        return apply_safe_ordering(
            queryset.distinct(),
            self.request.query_params.get("ordering"),
            {"recommended_at", "updated_at", "created_at", "title", "id"},
            ("-recommended_at", "-id"),
        )

    def create(self, request, *args, **kwargs):
        match, field = find_duplicate(
            title=request.data.get("title", ""),
            doi=request.data.get("doi", ""),
            arxiv_id=request.data.get("arxiv_id", request.data.get("arxivId", "")),
        )
        if match:
            return Response(duplicate_payload(match, field), status=status.HTTP_409_CONFLICT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                instance = serializer.save()
        except IntegrityError:
            match, field = find_duplicate(
                title=request.data.get("title", ""),
                doi=request.data.get("doi", ""),
                arxiv_id=request.data.get("arxiv_id", request.data.get("arxivId", "")),
            )
            if match:
                return Response(duplicate_payload(match, field), status=status.HTTP_409_CONFLICT)
            raise
        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        candidate_title = request.data.get("title", instance.title)
        candidate_doi = request.data.get("doi", instance.doi)
        candidate_arxiv = request.data.get("arxiv_id", request.data.get("arxivId", instance.arxiv_id))
        match, field = find_duplicate(
            title=candidate_title,
            doi=candidate_doi,
            arxiv_id=candidate_arxiv,
            exclude_id=instance.id,
        )
        if match:
            return Response(duplicate_payload(match, field), status=status.HTTP_409_CONFLICT)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                updated = serializer.save()
        except IntegrityError:
            match, field = find_duplicate(
                title=candidate_title,
                doi=candidate_doi,
                arxiv_id=candidate_arxiv,
                exclude_id=instance.id,
            )
            if match:
                return Response(duplicate_payload(match, field), status=status.HTTP_409_CONFLICT)
            raise
        return Response(self.get_serializer(updated).data)

    @action(detail=False, methods=["post"])
    def check(self, request):
        title = str(request.data.get("title", "")).strip()
        doi = str(request.data.get("doi", "")).strip()
        arxiv_id = str(request.data.get("arxiv_id", request.data.get("arxivId", ""))).strip()
        exclude_id = request.data.get("excludeId", request.data.get("exclude_id"))
        try:
            exclude_id = int(exclude_id) if exclude_id not in (None, "") else None
        except (TypeError, ValueError):
            exclude_id = None
        match, field = find_duplicate(title=title, doi=doi, arxiv_id=arxiv_id, exclude_id=exclude_id)
        payload = {"exists": match is not None}
        if match:
            payload.update({"paper_id": match.id, "status": match.status, "field": field})
        return Response(payload)

    @action(detail=False, methods=["get"])
    def export(self, request):
        format_name = request.query_params.get("format", "json").lower()
        records = list(self.get_queryset())
        if format_name == "markdown":
            lines = ["# Recommended papers", ""]
            for paper in records:
                lines.extend([
                    "## {}".format(paper.title),
                    "- Authors: {}".format(paper.authors),
                    "- Status: {}".format(paper.status),
                    "- Tags: {}".format(", ".join(paper.tags.values_list("name", flat=True))),
                    "- Notes: {}".format(", ".join(paper.notes.values_list("title", flat=True))),
                    "",
                    paper.reason,
                    "",
                ])
            return Response("\n".join(lines), content_type="text/markdown")
        return Response(RecommendedPaperSerializer(records, many=True).data)
