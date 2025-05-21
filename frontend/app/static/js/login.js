document.addEventListener('htmx:afterRequest', function (event) {
    if (event.detail.xhr.status === 200) {
        const response = JSON.parse(event.detail.xhr.responseText);
        if (response.token) {
            localStorage.setItem('jwt', response.token);
            document.getElementById('response-message').innerText = 'Успешная авторизация!';
        } else {
            document.getElementById('response-message').innerText = 'Ошибка авторизации!';
        }
    } else {
        document.getElementById('response-message').innerText = 'Ошибка сети!';
    }
});