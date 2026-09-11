from django.db import models
from django.utils.text import slugify

from apps.core.models import MediaAsset, Tag


class Publication(models.Model):
    TYPE_CONFERENCE = "Conference"
    TYPE_JOURNAL = "Journal"
    TYPE_PREPRINT = "Preprint"
    TYPE_CHOICES = (
        (TYPE_CONFERENCE, "Conference"),
        (TYPE_JOURNAL, "Journal"),
        (TYPE_PREPRINT, "Preprint"),
    )

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=260, unique=True)
    title = models.CharField(max_length=300)
    authors = models.TextField(blank=True)
    venue = models.CharField(max_length=240, blank=True)
    venue_short = models.CharField(max_length=80, blank=True)
    year = models.PositiveSmallIntegerField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CONFERENCE)
    motivation = models.TextField(blank=True)
    approach = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    paper_url = models.URLField(blank=True)
    code_url = models.URLField(blank=True)
    project_url = models.URLField(blank=True)
    bibtex = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    media_type = models.CharField(max_length=20, default="image")
    media_asset = models.ForeignKey(MediaAsset, null=True, blank=True, on_delete=models.SET_NULL, related_name="publications")
    media_url = models.TextField(blank=True)
    media_alt = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="publications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:240] or "publication"
            candidate = base
            counter = 2
            while Publication.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = "{}-{}".format(base[:235], counter)
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
