from django.db import transaction
from django.utils import timezone

from library.models import Borrowing


def return_book(borrowing: "Borrowing") -> "Borrowing":
    """
    Помечает займ как возвращённый прямо сейчас.
    """
    if borrowing.returned_at:
        return borrowing
    with transaction.atomic():
        borrowing.returned_at = timezone.localdate()
        borrowing.full_clean()
        borrowing.save(update_fields=["returned_at"])
    return borrowing
