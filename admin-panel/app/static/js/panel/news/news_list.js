let currentNewsId = null;

// Функции для работы с модальными окнами новостей

function createNews() {
    document.getElementById('modalTitle').textContent = 'Создать новость';
    document.getElementById('newsForm').reset();
    currentNewsId = null;
    document.getElementById('newsForm').setAttribute('action', '/news/create');
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

// Функция для скрытия скрытых новостей для обычных пользователей
function hideHiddenNews() {
    const container = document.querySelector('.news-container');
    const isSuperuser = container && container.dataset.isSuperuser === 'true';
    const showHidden = document.getElementById('showHidden');
    const showHiddenChecked = showHidden ? showHidden.checked : false;
    
    if (!isSuperuser && !showHiddenChecked) {
        const hiddenCards = document.querySelectorAll('.news-card.hidden');
        hiddenCards.forEach(card => {
            card.style.display = 'none';
        });
    } else if (isSuperuser && showHiddenChecked) {
        // Показываем все новости, если фильтр включен
        const hiddenCards = document.querySelectorAll('.news-card.hidden');
        hiddenCards.forEach(card => {
            card.style.display = 'flex';
        });
    }
    
    // Обновляем состояние видимости и счетчики
    updateNewsVisibility();
}

// Переключение отображения скрытых новостей
function toggleHiddenNews() {
    const showHidden = document.getElementById('showHidden').checked;
    const hiddenCards = document.querySelectorAll('.news-card.hidden');
    
    hiddenCards.forEach(card => {
        if (showHidden) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
    
    // Обновляем URL без перезагрузки страницы
    const url = new URL(window.location);
    if (showHidden) {
        url.searchParams.set('show_hidden', 'true');
    } else {
        url.searchParams.delete('show_hidden');
    }
    window.history.replaceState({}, '', url);
    
    // Обновляем все ссылки на странице
    updateAllLinks(showHidden);
    
    // Обновляем состояние "нет новостей" и счетчики
    updateNewsVisibility();
}

// Функция для обновления состояния видимости новостей и счетчиков
function updateNewsVisibility() {
    const newsCards = document.querySelectorAll('.news-card');
    const noNewsElement = document.querySelector('.no-news');
    const statsNumbers = document.querySelectorAll('.stat-number');
    
    let visibleCount = 0;
    let totalCount = 0;
    let approvedCount = 0;
    let hiddenCount = 0;
    
    newsCards.forEach(card => {
        totalCount++;
        
        // Проверяем, видим ли элемент (не скрыт через display: none)
        const isVisible = card.style.display !== 'none' && 
                         getComputedStyle(card).display !== 'none' &&
                         card.offsetParent !== null;
        
        if (isVisible) {
            visibleCount++;
        }
        
        if (card.classList.contains('hidden')) {
            hiddenCount++;
        } else {
            approvedCount++;
        }
    });
    
    // Обновляем счетчики
    if (statsNumbers.length >= 3) {
        statsNumbers[0].textContent = totalCount; // Всего новостей
        statsNumbers[1].textContent = approvedCount; // Опубликованных
        statsNumbers[2].textContent = hiddenCount; // Скрытых
    }
    
    // Показываем/скрываем сообщение "нет новостей"
    if (noNewsElement) {
        if (visibleCount === 0) {
            noNewsElement.style.display = 'flex';
        } else {
            noNewsElement.style.display = 'none';
        }
    }
}

// Функция для обновления всех ссылок на странице
function updateAllLinks(showHidden) {
    const links = document.querySelectorAll('a[href]');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && !href.startsWith('http') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
            try {
                const url = new URL(href, window.location.origin);
                if (showHidden) {
                    url.searchParams.set('show_hidden', 'true');
                } else {
                    url.searchParams.delete('show_hidden');
                }
                link.href = url.pathname + url.search;
            } catch (e) {
                // Игнорируем ошибки парсинга URL
            }
        }
    });
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

// Обработка изменения видимости новости
function handleNewsVisibilityToggle() {
    // После изменения видимости скрываем скрытые новости
    setTimeout(hideHiddenNews, 100);
}

// Функция для установки состояния чекбокса при загрузке страницы
function setCheckboxState() {
    const urlParams = new URLSearchParams(window.location.search);
    const showHidden = urlParams.get('show_hidden');
    const checkbox = document.getElementById('showHidden');
    
    if (checkbox && showHidden === 'true') {
        checkbox.checked = true;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем состояние чекбокса на основе URL параметра
    const urlParams = new URLSearchParams(window.location.search);
    const showHidden = urlParams.get('show_hidden') === 'true';
    
    const checkbox = document.getElementById('showHidden');
    if (checkbox) {
        checkbox.checked = showHidden;
        // Вызываем toggleHiddenNews для правильной настройки видимости
        toggleHiddenNews();
    } else {
        // Если чекбокса нет, все равно обновляем состояние
        updateNewsVisibility();
    }
    
    // Скрываем скрытые новости для обычных пользователей при загрузке
    const container = document.querySelector('.news-container');
    const isSuperuser = container && container.dataset.isSuperuser === 'true';
    
    if (!isSuperuser) {
        const hiddenCards = document.querySelectorAll('.news-card.hidden');
        hiddenCards.forEach(card => {
            card.style.display = 'none';
        });
        // Обновляем состояние после скрытия
        updateNewsVisibility();
    }
    
    // Добавляем обработчик для формы создания/обновления новостей
    const newsForm = document.getElementById('newsForm');
    if (newsForm) {
        newsForm.addEventListener('submit', function() {
            // После отправки формы скрываем скрытые новости
            setTimeout(hideHiddenNews, 100);
        });
    }
}); 