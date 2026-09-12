from rest_framework import serializers

from apps.core.serializers import TagNamesField, set_tag_names

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    publishedAt = serializers.DateField(source="published_at", allow_null=True, required=False)
    readingTime = serializers.CharField(source="reading_time", required=False)
    trashedAt = serializers.DateTimeField(source="trashed_at", read_only=True, allow_null=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    displayDate = serializers.SerializerMethodField()
    tags = TagNamesField(required=False)

    class Meta:
        model = Document
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }
        fields = [
            "id", "slug", "title", "summary", "excerpt", "kind", "content", "publishedAt",
            "displayDate", "readingTime", "visibility", "featured", "tags", "trashedAt", "updatedAt",
        ]

    def get_displayDate(self, obj):
        return obj.published_at.strftime("%d %b %Y") if obj.published_at else "Draft"

    def create(self, validated_data):
        names = validated_data.pop("tags", [])
        instance = super().create(validated_data)
        set_tag_names(instance, names)
        return instance

    def update(self, instance, validated_data):
        names = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        if names is not None:
            set_tag_names(instance, names)
        return instance
