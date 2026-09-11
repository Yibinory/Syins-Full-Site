from rest_framework.routers import DefaultRouter

from .views import RecommendedPaperViewSet

router = DefaultRouter()
router.register("", RecommendedPaperViewSet, basename="recommended-paper")
urlpatterns = router.urls
