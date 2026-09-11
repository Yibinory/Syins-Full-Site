from django.urls import path

from .views_settings import backup_download, settings_detail

urlpatterns = [
    path("", settings_detail, name="workspace-settings"),
    path("backup/", backup_download, name="workspace-backup"),
]
