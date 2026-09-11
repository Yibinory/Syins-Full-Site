from rest_framework.routers import DefaultRouter

from .views import MediaAssetViewSet

router = DefaultRouter()
router.register("", MediaAssetViewSet, basename="media")
urlpatterns = router.urls
