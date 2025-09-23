from django.contrib import admin

from .forms import BorrowingAdminForm
from .models import Author, Book, Borrowing, Loan


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name")
    search_fields = ("first_name", "last_name")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "genre",
        "published_year",
        "isbn",
        "total_copies",
        "available_copies",
    )
    search_fields = ("title", "isbn", "genre")
    list_filter = ("genre",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "book", "borrowed_at", "due_date", "returned_at")
    list_filter = ("borrowed_at", "returned_at")
    search_fields = ("user__username", "book__title")


@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    form = BorrowingAdminForm
    readonly_fields = ("returned_at",)
