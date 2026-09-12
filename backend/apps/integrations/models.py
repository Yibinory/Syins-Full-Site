from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils.text import slugify


class EmbeddedPage(models.Model):
    slug = models.SlugField(max_length=160, unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    url = models.URLField(max_length=1000)
    icon = models.CharField(max_length=40, blank=True)
    order = models.PositiveIntegerField(default=0)
    enabled = models.BooleanField(default=True)
    publicly_visible = models.BooleanField(default=False)
    open_in_new_tab = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title", "id"]
        indexes = [models.Index(fields=["enabled", "order"])]

    def clean(self):
        try:
            URLValidator(schemes=["http", "https"])(self.url)
        except ValidationError as exc:
            raise ValidationError({"url": "Only http:// and https:// URLs can be embedded."}) from exc

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:150] or "embedded-page"
            candidate = base
            counter = 2
            while type(self).objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = "{}-{}".format(base[:150 - len(str(counter)) - 1], counter)
                counter += 1
            self.slug = candidate
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
