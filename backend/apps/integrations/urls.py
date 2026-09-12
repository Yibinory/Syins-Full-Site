from rest_framework.routers import DefaultRouter

from .views import EmbeddedPageViewSet

router = DefaultRouter()
router.register("", EmbeddedPageViewSet, basename="embedded-page")
urlpatterns = router.urls
