// Функции для работы с модальными окнами пользователей

function openUserModal() {
    document.getElementById('userModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeUserModal() {
    document.getElementById('userModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Очищаем форму
    document.getElementById('userForm').reset();
}

function openInviteModal() {
    document.getElementById('inviteModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeInviteModal() {
    document.getElementById('inviteModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Очищаем форму
    document.getElementById('inviteForm').reset();
}

function editUser(userId) {
    // Здесь можно добавить логику для загрузки данных пользователя в форму
    // Пока просто открываем модальное окно
    openUserModal();
    return false; // Предотвращаем отправку формы
}

function resendInvite(email) {
    if (confirm('Повторно отправить приглашение на ' + email + '?')) {
        console.log('Повторная отправка приглашения на:', email);
        
        fetch('/users/resend-invite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify({
                email: email
            })
        })
        .then(response => {
            console.log('Ответ сервера (resend):', response.status, response.statusText);
            console.log('Редирект (resend):', response.redirected);
            console.log('URL (resend):', response.url);
            
            // Если есть редирект, переходим на новую страницу для отображения flash сообщения
            if (response.redirected || response.status === 302) {
                console.log('Обнаружен редирект (resend), переходим на:', response.url);
                window.location.href = response.url;
                return;
            }
            
            // Если нет редиректа, проверяем ответ
            return response.json();
        })
        .then(data => {
            if (data) {
                console.log('Данные ответа (resend):', data);
                // Если получили JSON ответ, значит что-то пошло не так
                alert('Ошибка: ' + (data.detail || data.message || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('Ошибка при повторной отправке приглашения:', error);
            alert('Ошибка при повторной отправке приглашения: ' + error.message);
        });
    }
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const userModal = document.getElementById('userModal');
    const inviteModal = document.getElementById('inviteModal');
    if (event.target === userModal) {
        closeUserModal();
    }
    if (event.target === inviteModal) {
        closeInviteModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeUserModal();
        closeInviteModal();
    }
});

// Обработка отправки формы приглашения
document.addEventListener('DOMContentLoaded', function() {
    const inviteForm = document.getElementById('inviteForm');
    if (inviteForm) {
        inviteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitButton = inviteForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;
            
            // Блокируем кнопку
            submitButton.disabled = true;
            submitButton.textContent = 'Отправка...';
            
            const formData = new FormData(inviteForm);
            const email = formData.get('email');
            const isRecruiter = formData.get('is_recruiter') === 'on';
            
            console.log('Отправка приглашения на:', email, 'is_recruiter:', isRecruiter);
            
            fetch('/users/invite', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify({
                    email: email,
                    is_recruiter: isRecruiter
                })
            })
            .then(response => {
                console.log('Ответ сервера:', response.status, response.statusText);
                console.log('Редирект:', response.redirected);
                console.log('URL:', response.url);
                
                // Если есть редирект, переходим на новую страницу для отображения flash сообщения
                if (response.redirected || response.status === 302) {
                    console.log('Обнаружен редирект, переходим на:', response.url);
                    window.location.href = response.url;
                    return;
                }
                
                // Если нет редиректа, проверяем ответ
                return response.json();
            })
            .then(data => {
                if (data) {
                    console.log('Данные ответа:', data);
                    // Если получили JSON ответ, значит что-то пошло не так
                    alert('Ошибка: ' + (data.detail || data.message || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке приглашения:', error);
                alert('Ошибка при отправке приглашения: ' + error.message);
            })
            .finally(() => {
                // Восстанавливаем кнопку
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
        });
    }
    
    // Проверяем наличие flash сообщений при загрузке страницы
    const flashMessages = document.querySelectorAll('.flash');
    console.log('Найдено flash сообщений при загрузке:', flashMessages.length);
    flashMessages.forEach((msg, index) => {
        const isError = msg.querySelector('.error') !== null;
        const isSuccess = msg.querySelector('.success') !== null;
        console.log(`Flash сообщение ${index + 1}:`, { isError, isSuccess, text: msg.textContent });
    });
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