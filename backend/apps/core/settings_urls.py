from django.urls import path

from .views_deployment import deployment_settings
from .views_settings import backup_download, settings_detail

urlpatterns = [
    path("deployment/", deployment_settings, name="deployment-settings"),
    path("", settings_detail, name="workspace-settings"),
    path("backup/", backup_download, name="workspace-backup"),
]
