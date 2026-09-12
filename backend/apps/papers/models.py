from django.db import models

from apps.core.models import Tag
from apps.documents.models import Document


class RecommendedPaper(models.Model):
    STATUS_CHOICES = (
        ("recommended", "Recommended"),
        ("to_read", "To read"),
        ("reading", "Reading"),
        ("read", "Read"),
        ("ignored", "Ignored"),
        ("important", "Important"),
    )

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=320)
    authors = models.TextField(blank=True)
    venue = models.CharField(max_length=240, blank=True)
    year = models.PositiveSmallIntegerField()
    topic = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="recommended")
    recommended_at = models.DateField()
    publicly_visible = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    abstract = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=180, blank=True)
    arxiv_id = models.CharField(max_length=120, blank=True)
    paper_url = models.URLField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="recommended_papers")
    notes = models.ManyToManyField(Document, blank=True, related_name="recommended_papers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-recommended_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["doi"], name="unique_recommended_paper_doi", condition=~models.Q(doi="")),
            models.UniqueConstraint(fields=["arxiv_id"], name="unique_recommended_paper_arxiv", condition=~models.Q(arxiv_id="")),
        ]

    def __str__(self):
        return self.title
