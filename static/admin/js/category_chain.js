// homeharmony/static/admin/js/category_chain.js
(function() {
    'use strict';

    function loadCategories(parentId, targetSelectId, defaultText, preserveValue) {
        var targetSelect = document.getElementById(targetSelectId);
        if (!targetSelect) return;

        // Сохраняем текущее значение, если нужно
        var currentValue = preserveValue ? targetSelect.value : null;

        targetSelect.innerHTML = '<option value="">' + (defaultText || '-- Выберите --') + '</option>';

        if (parentId && parentId !== '') {
            var url = '/admin/api/category-children/?parent_id=' + parentId;

            fetch(url)
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    if (data.categories && data.categories.length > 0) {
                        for (var i = 0; i < data.categories.length; i++) {
                            var cat = data.categories[i];
                            var option = document.createElement('option');
                            option.value = cat.id;
                            option.textContent = cat.name;
                            targetSelect.appendChild(option);
                        }
                    }

                    // Восстанавливаем значение, если оно было
                    if (currentValue && targetSelect.querySelector('option[value="' + currentValue + '"]')) {
                        targetSelect.value = currentValue;
                    }
                })
                .catch(function(error) {
                    console.error('Error loading categories:', error);
                });
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        var level1 = document.getElementById('id_category_level_1');
        var level2 = document.getElementById('id_category_level_2');
        var level3 = document.getElementById('id_category_level_3');

        if (!level1) {
            return;
        }

        // Сохраняем начальные значения
        var initialLevel1 = level1.value;
        var initialLevel2 = level2 ? level2.value : null;
        var initialLevel3 = level3 ? level3.value : null;

        console.log('Initial values - level1:', initialLevel1, 'level2:', initialLevel2, 'level3:', initialLevel3);

        // НЕ загружаем начальные значения, если они уже есть в HTML
        // Django уже установил правильные значения в HTML

        // При изменении 1-го уровня
        level1.addEventListener('change', function() {
            var parentId = this.value;
            loadCategories(parentId, 'id_category_level_2', '-- Выберите подкатегорию --', false);
            if (level3) {
                level3.innerHTML = '<option value="">-- Сначала выберите категорию 2-го уровня --</option>';
            }
        });

        // При изменении 2-го уровня
        if (level2) {
            level2.addEventListener('change', function() {
                var parentId = this.value;
                loadCategories(parentId, 'id_category_level_3', '-- Выберите подкатегорию --', false);
            });
        }

        // Загружаем дочерние категории для level2 ТОЛЬКО если level1 имеет значение,
        // но НЕ перезаписываем выбранные значения
        if (initialLevel1) {
            loadCategories(initialLevel1, 'id_category_level_2', '-- Выберите подкатегорию --', true);
        }

        // Загружаем дочерние категории для level3
        if (initialLevel2) {
            setTimeout(function() {
                loadCategories(initialLevel2, 'id_category_level_3', '-- Выберите подкатегорию --', true);
            }, 100);
        }
    });
})();