from rest_framework.routers import DefaultRouter

from .views import CurrentResearchViewSet, ResearchProjectViewSet

router = DefaultRouter()
router.register("projects", ResearchProjectViewSet, basename="research-project")
router.register("current", CurrentResearchViewSet, basename="current-research")
urlpatterns = router.urls
