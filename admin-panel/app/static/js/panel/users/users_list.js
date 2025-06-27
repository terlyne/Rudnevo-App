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