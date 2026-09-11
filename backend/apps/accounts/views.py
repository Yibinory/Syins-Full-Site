from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UserSerializer


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def session_detail(request):
    user = request.user
    payload = {"authenticated": bool(user and user.is_authenticated), "user": None}
    if user and user.is_authenticated:
        payload["user"] = UserSerializer(user).data
    response = Response(payload)
    response["X-CSRFToken"] = get_token(request)
    return response


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    identifier = str(request.data.get("email", request.data.get("username", ""))).strip()
    password = str(request.data.get("password", ""))
    user = authenticate(request, username=identifier, password=password)
    if user is None:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
    login(request, user)
    return Response({"authenticated": True, "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"authenticated": False, "user": None})
