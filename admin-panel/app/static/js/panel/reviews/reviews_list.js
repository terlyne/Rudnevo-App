let currentReviewId = null;

// Создание отзыва
function createReview() {
    currentReviewId = null;
    document.getElementById('modalTitle').textContent = 'Создать отзыв';
    document.getElementById('reviewForm').reset();
    document.getElementById('reviewModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
    
    // Устанавливаем начальный рейтинг
    resetStars();
    
    return false; // Предотвращаем любые нежелательные действия браузера
}

// Функции для работы с модальными окнами отзывов

function openReviewModal() {
    document.getElementById('reviewModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeReviewModal() {
    document.getElementById('reviewModal').style.display = 'none';
    document.body.style.overflow = 'auto';
    document.getElementById('reviewForm').reset();
    
    // Сбрасываем звездочки
    resetStars();
}

function editReview(reviewId) {
    // Здесь можно добавить логику для загрузки данных отзыва в форму
    // Пока просто открываем модальное окно
    openReviewModal();
    return false; // Предотвращаем отправку формы
}

// Функции для работы со звездочками
function resetStars() {
    const stars = document.querySelectorAll('.star-input');
    const ratingInput = document.getElementById('rating');
    
    stars.forEach((star, index) => {
        star.textContent = '★';
        star.style.color = '#f39c12';
        star.classList.add('active');
    });
    
    ratingInput.value = '5';
}

function updateStars(rating) {
    const stars = document.querySelectorAll('.star-input');
    const ratingInput = document.getElementById('rating');
    
    stars.forEach((star, index) => {
        if (index < rating) {
            star.textContent = '★';
            star.style.color = '#f39c12';
            star.classList.add('active');
        } else {
            star.textContent = '☆';
            star.style.color = '#bdc3c7';
            star.classList.remove('active');
        }
    });
    
    ratingInput.value = rating;
}

// Инициализация звездочек при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const stars = document.querySelectorAll('.star-input');
    
    stars.forEach((star, index) => {
        star.addEventListener('click', function() {
            updateStars(index + 1);
        });
        
        star.addEventListener('mouseenter', function() {
            const rating = index + 1;
            stars.forEach((s, i) => {
                if (i < rating) {
                    s.textContent = '★';
                    s.style.color = '#f39c12';
                } else {
                    s.textContent = '☆';
                    s.style.color = '#bdc3c7';
                }
            });
        });
        
        star.addEventListener('mouseleave', function() {
            const currentRating = document.getElementById('rating').value;
            updateStars(currentRating);
        });
    });
    
    // Устанавливаем начальный рейтинг
    resetStars();
});

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('reviewModal');
    if (event.target === modal) {
        closeReviewModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeReviewModal();
    }
});

// Переключение отображения скрытых отзывов
function toggleHiddenReviews() {
    const showHidden = document.getElementById('showHidden').checked;
    const hiddenCards = document.querySelectorAll('.review-card.hidden');
    
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
    
    // Обновляем состояние "нет отзывов" и счетчики
    updateReviewsVisibility();
}

// Функция для обновления состояния видимости отзывов и счетчиков
function updateReviewsVisibility() {
    const reviewCards = document.querySelectorAll('.review-card');
    const noReviewsElement = document.querySelector('.no-reviews');
    const statsNumbers = document.querySelectorAll('.stat-number');
    
    let visibleCount = 0;
    let totalCount = 0;
    let approvedCount = 0;
    let pendingCount = 0;
    
    reviewCards.forEach(card => {
        totalCount++;
        
        // Проверяем, видим ли элемент (не скрыт через display: none)
        const isVisible = card.style.display !== 'none' && 
                         getComputedStyle(card).display !== 'none' &&
                         card.offsetParent !== null;
        
        if (isVisible) {
            visibleCount++;
        }
        
        if (card.classList.contains('hidden')) {
            pendingCount++;
        } else {
            approvedCount++;
        }
    });
    
    // Обновляем счетчики
    if (statsNumbers.length >= 3) {
        statsNumbers[0].textContent = totalCount; // Всего отзывов
        statsNumbers[1].textContent = approvedCount; // Одобренных
        statsNumbers[2].textContent = pendingCount; // На модерации
    }
    
    // Показываем/скрываем сообщение "нет отзывов"
    if (noReviewsElement) {
        if (visibleCount === 0) {
            noReviewsElement.style.display = 'flex';
        } else {
            noReviewsElement.style.display = 'none';
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

// Одобрение отзыва
function approveReview(reviewId) {
    if (confirm('Вы уверены, что хотите одобрить этот отзыв?')) {
        fetch(`/reviews/${reviewId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Ошибка при одобрении');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('Ошибка при одобрении отзыва', 'error');
        });
    }
}

// Отклонение отзыва
function rejectReview(reviewId) {
    if (confirm('Вы уверены, что хотите отклонить этот отзыв?')) {
        fetch(`/reviews/${reviewId}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                location.reload();
            } else {
                throw new Error('Ошибка при отклонении');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFlashMessage('Ошибка при отклонении отзыва', 'error');
        });
    }
}

// Удаление отзыва
function deleteReview(reviewId) {
    if (confirm('Вы уверены, что хотите удалить этот отзыв? Это действие нельзя отменить.')) {
        fetch(`/reviews/${reviewId}/delete`, {
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
            showFlashMessage('Ошибка при удалении отзыва', 'error');
        });
    }
}

// Функция для скрытия неодобренных отзывов для обычных пользователей
function hidePendingReviews() {
    const container = document.querySelector('.reviews-container');
    const isSuperuser = container && container.dataset.isSuperuser === 'true';
    const showHidden = document.getElementById('showHidden');
    const showHiddenChecked = showHidden ? showHidden.checked : false;
    
    if (!isSuperuser && !showHiddenChecked) {
        const pendingCards = document.querySelectorAll('.review-card.pending');
        pendingCards.forEach(card => {
            card.style.display = 'none';
        });
    } else if (isSuperuser && showHiddenChecked) {
        // Показываем все отзывы, если фильтр включен
        const pendingCards = document.querySelectorAll('.review-card.pending');
        pendingCards.forEach(card => {
            card.style.display = 'flex';
        });
    }
    
    // Обновляем состояние видимости и счетчики
    updateReviewsVisibility();
}

// Обработка изменения видимости отзыва
function handleReviewVisibilityToggle() {
    // После изменения видимости скрываем неодобренные отзывы
    setTimeout(hidePendingReviews, 100);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем состояние чекбокса на основе URL параметра
    const urlParams = new URLSearchParams(window.location.search);
    const showHidden = urlParams.get('show_hidden') === 'true';
    
    const checkbox = document.getElementById('showHidden');
    if (checkbox) {
        checkbox.checked = showHidden;
        // Вызываем toggleHiddenReviews для правильной настройки видимости
        toggleHiddenReviews();
    } else {
        // Если чекбокса нет, все равно обновляем состояние
        updateReviewsVisibility();
    }
    
    // Скрываем неодобренные отзывы для обычных пользователей при загрузке
    const container = document.querySelector('.reviews-container');
    const isSuperuser = container && container.dataset.isSuperuser === 'true';
    
    if (!isSuperuser) {
        const hiddenCards = document.querySelectorAll('.review-card.hidden');
        hiddenCards.forEach(card => {
            card.style.display = 'none';
        });
        // Обновляем состояние после скрытия
        updateReviewsVisibility();
    }
    
    // Добавляем обработчик для формы создания/обновления отзывов
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function() {
            // После отправки формы скрываем неодобренные отзывы
            setTimeout(hidePendingReviews, 100);
        });
    }
}); 