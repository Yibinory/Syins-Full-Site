from rest_framework import serializers

from .models import EmbeddedPage


class EmbeddedPageSerializer(serializers.ModelSerializer):
    publiclyVisible = serializers.BooleanField(source="publicly_visible", required=False)
    openInNewTab = serializers.BooleanField(source="open_in_new_tab", required=False)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = EmbeddedPage
        fields = ["id", "slug", "title", "description", "url", "icon", "order", "enabled", "openInNewTab", "publiclyVisible", "createdAt", "updatedAt"]
        read_only_fields = ["slug"]

    def validate_url(self, value):
        if value.split(":", 1)[0].lower() not in {"http", "https"}:
            raise serializers.ValidationError("Only http:// and https:// URLs can be embedded.")
        return value


class PublicEmbeddedPageSerializer(EmbeddedPageSerializer):
    class Meta(EmbeddedPageSerializer.Meta):
        fields = ["id", "slug", "title", "description", "url", "icon", "order", "openInNewTab"]
