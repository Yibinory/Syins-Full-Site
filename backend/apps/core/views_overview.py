from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.content.models import CurrentResearchItem
from apps.documents.models import Document
from apps.papers.models import RecommendedPaper
from apps.servers.models import Server


class OverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        research = CurrentResearchItem.objects.filter(enabled=True)
        papers = RecommendedPaper.objects.all()
        docs = Document.objects.filter(trashed_at__isnull=True)
        servers = Server.objects.exclude(provider='mock').filter(enabled=True)
        return Response({
            'research': {'total': research.count(), 'active': research.filter(status__iexact='active').count()},
            'papers': {'total': papers.count(), 'toRead': papers.filter(status='to_read').count()},
            'documents': {'total': docs.count(), 'private': docs.filter(visibility='private').count()},
            'servers': {'total': servers.count(), 'online': servers.filter(status='online').count(), 'gpus': sum(len(s.gpus or []) for s in servers)},
        })
