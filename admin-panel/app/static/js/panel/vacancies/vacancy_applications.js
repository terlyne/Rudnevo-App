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


// Скачивание резюме
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.download-resume').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.href;
            // Создаём временный <a> для скачивания
            const a = document.createElement('a');
            a.href = url;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
    });
});

// Функции для работы с заявками на вакансии

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

// Фильтрация заявок по статусу
function filterApplications(status) {
    const applications = document.querySelectorAll('.application-item');
    
    applications.forEach(app => {
        const appStatus = app.getAttribute('data-status');
        if (status === 'all' || appStatus === status) {
            app.style.display = 'block';
        } else {
            app.style.display = 'none';
        }
    });
    
    // Обновляем активную кнопку фильтра
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

// Сортировка заявок
function sortApplications(criteria) {
    const container = document.querySelector('.applications-list');
    const applications = Array.from(container.children);
    
    applications.sort((a, b) => {
        let aValue, bValue;
        
        switch(criteria) {
            case 'date':
                aValue = new Date(a.getAttribute('data-date'));
                bValue = new Date(b.getAttribute('data-date'));
                return bValue - aValue; // Новые сначала
            case 'name':
                aValue = a.querySelector('.student-name').textContent.toLowerCase();
                bValue = b.querySelector('.student-name').textContent.toLowerCase();
                return aValue.localeCompare(bValue);
            case 'status':
                aValue = a.getAttribute('data-status');
                bValue = b.getAttribute('data-status');
                return aValue.localeCompare(bValue);
            default:
                return 0;
        }
    });
    
    // Переставляем элементы
    applications.forEach(app => container.appendChild(app));
}