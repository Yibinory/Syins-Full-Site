from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.documents.models import Document
from apps.papers.models import RecommendedPaper
from apps.publications.models import Publication
from apps.content.models import ResearchProject

from .models import MediaAsset, Tag
from .serializers import MediaAssetSerializer, TagSerializer


class MediaAssetViewSet(viewsets.ModelViewSet):
    queryset = MediaAsset.objects.all()
    serializer_class = MediaAssetSerializer
    http_method_names = ["get", "post", "head", "options", "delete"]

    def get_permissions(self):
        if self.action == "retrieve":
            return [AllowAny()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        asset = self.get_object()
        used = (
            ResearchProject.objects.filter(media_asset=asset).exists()
            or Publication.objects.filter(media_asset=asset).exists()
        )
        if used:
            return Response({"detail": "This file is still used by a record."}, status=status.HTTP_409_CONFLICT)
        asset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def rename(self, request):
        source = str(request.data.get("from", "")).strip()
        target = str(request.data.get("to", "")).strip()
        if not source:
            return Response({"detail": "from is required"}, status=status.HTTP_400_BAD_REQUEST)
        source_tag = Tag.objects.filter(Q(name__iexact=source) | Q(slug__iexact=source)).first()
        if source_tag is None:
            return Response({"detail": "Tag not found"}, status=status.HTTP_404_NOT_FOUND)
        relations = ((RecommendedPaper, "recommendedpaper"), (Publication, "publication"), (Document, "document"))
        if not target:
            for model, object_field in relations:
                model._meta.get_field("tags").remote_field.through.objects.filter(tag=source_tag).delete()
            source_tag.delete()
            return Response({"status": "removed"})
        if source_tag.name.casefold() == target.casefold():
            return Response({"status": "unchanged", "tag": TagSerializer(source_tag).data})
        target_tag = Tag.objects.filter(name__iexact=target).first()
        if target_tag is None:
            target_tag = Tag.objects.create(name=target)
        for model, object_field in relations:
            through = model._meta.get_field("tags").remote_field.through
            for row in through.objects.filter(tag=source_tag).select_related(object_field):
                through.objects.get_or_create(**{object_field: getattr(row, object_field), "tag": target_tag})
            through.objects.filter(tag=source_tag).delete()
        source_tag.delete()
        return Response({"status": "renamed", "tag": TagSerializer(target_tag).data})
