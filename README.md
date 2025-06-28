# Rudnevo App - Обновление вакансий

## Описание изменений

Добавлены новые поля для вакансий и стажировок:

### Новые поля в модели Vacancy:
- `salary_from` (int, optional) - Зарплата от
- `salary_to` (int, optional) - Зарплата до  
- `address` (text, optional) - Адрес
- `city` (varchar(100), optional) - Город
- `metro_station` (varchar(100), optional) - Станция метро
- `is_internship` (boolean, default=False) - Флаг стажировки
- `company_name` (varchar(200)) - Название компании

### Изменения в существующих полях:
- `start` и `end` теперь опциональные (nullable)
- `contact_person` теперь содержит только информацию о контактном лице

## Установка и настройка

### 1. Обновление базы данных

Выполните SQL-скрипт для добавления новых полей:

```bash
# Для PostgreSQL
psql -d your_database_name -f backend/migration_vacancy_fields.sql

# Или выполните SQL-команды вручную в вашей БД
```

### 2. Запуск приложения

```bash
# Backend
cd backend
poetry install
poetry run python -m app.run

# Admin Panel  
cd admin-panel
poetry install
poetry run python -m app.run
```

## Новый функционал

### Форма создания/редактирования вакансий

1. **Переключатель типа объявления**: Вакансия / Стажировка
2. **Для вакансий**: Поля зарплаты (от/до)
3. **Для стажировок**: Поля дат (начало/конец) - опциональные
4. **Общие поля**: Адрес, город, станция метро
5. **Контактная информация**: Отдельные поля для названия компании и контактного лица

### Flash-сообщения

- Success сообщения автоматически скрываются
- Error сообщения показываются 7 секунд с кнопкой закрытия
- Фиксированная ширина сообщений (400px)
- Плавная анимация появления

### Валидация

- Зарплата "от" не может быть больше зарплаты "до"
- Даты начала и окончания для стажировок
- Все новые поля опциональные

### Стилизация

- Все формы и элементы соответствуют единому стилю проекта
- Современный дизайн с использованием Montserrat шрифта
- Адаптивная верстка для мобильных устройств
- Улучшенные стили для заявок в вакансиях

## Структура изменений

### Backend
- `app/models/vacancy.py` - Обновлена модель с новыми полями
- `app/schemas/vacancy.py` - Обновлены схемы Pydantic
- `migration_vacancy_fields.sql` - SQL-миграция

### Admin Panel
- `app/templates/panel/vacancies/vacancy_form.html` - Обновлена форма с разделением полей
- `app/static/css/panel/vacancies/vacancy_form.css` - Стили формы
- `app/static/js/panel/vacancies/vacancy_form.js` - JavaScript логика
- `app/routes/panel.py` - Обновлены маршруты
- `app/static/js/flash.js` - Обновлены flash-сообщения
- `app/static/css/reset.css` - Стили flash-сообщений
- `app/templates/panel/vacancies/vacancies_list.html` - Список с новыми полями
- `app/static/css/panel/vacancies/vacancies_list.css` - Стили списка
- `app/static/css/panel/vacancies/vacancy_applications.css` - Стили заявок

## Тестирование

1. Создайте новую вакансию с зарплатой и названием компании
2. Создайте новую стажировку с датами
3. Проверьте валидацию полей
4. Проверьте flash-сообщения (success скрываются, error показываются 7 сек)
5. Проверьте отображение в списке вакансий
6. Проверьте стилизацию заявок в вакансиях 