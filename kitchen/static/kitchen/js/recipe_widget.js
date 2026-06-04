// ======================= ВИДЖЕТ ИНГРЕДИЕНТОВ =======================

document.addEventListener('DOMContentLoaded', function() {
    // Данные ингредиентов
    const ingredients = [];
    let currentRatio = 1;
    let currentBaseIngredient = null;
    let currentReplaceIngredient = null;
    let currentMode = 'portions';
    let currentIngredientId = null;

    // Базовые значения
    const baseServings = parseInt(document.getElementById('portionsSlider')?.value) || 4;

    // DOM элементы
    const modePortionsBtn = document.getElementById('modePortionsBtn');
    const modeProductsBtn = document.getElementById('modeProductsBtn');
    const portionsPanel = document.getElementById('portionsPanel');
    const productsPanel = document.getElementById('productsPanel');
    const portionsSlider = document.getElementById('portionsSlider');
    const portionsValue = document.getElementById('portionsValue');
    const resetPortionsBtn = document.getElementById('resetPortionsBtn');
    const portionsRatioInfo = document.getElementById('portionsRatioInfo');
    const baseIngredientRow = document.getElementById('baseIngredientRow');
    const baseIngredientWeight = document.getElementById('baseIngredientWeight');
    const baseIngredientUnit = document.getElementById('baseIngredientUnit');
    const baseOriginalValue = document.getElementById('baseOriginalValue');
    const applyBaseBtn = document.getElementById('applyBaseBtn');
    const resetBaseBtn = document.getElementById('resetBaseBtn');
    const baseRatioInfo = document.getElementById('baseRatioInfo');
    const baseIngredientName = document.getElementById('baseIngredientName');
    const checkAllBtn = document.getElementById('checkAllBtn');
    const uncheckAllBtn = document.getElementById('uncheckAllBtn');
    const copyCheckedBtn = document.getElementById('copyCheckedBtn');

    // Модальные окна
    const replaceModal = document.getElementById('replaceModal');
    const replaceOriginalName = document.getElementById('replaceOriginalName');
    const replaceOriginalUnit = document.getElementById('replaceOriginalUnit');
    const replaceWithSelect = document.getElementById('replaceWithSelect');
    const replaceRatio = document.getElementById('replaceRatio');
    const replaceNewUnit = document.getElementById('replaceNewUnit');
    const cancelReplaceBtn = document.getElementById('cancelReplaceBtn');
    const confirmReplaceBtn = document.getElementById('confirmReplaceBtn');
    const infoModal = document.getElementById('infoModal');
    const modeNormalBtn = document.getElementById('modeNormalBtn');
    const modeCompactBtn = document.getElementById('modeCompactBtn');
    const stepsContainer = document.getElementById('stepsList');

    // Проверка наличия элементов
    console.log('Mode buttons:', { modePortionsBtn, modeProductsBtn });
    console.log('Panels:', { portionsPanel, productsPanel });

    // Инициализация списка ингредиентов
    document.querySelectorAll('#ingredientsList .ingredient-row').forEach(row => {
        const id = row.dataset.id;
        const name = row.dataset.name;
        const baseQuantity = parseFloat(row.dataset.baseQuantity);
        const unit = row.dataset.unit;
        const amountSpan = row.querySelector('.ingredient-amount');

        ingredients.push({
            id: id,
            name: name,
            baseQuantity: baseQuantity,
            unit: unit,
            element: amountSpan,
            row: row,
            currentQuantity: baseQuantity
        });
    });

    // ======================= ОБРАБОТЧИК КЛИКОВ ПО ССЫЛКАМ НА ВЛОЖЕННЫЕ РЕЦЕПТЫ =======================
    function setupSubrecipeLinks() {
        document.querySelectorAll('.subrecipe-link').forEach(link => {
            // Удаляем старый обработчик, чтобы не навешивать несколько
            if (link._handler) {
                link.removeEventListener('click', link._handler);
            }

            const handler = function(e) {
                e.preventDefault();

                // Получаем текущий ratio в зависимости от режима
                let currentRatioValue;

                if (currentMode === 'products' && currentBaseIngredient) {
                    currentRatioValue = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                } else if (currentMode === 'portions' && portionsSlider) {
                    currentRatioValue = parseInt(portionsSlider.value) / baseServings;
                } else {
                    currentRatioValue = currentRatio;
                }

                // Получаем базовый URL
                let url = new URL(this.href);

                // Добавляем или обновляем параметры
                url.searchParams.set('ratio', currentRatioValue.toFixed(3));
                url.searchParams.set('mode', currentMode);

                if (currentMode === 'products' && currentBaseIngredient) {
                    url.searchParams.set('base_ingredient', currentBaseIngredient.id);
                    url.searchParams.set('base_value', currentBaseIngredient.currentValue);
                    url.searchParams.delete('portions');
                } else if (currentMode === 'portions' && portionsSlider) {
                    url.searchParams.set('portions', portionsSlider.value);
                    url.searchParams.delete('base_ingredient');
                    url.searchParams.delete('base_value');
                }

                console.log('Переход по ссылке:', url.toString());

                // Переходим по обновлённой ссылке
                window.location.href = url.toString();
            };

            link._handler = handler;
            link.addEventListener('click', handler);
        });
    }

    // ======================= ОБНОВЛЕНИЕ ССЫЛОК НА ВЛОЖЕННЫЕ РЕЦЕПТЫ =======================
    function updateSubrecipeLinks() {
        // Получаем текущий ratio в зависимости от режима
        let currentRatioValue;

        if (currentMode === 'products' && currentBaseIngredient) {
            currentRatioValue = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
        } else if (currentMode === 'portions' && portionsSlider) {
            currentRatioValue = parseInt(portionsSlider.value) / baseServings;
        } else {
            currentRatioValue = currentRatio;
        }

        document.querySelectorAll('.subrecipe-link').forEach(link => {
            try {
                const url = new URL(link.href);
                // Обновляем параметры в href (для случаев, если нужно показать правильную ссылку)
                url.searchParams.set('ratio', currentRatioValue.toFixed(3));
                url.searchParams.set('mode', currentMode);

                if (currentMode === 'products' && currentBaseIngredient) {
                    url.searchParams.set('base_ingredient', currentBaseIngredient.id);
                    url.searchParams.set('base_value', currentBaseIngredient.currentValue);
                    url.searchParams.delete('portions');
                } else if (currentMode === 'portions' && portionsSlider) {
                    url.searchParams.set('portions', portionsSlider.value);
                    url.searchParams.delete('base_ingredient');
                    url.searchParams.delete('base_value');
                }

                link.href = url.toString();
            } catch(e) {
                console.error('Ошибка обновления ссылки:', e);
            }
        });
    }

    // Функция обновления всех ингредиентов
    function updateAllIngredients(ratio) {
    console.log('updateAllIngredients вызван с ratio:', ratio);
    console.log('Ингредиентов для обновления:', ingredients.length);

    ingredients.forEach(ing => {
        const calculatedValue = ing.baseQuantity * ratio;
        console.log(`${ing.name}: ${ing.baseQuantity} * ${ratio} = ${calculatedValue}`);

        let displayValue;

        if (ing.unit === 'шт.' || ing.unit === 'зубч.' || ing.unit === 'ст. л.') {
            displayValue = Math.ceil(calculatedValue);  // ← исправлено!
        } else if (ing.unit === 'г' || ing.unit === 'мл') {
            displayValue = Math.round(calculatedValue);
        } else {
            displayValue = Math.round(calculatedValue * 10) / 10;
        }

        ing.element.innerText = `${displayValue} ${ing.unit}`;
        ing.currentQuantity = displayValue;
    });
    updateSubrecipeLinks();
    setupSubrecipeLinks();
}

    // ======================= ОБНОВЛЕНИЕ URL =======================
    function updateURL() {
        // Получаем существующие параметры из текущего URL
        const currentParams = new URLSearchParams(window.location.search);

        // Сохраняем параметры возврата, если они есть
        const returnTo = currentParams.get('return_to');
        const returnTitle = currentParams.get('return_title');
        const returnStep = currentParams.get('return_step');
        const returnContext = currentParams.get('return_context');
        const returnMode = currentParams.get('return_mode');
        const returnMeat = currentParams.get('return_meat');
        const returnPortions = currentParams.get('return_portions');

        // Создаём новые параметры
        const params = new URLSearchParams();

        // Восстанавливаем параметры возврата
        if (returnTo) params.set('return_to', returnTo);
        if (returnTitle) params.set('return_title', returnTitle);
        if (returnStep) params.set('return_step', returnStep);
        if (returnContext) params.set('return_context', returnContext);
        if (returnMode) params.set('return_mode', returnMode);
        if (returnMeat) params.set('return_meat', returnMeat);
        if (returnPortions) params.set('return_portions', returnPortions);

        // Добавляем параметры режима
        params.set('mode', currentMode);

        let ratioValue = 1;

        if (currentMode === 'products' && currentBaseIngredient) {
            params.set('base_ingredient', currentBaseIngredient.id);
            params.set('base_value', currentBaseIngredient.currentValue);
            ratioValue = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
            params.set('ratio', ratioValue.toFixed(3));
        } else if (currentMode === 'products' && !currentBaseIngredient) {
            const firstIngredient = document.querySelector('.ingredient-row');
            if (firstIngredient) {
                const originalValue = parseFloat(firstIngredient.dataset.baseQuantity);
                const currentValue = parseFloat(firstIngredient.querySelector('.ingredient-amount').innerText);
                ratioValue = currentValue / originalValue;
                params.set('ratio', ratioValue.toFixed(3));
            }
        } else {
            const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : baseServings;
            params.set('portions', portionsVal);
            ratioValue = portionsVal / baseServings;
            params.set('ratio', ratioValue.toFixed(3));
        }

        // Формируем новый URL
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({}, '', newUrl);
    }

// ======================= ВОССТАНОВЛЕНИЕ RATIO ИЗ URL =======================
function restoreRatioFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const ratioFromURL = urlParams.get('ratio');
    const modeFromURL = urlParams.get('mode');
    const baseIngredientId = urlParams.get('base_ingredient');
    const baseValue = urlParams.get('base_value');
    const portionsFromURL = urlParams.get('portions');

    console.log('=== restoreRatioFromURL ===');
    console.log('modeFromURL:', modeFromURL);
    console.log('ratioFromURL:', ratioFromURL);
    console.log('baseIngredientId:', baseIngredientId);
    console.log('baseValue:', baseValue);
    console.log('portionsFromURL:', portionsFromURL);

    // Проверяем, есть ли такой ингредиент на этой странице
    let baseBtn = null;
    if (baseIngredientId) {
        baseBtn = document.querySelector(`.chain-btn[data-id="${baseIngredientId}"]`);
        console.log('Поиск ингредиента с id', baseIngredientId, ':', baseBtn ? 'найден' : 'не найден');
    }

    // Если есть параметры базового ингредиента И он существует на странице - восстанавливаем режим продуктов
    if (modeFromURL === 'products' && baseIngredientId && baseValue && baseBtn) {
        // Режим продуктов
        console.log('Восстанавливаем режим продуктов (ингредиент найден)');

        // Устанавливаем режим без вызова setMode (чтобы не было лишних обновлений)
        currentMode = 'products';

        // Обновляем UI панелей
        if (portionsPanel) portionsPanel.classList.add('hidden');
        if (productsPanel) productsPanel.classList.remove('hidden');

        if (modePortionsBtn) {
            modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
            modePortionsBtn.classList.add('bg-white', 'text-gray-700', 'border-gray-200');
        }
        if (modeProductsBtn) {
            modeProductsBtn.classList.add('bg-amber-600', 'text-white');
            modeProductsBtn.classList.remove('bg-white', 'text-gray-700', 'border-gray-200');
        }

        // Получаем данные ингредиента
        const originalValue = parseFloat(baseBtn.dataset.quantity);
        const newValue = parseFloat(baseValue);
        const name = baseBtn.dataset.name;
        const unit = baseBtn.dataset.unit;

        // Создаём объект currentBaseIngredient
        currentBaseIngredient = {
            id: baseIngredientId,
            name: name,
            originalValue: originalValue,
            unit: unit,
            currentValue: newValue
        };

        // Обновляем UI
        baseIngredientName.innerText = name;
        baseOriginalValue.innerText = `${originalValue} ${unit}`;
        baseIngredientWeight.value = newValue;
        baseIngredientRow.classList.remove('hidden');
        applyBaseBtn.classList.remove('hidden');

        // Подсвечиваем кнопку
        document.querySelectorAll('.chain-btn').forEach(btn => {
            btn.classList.remove('text-amber-600');
            btn.classList.add('text-gray-400');
        });
        baseBtn.classList.remove('text-gray-400');
        baseBtn.classList.add('text-amber-600');

        // Пересчитываем ингредиенты
        if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
            const ratio = parseFloat(ratioFromURL);
            currentRatio = ratio;
            updateAllIngredients(ratio);
            console.log('Вызов updateAllIngredients с ratio:', ratio);
        }

        if (baseRatioInfo) {
            baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newValue} ${unit} ${name})`;
        }

        // Обновляем ссылки после восстановления
        updateSubrecipeLinks();
        setupSubrecipeLinks();
        updateURL();

        console.log('=== restoreRatioFromURL END (products) ===');
        console.log('currentMode:', currentMode);
        console.log('currentRatio:', currentRatio);

        return; // ВЫХОДИМ ИЗ ФУНКЦИИ
    }

    // Если есть параметр ratio - восстанавливаем режим порций (для вложенных рецептов)
    if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
        console.log('Восстанавливаем режим порций из ratio');

        // Устанавливаем режим
        currentMode = 'portions';

        // Обновляем UI панелей
        if (portionsPanel) portionsPanel.classList.remove('hidden');
        if (productsPanel) productsPanel.classList.add('hidden');

        if (modePortionsBtn) {
            modePortionsBtn.classList.add('bg-amber-600', 'text-white');
            modePortionsBtn.classList.remove('bg-white', 'text-gray-700', 'border-gray-200');
        }
        if (modeProductsBtn) {
            modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
            modeProductsBtn.classList.add('bg-white', 'text-gray-700', 'border-gray-200');
        }

        // Восстанавливаем количество порций
        const ratio = parseFloat(ratioFromURL);
        const portions = Math.round(ratio * baseServings);

        if (portionsSlider && portions > 0 && portions <= 20) {
            portionsSlider.value = portions;
            if (portionsValue) portionsValue.innerText = portions;
            currentRatio = ratio;
            updateAllIngredients(ratio);
            console.log('Вызов updateAllIngredients с ratio:', ratio);

            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${portions} порций)`;
            }
        }

        // Обновляем ссылки после восстановления
        updateSubrecipeLinks();
        setupSubrecipeLinks();
        updateURL();

        console.log('=== restoreRatioFromURL END (portions from ratio) ===');
        console.log('currentMode:', currentMode);
        console.log('currentRatio:', currentRatio);

        return; // ВЫХОДИМ ИЗ ФУНКЦИИ
    }

    // Режим порций из параметра portions
    if (modeFromURL === 'portions' || portionsFromURL) {
        console.log('Восстанавливаем режим порций');

        // Устанавливаем режим
        currentMode = 'portions';

        // Обновляем UI панелей
        if (portionsPanel) portionsPanel.classList.remove('hidden');
        if (productsPanel) productsPanel.classList.add('hidden');

        if (modePortionsBtn) {
            modePortionsBtn.classList.add('bg-amber-600', 'text-white');
            modePortionsBtn.classList.remove('bg-white', 'text-gray-700', 'border-gray-200');
        }
        if (modeProductsBtn) {
            modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
            modeProductsBtn.classList.add('bg-white', 'text-gray-700', 'border-gray-200');
        }

        // Восстанавливаем количество порций
        let portions;
        if (portionsFromURL) {
            portions = parseInt(portionsFromURL);
        } else if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
            portions = Math.round(parseFloat(ratioFromURL) * baseServings);
        } else {
            portions = baseServings;
        }

        if (portionsSlider && portions > 0 && portions <= 20) {
            portionsSlider.value = portions;
            if (portionsValue) portionsValue.innerText = portions;

            const ratio = portions / baseServings;
            currentRatio = ratio;
            updateAllIngredients(ratio);

            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${portions} порций)`;
            }
        }

        // Обновляем ссылки после восстановления
        updateSubrecipeLinks();
        setupSubrecipeLinks();
        updateURL();

        console.log('=== restoreRatioFromURL END (portions) ===');
        console.log('currentMode:', currentMode);
        console.log('currentRatio:', currentRatio);

        return;
    }

    // Нет параметров - используем порции по умолчанию
    console.log('Нет параметров, используем порции по умолчанию');
    currentMode = 'portions';
    updateAllIngredients(1);

    // Обновляем ссылки после восстановления
    updateSubrecipeLinks();
    setupSubrecipeLinks();
    updateURL();

    console.log('=== restoreRatioFromURL END (default) ===');
    console.log('currentMode:', currentMode);
    console.log('currentRatio:', currentRatio);
}

    // ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ =======================
    function setMode(mode) {
        console.log('Switching to mode:', mode);
        currentMode = mode;

        if (mode === 'portions') {
            if (portionsPanel) portionsPanel.classList.remove('hidden');
            if (productsPanel) productsPanel.classList.add('hidden');

            if (modePortionsBtn) {
                modePortionsBtn.classList.add('bg-amber-600', 'text-white');
                modePortionsBtn.classList.remove('bg-white', 'text-gray-700', 'border-gray-200');
            }
            if (modeProductsBtn) {
                modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
                modeProductsBtn.classList.add('bg-white', 'text-gray-700', 'border-gray-200');
            }

            const portions = parseInt(portionsSlider.value);
            currentRatio = portions / baseServings;
            updateAllIngredients(currentRatio);
            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${portions} порций)`;
            }
        } else {
            if (portionsPanel) portionsPanel.classList.add('hidden');
            if (productsPanel) productsPanel.classList.remove('hidden');

            if (modeProductsBtn) {
                modeProductsBtn.classList.add('bg-amber-600', 'text-white');
                modeProductsBtn.classList.remove('bg-white', 'text-gray-700', 'border-gray-200');
            }
            if (modePortionsBtn) {
                modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
                modePortionsBtn.classList.add('bg-white', 'text-gray-700', 'border-gray-200');
            }

            if (currentBaseIngredient) {
                const ratio = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                updateAllIngredients(ratio);
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
                }
            }
        }
        updateURL();
    }

    // Навешиваем обработчики на кнопки режимов
    if (modePortionsBtn) {
        modePortionsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            setMode('portions');
        });
    }
    if (modeProductsBtn) {
        modeProductsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            setMode('products');
        });
    }

    // ======================= КНОПКА 🔗 (сделать базовым) =======================
    document.querySelectorAll('.chain-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const id = this.dataset.id;
            const name = this.dataset.name;
            const originalValue = parseFloat(this.dataset.quantity);
            const unit = this.dataset.unit;
            const currentAmountSpan = this.closest('.ingredient-row').querySelector('.ingredient-amount');
            const currentMatch = currentAmountSpan.innerText.match(/^[\d\.]+/);
            const currentValue = currentMatch ? parseFloat(currentMatch[0]) : originalValue;

            document.querySelectorAll('.chain-btn').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });
            this.classList.remove('text-gray-400');
            this.classList.add('text-amber-600');

            currentBaseIngredient = {
                id: id,
                name: name,
                originalValue: originalValue,
                unit: unit,
                currentValue: currentValue
            };

            baseIngredientName.innerText = name;
            baseOriginalValue.innerText = `${originalValue} ${unit}`;
            baseIngredientWeight.value = currentValue;
            baseIngredientWeight.classList.remove('hidden');
            baseIngredientUnit.innerText = unit;
            baseIngredientUnit.classList.remove('hidden');
            baseIngredientRow.classList.remove('hidden');
            applyBaseBtn.classList.remove('hidden');

            setMode('products');
        });
    });

    // Применение пересчёта по базовому ингредиенту
    if (applyBaseBtn) {
        applyBaseBtn.addEventListener('click', function() {
            if (!currentBaseIngredient) return;

            let newValue = parseFloat(baseIngredientWeight.value);
            if (isNaN(newValue) || newValue <= 0) newValue = currentBaseIngredient.originalValue;

            const ratio = newValue / currentBaseIngredient.originalValue;
            currentBaseIngredient.currentValue = newValue;

            updateAllIngredients(ratio);

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${newValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
            }
            updateURL();
        });
    }

    // Сброс базового ингредиента
    if (resetBaseBtn) {
        resetBaseBtn.addEventListener('click', function() {
            currentBaseIngredient = null;
            baseIngredientRow.classList.add('hidden');
            baseRatioInfo.innerText = '';
            baseIngredientName.innerText = 'выбранному';

            document.querySelectorAll('.chain-btn').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });

            setMode('portions');
            updateURL();
        });
    }

    // ======================= КНОПКА ⟳ (замена ингредиента) =======================
    async function openReplaceModal(recipeIngredientId, ingredientName, unit) {
        currentReplaceIngredient = { id: recipeIngredientId, name: ingredientName, unit: unit };
        replaceOriginalName.innerText = ingredientName;
        replaceOriginalUnit.innerText = unit;
        replaceNewUnit.innerText = unit;
        replaceRatio.value = 1;

        replaceWithSelect.innerHTML = '<option value="">Загрузка вариантов замен...</option>';
        replaceModal.classList.remove('hidden');

        try {
            const response = await fetch(`/kitchen/api/substitutions/${recipeIngredientId}/`);
            if (response.ok) {
                const data = await response.json();

                replaceWithSelect.innerHTML = '<option value="custom">✏️ Другой ингредиент (ввести вручную)</option>';

                if (data.substitutions && data.substitutions.length > 0) {
                    data.substitutions.forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.name;
                        option.textContent = `${sub.name} (${sub.ratio} ${sub.unit} вместо 1 ${unit})`;
                        option.dataset.ratio = sub.ratio;
                        option.dataset.unit = sub.unit;
                        option.dataset.notes = sub.notes || '';
                        replaceWithSelect.appendChild(option);
                    });

                    replaceWithSelect.onchange = function() {
                        const selected = this.options[this.selectedIndex];
                        if (selected.value !== 'custom' && selected.dataset.ratio) {
                            replaceRatio.value = selected.dataset.ratio;
                            replaceNewUnit.innerText = selected.dataset.unit;
                        } else {
                            replaceRatio.value = 1;
                            replaceNewUnit.innerText = unit;
                        }
                    };
                } else {
                    const noOptionsMsg = document.createElement('option');
                    noOptionsMsg.value = 'custom';
                    noOptionsMsg.textContent = '✏️ Другой ингредиент (нет рекомендованных замен)';
                    replaceWithSelect.innerHTML = '';
                    replaceWithSelect.appendChild(noOptionsMsg);
                }
            } else {
                throw new Error('Ошибка загрузки замен');
            }
        } catch (error) {
            console.error('Ошибка загрузки замен:', error);
            replaceWithSelect.innerHTML = '<option value="custom">✏️ Другой ингредиент (ошибка загрузки)</option>';
        }
    }

    document.querySelectorAll('.replace-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const id = this.dataset.id;
            const name = this.dataset.name;
            const unit = this.closest('.ingredient-row').dataset.unit;
            openReplaceModal(id, name, unit);
        });
    });

    if (cancelReplaceBtn) {
        cancelReplaceBtn.addEventListener('click', () => replaceModal.classList.add('hidden'));
    }

    if (confirmReplaceBtn) {
        confirmReplaceBtn.addEventListener('click', function() {
            const selectedOption = replaceWithSelect.options[replaceWithSelect.selectedIndex];
            const newName = selectedOption.value;
            const ratio = parseFloat(replaceRatio.value);
            const ingredientRow = document.querySelector(`.ingredient-row[data-id="${currentReplaceIngredient.id}"]`);

            if (ingredientRow && newName !== 'custom' && selectedOption.dataset.ratio) {
                const label = ingredientRow.querySelector('label');
                const amountSpan = ingredientRow.querySelector('.ingredient-amount');
                const currentAmount = parseFloat(amountSpan.innerText);
                const newAmount = currentAmount * ratio;

                label.innerText = newName;
                amountSpan.innerText = `${Math.round(newAmount)} ${selectedOption.dataset.unit}`;

                const replaceBtn = ingredientRow.querySelector('.replace-btn');
                replaceBtn.innerHTML = '<i class="fas fa-undo-alt"></i>';
                replaceBtn.classList.remove('hover:text-blue-600');
                replaceBtn.classList.add('hover:text-red-600');
                replaceBtn.title = 'Сбросить замену';

                ingredientRow.dataset.replaced = 'true';
                ingredientRow.dataset.originalName = currentReplaceIngredient.name;
                ingredientRow.dataset.replacementName = newName;
                ingredientRow.dataset.replacementRatio = ratio;
            } else if (ingredientRow && newName !== 'custom') {
                const newAmount = parseFloat(ingredientRow.querySelector('.ingredient-amount').innerText) * ratio;
                ingredientRow.querySelector('label').innerText = newName;
                ingredientRow.querySelector('.ingredient-amount').innerText = `${Math.round(newAmount)} ${currentReplaceIngredient.unit}`;
            }

            replaceModal.classList.add('hidden');
        });
    }

    // ======================= КНОПКА ℹ️ (информация об ингредиенте) =======================
    document.querySelectorAll('.info-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const id = this.dataset.id;
        const name = this.dataset.name;
        openInfoModal(id, name);
    });
});

    // Закрытие модалок по клику на фон
    if (replaceModal) {
        replaceModal.addEventListener('click', (e) => {
            if (e.target === replaceModal) replaceModal.classList.add('hidden');
        });
    }
    if (infoModal) {
        infoModal.addEventListener('click', (e) => {
            if (e.target === infoModal) infoModal.classList.add('hidden');
        });
    }



    // ======================= ПОРЦИИ =======================
    if (portionsSlider) {
        portionsSlider.addEventListener('input', function() {
            const val = parseInt(this.value);
            portionsValue.innerText = val;
            currentRatio = val / baseServings;
            updateAllIngredients(currentRatio);
            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${val} порций)`;
                updateURL();
            }
        });
    }

    if (resetPortionsBtn) {
        resetPortionsBtn.addEventListener('click', function() {
            portionsSlider.value = baseServings;
            portionsValue.innerText = baseServings;
            currentRatio = 1;
            updateAllIngredients(1);
            if (portionsRatioInfo) portionsRatioInfo.innerText = '';
            updateURL();
        });
    }

    // ======================= ЧЕКБОКСЫ =======================
    function saveCheckboxStates() {
        document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
            localStorage.setItem(`checkbox_${cb.id}`, cb.checked);
        });
    }

    function restoreCheckboxStates() {
        document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
            const saved = localStorage.getItem(`checkbox_${cb.id}`);
            if (saved === 'true') cb.checked = true;
        });
    }

    document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
        cb.addEventListener('change', saveCheckboxStates);
    });

    restoreCheckboxStates();

    // Отметить всё / Снять всё
    if (checkAllBtn) {
        checkAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = true);
            saveCheckboxStates();
        });
    }
    if (uncheckAllBtn) {
        uncheckAllBtn.addEventListener('click', () => {
            document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = false);
            saveCheckboxStates();
        });
    }

    // Копировать НЕОТМЕЧЕННЫЕ ингредиенты (то, чего нет в наличии)
    if (copyCheckedBtn) {
        copyCheckedBtn.addEventListener('click', () => {
            const items = [];
            document.querySelectorAll('.ingredient-row').forEach(row => {
                const cb = row.querySelector('.ingredient-checkbox');
                const label = row.querySelector('label');
                const amount = row.querySelector('.ingredient-amount')?.innerText;
                if (cb && !cb.checked && label) {
                    items.push(`${label.innerText} — ${amount}`);
                }
            });
            if (items.length === 0) {
                showToast('Все ингредиенты есть в наличии! 🎉', 'Отлично!', 'success');
            } else {
                navigator.clipboard.writeText(items.join('\n')).then(() => {
                    showToast(`Скопировано ${items.length} ингредиентов для покупки`, 'Готово!', 'success');
                }).catch(() => {
                    showToast('Не удалось скопировать список', 'Ошибка', 'error');
                });
            }
        });
    }

    // ======================= ШАГИ ПРИГОТОВЛЕНИЯ =======================
    function updateStepsProgress() {
        const stepCheckboxes = document.querySelectorAll('.step-checkbox');
        const total = stepCheckboxes.length;
        const completed = Array.from(stepCheckboxes).filter(cb => cb.checked).length;
        const percent = total ? (completed / total) * 100 : 0;
        const stepsProgressSpan = document.getElementById('stepsProgress');
        const stepsProgressBar = document.getElementById('stepsProgressBar');
        if (stepsProgressSpan) stepsProgressSpan.innerText = `${completed}/${total}`;
        if (stepsProgressBar) stepsProgressBar.style.width = `${percent}%`;

        document.querySelectorAll('.step-card').forEach((card, idx) => {
            if (stepCheckboxes[idx]?.checked) card.classList.add('completed');
            else card.classList.remove('completed');
        });
    }

    document.querySelectorAll('.step-checkbox').forEach(cb => {
        const saved = localStorage.getItem(`step_${cb.id}`);
        if (saved === 'true') cb.checked = true;
        cb.addEventListener('change', function() {
            localStorage.setItem(`step_${cb.id}`, cb.checked);
            updateStepsProgress();
        });
    });

    updateStepsProgress();

    // Кликабельные карточки шагов
    document.querySelectorAll('.step-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.type === 'checkbox' || e.target.closest('.step-checkbox')) {
                return;
            }
            if (e.target.closest('a') || e.target.closest('button')) return;
            const checkbox = card.querySelector('.step-checkbox');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    });

    // Настройка обработчиков для ссылок на вложенные рецепты
    setupSubrecipeLinks();

    // Восстанавливаем ratio из URL после инициализации
    setTimeout(restoreRatioFromURL, 100);

        // ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ ОТОБРАЖЕНИЯ ШАГОВ =======================
    function setStepsMode(mode) {
        if (!stepsContainer) return;

        if (mode === 'compact') {
            stepsContainer.classList.add('compact-mode');
            if (modeCompactBtn) {
                modeCompactBtn.classList.add('bg-white', 'shadow-sm');
                modeCompactBtn.classList.remove('text-gray-600');
            }
            if (modeNormalBtn) {
                modeNormalBtn.classList.remove('bg-white', 'shadow-sm');
                modeNormalBtn.classList.add('text-gray-600');
            }
            localStorage.setItem('steps_display_mode', 'compact');
        } else {
            stepsContainer.classList.remove('compact-mode');
            if (modeNormalBtn) {
                modeNormalBtn.classList.add('bg-white', 'shadow-sm');
                modeNormalBtn.classList.remove('text-gray-600');
            }
            if (modeCompactBtn) {
                modeCompactBtn.classList.remove('bg-white', 'shadow-sm');
                modeCompactBtn.classList.add('text-gray-600');
            }
            localStorage.setItem('steps_display_mode', 'normal');
        }
    }

    if (modeNormalBtn && modeCompactBtn) {
        modeNormalBtn.addEventListener('click', () => setStepsMode('normal'));
        modeCompactBtn.addEventListener('click', () => setStepsMode('compact'));

        const savedMode = localStorage.getItem('steps_display_mode');
        if (savedMode === 'compact') {
            setStepsMode('compact');
        }
    }

    console.log('Виджет инициализирован');
});

// ======================= МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================
let methodsCache = {};

async function showMethodDetails(button) {
    const methodId = button.dataset.methodId;
    const methodName = button.dataset.methodName;

    // Если нет метода (ID = none или default), показываем сообщение
    if (!methodId || methodId === 'none' || methodId === 'default') {
        const modal = document.getElementById('methodModal');
        if (!modal) return;
        document.getElementById('methodModalName').innerText = 'Нет информации';
        document.getElementById('methodModalDesc').innerHTML = '<p class="text-gray-500">Для этого шага не указан метод приготовления.</p>';
        modal.classList.remove('hidden');
        return;
    }

    const modal = document.getElementById('methodModal');
    if (!modal) return;

    document.getElementById('methodModalName').innerText = methodName;
    document.getElementById('methodModalDesc').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Загрузка...</div>';
    modal.classList.remove('hidden');

    try {
        if (methodsCache[methodId]) {
            displayMethodData(methodsCache[methodId]);
            return;
        }

        const response = await fetch(`/kitchen/api/method/${methodId}/`);
        if (response.ok) {
            const data = await response.json();
            methodsCache[methodId] = data;
            displayMethodData(data);
        } else {
            throw new Error('Метод не найден');
        }
    } catch (error) {
        console.error('Ошибка загрузки метода:', error);
        document.getElementById('methodModalDesc').innerHTML = '<p class="text-red-600">Не удалось загрузить описание метода.</p>';
    }
}

function displayMethodData(data) {
    document.getElementById('methodModalName').innerText = data.name;
    const iconElem = document.getElementById('methodModalIcon');
    if (iconElem) iconElem.className = `fas ${data.icon || 'fa-fire'} text-amber-600`;
    const shortDescElem = document.getElementById('methodModalShortDesc');
    if (shortDescElem) shortDescElem.innerText = data.short_description || '';
    document.getElementById('methodModalDesc').innerHTML = data.description || '';

    // Добавляем информацию о заменах
    if (data.substitutions && data.substitutions.length > 0) {
        const substitutionsHtml = data.substitutions.map(sub =>
            `<div class="mt-3 p-3 bg-amber-50 rounded-lg">
                <div class="flex items-center gap-2">
                    <i class="fas fa-exchange-alt text-amber-500"></i>
                    <span class="font-medium text-sm">Можно заменить на:</span>
                    <span class="text-sm font-semibold text-amber-700">${sub.name || sub.substitute_method?.name || ''}</span>
                </div>
                ${sub.reason ? `<p class="text-xs text-gray-600 mt-1 ml-6">${sub.reason}</p>` : ''}
                ${sub.notes ? `<p class="text-xs text-gray-500 mt-1 ml-6">${sub.notes}</p>` : ''}
            </div>`
        ).join('');

        const modalContent = document.getElementById('methodModalDesc');
        modalContent.innerHTML += `<div class="mt-4 border-t border-gray-200 pt-3">
            <h4 class="font-semibold text-sm text-gray-700 mb-2">✨ Возможные замены:</h4>
            ${substitutionsHtml}
        </div>`;
    }

    const scienceBlock = document.getElementById('methodModalScience');
    const scienceText = document.getElementById('methodModalScienceText');
    if (data.scientific_background && scienceBlock && scienceText) {
        scienceText.innerText = data.scientific_background;
        scienceBlock.classList.remove('hidden');
    } else if (scienceBlock) {
        scienceBlock.classList.add('hidden');
    }

    const tempBlock = document.getElementById('methodModalTemp');
    const tempText = document.getElementById('methodModalTempText');
    if (data.typical_temperature && tempBlock && tempText) {
        tempText.innerText = data.typical_temperature;
        tempBlock.classList.remove('hidden');
    } else if (tempBlock) {
        tempBlock.classList.add('hidden');
    }

    const durationBlock = document.getElementById('methodModalDuration');
    const durationText = document.getElementById('methodModalDurationText');
    if (data.typical_duration && durationBlock && durationText) {
        durationText.innerText = data.typical_duration;
        durationBlock.classList.remove('hidden');
    } else if (durationBlock) {
        durationBlock.classList.add('hidden');
    }

    const tipsBlock = document.getElementById('methodModalTips');
    const tipsText = document.getElementById('methodModalTipsText');
    if (data.tips && tipsBlock && tipsText) {
        tipsText.innerText = data.tips;
        tipsBlock.classList.remove('hidden');
    } else if (tipsBlock) {
        tipsBlock.classList.add('hidden');
    }

    const mistakesBlock = document.getElementById('methodModalMistakes');
    const mistakesText = document.getElementById('methodModalMistakesText');
    if (data.common_mistakes && mistakesBlock && mistakesText) {
        mistakesText.innerText = data.common_mistakes;
        mistakesBlock.classList.remove('hidden');
    } else if (mistakesBlock) {
        mistakesBlock.classList.add('hidden');
    }

    const advancedBlock = document.getElementById('methodModalAdvanced');
    const advancedText = document.getElementById('methodModalAdvancedText');
    if (data.advanced_notes && advancedBlock && advancedText) {
        advancedText.innerText = data.advanced_notes;
        advancedBlock.classList.remove('hidden');
    } else if (advancedBlock) {
        advancedBlock.classList.add('hidden');
    }
}

function closeMethodModal() {
    const modal = document.getElementById('methodModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= ПОДГОТОВКА ПРОДУКТОВ =======================
let preparationsCache = {};

async function showPreparationDetails(button) {
    const preparationId = button.dataset.preparationId;
    const preparationName = button.dataset.preparationName;

    // Если нет подготовки (ID = none или default)
    if (!preparationId || preparationId === 'none' || preparationId === 'default') {
        const modal = document.getElementById('preparationModal');
        if (!modal) return;
        document.getElementById('preparationModalName').innerText = 'Нет информации';
        document.getElementById('preparationModalDesc').innerHTML = '<p class="text-gray-500">Для этого шага не указана подготовка продуктов.</p>';
        modal.classList.remove('hidden');
        return;
    }

    const modal = document.getElementById('preparationModal');
    if (!modal) return;

    document.getElementById('preparationModalName').innerText = preparationName;
    document.getElementById('preparationModalDesc').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Загрузка...</div>';
    modal.classList.remove('hidden');

    try {
        if (preparationsCache[preparationId]) {
            displayPreparationData(preparationsCache[preparationId]);
            return;
        }

        const response = await fetch(`/kitchen/api/preparation/${preparationId}/`);
        if (response.ok) {
            const data = await response.json();
            preparationsCache[preparationId] = data;
            displayPreparationData(data);
        } else {
            throw new Error('Подготовка не найдена');
        }
    } catch (error) {
        console.error('Ошибка загрузки подготовки:', error);
        document.getElementById('preparationModalDesc').innerHTML = '<p class="text-red-600">Не удалось загрузить описание.</p>';
    }
}

function displayPreparationData(data) {
    document.getElementById('preparationModalName').innerText = data.name;
    document.getElementById('preparationModalDesc').innerHTML = data.description || '';

    const tipsBlock = document.getElementById('preparationModalTips');
    const tipsText = document.getElementById('preparationModalTipsText');
    if (data.tips && tipsBlock && tipsText) {
        tipsText.innerText = data.tips;
        tipsBlock.classList.remove('hidden');
    } else if (tipsBlock) {
        tipsBlock.classList.add('hidden');
    }

    const timeBlock = document.getElementById('preparationModalTime');
    const timeText = document.getElementById('preparationModalTimeText');
    if (data.time_factor && timeBlock && timeText) {
        timeText.innerText = `Увеличивает время приготовления в ${data.time_factor} раз`;
        timeBlock.classList.remove('hidden');
    } else if (timeBlock) {
        timeBlock.classList.add('hidden');
    }
}

function closePreparationModal() {
    const modal = document.getElementById('preparationModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= РЕКОМЕНДОВАННАЯ УТВАРЬ =======================
let utensilsCache = {};

async function showUtensilDetails(button) {
    const utensilId = button.dataset.utensilId;
    const utensilName = button.dataset.utensilName;

    // Если нет утвари (ID = none или default)
    if (!utensilId || utensilId === 'none' || utensilId === 'default') {
        const modal = document.getElementById('utensilModal');
        if (!modal) return;
        document.getElementById('utensilModalName').innerText = 'Нет информации';
        document.getElementById('utensilModalDesc').innerHTML = '<p class="text-gray-500">Для этого шага не указана рекомендуемая утварь.</p>';
        modal.classList.remove('hidden');
        return;
    }

    const modal = document.getElementById('utensilModal');
    if (!modal) return;

    document.getElementById('utensilModalName').innerText = utensilName;
    document.getElementById('utensilModalDesc').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Загрузка...</div>';
    modal.classList.remove('hidden');

    try {
        if (utensilsCache[utensilId]) {
            displayUtensilData(utensilsCache[utensilId]);
            return;
        }

        const response = await fetch(`/kitchen/api/utensil/${utensilId}/`);
        if (response.ok) {
            const data = await response.json();
            utensilsCache[utensilId] = data;
            displayUtensilData(data);
        } else {
            throw new Error('Утварь не найдена');
        }
    } catch (error) {
        console.error('Ошибка загрузки утвари:', error);
        document.getElementById('utensilModalDesc').innerHTML = '<p class="text-red-600">Не удалось загрузить описание.</p>';
    }
}

function displayUtensilData(data) {
    document.getElementById('utensilModalName').innerText = data.name;
    document.getElementById('utensilModalDesc').innerHTML = data.description || '';

    // Добавляем информацию о заменах утвари
    if (data.substitutions && data.substitutions.length > 0) {
        const substitutionsHtml = data.substitutions.map(sub =>
            `<div class="mt-2 p-2 bg-blue-50 rounded-lg">
                <div class="flex items-center gap-2">
                    <i class="fas fa-exchange-alt text-blue-500"></i>
                    <span class="font-medium text-sm">Можно заменить на:</span>
                    <span class="text-sm font-semibold text-blue-700">${sub.name || sub.substitute_utensil?.name || ''}</span>
                </div>
                ${sub.reason ? `<p class="text-xs text-gray-600 mt-1 ml-6">${sub.reason}</p>` : ''}
            </div>`
        ).join('');

        const modalContent = document.getElementById('utensilModalDesc');
        modalContent.innerHTML += `<div class="mt-3">
            <h4 class="font-semibold text-sm text-gray-700 mb-1">🔄 Возможные замены:</h4>
            ${substitutionsHtml}
        </div>`;
    }

    // Альтернатива и уход
    const altBlock = document.getElementById('utensilModalAlternative');
    const altText = document.getElementById('utensilModalAlternativeText');
    if (data.alternative && altBlock && altText) {
        altText.innerText = data.alternative;
        altBlock.classList.remove('hidden');
    } else if (altBlock) {
        altBlock.classList.add('hidden');
    }

    const careBlock = document.getElementById('utensilModalCare');
    const careText = document.getElementById('utensilModalCareText');
    if (data.care_instructions && careBlock && careText) {
        careText.innerText = data.care_instructions;
        careBlock.classList.remove('hidden');
    } else if (careBlock) {
        careBlock.classList.add('hidden');
    }
}


function closeMethodModal() {
    const modal = document.getElementById('methodModal');
    if (modal) modal.classList.add('hidden');
}

function closePreparationModal() {
    const modal = document.getElementById('preparationModal');
    if (modal) modal.classList.add('hidden');
}

function closeUtensilModal() {  // ← ДОБАВИТЬ ЭТУ ФУНКЦИЮ
    const modal = document.getElementById('utensilModal');
    if (modal) modal.classList.add('hidden');
}

function openInfoModal(ingredientId, ingredientName) {
    currentIngredientId = ingredientId;
    document.getElementById('infoModalName').innerText = ingredientName;

    const link = document.getElementById('fullIngredientInfoLink');
    if (link) {
        // Получаем параметры из текущего URL
        const urlParams = new URLSearchParams(window.location.search);

        // Сохраняем параметры возврата из текущей страницы
        const returnTo = window.location.pathname;
        const returnTitle = document.querySelector('h1')?.innerText || document.title || 'Рецепт';
        const returnStep = urlParams.get('step') || '';
        const returnContext = urlParams.get('return_context') || '';
        const returnMode = urlParams.get('mode') || '';
        const returnMeat = urlParams.get('meat') || '';
        const returnPortions = urlParams.get('portions') || '';
        const ratio = urlParams.get('ratio') || '';

        // Формируем URL для страницы ингредиента
        let url = `/kitchen/ingredient/${ingredientId}/`;
        const params = new URLSearchParams();

        if (returnTo) params.set('return_to', returnTo);
        if (returnTitle) params.set('return_title', returnTitle);
        if (returnStep) params.set('return_step', returnStep);
        if (returnContext) params.set('return_context', returnContext);
        if (returnMode) params.set('return_mode', returnMode);
        if (returnMeat) params.set('return_meat', returnMeat);
        if (returnPortions) params.set('return_portions', returnPortions);
        if (ratio) params.set('ratio', ratio);

        const queryString = params.toString();
        if (queryString) {
            url += '?' + queryString;
        }

        console.log('Redirecting to:', url);  // для отладки
        link.href = url;
    }

    const modal = document.getElementById('infoModal');
    if (modal) modal.classList.remove('hidden');
}

function closeInfoModal() {
    const modal = document.getElementById('infoModal');
    if (modal) modal.classList.add('hidden');
}

// Тост-уведомление
let toastTimeout = null;

function showToast(message, title = 'Готово!', type = 'success') {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;

    // Очищаем предыдущий таймер
    if (toastTimeout) clearTimeout(toastTimeout);

    // Настройка иконки и цвета в зависимости от типа
    const configs = {
        success: { icon: 'fa-check-circle', color: 'text-green-400', bg: 'bg-gray-800/95' },
        error: { icon: 'fa-exclamation-circle', color: 'text-red-400', bg: 'bg-gray-800/95' },
        warning: { icon: 'fa-exclamation-triangle', color: 'text-yellow-400', bg: 'bg-gray-800/95' },
        info: { icon: 'fa-info-circle', color: 'text-blue-400', bg: 'bg-gray-800/95' }
    };

    const config = configs[type] || configs.success;

    // Обновляем содержимое
    const iconSpan = toast.querySelector('#toastIcon');
    const titleSpan = toast.querySelector('#toastTitle');
    const messageSpan = toast.querySelector('#toastMessage');
    const container = toast.querySelector('div:first-child');

    if (iconSpan) iconSpan.className = `fas ${config.icon} ${config.color} text-xl`;
    if (titleSpan) titleSpan.innerText = title;
    if (messageSpan) messageSpan.innerHTML = message;
    if (container) container.className = `${config.bg} backdrop-blur-sm text-white rounded-xl shadow-2xl px-5 py-3.5 flex items-center gap-3 min-w-[260px]`;

    // Показываем тост
    toast.classList.remove('hidden');
    toast.classList.add('toast-show');
    toast.classList.remove('toast-hide');

    // Автоматическое скрытие через 3 секунды
    toastTimeout = setTimeout(() => {
        closeToast();
    }, 3000);
}

function closeToast() {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;

    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');

    setTimeout(() => {
        toast.classList.add('hidden');
        toast.classList.remove('toast-hide');
    }, 300);
}

// Делаем функции глобальными для доступа из HTML
window.showMethodDetails = showMethodDetails;
window.closeMethodModal = closeMethodModal;
window.showPreparationDetails = showPreparationDetails;
window.closePreparationModal = closePreparationModal;
window.showUtensilDetails = showUtensilDetails;
window.closeUtensilModal = closeUtensilModal;  // ← теперь функция существует
window.closeInfoModal = closeInfoModal;
window.showToast = showToast;
window.closeToast = closeToast;
window.openInfoModal = openInfoModal;

//Дополнительно: очередь тостов (для нескольких уведомлений):
//javascript
//let toastQueue = [];
//let isToastShowing = false;
//
//function showToast(message, title = 'Готово!', type = 'success') {
//    toastQueue.push({ message, title, type });
//    processToastQueue();
//}
//
//function processToastQueue() {
//    if (isToastShowing || toastQueue.length === 0) return;
//
//    isToastShowing = true;
//    const { message, title, type } = toastQueue.shift();
//
//    // Показываем тост (как в предыдущем примере)
//    const toast = document.getElementById('toastNotification');
//    if (!toast) return;
//
//    // ... код отображения тоста (из пункта 3) ...
//
//    toastTimeout = setTimeout(() => {
//        closeToast();
//        setTimeout(() => {
//            isToastShowing = false;
//            processToastQueue();
//        }, 300);
//    }, 3000);
//}