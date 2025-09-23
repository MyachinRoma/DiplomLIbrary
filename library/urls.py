from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuthorViewSet, BookViewSet, LoanViewSet

router = DefaultRouter()
router.register(r"authors", AuthorViewSet, basename="author")
router.register(r"books", BookViewSet, basename="book")
router.register(r"loans", LoanViewSet, basename="loan")

urlpatterns = [
    path("", include(router.urls)),
]
