from rest_framework.routers import DefaultRouter

from .public_views import PublicRecommendedPaperViewSet

router = DefaultRouter()
router.register("", PublicRecommendedPaperViewSet, basename="public-recommended-paper")
urlpatterns = router.urls
