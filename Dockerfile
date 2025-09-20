FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

# Copy only lock/pyproject for better caching
COPY pyproject.toml /app/

# Install dependencies (no project code yet for caching)
RUN poetry install --no-interaction --no-ansi --only main

# Copy project files
COPY . /app/

# Migrate on container start
RUN chmod +x docker/web/entrypoint.sh
ENTRYPOINT ["docker/web/entrypoint.sh"]