FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY backend/pyproject.toml backend/poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Копируем код приложения
COPY backend/app ./app

# Создаем директорию для медиафайлов
RUN mkdir -p /app/media

# Открываем порт
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.run:app", "--host", "0.0.0.0", "--port", "8000"]