let currentScheduleId = null;

// Создание события
function createSchedule() {
    currentScheduleId = null;
    document.getElementById('modalTitle').textContent = 'Создать событие';
    document.getElementById('scheduleForm').reset();
    document.getElementById('scheduleModal').style.display = 'block';
}

// Функции для работы с модальными окнами расписания

function openScheduleModal() {
    document.getElementById('scheduleModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeScheduleModal() {
    document.getElementById('scheduleModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Очищаем форму
    document.getElementById('scheduleForm').reset();
}

function editSchedule(scheduleId) {
    // Здесь можно добавить логику для загрузки данных события в форму
    // Пока просто открываем модальное окно
    openScheduleModal();
    return false; // Предотвращаем отправку формы
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('scheduleModal');
    if (event.target === modal) {
        closeScheduleModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeScheduleModal();
    }
});

// Показать flash сообщение
function showFlashMessage(message, type = 'info') {
    const flashContainer = document.getElementById('flash-messages');
    if (!flashContainer) return;

    const flashDiv = document.createElement('div');
    flashDiv.className = `flash-message flash-${type}`;
    flashDiv.textContent = message;

    flashContainer.appendChild(flashDiv);

    // Автоматически удаляем сообщение через 5 секунд
    setTimeout(() => {
        if (flashDiv.parentNode) {
            flashDiv.parentNode.removeChild(flashDiv);
        }
    }, 5000);
}

// Удаление события
function deleteSchedule(scheduleId) {
    if (confirm('Вы уверены, что хотите удалить это событие? Это действие нельзя отменить.')) {
        fetch(`/schedule/${scheduleId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Ошибка при удалении');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('Ошибка при удалении события', 'error');
        });
    }
}

// Удаление всех шаблонов расписаний
function deleteAllSchedules() {
    if (confirm('Вы уверены, что хотите удалить все расписания? Это действие нельзя отменить.')) {
        fetch('/schedule/delete-all-templates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Ошибка при удалении');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('Ошибка при удалении расписаний', 'error');
        });
    }
}

// Показать расписание колледжа
function showCollegeSchedule(collegeName) {
    // Убираем активный класс у всех кнопок
    document.querySelectorAll('.college-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Добавляем активный класс к нажатой кнопке
    event.target.classList.add('active');
    
    // Показываем загрузку
    const scheduleContent = document.getElementById('schedule-content');
    scheduleContent.innerHTML = '<div class="loading">Загрузка расписания...</div>';
    
    // Загружаем расписание
    fetch(`/schedule/template/${encodeURIComponent(collegeName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.schedule) {
                displayScheduleData(data);
            } else {
                scheduleContent.innerHTML = '<div class="no-data">Данные расписания не найдены</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            scheduleContent.innerHTML = '<div class="error">Ошибка при загрузке расписания</div>';
        });
}

// Отображение данных расписания
function displayScheduleData(data) {
    const scheduleContent = document.getElementById('schedule-content');
    
    let html = '<div class="schedule-data">';
    html += `<h3>${data.college_name}</h3>`;
    html += `<p class="last-updated">Обновлено: ${new Date(data.last_updated).toLocaleString()}</p>`;
    
    if (data.schedule && Object.keys(data.schedule).length > 0) {
        html += '<div class="schedule-table">';
        html += '<table>';
        
        // Заголовки
        const firstEntry = Object.values(data.schedule)[0];
        if (firstEntry && typeof firstEntry === 'object') {
            html += '<thead><tr>';
            html += '<th>Время/Группа</th>';
            Object.keys(firstEntry).forEach(day => {
                html += `<th>${day}</th>`;
            });
            html += '</tr></thead>';
        }
        
        // Данные
        html += '<tbody>';
        Object.entries(data.schedule).forEach(([time, dayData]) => {
            html += '<tr>';
            html += `<td><strong>${time}</strong></td>`;
            if (typeof dayData === 'object') {
                Object.values(dayData).forEach(value => {
                    html += `<td>${value || '-'}</td>`;
                });
            } else {
                html += `<td>${dayData || '-'}</td>`;
            }
            html += '</tr>';
        });
        html += '</tbody>';
        html += '</table>';
        html += '</div>';
    } else {
        html += '<div class="no-data">Данные расписания пусты</div>';
    }
    
    html += '</div>';
    scheduleContent.innerHTML = html;
}

// Автоматически открываем первый колледж при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const firstCollegeBtn = document.querySelector('.college-btn');
    if (firstCollegeBtn) {
        firstCollegeBtn.click();
    }
});

// Обработка отправки формы
document.getElementById('scheduleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        title: document.getElementById('title').value.trim(),
        date: document.getElementById('date').value,
        time: document.getElementById('time').value || null,
        location: document.getElementById('location').value.trim() || null,
        description: document.getElementById('description').value.trim() || null
    };
    
    if (!formData.title || !formData.date) {
        showFlashMessage('Заполните обязательные поля', 'error');
        return;
    }
    
    const url = currentScheduleId ? `/schedule/${currentScheduleId}/edit` : '/schedule/create';
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (response.ok) {
            closeScheduleModal();
            location.reload();
        } else {
            return response.json().then(data => {
                throw new Error(data.message || 'Ошибка при сохранении события');
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage(error.message, 'error');
    });
}); 