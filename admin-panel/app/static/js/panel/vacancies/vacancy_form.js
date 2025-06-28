// Получаем элементы формы
const startDateInput = document.getElementById('start');
const endDateInput = document.getElementById('end');
const form = document.querySelector('.vacancy-form');

// Элементы для переключения типа объявления
const internshipRadios = document.querySelectorAll('input[name="is_internship"]');
const vacancyFields = document.querySelector('.vacancy-fields');
const internshipFields = document.querySelector('.internship-fields');

// Элементы для зарплаты
const salaryFromInput = document.getElementById('salary_from');
const salaryToInput = document.getElementById('salary_to');

// Установка минимальной даты сегодня
const today = new Date().toISOString().split('T')[0];
if (startDateInput) startDateInput.min = today;
if (endDateInput) endDateInput.min = today;

// Функция для показа ошибки
function showDateError(message) {
    // Удаляем предыдущие ошибки
    const existingError = document.querySelector('.date-error');
    if (existingError) {
        existingError.remove();
    }

    // Добавляем класс ошибки к полям
    if (startDateInput) startDateInput.parentNode.classList.add('has-error');
    if (endDateInput) endDateInput.parentNode.classList.add('has-error');

    // Создаем элемент ошибки
    const errorDiv = document.createElement('div');
    errorDiv.className = 'date-error';
    errorDiv.textContent = message;

    // Вставляем ошибку после поля даты окончания
    if (endDateInput) {
        endDateInput.parentNode.appendChild(errorDiv);
    }
}

// Функция для скрытия ошибки
function hideDateError() {
    const existingError = document.querySelector('.date-error');
    if (existingError) {
        existingError.remove();
    }

    // Убираем класс ошибки с полей
    if (startDateInput) startDateInput.parentNode.classList.remove('has-error');
    if (endDateInput) endDateInput.parentNode.classList.remove('has-error');
}

// Функция для показа ошибки зарплаты
function showSalaryError(message) {
    // Удаляем предыдущие ошибки
    const existingError = document.querySelector('.salary-error');
    if (existingError) {
        existingError.remove();
    }

    // Добавляем класс ошибки к полям
    if (salaryFromInput) salaryFromInput.parentNode.classList.add('has-error');
    if (salaryToInput) salaryToInput.parentNode.classList.add('has-error');

    // Создаем элемент ошибки
    const errorDiv = document.createElement('div');
    errorDiv.className = 'salary-error';
    errorDiv.style.color = '#e74c3c';
    errorDiv.style.fontSize = '12px';
    errorDiv.style.marginTop = '5px';
    errorDiv.textContent = message;

    // Вставляем ошибку после поля зарплаты до
    if (salaryToInput) {
        salaryToInput.parentNode.appendChild(errorDiv);
    }
}

// Функция для скрытия ошибки зарплаты
function hideSalaryError() {
    const existingError = document.querySelector('.salary-error');
    if (existingError) {
        existingError.remove();
    }

    // Убираем класс ошибки с полей
    if (salaryFromInput) salaryFromInput.parentNode.classList.remove('has-error');
    if (salaryToInput) salaryToInput.parentNode.classList.remove('has-error');
}

// Функция переключения между вакансией и стажировкой
function toggleVacancyType() {
    const isInternship = document.querySelector('input[name="is_internship"]:checked').value === 'true';
    
    if (isInternship) {
        // Показываем поля для стажировки, скрываем поля для вакансии
        if (internshipFields) internshipFields.style.display = 'grid';
        if (vacancyFields) vacancyFields.style.display = 'none';
        
        // Убираем required с полей зарплаты
        if (salaryFromInput) salaryFromInput.removeAttribute('required');
        if (salaryToInput) salaryToInput.removeAttribute('required');
        
        // Добавляем required к полям дат (если они заполнены)
        if (startDateInput && startDateInput.value) startDateInput.setAttribute('required', 'required');
        if (endDateInput && endDateInput.value) endDateInput.setAttribute('required', 'required');
    } else {
        // Показываем поля для вакансии, скрываем поля для стажировки
        if (vacancyFields) vacancyFields.style.display = 'grid';
        if (internshipFields) internshipFields.style.display = 'none';
        
        // Убираем required с полей дат
        if (startDateInput) startDateInput.removeAttribute('required');
        if (endDateInput) endDateInput.removeAttribute('required');
        
        // Поля зарплаты остаются необязательными
        if (salaryFromInput) salaryFromInput.removeAttribute('required');
        if (salaryToInput) salaryToInput.removeAttribute('required');
    }
}

// Обработчики для радио-кнопок
internshipRadios.forEach(radio => {
    radio.addEventListener('change', toggleVacancyType);
});

// Валидация даты начала
if (startDateInput) {
    startDateInput.addEventListener('change', function () {
        const startDate = this.value;

        if (startDate) {
            // Устанавливаем минимальную дату для поля "конец" равной дате начала
            if (endDateInput) endDateInput.min = startDate;

            // Если дата окончания меньше даты начала, сбрасываем её
            if (endDateInput && endDateInput.value && endDateInput.value < startDate) {
                endDateInput.value = startDate;
                showDateError('Дата окончания автоматически установлена равной дате начала');
                setTimeout(hideDateError, 3000); // Скрываем сообщение через 3 секунды
            } else {
                hideDateError();
            }
        }
    });
}

// Валидация даты окончания
if (endDateInput) {
    endDateInput.addEventListener('change', function () {
        const endDate = this.value;
        const startDate = startDateInput ? startDateInput.value : '';

        if (endDate && startDate) {
            if (endDate < startDate) {
                showDateError('Дата окончания не может быть раньше даты начала');
                this.value = startDate;
            } else {
                hideDateError();
            }
        }
    });
}

// Валидация зарплаты
if (salaryFromInput) {
    salaryFromInput.addEventListener('change', function() {
        const salaryFrom = parseInt(this.value) || 0;
        const salaryTo = parseInt(salaryToInput ? salaryToInput.value : 0) || 0;
        
        if (salaryTo > 0 && salaryFrom > salaryTo) {
            showSalaryError('Зарплата "от" не может быть больше зарплаты "до"');
        } else {
            hideSalaryError();
        }
    });
}

if (salaryToInput) {
    salaryToInput.addEventListener('change', function() {
        const salaryFrom = parseInt(salaryFromInput ? salaryFromInput.value : 0) || 0;
        const salaryTo = parseInt(this.value) || 0;
        
        if (salaryFrom > 0 && salaryTo > 0 && salaryFrom > salaryTo) {
            showSalaryError('Зарплата "до" не может быть меньше зарплаты "от"');
        } else {
            hideSalaryError();
        }
    });
}

// Валидация формы перед отправкой
form.addEventListener('submit', function (e) {
    const isInternship = document.querySelector('input[name="is_internship"]:checked').value === 'true';
    
    // Валидация дат для стажировки
    if (isInternship && startDateInput && endDateInput) {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        if (startDate && endDate) {
            if (startDate >= endDate) {
                e.preventDefault();
                showDateError('Дата начала должна быть раньше даты окончания');
                return false;
            }
        }
    }
    
    // Валидация зарплаты для вакансии
    if (!isInternship && salaryFromInput && salaryToInput) {
        const salaryFrom = parseInt(salaryFromInput.value) || 0;
        const salaryTo = parseInt(salaryToInput.value) || 0;
        
        if (salaryFrom > 0 && salaryTo > 0 && salaryFrom > salaryTo) {
            e.preventDefault();
            showSalaryError('Зарплата "от" не может быть больше зарплаты "до"');
            return false;
        }
    }

    hideDateError();
    hideSalaryError();
});

// Данные по направлениям и специальностям
const specialityOptions = {
    'Электроника': [
        'Монтажник радиоэлектронной аппаратуры и приборов',
        'Слесарь-сборщик радиоэлектронной аппаратуры и приборов',
        'Регулировщик радиоэлектронной аппаратуры и приборов',
        'Слесарь-сборщик радиоэлектронной аппаратуры и приборов'
    ],
    'Машиностроение': [
        'Слесарь механосборочных работ',
        'Токарь',
        'Фрезеровщик',
        'Оператор станков с ПУ',
        'Станочник широкого профиля',
        'Сварщик (ручной и частично механизированной сварки (наплавки))',
        'Наладчик станков и оборудования в механообработке',
        'Специалист ОТК'
    ],
    'Автоматизация производства': [
        'Специалист по обслуживанию механотронных и роботизированных комплексов',
        'Слесарь контрольно-измерительных приборов и автоматики',
        'Специалист по аддитивным технологиям'
    ],
    'Авиационная промышленность и беспилотные авиационные системы': [
        'Монтажник электрооборудования летательных аппаратов',
        'Слесарь-сборщик авиационной техники',
        'Слесарь-сборщик авиационных изделий из композитных материалов',
        'Оператор беспилотных авиационных систем до 30 кг'
    ]
};

const directionSelect = document.getElementById('direction');
const specialitySelect = document.getElementById('speciality');

// Получаем значения из вакансии (если редактируем)
const selectedSpeciality = "{{ vacancy.speciality if vacancy and vacancy.speciality else '' }}";
const selectedDirection = "{{ vacancy.direction if vacancy and vacancy.direction else '' }}";

console.log('Raw selectedSpeciality:', selectedSpeciality);
console.log('Raw selectedDirection:', selectedDirection);

function updateSpecialities() {
    const direction = directionSelect.value;
    const specs = specialityOptions[direction] || [];
    
    console.log('Updating specialities for direction:', direction);
    console.log('Available specs:', specs);
    console.log('Selected speciality:', selectedSpeciality);
    
    // Сохраняем текущее выбранное значение
    const currentValue = specialitySelect.value;
    
    specialitySelect.innerHTML = '<option value="">Выберите специальность</option>';
    
    specs.forEach(spec => {
        const option = document.createElement('option');
        option.value = spec;
        option.textContent = spec;
        
        // Сравниваем специальности (без учета регистра и пробелов)
        const normalizedSpec = spec.trim().toLowerCase();
        const normalizedSelected = selectedSpeciality.trim().toLowerCase();
        const normalizedCurrent = currentValue.trim().toLowerCase();
        
        // Выбираем опцию, если она совпадает с сохраненным значением или с значением из вакансии
        if (normalizedSpec === normalizedSelected || normalizedSpec === normalizedCurrent) {
            option.selected = true;
            console.log('Found matching speciality:', spec);
        }
        
        specialitySelect.appendChild(option);
    });
}

// Обработчик изменения направления
if (directionSelect) {
    directionSelect.addEventListener('change', updateSpecialities);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded');
    console.log('Initial direction value:', directionSelect ? directionSelect.value : 'N/A');
    console.log('Selected direction from vacancy:', selectedDirection);
    console.log('Selected speciality from vacancy:', selectedSpeciality);
    
    // Инициализируем переключение типа объявления
    toggleVacancyType();
    
    // Если есть значения дат, устанавливаем ограничения
    if (startDateInput && startDateInput.value) {
        if (endDateInput) endDateInput.min = startDateInput.value;
    }
    if (endDateInput && endDateInput.value) {
        if (startDateInput) startDateInput.max = endDateInput.value;
    }

    // Проверяем валидность существующих дат
    if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
        if (startDateInput.value >= endDateInput.value) {
            showDateError('Дата начала должна быть раньше даты окончания');
        }
    }
    
    // Проверяем валидность существующей зарплаты
    if (salaryFromInput && salaryToInput && salaryFromInput.value && salaryToInput.value) {
        const salaryFrom = parseInt(salaryFromInput.value) || 0;
        const salaryTo = parseInt(salaryToInput.value) || 0;
        
        if (salaryFrom > salaryTo) {
            showSalaryError('Зарплата "от" не может быть больше зарплаты "до"');
        }
    }
    
    // Инициализируем специальности
    updateSpecialities();
});