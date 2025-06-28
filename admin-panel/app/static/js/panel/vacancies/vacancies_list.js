// Функции для работы с модальными окнами вакансий

function openVacancyModal() {
    document.getElementById('vacancyModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeVacancyModal() {
    document.getElementById('vacancyModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    // Очищаем форму
    document.getElementById('vacancyForm').reset();
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('vacancyModal');
    if (event.target === modal) {
        closeVacancyModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeVacancyModal();
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

function deleteVacancy(vacancyId) {
    if (confirm('Вы уверены, что хотите удалить эту вакансию?')) {
        const form = document.getElementById('delete-form');
        form.action = `/vacancies/${vacancyId}/delete`;
        form.submit();
    }
}