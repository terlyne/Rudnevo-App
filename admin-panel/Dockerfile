FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

COPY app ./app

EXPOSE 5000

CMD ["flask", "--app", "app.run", "run", "--host=0.0.0.0", "--port=5000"]