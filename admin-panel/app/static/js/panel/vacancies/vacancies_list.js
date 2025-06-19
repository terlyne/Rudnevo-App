function toggleHiddenVacancies() {
    const checkbox = document.getElementById('show-hidden');
    const url = new URL(window.location);
    url.searchParams.set('show_hidden', checkbox.checked);
    window.location.href = url.toString();
}

function deleteVacancy(vacancyId) {
    if (confirm('Вы уверены, что хотите удалить эту вакансию?')) {
        const form = document.getElementById('delete-form');
        form.action = `/vacancies/${vacancyId}/delete`;
        form.submit();
    }
}