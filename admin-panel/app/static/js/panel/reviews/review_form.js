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