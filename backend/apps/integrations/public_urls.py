from rest_framework.routers import DefaultRouter
from .views import PublicEmbeddedPageViewSet
router = DefaultRouter()
router.register("", PublicEmbeddedPageViewSet, basename="public-embedded-page")
urlpatterns = router.urls
