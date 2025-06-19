# API для работы со студентами и вакансиями

## Обзор

Добавлена новая сущность `Student` для откликов студентов на вакансии через форму на сайте. Реализован полный функционал согласно ТЗ.

## Модели

### Student
- `id` - ID студента
- `full_name` - ФИО студента
- `birth_date` - Дата рождения
- `speciality` - Специальность/профессия
- `phone` - Контактный номер
- `resume_link` - Ссылка на резюме (опционально)
- `resume_file` - Путь к загруженному файлу резюме (опционально)
- `status` - Статус заявки (new, in_review, invited, rejected)
- `vacancy_id` - ID вакансии

### ApplicationStatus (Enum)
- `NEW` - Новая заявка
- `IN_REVIEW` - В рассмотрении
- `INVITED` - Приглашён
- `REJECTED` - Отказ

### Vacancy (обновлена)
Добавлено поле:
- `contact_person` - Контактное лицо от компании

## Публичные эндпоинты (без авторизации)

### Получение доступных вакансий
```
GET /api/v1/vacancies/public
```

### Получение вакансии по ID
```
GET /api/v1/vacancies/public/{vacancy_id}
```

### Подача заявки на вакансию
```
POST /api/v1/students/apply
```

**Content-Type:** `multipart/form-data`

**Параметры:**
- `full_name` - ФИО (обязательно)
- `birth_date` - Дата рождения в формате YYYY-MM-DD (обязательно)
- `speciality` - Специальность (обязательно)
- `phone` - Телефон (обязательно)
- `resume_link` - Ссылка на резюме (опционально)
- `vacancy_id` - ID вакансии (обязательно)
- `resume_file` - Файл резюме (опционально)

**Варианты предоставления резюме:**
1. **Только ссылка** - заполнить `resume_link`, оставить `resume_file` пустым
2. **Только файл** - загрузить `resume_file`, оставить `resume_link` пустым
3. **И ссылка, и файл** - заполнить оба поля (удобно для работодателя)
4. **Без резюме** - оставить оба поля пустыми (не рекомендуется, но допустимо)

**Поддерживаемые типы файлов резюме:**
- **PDF документы:** PDF (.pdf)
- **Microsoft Office:** Word (.doc, .docx), Excel (.xls, .xlsx), PowerPoint (.ppt, .pptx)
- **Текстовые форматы:** TXT (.txt), RTF (.rtf), HTML (.html, .htm), Markdown (.md)
- **OpenDocument:** Writer (.odt), Calc (.ods), Impress (.odp)

**Максимальный размер файла:** 10MB

**Ответ:**
```json
{
  "id": 1,
  "full_name": "Иванов Иван Иванович",
  "birth_date": "2000-01-01",
  "speciality": "Frontend разработчик",
  "phone": "+7 999 123-45-67",
  "resume_link": "https://github.com/username/resume",
  "resume_file": "/media/resumes/uuid-filename.pdf",
  "status": "new",
  "vacancy_id": 1
}
```

## Эндпоинты для работодателей (требуют авторизации)

### Создание вакансии
```
POST /api/v1/vacancies/
```

**Параметры:**
- `title` - Название вакансии
- `description` - Описание
- `direction` - Направление (IT, маркетинг и т.д.)
- `speciality` - Специальность
- `requirements` - Требования
- `work_format` - Формат работы (очно/удаленно)
- `start` - Дата начала
- `end` - Дата окончания
- `chart` - График работы
- `contact_person` - Контактное лицо
- `required_amount` - Количество требуемых студентов
- `is_hidden` - Скрыть вакансию (по умолчанию false)

### Получение списка вакансий работодателя
```
GET /api/v1/vacancies/
```

### Получение вакансии по ID
```
GET /api/v1/vacancies/{vacancy_id}
```

### Обновление вакансии
```
PUT /api/v1/vacancies/{vacancy_id}
```

### Удаление вакансии
```
DELETE /api/v1/vacancies/{vacancy_id}
```

### Получение статистики вакансии
```
GET /api/v1/vacancies/{vacancy_id}/statistics
```

**Ответ:**
```json
{
  "vacancy_id": 1,
  "total_applications": 10,
  "new_applications": 3,
  "in_review_applications": 4,
  "invited_applications": 2,
  "rejected_applications": 1,
  "conversion_rate": 20.0,
  "required_amount": 5,
  "is_full": false
}
```

### Получение списка заявок студентов
```
GET /api/v1/students/
```

**Параметры:**
- `vacancy_id` - ID вакансии (опционально)
- `status` - Статус заявки (опционально)

### Получение деталей студента
```
GET /api/v1/students/{student_id}
```

### Обновление данных студента
```
PUT /api/v1/students/{student_id}
```

### Массовое обновление статусов
```
POST /api/v1/students/bulk-status-update
```

**Параметры:**
- `student_ids` - Список ID студентов
- `status` - Новый статус

## Права доступа

### Публичные эндпоинты
- Доступны всем без авторизации
- Позволяют просматривать доступные вакансии и подавать заявки

### Эндпоинты работодателей
- Требуют авторизации
- Доступны только пользователям с `is_recruiter = true`
- Работодатели видят только заявки на свои вакансии

### Эндпоинты администраторов
- Требуют авторизации
- Доступны только пользователям с `is_superuser = true`
- Администраторы имеют доступ ко всем данным

## Бизнес-логика

### Подача заявок
1. Проверяется существование вакансии
2. Проверяется что вакансия не скрыта
3. Проверяется что не достигнуто максимальное количество заявок
4. Если загружен файл резюме, он сохраняется в папку `media/resumes/`

### Статистика
- Подсчитывается общее количество заявок
- Заявки группируются по статусам
- Рассчитывается конверсия (приглашенные / общее количество)
- Проверяется заполненность вакансии

### Автоматическое закрытие
- При достижении `required_amount` заявок вакансия считается заполненной
- Дальнейшие заявки отклоняются с соответствующим сообщением

## Файлы

### Загрузка резюме
- Поддерживается загрузка файлов через `multipart/form-data`
- Файлы сохраняются в папку `media/resumes/`
- Путь к файлу сохраняется в поле `resume_file`
- Максимальный размер файла: 10MB

## Примеры использования

### Подача заявки с файлом резюме
```javascript
const formData = new FormData();
formData.append('full_name', 'Иванов Иван Иванович');
formData.append('birth_date', '2000-01-01');
formData.append('speciality', 'Frontend разработчик');
formData.append('phone', '+7 999 123-45-67');
formData.append('vacancy_id', '1');
formData.append('resume_file', fileInput.files[0]);

fetch('/api/v1/students/apply', {
  method: 'POST',
  body: formData
});
```

### Подача заявки со ссылкой на резюме
```javascript
const formData = new FormData();
formData.append('full_name', 'Иванов Иван Иванович');
formData.append('birth_date', '2000-01-01');
formData.append('speciality', 'Frontend разработчик');
formData.append('phone', '+7 999 123-45-67');
formData.append('resume_link', 'https://github.com/username/resume');
formData.append('vacancy_id', '1');

fetch('/api/v1/students/apply', {
  method: 'POST',
  body: formData
});
```

### Подача заявки с файлом и ссылкой
```javascript
const formData = new FormData();
formData.append('full_name', 'Иванов Иван Иванович');
formData.append('birth_date', '2000-01-01');
formData.append('speciality', 'Frontend разработчик');
formData.append('phone', '+7 999 123-45-67');
formData.append('resume_link', 'https://github.com/username/resume');
formData.append('vacancy_id', '1');
formData.append('resume_file', fileInput.files[0]);

fetch('/api/v1/students/apply', {
  method: 'POST',
  body: formData
});
```

### Получение статистики вакансии
```javascript
fetch('/api/v1/vacancies/1/statistics', {
  headers: {
    'Authorization': 'Bearer ' + token
  }
});
```

### Массовое обновление статусов
```javascript
fetch('/api/v1/students/bulk-status-update', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    student_ids: [1, 2, 3],
    status: 'invited'
  })
});
``` 