// Глобальный скрипт для сохранения состояния фильтра show_hidden
document.addEventListener('DOMContentLoaded', function() {
    // Получаем состояние фильтра из URL
    const urlParams = new URLSearchParams(window.location.search);
    const showHidden = urlParams.get('show_hidden') === 'true';
    
    // Если фильтр включен, обновляем все ссылки на странице
    if (showHidden) {
        updateAllLinks(showHidden);
    }
    
    // Добавляем обработчик для всех ссылок, чтобы они сохраняли фильтр
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'A' || e.target.closest('a')) {
            const link = e.target.tagName === 'A' ? e.target : e.target.closest('a');
            const href = link.getAttribute('href');
            
            if (href && !href.startsWith('http') && !href.startsWith('mailto:') && !href.startsWith('tel:') && !href.startsWith('#')) {
                try {
                    const url = new URL(href, window.location.origin);
                    if (showHidden) {
                        url.searchParams.set('show_hidden', 'true');
                    }
                    link.href = url.pathname + url.search;
                } catch (e) {
                    // Игнорируем ошибки парсинга URL
                }
            }
        }
    });
});

// Функция для обновления всех ссылок на странице
function updateAllLinks(showHidden) {
    const links = document.querySelectorAll('a[href]');
    links.forEach(link => {
        const href = link.getAttribute('href');
        if (href && !href.startsWith('http') && !href.startsWith('mailto:') && !href.startsWith('tel:') && !href.startsWith('#')) {
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