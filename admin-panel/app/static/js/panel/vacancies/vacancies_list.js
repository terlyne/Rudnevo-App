function toggleHiddenVacancies() {
    const checkbox = document.getElementById('show-hidden');
    const showHidden = checkbox.checked;

    // Отправляем AJAX запрос
    fetch(`/vacancies?show_hidden=${showHidden}`)
        .then(response => response.text())
        .then(html => {
            // Создаем временный элемент для парсинга HTML
            const temp = document.createElement('div');
            temp.innerHTML = html;

            // Находим контейнер с вакансиями в полученном HTML
            const newVacancies = temp.querySelector('.vacancies-scroll').innerHTML;

            // Заменяем содержимое контейнера
            document.querySelector('.vacancies-scroll').innerHTML = newVacancies;
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Произошла ошибка при загрузке вакансий');
        });
}

function deleteVacancy(vacancyId) {
    if (confirm('Вы уверены, что хотите удалить эту вакансию?')) {
        const form = document.getElementById('delete-form');
        form.action = `/vacancies/${vacancyId}/delete`;
        form.submit();
    }
}