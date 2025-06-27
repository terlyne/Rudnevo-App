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