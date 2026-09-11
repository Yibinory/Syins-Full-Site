from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source="is_staff", read_only=True)
    displayName = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "isStaff", "displayName"]

    def get_displayName(self, obj):
        name = obj.get_full_name().strip()
        return name or obj.username
