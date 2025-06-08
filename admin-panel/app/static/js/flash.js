document.addEventListener('DOMContentLoaded', function () {
    const flashMessages = document.querySelectorAll('.flash');
    const redirectAfter = document.body.dataset.redirectAfter;

    if (flashMessages.length > 0) {
        document.body.classList.add('has-flash');

        flashMessages.forEach(message => {
            // Проверяем, является ли сообщение успешным
            const isSuccess = message.querySelector('.success') !== null;

            if (isSuccess && redirectAfter) {
                // Для успешных сообщений сразу делаем редирект
                window.location.href = redirectAfter;
            } else {
                // Для сообщений об ошибках показываем анимацию
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
    }
}); 