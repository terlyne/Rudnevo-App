// Получаем элементы формы
const startDateInput = document.getElementById('start');
const endDateInput = document.getElementById('end');
const form = document.querySelector('.vacancy-form');

// Установка минимальной даты сегодня
const today = new Date().toISOString().split('T')[0];
startDateInput.min = today;
endDateInput.min = today;

// Функция для показа ошибки
function showDateError(message) {
    // Удаляем предыдущие ошибки
    const existingError = document.querySelector('.date-error');
    if (existingError) {
        existingError.remove();
    }

    // Добавляем класс ошибки к полям
    startDateInput.parentNode.classList.add('has-error');
    endDateInput.parentNode.classList.add('has-error');

    // Создаем элемент ошибки
    const errorDiv = document.createElement('div');
    errorDiv.className = 'date-error';
    errorDiv.textContent = message;

    // Вставляем ошибку после поля даты окончания
    endDateInput.parentNode.appendChild(errorDiv);
}

// Функция для скрытия ошибки
function hideDateError() {
    const existingError = document.querySelector('.date-error');
    if (existingError) {
        existingError.remove();
    }

    // Убираем класс ошибки с полей
    startDateInput.parentNode.classList.remove('has-error');
    endDateInput.parentNode.classList.remove('has-error');
}

// Валидация даты начала
startDateInput.addEventListener('change', function () {
    const startDate = this.value;

    if (startDate) {
        // Устанавливаем минимальную дату для поля "конец" равной дате начала
        endDateInput.min = startDate;

        // Если дата окончания меньше даты начала, сбрасываем её
        if (endDateInput.value && endDateInput.value < startDate) {
            endDateInput.value = startDate;
            showDateError('Дата окончания автоматически установлена равной дате начала');
            setTimeout(hideDateError, 3000); // Скрываем сообщение через 3 секунды
        } else {
            hideDateError();
        }
    }
});

// Валидация даты окончания
endDateInput.addEventListener('change', function () {
    const endDate = this.value;
    const startDate = startDateInput.value;

    if (endDate && startDate) {
        if (endDate < startDate) {
            showDateError('Дата окончания не может быть раньше даты начала');
            this.value = startDate;
        } else {
            hideDateError();
        }
    }
});

// Валидация формы перед отправкой
form.addEventListener('submit', function (e) {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;

    if (startDate && endDate) {
        if (startDate >= endDate) {
            e.preventDefault();
            showDateError('Дата начала должна быть раньше даты окончания');
            return false;
        }
    }

    hideDateError();
});

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    // Если есть значения дат, устанавливаем ограничения
    if (startDateInput.value) {
        endDateInput.min = startDateInput.value;
    }
    if (endDateInput.value) {
        startDateInput.max = endDateInput.value;
    }

    // Проверяем валидность существующих дат
    if (startDateInput.value && endDateInput.value) {
        if (startDateInput.value >= endDateInput.value) {
            showDateError('Дата начала должна быть раньше даты окончания');
        }
    }
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
        'Специалист по обслуживанию мехатронных и роботизированных комплексов',
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

const selectedSpeciality = "{{ vacancy.speciality if vacancy and vacancy.speciality else '' }}";

function updateSpecialities() {
    const direction = directionSelect.value;
    const specs = specialityOptions[direction] || [];
    specialitySelect.innerHTML = '<option value="">Выберите специальность</option>';
    specs.forEach(spec => {
        const option = document.createElement('option');
        option.value = spec;
        option.textContent = spec;
        if (spec === selectedSpeciality) {
            option.selected = true;
        }
        specialitySelect.appendChild(option);
    });
}

directionSelect.addEventListener('change', updateSpecialities);

document.addEventListener('DOMContentLoaded', function () {
    updateSpecialities();
});