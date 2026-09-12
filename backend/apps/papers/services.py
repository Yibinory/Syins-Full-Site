import re

from .models import RecommendedPaper


def normalize_doi(value):
    value = str(value or "").strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.strip().rstrip(".")


def normalize_arxiv_id(value):
    value = str(value or "").strip()
    value = re.sub(r"^https?://(?:export\.)?arxiv\.org/(?:abs|pdf)/", "", value, flags=re.I)
    value = re.sub(r"^arxiv:\s*", "", value, flags=re.I)
    return value.split("?")[0].split("#")[0].removesuffix(".pdf").strip().lower()


def normalize_title(value):
    return " ".join(str(value or "").split()).casefold()


def find_duplicate(*, title="", doi="", arxiv_id="", exclude_id=None):
    queryset = RecommendedPaper.objects.all()
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)

    normalized_doi = normalize_doi(doi)
    if normalized_doi:
        match = queryset.filter(doi__iexact=normalized_doi).first()
        if match:
            return match, "doi"

    normalized_arxiv = normalize_arxiv_id(arxiv_id)
    if normalized_arxiv:
        match = queryset.filter(arxiv_id__iexact=normalized_arxiv).first()
        if match:
            return match, "arxiv_id"

    normalized = normalize_title(title)
    if normalized:
        for match in queryset.only("id", "title", "status").iterator():
            if normalize_title(match.title) == normalized:
                return match, "title"
    return None, None


def duplicate_payload(match, field):
    return {
        "detail": "A recommended paper with the same {} already exists.".format(field.replace("_", " ")),
        "code": "duplicate_paper",
        "duplicate": {"paperId": match.id, "field": field, "status": match.status},
    }
