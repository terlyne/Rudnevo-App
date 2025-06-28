-- Миграция для добавления новых полей в таблицу вакансий
-- Выполните этот скрипт в вашей базе данных

-- Добавляем новые поля для вакансий
ALTER TABLE vacancies 
ADD COLUMN salary_from INTEGER,
ADD COLUMN salary_to INTEGER,
ADD COLUMN address TEXT,
ADD COLUMN city VARCHAR(100),
ADD COLUMN metro_station VARCHAR(100),
ADD COLUMN is_internship BOOLEAN DEFAULT FALSE,
ADD COLUMN company_name VARCHAR(200);

-- Делаем поля start и end опциональными (если они еще не nullable)
ALTER TABLE vacancies 
ALTER COLUMN start DROP NOT NULL,
ALTER COLUMN end DROP NOT NULL;

-- Добавляем комментарии к полям
COMMENT ON COLUMN vacancies.salary_from IS 'Зарплата от (в рублях)';
COMMENT ON COLUMN vacancies.salary_to IS 'Зарплата до (в рублях)';
COMMENT ON COLUMN vacancies.address IS 'Полный адрес места работы';
COMMENT ON COLUMN vacancies.city IS 'Город';
COMMENT ON COLUMN vacancies.metro_station IS 'Станция метро';
COMMENT ON COLUMN vacancies.is_internship IS 'Флаг стажировки (true - стажировка, false - вакансия)';
COMMENT ON COLUMN vacancies.company_name IS 'Название компании'; 