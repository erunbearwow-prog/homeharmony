// Ждём загрузки Django Admin
window.addEventListener('load', function() {
    // Проверяем, что django и его jQuery доступны
    if (typeof django === 'undefined') {
        console.error('django не загружен');
        return;
    }

    if (typeof django.jQuery === 'undefined') {
        console.error('django.jQuery не загружен');
        return;
    }

    var $ = django.jQuery;

    console.log('✅ food_item.js загружен, jQuery доступен');

    function initFoodItemRow(row) {
        console.log('Инициализация строки');

        var ingredientField = row.find('.field-ingredient select');
        var productField = row.find('.field-product select');
        var ingredientRow = row.find('.field-ingredient');
        var productRow = row.find('.field-product');

        if (ingredientField.length === 0 && productField.length === 0) {
            console.log('Поля не найдены');
            return;
        }

        // Скрываем оба поля
        ingredientRow.hide();
        productRow.hide();

        // Создаём переключатель
        var switchHtml = '<div class="food-item-type-switch" style="margin-bottom: 8px;">' +
            '<button type="button" class="type-ingredient active" style="background:#79aec8; color:white; border:none; padding:5px 12px; border-radius:4px 0 0 4px; cursor:pointer;">🍃 Ингредиент</button>' +
            '<button type="button" class="type-product" style="background:#f0f0f0; border:none; padding:5px 12px; border-radius:0 4px 4px 0; cursor:pointer;">🏭 Готовый продукт</button>' +
            '</div>';

        row.find('.field-ingredient').before(switchHtml);

        var ingredientBtn = row.find('.type-ingredient');
        var productBtn = row.find('.type-product');

        // По умолчанию показываем ингредиент
        ingredientRow.show();
        productRow.hide();
        ingredientField.prop('required', true);
        productField.prop('required', false);

        ingredientBtn.on('click', function() {
            ingredientBtn.css({'background': '#79aec8', 'color': 'white'});
            productBtn.css({'background': '#f0f0f0', 'color': 'black'});
            ingredientRow.show();
            productRow.hide();
            ingredientField.prop('required', true);
            productField.prop('required', false);
            productField.val('');
        });

        productBtn.on('click', function() {
            productBtn.css({'background': '#79aec8', 'color': 'white'});
            ingredientBtn.css({'background': '#f0f0f0', 'color': 'black'});
            productRow.show();
            ingredientRow.hide();
            productField.prop('required', true);
            ingredientField.prop('required', false);
            ingredientField.val('');
        });
    }

    // Ищем инлайн
    var inline = $('.dynamic-recipefooditem_set');

    if (inline.length === 0) {
        console.log('⚠️ .dynamic-recipefooditem_set не найден');
        // Пробуем другие селекторы
        inline = $('.inline-related').filter(function() {
            return $(this).find('.field-ingredient').length > 0;
        });
        console.log('Найдено через .inline-related:', inline.length);
    }

    inline.each(function() {
        $(this).find('.form-row, .row').each(function() {
            initFoodItemRow($(this));
        });
    });

    // Отслеживаем добавление новых строк
    $(document).on('click', '.add-row a', function() {
        setTimeout(function() {
            $('.dynamic-recipefooditem_set .form-row, .dynamic-recipefooditem_set .row, .inline-related .form-row').each(function() {
                initFoodItemRow($(this));
            });
        }, 150);
    });
});