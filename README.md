Инструкции по установке и запуску проекта
Локальная установка (без Docker)
Клонировать репозиторий: git clone https://github.com/MyachinRoma/DiplomLIbrary.git
Перейти в папку проекта: DiplomLIbrary
Установить зависимости: из requirements.txt
Создайте файл .env в корневой папке проекта и заполните его по шаблону .env.sample переменными:
SECRET_KEY: секретный ключ проекта (например, случайная строка из 50 символов)
NAME: имя базы данных
DBUSER: имя пользователя базы данных
PASSWORD: пароль пользователя базы данных
HOST: адрес хоста базы данных (например, localhost)
PORT: порт базы данных (например, 5432)
Создать базу данных: python manage.py migrate
Запустить сервер: python manage.py runserver
Запуск через Docker Compose
Клонировать репозиторий: git clone https://github.com/MyachinRoma/DiplomLIbrary.git
Перейти в папку проекта: DiplomLIbrary
Создать файл .env на основе .env.sample
Запустить проект: docker-compose up -d --build
Проект будет доступен по адресу: http://localhost:8000
Проверка работоспособности сервисов
Django-приложение (web):

Откройте в браузере: http://localhost:8000
Проверка логов: docker-compose logs web
PostgreSQL (db):

Проверить подключение: docker-compose exec db psql -U postgres -d drf
Проверка логов: docker-compose logs db

Проверить работу: docker-compose exec redis redis-cli ping (должен ответить "PONG")
Проверка логов: docker-compose logs redis

Для остановки всех сервисов выполните: docker-compose down

Для полной очистки (с удалением volumes): docker-compose down -v