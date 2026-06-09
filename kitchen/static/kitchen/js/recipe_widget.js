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
            if (link._handler) {
                link.removeEventListener('click', link._handler);
            }

            const handler = function(e) {
                e.preventDefault();

                let currentRatioValue;

                if (currentMode === 'products' && currentBaseIngredient) {
                    currentRatioValue = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                } else if (currentMode === 'portions' && portionsSlider) {
                    currentRatioValue = parseInt(portionsSlider.value) / baseServings;
                } else {
                    currentRatioValue = currentRatio;
                }

                let url = new URL(this.href);
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
                window.location.href = url.toString();
            };

            link._handler = handler;
            link.addEventListener('click', handler);
        });
    }

    // ======================= ОБНОВЛЕНИЕ ССЫЛОК НА ВЛОЖЕННЫЕ РЕЦЕПТЫ =======================
    function updateSubrecipeLinks() {
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
                displayValue = Math.ceil(calculatedValue);
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
        const currentParams = new URLSearchParams(window.location.search);

        const returnTo = currentParams.get('return_to');
        const returnTitle = currentParams.get('return_title');
        const returnStep = currentParams.get('return_step');
        const returnContext = currentParams.get('return_context');
        const returnMode = currentParams.get('return_mode');
        const returnMeat = currentParams.get('return_meat');
        const returnPortions = currentParams.get('return_portions');

        const params = new URLSearchParams();

        if (returnTo) params.set('return_to', returnTo);
        if (returnTitle) params.set('return_title', returnTitle);
        if (returnStep) params.set('return_step', returnStep);
        if (returnContext) params.set('return_context', returnContext);
        if (returnMode) params.set('return_mode', returnMode);
        if (returnMeat) params.set('return_meat', returnMeat);
        if (returnPortions) params.set('return_portions', returnPortions);

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

        let baseBtn = null;
        if (baseIngredientId) {
            baseBtn = document.querySelector(`.chain-btn[data-id="${baseIngredientId}"]`);
            console.log('Поиск ингредиента с id', baseIngredientId, ':', baseBtn ? 'найден' : 'не найден');
        }

        if (modeFromURL === 'products' && baseIngredientId && baseValue && baseBtn) {
            console.log('Восстанавливаем режим продуктов (ингредиент найден)');

            currentMode = 'products';

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

            const originalValue = parseFloat(baseBtn.dataset.quantity);
            const newValue = parseFloat(baseValue);
            const name = baseBtn.dataset.name;
            const unit = baseBtn.dataset.unit;

            currentBaseIngredient = {
                id: baseIngredientId,
                name: name,
                originalValue: originalValue,
                unit: unit,
                currentValue: newValue
            };

            baseIngredientName.innerText = name;
            baseOriginalValue.innerText = `${originalValue} ${unit}`;
            baseIngredientWeight.value = newValue;
            baseIngredientRow.classList.remove('hidden');
            applyBaseBtn.classList.remove('hidden');

            document.querySelectorAll('.chain-btn').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });
            baseBtn.classList.remove('text-gray-400');
            baseBtn.classList.add('text-amber-600');

            if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
                const ratio = parseFloat(ratioFromURL);
                currentRatio = ratio;
                updateAllIngredients(ratio);
                console.log('Вызов updateAllIngredients с ratio:', ratio);
            }

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newValue} ${unit} ${name})`;
            }

            updateSubrecipeLinks();
            setupSubrecipeLinks();
            updateURL();

            console.log('=== restoreRatioFromURL END (products) ===');
            console.log('currentMode:', currentMode);
            console.log('currentRatio:', currentRatio);

            return;
        }

        if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
            console.log('Восстанавливаем режим порций из ratio');

            currentMode = 'portions';

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

            const ratio = parseFloat(ratioFromURL);
            const portions = Math.round(ratio * baseServings);

            // ======================= ПОРЦИИ =======================
            if (portionsSlider) {
                portionsSlider.addEventListener('input', function() {
                    const val = parseInt(this.value);
                    portionsValue.innerText = val;
                    currentRatio = val / baseServings;

                    // 🔥 ВАЖНО: обновляем currentRatio глобально
                    window.currentRatio = currentRatio;

                    updateAllIngredients(currentRatio);
                    if (portionsRatioInfo) {
                        portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${val} порций)`;
                        updateURL();
                    }
                });
            }

            updateSubrecipeLinks();
            setupSubrecipeLinks();
            updateURL();

            console.log('=== restoreRatioFromURL END (portions from ratio) ===');
            console.log('currentMode:', currentMode);
            console.log('currentRatio:', currentRatio);

            return;
        }

        if (modeFromURL === 'portions' || portionsFromURL) {
            console.log('Восстанавливаем режим порций');

            currentMode = 'portions';

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

            updateSubrecipeLinks();
            setupSubrecipeLinks();
            updateURL();

            console.log('=== restoreRatioFromURL END (portions) ===');
            console.log('currentMode:', currentMode);
            console.log('currentRatio:', currentRatio);

            return;
        }

        console.log('Нет параметров, используем порции по умолчанию');
        currentMode = 'portions';
        updateAllIngredients(1);

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

        // Запоминаем текущий коэффициент ДО переключения
        const previousMode = currentMode;
        const previousRatio = currentRatio;

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

            // При переключении из режима продуктов в режим порций
            if (previousMode === 'products' && currentBaseIngredient) {
                // Берём текущий коэффициент из базового ингредиента
                const ratioFromProduct = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                const newPortions = Math.round(ratioFromProduct * baseServings);

                if (portionsSlider && newPortions >= 1 && newPortions <= 20) {
                    portionsSlider.value = newPortions;
                    if (portionsValue) portionsValue.innerText = newPortions;
                    currentRatio = ratioFromProduct;
                    updateAllIngredients(currentRatio);
                    if (portionsRatioInfo) {
                        portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newPortions} порций)`;
                    }
                }
            } else {
                // Обычное переключение
                const portions = parseInt(portionsSlider.value);
                currentRatio = portions / baseServings;
                updateAllIngredients(currentRatio);
                if (portionsRatioInfo) {
                    portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${portions} порций)`;
                }
            }

            updateURL();

        } else { // mode === 'products'
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

            // При переключении из режима порций в режим продуктов
            if (previousMode === 'portions') {
                // Берём текущий коэффициент из режима порций
                const ratioFromPortions = currentRatio;

                // Находим первый ингредиент для создания базового
                if (ingredients.length > 0) {
                    const firstIngredient = ingredients[0];
                    const newBaseValue = firstIngredient.baseQuantity * ratioFromPortions;

                    // Создаём базовый ингредиент с правильным коэффициентом
                    currentBaseIngredient = {
                        id: firstIngredient.id,
                        name: firstIngredient.name,
                        originalValue: firstIngredient.baseQuantity,
                        unit: firstIngredient.unit,
                        currentValue: newBaseValue
                    };

                    // Обновляем UI
                    baseIngredientName.innerText = firstIngredient.name;
                    baseOriginalValue.innerText = `${firstIngredient.baseQuantity} ${firstIngredient.unit}`;
                    baseIngredientWeight.value = newBaseValue;
                    baseIngredientRow.classList.remove('hidden');
                    applyBaseBtn.classList.remove('hidden');

                    // Подсвечиваем соответствующую кнопку 🔗
                    document.querySelectorAll('.chain-btn').forEach(btn => {
                        btn.classList.remove('text-amber-600');
                        btn.classList.add('text-gray-400');
                        if (btn.dataset.id == firstIngredient.id) {
                            btn.classList.remove('text-gray-400');
                            btn.classList.add('text-amber-600');
                        }
                    });

                    // Обновляем ингредиенты с новым коэффициентом
                    currentRatio = ratioFromPortions;
                    updateAllIngredients(currentRatio);

                    if (baseRatioInfo) {
                        baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newBaseValue.toFixed(1)} ${firstIngredient.unit} ${firstIngredient.name})`;
                    }
                } else {
                    // Если нет ингредиентов, просто обновляем
                    updateAllIngredients(currentRatio);
                }
            } else if (currentBaseIngredient) {
                // Уже есть базовый ингредиент, просто обновляем
                const ratio = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                updateAllIngredients(ratio);
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
                }
            }

            updateURL();
        }
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

    // Сброс базового ингредиента (остаёмся в режиме продуктов)
if (resetBaseBtn) {
    resetBaseBtn.addEventListener('click', function() {
        // 1. Сбрасываем базовый ингредиент
        currentBaseIngredient = null;

        // 2. Сбрасываем коэффициент к 1
        currentRatio = 1;

        // 3. Обновляем все ингредиенты с ratio = 1
        updateAllIngredients(1);

        // 4. Обновляем UI (убираем отображение базового ингредиента)
        updateBaseIngredientUI();

        // 5. Очищаем информационную строку
        if (baseRatioInfo) {
            baseRatioInfo.innerText = '';
        }

        // 6. Синхронизируем ползунок порций с базовым значением
        if (portionsSlider) {
            portionsSlider.value = baseServings;
            if (portionsValue) portionsValue.innerText = baseServings;
        }

        // 7. Обновляем ссылки на вложенные рецепты и URL
        updateSubrecipeLinks();
        updateURL();

        // 8. Меняем активный класс кнопки "По продуктам" (гарантия)
        if (modeProductsBtn) {
            modeProductsBtn.classList.add('bg-amber-600', 'text-white');
            modeProductsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
        }
        if (modePortionsBtn) {
            modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
            modePortionsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');
        }
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
            const response = await fetch(`/cooking/api/substitutions/${recipeIngredientId}/`);
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

    // Копировать НЕОТМЕЧЕННЫЕ ингредиенты
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

        if (total > 0) {
            const recipeIdMatch = window.location.pathname.match(/\/recipe\/(\d+)\//);
            const recipeId = recipeIdMatch ? recipeIdMatch[1] : null;

            if (recipeId) {
                fetch('/cooking/api/update_progress/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        recipe_id: parseInt(recipeId),
                        progress: Math.round(percent)
                    })
                }).catch(err => console.error('Ошибка сохранения прогресса:', err));
            }
        }
    }

    // Инициализация чекбоксов шагов
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        const saved = localStorage.getItem(`step_${cb.id}`);
        if (saved === 'true') cb.checked = true;

        cb.addEventListener('change', function() {
            localStorage.setItem(`step_${cb.id}`, cb.checked);
            updateStepsProgress();
        });
    });

    // Первоначальный расчёт прогресса
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

        const response = await fetch(`/cooking/api/method/${methodId}/`);
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

        const response = await fetch(`/cooking/api/preparation/${preparationId}/`);
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

        const response = await fetch(`/cooking/api/utensil/${utensilId}/`);
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

function closeUtensilModal() {
    const modal = document.getElementById('utensilModal');
    if (modal) modal.classList.add('hidden');
}

function openInfoModal(ingredientId, ingredientName) {
    currentIngredientId = ingredientId;
    document.getElementById('infoModalName').innerText = ingredientName;

    const link = document.getElementById('fullIngredientInfoLink');
    if (link) {
        const urlParams = new URLSearchParams(window.location.search);
        const returnTo = window.location.pathname;
        const returnTitle = document.querySelector('h1')?.innerText || document.title || 'Рецепт';
        const returnStep = urlParams.get('step') || '';
        const returnContext = urlParams.get('return_context') || '';
        const returnMode = urlParams.get('mode') || '';
        const returnMeat = urlParams.get('meat') || '';
        const returnPortions = urlParams.get('portions') || '';
        const ratio = urlParams.get('ratio') || '';

        let url = `/cooking/ingredient/${ingredientId}/`;
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

        console.log('Redirecting to:', url);
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

    if (toastTimeout) clearTimeout(toastTimeout);

    const configs = {
        success: { icon: 'fa-check-circle', color: 'text-green-400', bg: 'bg-gray-800/95' },
        error: { icon: 'fa-exclamation-circle', color: 'text-red-400', bg: 'bg-gray-800/95' },
        warning: { icon: 'fa-exclamation-triangle', color: 'text-yellow-400', bg: 'bg-gray-800/95' },
        info: { icon: 'fa-info-circle', color: 'text-blue-400', bg: 'bg-gray-800/95' }
    };

    const config = configs[type] || configs.success;

    const iconSpan = toast.querySelector('#toastIcon');
    const titleSpan = toast.querySelector('#toastTitle');
    const messageSpan = toast.querySelector('#toastMessage');
    const container = toast.querySelector('div:first-child');

    if (iconSpan) iconSpan.className = `fas ${config.icon} ${config.color} text-xl`;
    if (titleSpan) titleSpan.innerText = title;
    if (messageSpan) messageSpan.innerHTML = message;
    if (container) container.className = `${config.bg} backdrop-blur-sm text-white rounded-xl shadow-2xl px-5 py-3.5 flex items-center gap-3 min-w-[260px]`;

    toast.classList.remove('hidden');
    toast.classList.add('toast-show');
    toast.classList.remove('toast-hide');

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

// Функция для получения CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Делаем функции глобальными для доступа из HTML
window.showMethodDetails = showMethodDetails;
window.closeMethodModal = closeMethodModal;
window.showPreparationDetails = showPreparationDetails;
window.closePreparationModal = closePreparationModal;
window.showUtensilDetails = showUtensilDetails;
window.closeUtensilModal = closeUtensilModal;
window.closeInfoModal = closeInfoModal;
window.showToast = showToast;
window.closeToast = closeToast;
window.openInfoModal = openInfoModal;