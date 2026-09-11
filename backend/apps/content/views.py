import uuid

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CurrentResearchItem, ResearchProject, SiteProfile
from .serializers import CurrentResearchItemSerializer, ResearchProjectSerializer, SiteProfileSerializer


def content_payload():
    profile = SiteProfile.get_solo()
    payload = SiteProfileSerializer(profile).data
    payload["selectedProjects"] = ResearchProjectSerializer(ResearchProject.objects.all(), many=True).data
    payload["currentResearch"] = CurrentResearchItemSerializer(CurrentResearchItem.objects.filter(enabled=True), many=True).data
    return payload


@api_view(["GET", "PUT", "PATCH"])
def site_content(request):
    if request.method in {"PUT", "PATCH"} and not request.user.is_authenticated:
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    if request.method == "GET":
        return Response(content_payload())
    profile = SiteProfile.get_solo()
    profile_data = {key: value for key, value in request.data.items() if key not in {"selectedProjects", "currentResearch"}}
    with transaction.atomic():
        serializer = SiteProfileSerializer(profile, data=profile_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if "selectedProjects" in request.data:
            incoming = request.data.get("selectedProjects") or []
            keep_ids = []
            for index, item in enumerate(incoming):
                item = dict(item)
                raw_id = item.get("id")
                try:
                    project_id = uuid.UUID(str(raw_id)) if raw_id else uuid.uuid4()
                except ValueError:
                    project_id = uuid.uuid4()
                item["id"] = str(project_id)
                item.setdefault("order", index)
                project_serializer = ResearchProjectSerializer(data=item)
                project_serializer.is_valid(raise_exception=True)
                ResearchProject.objects.update_or_create(id=project_id, defaults=dict(project_serializer.validated_data, order=index))
                keep_ids.append(project_id)
            ResearchProject.objects.exclude(id__in=keep_ids).delete()
        if "currentResearch" in request.data:
            incoming = request.data.get("currentResearch") or []
            keep_ids = []
            for index, item in enumerate(incoming):
                item = dict(item)
                item.setdefault("order", index)
                item.setdefault("updated", "")
                item_serializer = CurrentResearchItemSerializer(data=item)
                item_serializer.is_valid(raise_exception=True)
                item_id = item.get("id")
                if item_id and CurrentResearchItem.objects.filter(pk=item_id).exists():
                    obj = CurrentResearchItem.objects.get(pk=item_id)
                    for field, value in dict(item_serializer.validated_data, order=index).items():
                        setattr(obj, field, value)
                    obj.save()
                else:
                    obj = CurrentResearchItem.objects.create(**dict(item_serializer.validated_data, order=index))
                keep_ids.append(obj.id)
            CurrentResearchItem.objects.exclude(id__in=keep_ids).delete()
    return Response(content_payload())


class ResearchProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer
    permission_classes = [AllowAny]


class CurrentResearchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CurrentResearchItem.objects.filter(enabled=True)
    serializer_class = CurrentResearchItemSerializer
    permission_classes = [AllowAny]
