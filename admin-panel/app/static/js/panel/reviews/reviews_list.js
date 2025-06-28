let currentReviewId = null;

// Создание отзыва
function createReview() {
    document.getElementById('reviewModal').style.display = 'block';
    document.getElementById('modalTitle').textContent = 'Создать отзыв';
    document.getElementById('reviewForm').reset();
    
    // Инициализируем звездочки
    resetStars();
    
    // Добавляем обработчики событий для звездочек
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
            updateStars(parseInt(currentRating));
        });
    });
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
    // Инициализация звездочек теперь происходит при открытии модального окна
    // в функции createReview()
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

// Функции для работы с отзывами

function openCreateModal() {
    document.getElementById('createReviewModal').style.display = 'block';
}

function closeCreateModal() {
    document.getElementById('createReviewModal').style.display = 'none';
}

function toggleReviewVisibility(reviewId) {
    if (confirm('Вы уверены, что хотите изменить статус этого отзыва?')) {
        fetch(`/reviews/${reviewId}/toggle-visibility`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then(response => {
            if (response.ok) {
                // Перезагружаем страницу для обновления счетчиков
                window.location.reload();
            } else {
                alert('Ошибка при изменении статуса отзыва');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при изменении статуса отзыва');
        });
    }
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('createReviewModal');
    if (event.target === modal) {
        closeCreateModal();
    }
}

// Закрытие модального окна при нажатии Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeCreateModal();
    }
}); 