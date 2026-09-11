from django.urls import path

from .views import login_view, logout_view, session_detail

urlpatterns = [
    path("session/", session_detail, name="session-detail"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
