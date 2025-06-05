FROM python:3.10-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY pyproject.toml README.md ./

# Копирование кода приложения
COPY . .

# Создание директорий для медиафайлов
RUN mkdir -p media/news

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Установка переменных окружения
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Запуск приложения
CMD ["uvicorn", "app.run:app", "--host", "0.0.0.0", "--port", "8000"] 