FROM python:3.9.22-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /rudnevo-backend

RUN pip install --upgrade pip wheel "poetry==2.1.2"

RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./

RUN poetry install --no-root

COPY app app

COPY .env ./

CMD ["python", "app/main.py"]