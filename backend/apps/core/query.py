from typing import Optional, Set, Tuple

from django.db.models import QuerySet


def apply_safe_ordering(
    queryset: QuerySet,
    raw_ordering: Optional[str],
    allowed_fields: Set[str],
    default_ordering: Tuple[str, ...],
) -> QuerySet:
    """Apply comma-separated ordering only for explicitly allowed fields."""

    if not raw_ordering:
        return queryset.order_by(*default_ordering)

    requested = []
    for token in raw_ordering.split(","):
        token = token.strip()
        if not token:
            continue
        field = token[1:] if token.startswith("-") else token
        if field in allowed_fields:
            requested.append(token)

    return queryset.order_by(*(requested or default_ordering))
