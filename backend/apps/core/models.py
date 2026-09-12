import hashlib
import os
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import models
from django.utils.text import slugify


MAX_MEDIA_UPLOAD_BYTES = 25 * 1024 * 1024


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    color = models.CharField(max_length=7, default="#5C7891")
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.strip().split())
        if not self.name:
            raise ValidationError("Tag name cannot be empty.")
        self.color = (self.color or "#5C7891").upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", self.color):
            raise ValidationError("Tag color must be a six-digit hexadecimal value.")
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError("A tag cannot be its own parent.")
        parent = self.parent
        visited = {self.pk} if self.pk else set()
        while parent is not None:
            if parent.pk in visited:
                raise ValidationError("Tag hierarchy cannot contain a cycle.")
            visited.add(parent.pk)
            parent = parent.parent
        base_slug = slugify(self.name, allow_unicode=True)[:80]
        if not base_slug:
            base_slug = "tag-" + hashlib.sha256(self.name.encode("utf-8")).hexdigest()[:12]
        candidate = base_slug
        counter = 2
        while Tag.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            suffix = "-{}".format(counter)
            candidate = base_slug[:90 - len(suffix)] + suffix
            counter += 1
        self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


def media_upload_path(instance, filename):
    safe_name = os.path.basename(filename).replace(" ", "-") or "upload.bin"
    return "assets/{}/{}".format(instance.id, safe_name)


class MediaAsset(models.Model):
    KIND_IMAGE = "image"
    KIND_VIDEO = "video"
    KIND_INTERACTIVE = "interactive"
    KIND_CHOICES = (
        (KIND_IMAGE, "Image"),
        (KIND_VIDEO, "Video"),
        (KIND_INTERACTIVE, "Interactive"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    content_type = models.CharField(max_length=150, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True)
    source_file = models.FileField(upload_to=media_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.size and self.size > MAX_MEDIA_UPLOAD_BYTES:
            raise ValidationError("Uploaded media exceeds the 25 MB limit.")

    @property
    def file_url(self):
        return self.source_file.url if self.source_file else ""

    def calculate_checksum(self):
        if not self.source_file:
            return ""
        digest = hashlib.sha256()
        self.source_file.open("rb")
        try:
            for chunk in self.source_file.chunks():
                digest.update(chunk)
        finally:
            self.source_file.close()
        return digest.hexdigest()

    def delete(self, *args, **kwargs):
        file_name = self.source_file.name
        result = super().delete(*args, **kwargs)
        if file_name:
            default_storage.delete(file_name)
        return result

    def __str__(self):
        return self.original_name


class WorkspaceSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    default_note_visibility = models.CharField(max_length=12, default="private")
    default_note_kind = models.CharField(max_length=30, default="Research Note")
    page_size = models.PositiveSmallIntegerField(default=20)
    site_title = models.CharField(max_length=120, default="Research OS")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=120)
    resource_type = models.CharField(max_length=80, blank=True)
    resource_id = models.CharField(max_length=120, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ServerActionLog(models.Model):
    server_id = models.PositiveBigIntegerField()
    action = models.CharField(max_length=80)
    accepted = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
