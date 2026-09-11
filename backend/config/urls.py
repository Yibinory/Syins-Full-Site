from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/site/", include("apps.content.urls")),
    path("api/v1/research/", include("apps.content.research_urls")),
    path("api/v1/publications/", include("apps.publications.urls")),
    path("api/v1/docs/", include("apps.documents.urls")),
    path("api/v1/papers/", include("apps.papers.urls")),
    path("api/v1/servers/", include("apps.servers.urls")),
    path("api/v1/media/", include("apps.core.media_urls")),
    path("api/v1/tags/", include("apps.core.tag_urls")),
    path("api/v1/settings/", include("apps.core.settings_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
