from rest_framework.routers import DefaultRouter

from .views import PublicationViewSet

router = DefaultRouter()
router.register("", PublicationViewSet, basename="publication")
urlpatterns = router.urls
