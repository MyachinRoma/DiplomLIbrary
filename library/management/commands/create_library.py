import random
from datetime import timedelta
from typing import Optional, Type

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import ForeignKey, ManyToManyField, Model
from django.utils import timezone


def find_model(name: str) -> Optional[Type[Model]]:
    """
    Ищет модель по имени среди всех установленных приложений (без учёта регистра).
    """
    lname = name.lower()
    for model in apps.get_models():
        if model.__name__.lower() == lname:
            return model
    return None


def has_field(model: Type[Model], field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


def get_fk_field(model: Type[Model], candidate_names):
    for name in candidate_names:
        try:
            f = model._meta.get_field(name)
            if isinstance(f, ForeignKey):
                return name
        except Exception:
            pass
    return None


def get_m2m_field(model: Type[Model], candidate_names):
    for name in candidate_names:
        try:
            f = model._meta.get_field(name)
            if isinstance(f, ManyToManyField):
                return name
        except Exception:
            pass
    return None


class Command(BaseCommand):
    help = "Заполняет БД демо-данными (пользователи, авторы, жанры, книги, выдачи)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Очистить целевые таблицы перед заполнением.",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=5,
            help="Сколько создать пользователей (по умолчанию 5).",
        )
        parser.add_argument(
            "--authors",
            type=int,
            default=5,
            help="Сколько создать авторов (по умолчанию 5).",
        )
        parser.add_argument(
            "--genres",
            type=int,
            default=6,
            help="Сколько создать жанров (по умолчанию 6).",
        )
        parser.add_argument(
            "--books",
            type=int,
            default=20,
            help="Сколько создать книг (по умолчанию 20).",
        )
        parser.add_argument(
            "--borrowings",
            type=int,
            default=20,
            help="Сколько создать выдач (по умолчанию 20).",
        )
        parser.add_argument(
            "--create-admin",
            action="store_true",
            help="Создать суперпользователя admin:admin12345, если его нет.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Базовые модели
        User = get_user_model()
        Author = find_model("Author")
        Genre = find_model("Genre")
        Book = find_model("Book")
        Borrowing = find_model("Borrowing")

        # Опциональный reset
        if options["reset"]:
            # удаляем от зависимых к независимым
            if Borrowing:
                Borrowing.objects.all().delete()
            if Book:
                # M2M очистится каскадно
                Book.objects.all().delete()
            if Author:
                Author.objects.all().delete()
            if Genre:
                Genre.objects.all().delete()
            # Пользователей «резать» не будем — вдруг уже заведены реальные
            self.stdout.write(
                self.style.WARNING(
                    "Существующие демо-данные удалены (кроме пользователей)."
                )
            )

        # Создать базовых пользователей
        users = list(User.objects.all()[: options["users"]])
        need = options["users"] - len(users)
        password = "demo12345"

        for i in range(max(0, need)):
            u = User.objects.create_user(
                username=f"demo_user_{i + 1:02d}",
                email=f"demo_user_{i + 1:02d}@example.com",
                password=password,
            )
            users.append(u)

        if options["create-admin"]:
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    "admin", "admin@example.com", "admin12345"
                )
                self.stdout.write(
                    self.style.SUCCESS("Создан суперпользователь admin / admin12345")
                )

        # Авторы
        authors = []
        if Author:
            name_fields = [
                f.name for f in Author._meta.get_fields() if f.concrete and f.editable
            ]
            for i in range(options["authors"]):
                payload = {}
                # Попробуем разные варианты наименования
                if "name" in name_fields:
                    payload["name"] = f"Автор {i + 1}"
                else:
                    if "first_name" in name_fields:
                        payload["first_name"] = f"Имя{i + 1}"
                    if "last_name" in name_fields:
                        payload["last_name"] = f"Фамилия{i + 1}"
                    if not payload:
                        # Совсем неизвестная схема — создадим пустую строку в первом CharField
                        for f in Author._meta.get_fields():
                            if getattr(f, "max_length", None):
                                payload[f.name] = f"Автор {i + 1}"
                                break
                authors.append(Author.objects.create(**payload))
        else:
            self.stdout.write(
                self.style.WARNING("Модель Author не найдена — пропускаю.")
            )

        # Жанры
        genres = []
        if Genre:
            for i in range(options["genres"]):
                payload = {}
                if has_field(Genre, "name"):
                    payload["name"] = f"Жанр {i + 1}"
                else:
                    # fallback: любой первый CharField
                    for f in Genre._meta.get_fields():
                        if getattr(f, "max_length", None):
                            payload[f.name] = f"Жанр {i + 1}"
                            break
                genres.append(Genre.objects.create(**payload))
        else:
            self.stdout.write(
                self.style.WARNING("Модель Genre не найдена — пропускаю.")
            )

        # Книги
        books = []
        if Book:
            author_fk = get_fk_field(Book, ["author", "writer", "creator"])
            genre_fk = get_fk_field(Book, ["genre", "category"])
            genres_m2m = get_m2m_field(Book, ["genres", "tags", "categories"])

            for i in range(options["books"]):
                payload = {}

                # title / name
                if has_field(Book, "title"):
                    payload["title"] = f"Демо-книга {i + 1}"
                elif has_field(Book, "name"):
                    payload["name"] = f"Демо-книга {i + 1}"

                # isbn / код
                if has_field(Book, "isbn"):
                    payload["isbn"] = f"9780{random.randint(100000000, 999999999)}"
                elif has_field(Book, "code"):
                    payload["code"] = f"BK{random.randint(10000, 99999)}"

                # published_year / publication_date
                if has_field(Book, "published_year"):
                    payload["published_year"] = random.randint(
                        1990, timezone.now().year
                    )
                elif has_field(Book, "publication_date"):
                    year = random.randint(1990, timezone.now().year)
                    payload["publication_date"] = timezone.datetime(
                        year, 1, 1, tzinfo=timezone.get_current_timezone()
                    )

                # FK: author / genre
                if author_fk and authors:
                    payload[author_fk] = random.choice(authors)
                if genre_fk and genres:
                    payload[genre_fk] = random.choice(genres)

                book = Book.objects.create(**payload)

                # M2M: genres
                if genres_m2m and genres:
                    getattr(book, genres_m2m).add(
                        *random.sample(genres, k=min(len(genres), random.randint(1, 2)))
                    )

                # возможные числовые поля
                for fname in ("copies_total", "stock", "quantity_total"):
                    if has_field(Book, fname):
                        setattr(book, fname, random.randint(1, 10))
                for fname in ("copies_available", "available", "quantity_available"):
                    if has_field(Book, fname):
                        setattr(
                            book,
                            fname,
                            random.randint(
                                0,
                                (
                                    getattr(book, "copies_total", 5)
                                    if hasattr(book, "copies_total")
                                    else 5
                                ),
                            ),
                        )
                book.save()
                books.append(book)
        else:
            self.stdout.write(self.style.WARNING("Модель Book не найдена — пропускаю."))

        # Выдачи
        if Borrowing and books:
            user_fk = get_fk_field(Borrowing, ["user", "borrower", "customer"])
            book_fk = get_fk_field(Borrowing, ["book", "item"])
            borrowed_at_field = None
            due_at_field = None
            returned_at_field = None

            for cand in [
                "borrowed_at",
                "issued_at",
                "start_at",
                "start_date",
                "date_borrowed",
            ]:
                if has_field(Borrowing, cand):
                    borrowed_at_field = cand
                    break
            for cand in ["due_at", "due_date", "end_at", "return_due", "deadline_at"]:
                if has_field(Borrowing, cand):
                    due_at_field = cand
                    break
            for cand in ["returned_at", "return_at", "date_returned"]:
                if has_field(Borrowing, cand):
                    returned_at_field = cand
                    break

            created = 0
            for i in range(options["borrowings"]):
                payload = {}
                if user_fk:
                    payload[user_fk] = random.choice(users)
                if book_fk:
                    payload[book_fk] = random.choice(books)

                now = timezone.now()
                start = now - timedelta(days=random.randint(1, 20))
                due = start + timedelta(days=random.randint(7, 21))

                if borrowed_at_field:
                    payload[borrowed_at_field] = start
                if due_at_field:
                    payload[due_at_field] = due

                br = Borrowing.objects.create(**payload)

                # Часть выдач «вернём» прямо сейчас
                # — чтобы пройти бизнес-правило «только настоящее время»
                if returned_at_field and random.random() < 0.5:
                    setattr(br, returned_at_field, timezone.now())  # «сейчас»
                    br.save(update_fields=[returned_at_field])

                created += 1

            self.stdout.write(self.style.SUCCESS(f"Создано выдач: {created}"))
        else:
            if not Borrowing:
                self.stdout.write(
                    self.style.WARNING("Модель Borrowing не найдена — пропускаю.")
                )
            elif not books:
                self.stdout.write(
                    self.style.WARNING("Книги отсутствуют — пропускаю создание выдач.")
                )

        # Резюме
        self.stdout.write(self.style.SUCCESS("Готово:"))
        self.stdout.write(
            f"  Пользователи: {get_user_model().objects.count()} (пароль для демо: demo12345)"
        )
        if Author:
            self.stdout.write(f"  Авторы: {Author.objects.count()}")
        if Genre:
            self.stdout.write(f"  Жанры: {Genre.objects.count()}")
        if Book:
            self.stdout.write(f"  Книги: {Book.objects.count()}")
        if Borrowing:
            self.stdout.write(f"  Выдачи: {Borrowing.objects.count()}")
