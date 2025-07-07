let currentPartnerId = null;

document.addEventListener('DOMContentLoaded', function () {
    // Закрытие модальных окон при клике вне их
    window.addEventListener('click', function (event) {
        const partnerModal = document.getElementById('partnerModal');
        
        if (event.target === partnerModal) {
            closePartnerModal();
        }
    });

    // Обработчик для изображения
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    
                    const removeBtn = document.getElementById('removeImageBtn');
                    removeBtn.style.display = 'inline-block';
                    
                    // Скрываем кнопку "Выбрать файл"
                    imageInput.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Обработчик для кнопки удаления изображения
    const removeImageBtn = document.getElementById('removeImageBtn');
    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', function() {
            const imageInput = document.getElementById('image');
            const preview = document.getElementById('imagePreview');
            
            imageInput.value = '';
            preview.style.display = 'none';
            removeImageBtn.style.display = 'none';
            
            // Показываем кнопку "Выбрать файл"
            imageInput.style.display = 'block';
        });
    }
});

function createPartner() {
    const modal = document.getElementById('partnerModal');
    const modalTitle = document.getElementById('modalTitle');
    const form = document.getElementById('partnerForm');
    const nameInput = document.getElementById('name');
    const isActiveCheckbox = document.getElementById('is_active');
    const imageInput = document.getElementById('image');
    const preview = document.getElementById('imagePreview');
    const removeBtn = document.getElementById('removeImageBtn');

    currentPartnerId = null;
    modalTitle.textContent = 'Создать партнера';
    form.action = '/partners/create';
    
    // Очищаем форму
    nameInput.value = '';
    isActiveCheckbox.checked = true;
    imageInput.value = '';
    imageInput.style.display = 'block';
    preview.style.display = 'none';
    removeBtn.style.display = 'none';

    modal.style.display = 'block';
}

function editPartner(partnerId) {
    currentPartnerId = partnerId;
    
    // Получаем данные партнера через AJAX
    fetch(`/partners/${partnerId}`)
        .then(response => response.json())
        .then(partner => {
            const modal = document.getElementById('partnerModal');
            const modalTitle = document.getElementById('modalTitle');
            const form = document.getElementById('partnerForm');
            const nameInput = document.getElementById('name');
            const isActiveCheckbox = document.getElementById('is_active');
            const imageInput = document.getElementById('image');
            const preview = document.getElementById('imagePreview');
            const removeBtn = document.getElementById('removeImageBtn');

            modalTitle.textContent = 'Редактировать партнера';
            form.action = `/partners/${partnerId}/edit`;
            
            nameInput.value = partner.name || '';
            isActiveCheckbox.checked = partner.is_active || false;
            
            if (partner.image_url) {
                preview.src = `/partners/${partnerId}/image`;
                preview.style.display = 'block';
                removeBtn.style.display = 'inline-block';
                imageInput.style.display = 'none';
            } else {
                preview.style.display = 'none';
                removeBtn.style.display = 'none';
                imageInput.style.display = 'block';
            }

            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при загрузке данных партнера');
        });
}

function closePartnerModal() {
    const modal = document.getElementById('partnerModal');
    modal.style.display = 'none';
    currentPartnerId = null;
} 