document.addEventListener('DOMContentLoaded', function () {
    const authForm = document.getElementById('auth-form');

    function showModal(message, isSuccess) {
        // Удаляем предыдущее сообщение, если есть
        const existingMessage = document.getElementById('modal-message');
        if (existingMessage) {
            closeModal(existingMessage);
            return; // Ждём завершения анимации закрытия
        }

        // Создаем контейнер для модального сообщения
        const modal = document.createElement('div');
        modal.id = 'modal-message';
        modal.className = 'modal-message-container';
        document.body.appendChild(modal);

        // Добавляем содержимое модального окна
        modal.innerHTML = `
            <div class="modal-message ${isSuccess ? 'modal-success' : 'modal-error'}">
                <div class="modal-content">
                    <span class="modal-icon">${isSuccess ? '✓' : '!'}</span>
                    <h3 class="modal-title">${message.title}</h3>
                    <p class="modal-text">${message.text}</p>
                </div>
            </div>
        `;

        // Активируем анимацию появления
        setTimeout(() => {
            modal.classList.add('active');
        }, 10);

        return modal;
    }

    function closeModal(modal) {
        if (!modal) return;

        modal.classList.remove('active');
        modal.classList.add('closing');

        modal.addEventListener('transitionend', () => {
            modal.remove();
        }, { once: true });
    }

    authForm.addEventListener('htmx:afterRequest', function (evt) {
        try {
            const response = evt.detail.xhr;
            const responseData = JSON.parse(response.responseText);

            if (evt.detail.successful && responseData.token) {
                localStorage.setItem('jwt_token', responseData.token);

                const modal = showModal({
                    title: 'Успешный вход',
                    text: 'Вы будете перенаправлены...'
                }, true);

                setTimeout(() => {
                    closeModal(modal);
                    window.location.href = '/dashboard';
                }, 2000);
            } else {
                // Обработка ошибок
                let errorTitle = 'Ошибка входа';
                let errorText = 'Произошла ошибка';

                switch (response.status) {
                    case 400: errorTitle = 'Некорректный запрос'; break;
                    case 401: errorTitle = 'Ошибка авторизации'; break;
                    case 403: errorTitle = 'Доступ запрещен'; break;
                    case 404: errorTitle = 'Ресурс не найден'; break;
                    case 422: errorTitle = 'Ошибка валидации'; break;
                    case 500: errorTitle = 'Ошибка сервера'; break;
                }

                if (responseData.message) errorText = responseData.message;
                if (responseData.detail) {
                    errorText = typeof responseData.detail === 'string'
                        ? responseData.detail
                        : responseData.detail.map(item => item.msg).join(', ');
                }

                const modal = showModal({
                    title: errorTitle,
                    text: errorText
                }, false);

                setTimeout(() => closeModal(modal), 2000);
            }
        } catch (e) {
            console.error('Error processing response:', e);
            const modal = showModal({
                title: 'Ошибка клиента',
                text: 'Не удалось обработать ответ сервера'
            }, false);

            setTimeout(() => closeModal(modal), 2000);
        }
    });

    // Функционал показа/скрытия пароля
    const togglePassword = document.querySelector('.toggle-password');
    const passwordInput = document.getElementById('auth-form__password-input');
    const eyeShow = document.querySelector('.eye-show');
    const eyeHide = document.querySelector('.eye-hide');

    if (togglePassword && passwordInput && eyeShow && eyeHide) {
        togglePassword.addEventListener('click', function () {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';

            eyeShow.style.display = isPassword ? 'none' : 'block';
            eyeHide.style.display = isPassword ? 'block' : 'none';
        });
    }

    // Обработчик для HTMX запросов
    document.body.addEventListener('htmx:configRequest', function (evt) {
        const token = localStorage.getItem('jwt_token');
        if (token) {
            evt.detail.headers = evt.detail.headers || {};
            evt.detail.headers['Authorization'] = 'Bearer ' + token;
        }
    });
});