// Переключение табов
document.querySelectorAll('.tab-item').forEach(tab => {
    tab.addEventListener('click', function () {
        const targetTab = this.dataset.tab;

        // Убираем активный класс у всех табов
        document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

        // Добавляем активный класс к выбранному табу
        this.classList.add('active');
        document.getElementById('tab-' + targetTab).classList.add('active');
    });
});

// Выбрать все
function toggleSelectAll() {
    const selectAll = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.student-checkbox-input');

    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });

    updateBulkButton();
}

// Обновить кнопку массового обновления
function updateBulkButton() {
    const checkboxes = document.querySelectorAll('.student-checkbox-input:checked');
    const updateBtn = document.getElementById('update-status-btn');
    const statusSelect = document.getElementById('bulk-status');

    updateBtn.disabled = checkboxes.length === 0 || !statusSelect.value;
}

// Модальное окно статуса
function showStatusModal(studentId, currentStatus) {
    document.getElementById('modal-student-id').value = studentId;
    document.getElementById('modal-status').value = currentStatus;
    document.getElementById('status-modal').style.display = 'block';
}

function closeStatusModal() {
    document.getElementById('status-modal').style.display = 'none';
}

// Модальное окно деталей студента
function showStudentDetails(studentId) {
    // Здесь можно загрузить детали студента через AJAX
    document.getElementById('student-modal').style.display = 'block';
}

function closeStudentModal() {
    document.getElementById('student-modal').style.display = 'none';
}

// Закрытие модальных окон при клике вне их
window.onclick = function (event) {
    const statusModal = document.getElementById('status-modal');
    const studentModal = document.getElementById('student-modal');

    if (event.target === statusModal) {
        closeStatusModal();
    }
    if (event.target === studentModal) {
        closeStudentModal();
    }
}

// Обработка изменения статуса в массовом обновлении
document.getElementById('bulk-status').addEventListener('change', updateBulkButton);