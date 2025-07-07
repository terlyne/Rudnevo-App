let currentCollegeId = null;

// Функции для работы с модальными окнами колледжей

function createCollege() {
    document.getElementById('modalTitle').textContent = 'Создать колледж';
    document.getElementById('collegeForm').reset();
    currentCollegeId = null;
    document.getElementById('collegeForm').setAttribute('action', '/colleges/create');
    
    // Сбрасываем состояние изображения
    const imageInput = document.getElementById('image');
    const preview = document.getElementById('imagePreview');
    const removeBtn = document.getElementById('removeImageBtn');
    
    imageInput.style.display = 'block';
    preview.style.display = 'none';
    removeBtn.style.display = 'none';
    
    openCollegeModal();
}

function openCollegeModal() {
    document.getElementById('collegeModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeCollegeModal() {
    document.getElementById('collegeModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    document.getElementById('collegeForm').reset();
    currentCollegeId = null;
    document.getElementById('collegeForm').setAttribute('action', '/colleges/create');
}

function editCollege(collegeId, collegeName) {
    fetch(`/colleges/${collegeId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('modalTitle').textContent = 'Редактировать колледж';
            document.getElementById('name').value = data.name || '';
            currentCollegeId = collegeId;
            document.getElementById('collegeForm').setAttribute('action', `/colleges/${collegeId}/edit`);
            
            // Показываем превью изображения, если есть, и скрываем input file
            const imagePreview = document.getElementById('imagePreview');
            const removeImageBtn = document.getElementById('removeImageBtn');
            const imageInput = document.getElementById('image');
            
            if (data.image_url) {
                imagePreview.src = `/colleges/${collegeId}/image`;
                imagePreview.style.display = 'block';
                removeImageBtn.style.display = 'inline-block';
                imageInput.style.display = 'none';
            } else {
                imagePreview.style.display = 'none';
                removeImageBtn.style.display = 'none';
                imageInput.style.display = 'block';
            }
            
            // Удаляем скрытое поле remove_image если оно было
            let removeField = document.getElementById('remove_image');
            if (removeField) removeField.remove();
            
            openCollegeModal();
        });
    return false;
}

// Обработчик для изображения при выборе файла
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    const removeBtn = document.getElementById('removeImageBtn');
                    
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    removeBtn.style.display = 'inline-block';
                    
                    // Скрываем кнопку "Выбрать файл"
                    imageInput.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

// Кнопка удаления изображения
if (document.getElementById('removeImageBtn')) {
    document.getElementById('removeImageBtn').onclick = function() {
        const imageInput = document.getElementById('image');
        imageInput.value = '';
        this.style.display = 'none';
        document.getElementById('imagePreview').style.display = 'none';
        imageInput.style.display = 'block';
        // Добавляем скрытое поле для передачи remove_image
        let removeField = document.getElementById('remove_image');
        if (!removeField) {
            removeField = document.createElement('input');
            removeField.type = 'hidden';
            removeField.name = 'remove_image';
            removeField.id = 'remove_image';
            document.getElementById('collegeForm').appendChild(removeField);
        }
        removeField.value = 'true';
    }
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('collegeModal');
    if (event.target === modal) {
        closeCollegeModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeCollegeModal();
    }
});

// Удаление колледжа
function deleteCollege(collegeId, collegeName) {
    if (confirm('Вы уверены, что хотите удалить этот колледж? Это действие нельзя отменить.')) {
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        fetch(`/colleges/${collegeId}/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
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
            alert('Ошибка при удалении колледжа');
        });
    }
}

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