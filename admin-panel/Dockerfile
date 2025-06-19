FROM python:3.11-slim

WORKDIR /app

COPY admin-panel/pyproject.toml admin-panel/poetry.lock ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

COPY admin-panel/app ./app

EXPOSE 5000

CMD ["flask", "--app", "app.run", "run", "--host=0.0.0.0", "--port=5000"]