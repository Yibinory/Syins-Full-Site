from rest_framework import serializers

from .models import MediaAsset, Tag, WorkspaceSettings


class TagNamesField(serializers.ListField):
    child = serializers.CharField(max_length=80)

    def to_representation(self, value):
        return [tag.name for tag in value.all()]

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        seen = set()
        result = []
        for value in values:
            clean = " ".join(value.strip().split())
            key = clean.casefold()
            if clean and key not in seen:
                seen.add(key)
                result.append(clean)
        return result


def set_tag_names(instance, names):
    tags = []
    for name in names:
        tag = Tag.objects.filter(name__iexact=name).first()
        if tag is None:
            tag = Tag.objects.create(name=name)
        tags.append(tag)
    instance.tags.set(tags)


class MediaAssetSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(source="original_name", read_only=True)
    kind = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    contentType = serializers.CharField(source="content_type", read_only=True)
    sourceUrl = serializers.SerializerMethodField()
    renderedUrl = serializers.SerializerMethodField()
    upload = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = MediaAsset
        fields = [
            "id", "name", "kind", "size", "contentType", "createdAt",
            "sourceUrl", "renderedUrl", "upload",
        ]

    def get_sourceUrl(self, obj):
        request = self.context.get("request")
        url = obj.file_url
        return request.build_absolute_uri(url) if request and url else url

    def get_renderedUrl(self, obj):
        return self.get_sourceUrl(obj)

    def create(self, validated_data):
        uploaded = validated_data.pop("upload", None)
        if uploaded is None:
            raise serializers.ValidationError({"upload": "A file is required."})
        if uploaded.size > 25 * 1024 * 1024:
            raise serializers.ValidationError({"upload": "File exceeds the 25 MB limit."})
        name = uploaded.name or "upload.bin"
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext in {"mp4", "webm"}:
            kind = MediaAsset.KIND_VIDEO
        elif ext in {"html", "htm", "vue", "zip"}:
            kind = MediaAsset.KIND_INTERACTIVE
        elif ext in {"png", "jpg", "jpeg", "webp", "svg", "gif", "avif"}:
            kind = MediaAsset.KIND_IMAGE
        else:
            raise serializers.ValidationError({"upload": "Unsupported media type."})
        asset = MediaAsset.objects.create(
            original_name=name,
            kind=kind,
            content_type=getattr(uploaded, "content_type", "") or "application/octet-stream",
            size=uploaded.size,
            source_file=uploaded,
        )
        asset.checksum = asset.calculate_checksum()
        asset.save(update_fields=["checksum", "updated_at"])
        return asset


class TagSerializer(serializers.ModelSerializer):
    parentId = serializers.PrimaryKeyRelatedField(source="parent", queryset=Tag.objects.all(), allow_null=True, required=False)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "color", "description", "parentId", "updatedAt"]
        read_only_fields = ["slug"]

    def validate_color(self, value):
        value = value.strip().upper()
        if not value.startswith("#") or len(value) != 7 or any(character not in "0123456789ABCDEF" for character in value[1:]):
            raise serializers.ValidationError("Use a six-digit hexadecimal color such as #5C7891.")
        return value

    def validate_name(self, value):
        value = " ".join(value.strip().split())
        queryset = Tag.objects.filter(name__iexact=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A tag with this name already exists.")
        return value

    def validate_parentId(self, value):
        instance = self.instance
        if value is not None and instance is not None:
            if value.pk == instance.pk:
                raise serializers.ValidationError("A tag cannot be its own parent.")
            ancestor = value
            while ancestor is not None:
                if ancestor.pk == instance.pk:
                    raise serializers.ValidationError("Tag hierarchy cannot contain a cycle.")
                ancestor = ancestor.parent
        return value


class WorkspaceSettingsSerializer(serializers.ModelSerializer):
    defaultNoteVisibility = serializers.CharField(source="default_note_visibility")
    defaultNoteKind = serializers.CharField(source="default_note_kind")
    pageSize = serializers.IntegerField(source="page_size")
    siteTitle = serializers.CharField(source="site_title")
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = WorkspaceSettings
        fields = ["defaultNoteVisibility", "defaultNoteKind", "pageSize", "siteTitle", "updatedAt"]
