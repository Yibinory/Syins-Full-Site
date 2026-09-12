from io import BytesIO
import json
import os
from zipfile import ZIP_DEFLATED, ZipFile

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MediaAsset, WorkspaceSettings
from .serializers import WorkspaceSettingsSerializer


@api_view(["GET", "PATCH", "PUT"])
@permission_classes([IsAuthenticated])
def settings_detail(request):
    instance = WorkspaceSettings.get_solo()
    if request.method == "GET":
        return Response(WorkspaceSettingsSerializer(instance).data)
    serializer = WorkspaceSettingsSerializer(instance, data=request.data, partial=request.method == "PATCH")
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_download(request):
    from apps.content.models import CurrentResearchItem, ResearchProject, SiteProfile
    from apps.content.serializers import CurrentResearchItemSerializer, ResearchProjectSerializer, SiteProfileSerializer
    from apps.documents.models import Document
    from apps.documents.serializers import DocumentSerializer
    from apps.integrations.models import EmbeddedPage
    from apps.integrations.serializers import EmbeddedPageSerializer
    from apps.papers.models import RecommendedPaper
    from apps.papers.serializers import RecommendedPaperSerializer
    from apps.publications.models import Publication
    from apps.publications.serializers import PublicationSerializer
    from apps.servers.models import Server, ServerMetricSample
    from apps.servers.serializers import ServerMetricSampleSerializer, ServerSerializer
    from .models import Tag
    from .serializers import TagSerializer

    records = {
        "version": 2,
        "exportedAt": timezone.now().isoformat(),
        "site": SiteProfileSerializer(SiteProfile.get_solo()).data,
        "selectedProjects": ResearchProjectSerializer(ResearchProject.objects.all(), many=True).data,
        "currentResearch": CurrentResearchItemSerializer(CurrentResearchItem.objects.all(), many=True).data,
        "publications": PublicationSerializer(Publication.objects.prefetch_related("tags"), many=True).data,
        "documents": DocumentSerializer(Document.objects.prefetch_related("tags"), many=True).data,
        "papers": RecommendedPaperSerializer(RecommendedPaper.objects.prefetch_related("tags", "notes"), many=True).data,
        "servers": ServerSerializer(Server.objects.all(), many=True).data,
        "serverMetrics": ServerMetricSampleSerializer(ServerMetricSample.objects.all(), many=True).data,
        "tags": TagSerializer(Tag.objects.select_related("parent").all(), many=True).data,
        "integrations": EmbeddedPageSerializer(EmbeddedPage.objects.all(), many=True).data,
        "settings": WorkspaceSettingsSerializer(WorkspaceSettings.get_solo()).data,
    }
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("research-os.json", json.dumps(records, ensure_ascii=False, indent=2, default=str))
        for asset in MediaAsset.objects.all():
            if not asset.source_file:
                continue
            asset.source_file.open("rb")
            try:
                archive.writestr("media/{}/{}".format(asset.id, os.path.basename(asset.original_name)), asset.source_file.read())
            finally:
                asset.source_file.close()
    response = HttpResponse(output.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="research-os-backup.zip"'
    return response
