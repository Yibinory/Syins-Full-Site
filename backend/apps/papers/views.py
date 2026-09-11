from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RecommendedPaper
from .serializers import RecommendedPaperSerializer


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
        return queryset.distinct()

    @action(detail=False, methods=["post"])
    def check(self, request):
        title = str(request.data.get("title", "")).strip()
        doi = str(request.data.get("doi", "")).strip()
        arxiv_id = str(request.data.get("arxiv_id", request.data.get("arxivId", ""))).strip()
        query = RecommendedPaper.objects.all()
        match = query.filter(Q(doi=doi) if doi else Q(pk__in=[])).first()
        if match is None and arxiv_id:
            match = query.filter(arxiv_id=arxiv_id).first()
        if match is None and title:
            match = query.filter(title__iexact=title).first()
        payload = {"exists": match is not None}
        if match:
            payload.update({"paper_id": match.id, "status": match.status})
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
