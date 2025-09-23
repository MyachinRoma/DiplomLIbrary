from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def validate_today(value):
    """
    Разрешаем указать только сегодняшнюю дату (локальное сегодня).
    """
    today = timezone.localdate()
    if value != today:
        raise ValidationError("Дата возврата должна быть сегодняшним днём.")


class Borrowing(models.Model):
    # ...
    returned_at = models.DateField(null=True, blank=True, validators=[validate_today])

    def clean(self):
        super().clean()
        if self.returned_at is not None:
            validate_today(self.returned_at)


User = get_user_model()


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class Book(models.Model):
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, related_name="books")
    genre = models.CharField(max_length=100, blank=True)
    published_year = models.PositiveIntegerField(null=True, blank=True)
    isbn = models.CharField(max_length=13, unique=True, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="loans")
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-borrowed_at"]

    @property
    def is_returned(self):
        return self.returned_at is not None
