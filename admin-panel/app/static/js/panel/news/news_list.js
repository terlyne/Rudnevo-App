let currentNewsId = null;

// Функции для работы с модальными окнами новостей

function createNews() {
    document.getElementById('modalTitle').textContent = 'Создать новость';
    document.getElementById('newsForm').reset();
    currentNewsId = null;
    document.getElementById('newsForm').setAttribute('action', '/news/create');
    
    // Сбрасываем состояние изображения
    const imageInput = document.getElementById('image');
    const preview = document.getElementById('imagePreview');
    const removeBtn = document.getElementById('removeImageBtn');
    
    imageInput.style.display = 'block';
    preview.style.display = 'none';
    removeBtn.style.display = 'none';
    
    openNewsModal();
}

function openNewsModal() {
    document.getElementById('newsModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeNewsModal() {
    document.getElementById('newsModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    document.getElementById('newsForm').reset();
    currentNewsId = null;
    document.getElementById('newsForm').setAttribute('action', '/news/create');
}

function editNews(newsId) {
    fetch(`/news/${newsId}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('modalTitle').textContent = 'Редактировать новость';
            document.getElementById('title').value = data.title || '';
            document.getElementById('content').value = data.content || '';
            document.getElementById('is_hidden').checked = !!data.is_hidden;
            currentNewsId = newsId;
            document.getElementById('newsForm').setAttribute('action', `/news/${newsId}/edit`);
            // Показываем превью изображения, если есть, и скрываем input file
            const imagePreview = document.getElementById('imagePreview');
            const removeImageBtn = document.getElementById('removeImageBtn');
            const imageInput = document.getElementById('image');
            if (data.image_url) {
                imagePreview.src = `/news/${newsId}/image`;
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
            openNewsModal();
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
            document.getElementById('newsForm').appendChild(removeField);
        }
        removeField.value = 'true';
    }
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('newsModal');
    if (event.target === modal) {
        closeNewsModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeNewsModal();
    }
});

// Удаление новости
function deleteNews(newsId) {
    if (confirm('Вы уверены, что хотите удалить эту новость? Это действие нельзя отменить.')) {
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        fetch(`/news/${newsId}/delete`, {
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
            showFlashMessage('Ошибка при удалении новости', 'error');
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