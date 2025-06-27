let currentFeedbackId = null;

// Функции для работы с модальными окнами вопросов

function openResponseModal() {
    document.getElementById('responseModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeResponseModal() {
    document.getElementById('responseModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Очищаем форму
    document.getElementById('responseForm').reset();
}

function respondToFeedback(feedbackId) {
    currentFeedbackId = feedbackId;
    // Устанавливаем правильный action для формы
    document.getElementById('responseForm').action = `/feedback/${feedbackId}/respond`;
    openResponseModal();
    return false; // Предотвращаем отправку формы
}

// Закрытие модального окна при клике вне его
window.onclick = function (event) {
    const modal = document.getElementById('responseModal');
    if (event.target === modal) {
        closeResponseModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        closeResponseModal();
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

// Блокировка кнопки 'Отправить ответ' при отправке формы
const responseForm = document.getElementById('responseForm');
if (responseForm) {
    responseForm.addEventListener('submit', function() {
        const submitBtn = responseForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
        }
    });
} 