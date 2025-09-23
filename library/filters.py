import django_filters

from .models import Book


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    genre = django_filters.CharFilter(field_name="genre", lookup_expr="iexact")
    author = django_filters.CharFilter(method="filter_author")

    class Meta:
        model = Book
        fields = ("title", "genre", "author", "published_year", "isbn")

    def filter_author(self, queryset, name, value):
        return queryset.filter(authors__first_name__icontains=value) | queryset.filter(
            authors__last_name__icontains=value
        )
