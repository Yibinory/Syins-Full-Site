from django.db import models
from django.utils.text import slugify

from apps.core.models import Tag


class Document(models.Model):
    KIND_RESEARCH = "Research Note"
    KIND_ESSAY = "Essay"
    KIND_GUIDE = "Guide"
    KIND_REFERENCE = "Reference"
    KIND_CHOICES = (
        (KIND_RESEARCH, "Research Note"),
        (KIND_ESSAY, "Essay"),
        (KIND_GUIDE, "Guide"),
        (KIND_REFERENCE, "Reference"),
    )
    VISIBILITY_PRIVATE = "private"
    VISIBILITY_PUBLIC = "public"
    VISIBILITY_UNLISTED = "unlisted"
    VISIBILITY_CHOICES = (
        (VISIBILITY_PRIVATE, "Private"),
        (VISIBILITY_PUBLIC, "Public"),
        (VISIBILITY_UNLISTED, "Unlisted"),
    )

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=260, unique=True)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    excerpt = models.TextField(blank=True)
    kind = models.CharField(max_length=30, choices=KIND_CHOICES, default=KIND_RESEARCH)
    content = models.TextField(blank=True)
    published_at = models.DateField(null=True, blank=True)
    reading_time = models.CharField(max_length=60, default="1 min")
    visibility = models.CharField(max_length=12, choices=VISIBILITY_CHOICES, default=VISIBILITY_PRIVATE)
    featured = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name="documents")
    trashed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-updated_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:240] or "note"
            candidate = base
            counter = 2
            while Document.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = "{}-{}".format(base[:235], counter)
                counter += 1
            self.slug = candidate
        if not self.excerpt:
            self.excerpt = self.summary or self.content.replace("\n", " ")[:280]
        if not self.reading_time:
            self.reading_time = "{} min".format(max(1, (len(self.content) + 999) // 1000))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
