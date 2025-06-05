# Rudnevo Admin Panel

Административная панель для управления API Rudnevo.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл .env со следующими параметрами:
```
API_BASE_URL=http://localhost:8000
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=changeme
```

## Запуск

```bash
python run.py
```

Приложение будет доступно по адресу http://localhost:5000 