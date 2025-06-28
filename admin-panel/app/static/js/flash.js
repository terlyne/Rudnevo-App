document.addEventListener('DOMContentLoaded', function () {
    const flashMessages = document.querySelectorAll('.flash');
    const redirectAfter = document.body.dataset.redirectAfter;

    if (flashMessages.length > 0) {
        document.body.classList.add('has-flash');

        flashMessages.forEach(message => {
            const isSuccess = message.querySelector('.success') !== null;
            const isError = message.querySelector('.error') !== null;

            // Убираем все success сообщения
            if (isSuccess) {
                message.remove();
                return;
            }

            if (isError) {
                // Для сообщений об ошибках добавляем кнопку закрытия
                const errorSpan = message.querySelector('.error');
                if (errorSpan) {
                    // Добавляем кнопку закрытия для error сообщений
                    const closeButton = document.createElement('button');
                    closeButton.innerHTML = '×';
                    closeButton.className = 'flash-close';
                    
                    closeButton.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = 'rgba(198, 40, 40, 0.1)';
                    });
                    
                    closeButton.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'transparent';
                    });
                    
                    closeButton.addEventListener('click', function() {
                        message.remove();
                        if (document.querySelectorAll('.flash').length === 0) {
                            document.body.classList.remove('has-flash');
                        }
                        // Если есть URL для перенаправления, выполняем его
                        if (redirectAfter) {
                            window.location.href = redirectAfter;
                        }
                    });
                    
                    message.appendChild(closeButton);
                }
                
                // Error сообщения автоматически исчезают через 10 секунд
                // благодаря CSS анимации flashAnimation
                message.addEventListener('animationend', function (e) {
                    // Проверяем, что это именно конец анимации исчезновения
                    if (e.animationName === 'flashAnimation') {
                        message.remove();
                        // Проверяем, остались ли еще flash-сообщения
                        if (document.querySelectorAll('.flash').length === 0) {
                            document.body.classList.remove('has-flash');
                            // Если есть URL для перенаправления, выполняем его
                            if (redirectAfter) {
                                window.location.href = redirectAfter;
                            }
                        }
                    }
                });
            } else {
                // Для других типов сообщений (info, warning) показываем анимацию
                message.addEventListener('animationend', function (e) {
                    // Проверяем, что это именно конец анимации исчезновения
                    if (e.animationName === 'flashAnimation') {
                        message.remove();
                        // Проверяем, остались ли еще flash-сообщения
                        if (document.querySelectorAll('.flash').length === 0) {
                            document.body.classList.remove('has-flash');
                            // Если есть URL для перенаправления, выполняем его
                            if (redirectAfter) {
                                window.location.href = redirectAfter;
                            }
                        }
                    }
                });
            }
        });

        // Проверяем, остались ли flash сообщения после фильтрации
        const remainingMessages = document.querySelectorAll('.flash');
        if (remainingMessages.length === 0) {
            document.body.classList.remove('has-flash');
        }
    }

    console.log('Найдено flash сообщений при загрузке:', flashMessages.length);
    flashMessages.forEach((msg, index) => {
        const isError = msg.querySelector('.error') !== null;
        const isSuccess = msg.querySelector('.success') !== null;
        console.log(`Flash сообщение ${index + 1}:`, { isError, isSuccess, text: msg.textContent });
    });
});


