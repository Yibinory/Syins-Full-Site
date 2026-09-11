from django.urls import path

from .views import site_content

urlpatterns = [path("content/", site_content, name="site-content")]
