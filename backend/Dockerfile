FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Копируем код приложения
COPY app ./app

# Создаем директории для медиафайлов и шаблонов
RUN mkdir -p /app/media /app/templates /app/temp_uploads

RUN printenv

# Открываем порт
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "app.run:app", "--host", "0.0.0.0", "--port", "8000"]