document.addEventListener('DOMContentLoaded', function () {
    const authForm = document.getElementById('auth-form');

    function showModal(type, title, message) {
        // Удаляем предыдущее сообщение, если есть
        const existingMessage = document.getElementById('modal-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        // Создаем контейнер для модального сообщения
        const modal = document.createElement('div');
        modal.id = 'modal-message';
        modal.className = 'modal-message-container active';
        document.body.appendChild(modal);

        modal.innerHTML = `
            <div class="modal-message modal-${type}">
                <div class="modal-content">
                    <span class="modal-icon">${type === 'success' ? '✓' : '!'}</span>
                    <h3 class="modal-title">${title}</h3>
                    <p class="modal-text">${message}</p>
                </div>
            </div>
        `;

        return modal;
    }

    authForm.addEventListener('htmx:afterRequest', function (evt) {
        const response = evt.detail.xhr;

        try {
            // Проверяем, является ли ответ JSON
            const contentType = response.getResponseHeader('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                const responseData = JSON.parse(response.responseText);

                // Успешная регистрация (статус 200 и есть данные пользователя)
                if (response.status === 200 && responseData.id) {
                    const modal = showModal(
                        'success',
                        'Регистрация успешна',
                        'Вы будете перенаправлены на страницу входа...'
                    );

                    // Перенаправление через 2 секунды
                    setTimeout(() => {
                        window.location.href = "{{ url_for('auth_app.login') }}";
                    }, 2000);
                    return;
                }
            }

            // Если дошли сюда, значит что-то пошло не так
            throw new Error('Неожиданный ответ сервера');

        } catch (e) {
            console.error('Error processing response:', e);
            showModal(
                'error',
                'Ошибка регистрации',
                'Произошла ошибка. Пожалуйста, попробуйте ещё раз.'
            );
        }
    });

    // Проверка совпадения паролей перед отправкой
    authForm.addEventListener('submit', function (e) {
        const password = document.getElementById('auth-form__password-input').value;
        const confirmPassword = document.getElementById('auth-form__confirm-password-input').value;

        if (password !== confirmPassword) {
            e.preventDefault();
            showModal(
                'error',
                'Ошибка',
                'Пароли не совпадают. Пожалуйста, проверьте введённые данные.'
            );
            return false;
        }
        return true;
    });

    // Инициализация переключателей видимости пароля
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function () {
            const input = this.parentElement.querySelector('input');
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            const icons = this.querySelectorAll('.eye-icon');
            icons[0].style.display = isPassword ? 'none' : 'block';
            icons[1].style.display = isPassword ? 'block' : 'none';
        });
    });
});