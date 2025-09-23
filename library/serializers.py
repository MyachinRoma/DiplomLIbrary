from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Author, Book, Borrowing, Loan
from .services import return_book


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("id", "first_name", "last_name", "bio")


class BookSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(many=True, read_only=True)
    author_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Author.objects.all(), source="authors"
    )

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "authors",
            "author_ids",
            "genre",
            "published_year",
            "isbn",
            "total_copies",
            "available_copies",
        )
        read_only_fields = ("available_copies",)

    def create(self, validated_data):
        authors = validated_data.pop("authors", [])
        book = Book.objects.create(**validated_data)
        if authors:
            book.authors.set(authors)
        # keep available_copies in sync initially
        book.available_copies = book.total_copies
        book.save()
        return book

    def update(self, instance, validated_data):
        authors = validated_data.pop("authors", None)
        # Adjust available_copies if total_copies changed
        total_before = instance.total_copies
        instance = super().update(instance, validated_data)
        if authors is not None:
            instance.authors.set(authors)
        if "total_copies" in validated_data:
            delta = instance.total_copies - total_before
            instance.available_copies = max(0, instance.available_copies + delta)
            instance.save()
        return instance


class LoanSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Loan
        fields = ("id", "user", "book", "borrowed_at", "due_date", "returned_at")
        read_only_fields = ("borrowed_at", "returned_at")

    def validate(self, attrs):
        book = attrs.get("book") or getattr(self.instance, "book", None)
        if self.instance is None:
            # create
            if book is None:
                raise serializers.ValidationError("Book is required.")
            if book.available_copies <= 0:
                raise serializers.ValidationError("No available copies for this book.")
        return attrs

    def create(self, validated_data):
        book = validated_data["book"]
        # decrement available copies
        book.available_copies = max(0, book.available_copies - 1)
        book.save()
        return super().create(validated_data)


class LoanReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ("id", "returned_at")
        read_only_fields = ("id",)

    def update(self, instance, validated_data):
        if instance.returned_at is None:
            instance.returned_at = timezone.now()
            # increment copies
            book = instance.book
            book.available_copies = min(book.total_copies, book.available_copies + 1)
            book.save()
            instance.save()
        return instance


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "__all__"
        read_only_fields = ("returned_at",)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer

    @action(detail=True, methods=["post"], url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()
        borrowing = return_book(borrowing)
        return Response(BorrowingSerializer(borrowing).data, status=status.HTTP_200_OK)
