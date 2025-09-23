from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import BookFilter
from .models import Author, Book, Loan
from .permissions import IsAdminOrReadOnly
from .serializers import (
    AuthorSerializer,
    BookSerializer,
    LoanReturnSerializer,
    LoanSerializer,
)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["first_name", "last_name"]
    ordering_fields = ["first_name", "last_name"]


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().prefetch_related("authors")
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = [
        "title",
        "isbn",
        "genre",
        "authors__first_name",
        "authors__last_name",
    ]
    ordering_fields = ["title", "published_year"]


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.select_related("book", "user").all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["borrowed_at", "due_date"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def return_(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanReturnSerializer(instance=loan, data={}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(LoanSerializer(loan).data, status=status.HTTP_200_OK)
