# 📚 DiplomLIbrary — библиотечная система на Django

> Бэкенд для учёта книг, авторов и выдач. В проекте реализовано правило: **дату возврата можно указывать только «сейчас»** — система выставляет её автоматически при операции возврата.

[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](#)
[![DRF](https://img.shields.io/badge/DRF-ready-red)](#api)
[![Poetry](https://img.shields.io/badge/Poetry-enabled-60A5FA?logo=poetry&logoColor=white)](#установка-и-запуск)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#лицензия)

---

## Содержание

- [Особенности](#особенности)
- [Архитектура](#архитектура)
- [Схема данных (Mermaid)](#схема-данных-mermaid)
- [Правило возврата книг](#правило-возврата-книг)
- [Установка и запуск](#установка-и-запуск)
  - [Poetry](#poetry)
  - [venv + pip](#venv--pip)
- [ENV-переменные](#env-переменные)
- [Наполнение БД](#наполнение-бд)
- [API](#api)
  - [Справочники](#справочники)
  - [Выдачи и возврат](#выдачи-и-возврат)
- [Статика на Windows](#статика-на-windows)
- [Тестирование](#тестирование)
- [Тр Troubleshooting](#tr-troubleshooting)
- [Лицензия](#лицензия)

---

## Особенности

- ✅ **Возврат только «сейчас»** — `returned_at` ставится системой в момент возврата (клиент не задаёт вручную).
- ✅ **Демо-данные за 1 команду** — `create_library` для быстрого старта.
- ✅ **Гибкая схема** — команда засевания подстраивается под названия полей.
- ✅ **Готово к DRF** — удобно подключать REST API.
- ✅ **Poetry / pip** — выбери привычный способ установки.

---

## Архитектура

```
DiplomLIbrary/
├─ manage.py
├─ pyproject.toml / poetry.lock      # Poetry (если используется)
├─ requirements.txt                  # pip (если используется)
├─ .env                              # локальные переменные окружения
├─ <project_package>/settings.py
├─ library/
│  ├─ models.py                      # Author, Genre, Book, Borrowing
│  ├─ admin.py
│  ├─ management/
│  │  └─ commands/
│  │     ├─ create_library.py
│  │     └─ seed_demo.py
│  └─ ...
└─ static/                           # опционально
```

---

## Схема данных (Mermaid)

> GitHub поддерживает Mermaid. Диаграмма автоматически отрисуется на странице репозитория.

```mermaid
classDiagram
  class User

  class Author {
    +id: int
    +name: str
    +first_name?: str
    +last_name?: str
  }

  class Genre {
    +id: int
    +name: str
  }

  class Book {
    +id: int
    +title/name: str
    +isbn?: str
    +published_year?: int
    +publication_date?: datetime
  }

  class Borrowing {
    +id: int
    +borrowed_at: datetime
    +due_at?: datetime
    +returned_at?: datetime  <<only-now>>
  }

  Book --> Author : author
  Book --> Genre : genres (M2M)
  Borrowing --> Book : book
  Borrowing --> User : user
```

Легенда: `returned_at` помечен как `<<only-now>>`, что означает — значение устанавливается автоматически при возврате.

---

## Правило возврата книг

- Поле `returned_at` считается **только для чтения** в API/формах.
- Сервисный метод возврата **проставляет текущий момент** (timezone‑aware) в момент операции.
- Валидация на уровне модели/сериалайзера блокирует любые даты не «сейчас» (для `DateTimeField` допускается небольшой люфт 2–5 минут из‑за сетевых задержек).

**Бизнес-выгода:** исключены «задние числа», повышена целостность данных, снизился риск манипуляций.

---

## Установка и запуск

### Poetry

```bash
poetry install
poetry shell
python manage.py migrate
python manage.py runserver
```

### venv + pip

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## ENV-переменные

Создайте `.env` рядом с `manage.py`:

```dotenv
SECRET_KEY=change-me-please
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB
DATABASE_URL=sqlite:///db.sqlite3

TIME_ZONE=Europe/Berlin
LANGUAGE_CODE=ru-ru
```

> Если не используете `DATABASE_URL`, настройте `DATABASES` в `settings.py` вручную.

---

## Наполнение БД

Два варианта (в проекте может быть один/оба):

```bash
# Универсальная команда засевания
python manage.py seed_demo --reset --users=5 --authors=5 --genres=6 --books=20 --borrowings=20 --create-admin

# Пример альтернативной команды
python manage.py create_library --reset --users=5 --authors=5 --genres=6 --books=20 --borrowings=20 --create-admin
```
> Примечание: в коде аргумент `--create-admin` будет доступен как `options["create_admin"]` (defis → underscore).

---

## API

Ниже — типичный контракт (может отличаться от вашей сборки; подстройте названия путей при необходимости).

### Справочники

**GET** `/api/books/` — список книг  
**GET** `/api/books/{id}/` — детальная карточка  
**GET** `/api/authors/`, `/api/genres/` — справочники

Пример ответа `/api/books/`:
```json
[
  {
    "id": 1,
    "title": "Демо-книга 1",
    "isbn": "9780123456789",
    "author": {"id": 2, "name": "Автор 2"},
    "genres": [{"id": 1, "name": "Жанр 1"}],
    "published_year": 2021
  }
]
```

### Выдачи и возврат

**GET** `/api/borrowings/` — список выдач  
**POST** `/api/borrowings/` — создать выдачу
```json
{
  "user": 5,
  "book": 12,
  "borrowed_at": "2025-09-01T12:00:00Z",
  "due_at": "2025-09-21T12:00:00Z"
}
```

**POST** `/api/borrowings/{id}/return` — вернуть книгу **сейчас**  
> Тело запроса не требуется; `returned_at` проставится автоматически.

Пример ответа:
```json
{
  "id": 42,
  "user": 5,
  "book": 12,
  "borrowed_at": "2025-09-01T12:00:00Z",
  "due_at": "2025-09-21T12:00:00Z",
  "returned_at": "2025-09-23T10:15:31Z"
}
```

> Если в проекте используется другой маршрут, оставьте только тот, что реализован, и обновите примеры.

---

## Статика на Windows

Предупреждение Django:
```
(staticfiles.W004) The directory '<...>\DiplomLIbrary\static' in STATICFILES_DIRS does not exist.
```
Решение — создать папку `static` или подключить её «умно»:
```python
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_URL = "static/"
STATICFILES_DIRS = [p for p in [BASE_DIR / "static"] if p.exists()]
```

---

---

## Tr Troubleshooting

- **KeyError: 'create-admin'** — обращайтесь к флагу как `options["create_admin"]` или задайте `dest="create_admin"` в `add_arguments`.
- **Naive datetime** — используйте `timezone.now()` и `timezone.make_aware(...)` для «aware» дат.
- **Возврат книги** — эндпоинт возврата не должен принимать `returned_at` из запроса; его ставит сервер.

---

## Лицензия

Проект распространяется по лицензии **MIT**. Добавьте файл `LICENSE` при необходимости.
