// kitchen/static/kitchen/js/recipe_widget.js

// ======================= УПРАВЛЕНИЕ КОНТЕКСТОМ РЕЦЕПТА =======================

/**
 * Сохраняет контекст рецепта в sessionStorage
 */
function saveRecipeContext(recipeId, title, image, path, mode, portions, ratio) {
    const context = {
        id: recipeId,
        title: title || '',
        image: image || '',
        path: path || window.location.pathname,
        mode: mode || 'portions',
        portions: portions || null,
        ratio: ratio || null,
        timestamp: Date.now()
    };

    try {
        sessionStorage.setItem('recipe_context', JSON.stringify(context));
        console.log('✅ Контекст рецепта сохранён:', context);
    } catch (e) {
        console.warn('⚠️ Не удалось сохранить контекст в sessionStorage:', e);
    }
}

/**
 * Восстанавливает контекст рецепта из sessionStorage
 */
function getRecipeContext() {
    try {
        const data = sessionStorage.getItem('recipe_context');
        if (data) {
            const context = JSON.parse(data);
            console.log('📦 Контекст рецепта восстановлен:', context);
            return context;
        }
    } catch (e) {
        console.warn('⚠️ Не удалось восстановить контекст:', e);
    }
    return null;
}

/**
 * Очищает контекст рецепта (при выходе из рецепта)
 */
function clearRecipeContext() {
    try {
        sessionStorage.removeItem('recipe_context');
        console.log('🗑️ Контекст рецепта очищен');
    } catch (e) {
        console.warn('⚠️ Не удалось очистить контекст:', e);
    }
}

/**
 * Обновляет контекст рецепта (например, при изменении порций)
 */
function updateRecipeContext(updates) {
    const context = getRecipeContext();
    if (context) {
        Object.assign(context, updates);
        try {
            sessionStorage.setItem('recipe_context', JSON.stringify(context));
            console.log('🔄 Контекст обновлён:', context);
        } catch (e) {
            console.warn('⚠️ Не удалось обновить контекст:', e);
        }
    }
}

// Делаем функции глобальными для доступа из HTML
window.saveRecipeContext = saveRecipeContext;
window.getRecipeContext = getRecipeContext;
window.clearRecipeContext = clearRecipeContext;
window.updateRecipeContext = updateRecipeContext;

// ======================= ОСНОВНОЙ СКРИПТ =======================

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
    const stepsContainer = document.getElementById('stepsList');

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

    // ======================= ФУНКЦИЯ ОБНОВЛЕНИЯ ВСЕХ ИНГРЕДИЕНТОВ =======================
    function updateAllIngredients(ratio) {
        console.log('updateAllIngredients вызван с ratio:', ratio);
        console.log('Ингредиентов для обновления:', ingredients.length);

        ingredients.forEach(ing => {
            const calculatedValue = ing.baseQuantity * ratio;

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
        setTimeout(updateNutritionOnChange, 100);
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

            // Сохраняем существующие параметры return_*
            // Не удаляем их!
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

            // НЕ УДАЛЯЕМ return_* параметры!

            link.href = url.toString();
        } catch(e) {
            console.error('Ошибка обновления ссылки:', e);
        }
    });
}

    // ======================= ОБРАБОТЧИК КЛИКОВ ПО ССЫЛКАМ НА ВЛОЖЕННЫЕ РЕЦЕПТЫ =======================
    function setupSubrecipeLinks() {
        document.querySelectorAll('.subrecipe-link').forEach(link => {
            if (link._handler) {
                link.removeEventListener('click', link._handler);
            }

            const handler = function(e) {
                e.preventDefault();

                const recipeId = window.location.pathname.match(/\/recipe\/(\d+)\//)?.[1] || null;
                const recipeTitle = document.querySelector('h1')?.innerText || document.title || 'Рецепт';
                const recipeImage = document.querySelector('.relative img:first-child')?.src || '';

                const urlParams = new URLSearchParams(window.location.search);
                const currentModeParam = urlParams.get('mode') || 'portions';
                const currentPortions = urlParams.get('portions') || null;
                const currentRatioParam = urlParams.get('ratio') || null;

                saveRecipeContext(
                    recipeId,
                    recipeTitle,
                    recipeImage,
                    window.location.pathname,
                    currentModeParam,
                    currentPortions,
                    currentRatioParam ? parseFloat(currentRatioParam) : 1
                );

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

//                url.searchParams.delete('return_to');
//                url.searchParams.delete('return_title');
//                url.searchParams.delete('return_image');
//                url.searchParams.delete('return_step');
//                url.searchParams.delete('return_context');
//                url.searchParams.delete('return_mode');
//                url.searchParams.delete('return_portions');

                window.location.href = url.toString();
            };

            link._handler = handler;
            link.addEventListener('click', handler);
        });
    }

    // ======================= ВОССТАНОВЛЕНИЕ RATIO ИЗ URL =======================
    function restoreRatioFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const ratioFromURL = urlParams.get('ratio');
        const modeFromURL = urlParams.get('mode');
        const baseIngredientId = urlParams.get('base_ingredient');
        const baseValue = urlParams.get('base_value');
        const portionsFromURL = urlParams.get('portions');

        let baseBtn = null;
        if (baseIngredientId) {
            baseBtn = document.querySelector(`.chain-btn[data-id="${baseIngredientId}"]`);
        }

        if (modeFromURL === 'products' && baseIngredientId && baseValue && baseBtn) {
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
            }

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newValue} ${unit} ${name})`;
            }

            updateSubrecipeLinks();
            setupSubrecipeLinks();
            updateURL();
            return;
        }

        if (ratioFromURL && !isNaN(parseFloat(ratioFromURL))) {
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

            if (portionsSlider && portions > 0 && portions <= 20) {
                portionsSlider.value = portions;
                if (portionsValue) portionsValue.innerText = portions;

                currentRatio = ratio;
                updateAllIngredients(ratio);

                if (portionsRatioInfo) {
                    portionsRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${portions} порций)`;
                }
            }

            updateSubrecipeLinks();
            setupSubrecipeLinks();
            updateURL();
            return;
        }

        if (modeFromURL === 'portions' || portionsFromURL) {
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
            return;
        }

        currentMode = 'portions';
        updateAllIngredients(1);

        updateSubrecipeLinks();
        setupSubrecipeLinks();
        updateURL();
    }

    // ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ =======================
    function setMode(mode) {
        const previousMode = currentMode;
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

            if (previousMode === 'products' && currentBaseIngredient) {
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

            if (previousMode === 'portions') {
                const ratioFromPortions = currentRatio;

                if (ingredients.length > 0) {
                    const firstIngredient = ingredients[0];
                    const newBaseValue = firstIngredient.baseQuantity * ratioFromPortions;

                    currentBaseIngredient = {
                        id: firstIngredient.id,
                        name: firstIngredient.name,
                        originalValue: firstIngredient.baseQuantity,
                        unit: firstIngredient.unit,
                        currentValue: newBaseValue
                    };

                    baseIngredientName.innerText = firstIngredient.name;
                    baseOriginalValue.innerText = `${firstIngredient.baseQuantity} ${firstIngredient.unit}`;
                    baseIngredientWeight.value = newBaseValue;
                    baseIngredientRow.classList.remove('hidden');
                    applyBaseBtn.classList.remove('hidden');

                    document.querySelectorAll('.chain-btn').forEach(btn => {
                        btn.classList.remove('text-amber-600');
                        btn.classList.add('text-gray-400');
                        if (btn.dataset.id == firstIngredient.id) {
                            btn.classList.remove('text-gray-400');
                            btn.classList.add('text-amber-600');
                        }
                    });

                    currentRatio = ratioFromPortions;
                    updateAllIngredients(currentRatio);

                    if (baseRatioInfo) {
                        baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newBaseValue.toFixed(1)} ${firstIngredient.unit} ${firstIngredient.name})`;
                    }
                } else {
                    updateAllIngredients(currentRatio);
                }
            } else if (currentBaseIngredient) {
                const ratio = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
                updateAllIngredients(ratio);
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
                }
            }

            updateURL();
        }
        setTimeout(updateNutritionOnChange, 50);
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
            if (!currentBaseIngredient) return;

            currentBaseIngredient = null;
            currentRatio = 1;
            updateAllIngredients(1);

            if (portionsSlider) {
                portionsSlider.value = baseServings;
                if (portionsValue) portionsValue.innerText = baseServings;
            }

            setMode('portions');
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
                fetch('/kitchen/api/update_progress/', {
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

    // ======================= КНОПКА ℹ️ (информация об ингредиенте) =======================
    document.querySelectorAll('.info-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const id = this.dataset.id;
            const name = this.dataset.name;
            console.log('Кнопка информации нажата:', { id, name });
            openInfoModal(id, name);
        });
    });

    // ======================= КНОПКА ⟳ (замена ингредиента) =======================
    document.querySelectorAll('.replace-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const id = this.dataset.id;
            const name = this.dataset.name;
            const row = this.closest('.ingredient-row');
            const unit = row?.dataset?.unit || 'г';
            console.log('Кнопка замены нажата:', { id, name, unit });
            openReplaceModal(id, name, unit);
        });
    });

    // ======================= ОБРАБОТЧИКИ МОДАЛЬНОГО ОКНА ЗАМЕНЫ =======================
    if (cancelReplaceBtn) {
        cancelReplaceBtn.addEventListener('click', function() {
            if (replaceModal) replaceModal.classList.add('hidden');
        });
    }

    if (confirmReplaceBtn) {
        confirmReplaceBtn.addEventListener('click', function() {
            const selectedOption = replaceWithSelect;
            const replaceRatioInput = replaceRatio;
            const replaceOriginalNameEl = replaceOriginalName;

            if (!selectedOption || !replaceRatioInput) return;

            const newName = selectedOption.value;
            const ratio = parseFloat(replaceRatioInput.value) || 1;

            // Находим строку ингредиента по имени
            const rows = document.querySelectorAll('.ingredient-row');
            let targetRow = null;
            rows.forEach(row => {
                const label = row.querySelector('label');
                if (label && label.innerText === replaceOriginalNameEl?.innerText) {
                    targetRow = row;
                }
            });

            if (targetRow && newName !== 'custom') {
                const label = targetRow.querySelector('label');
                const amountSpan = targetRow.querySelector('.ingredient-amount');
                const currentAmount = parseFloat(amountSpan?.innerText) || 0;
                const newAmount = currentAmount * ratio;

                if (label) label.innerText = newName;
                if (amountSpan) {
                    const unit = targetRow.dataset.unit || 'г';
                    amountSpan.innerText = `${Math.round(newAmount)} ${unit}`;
                }

                // Меняем кнопку замены на кнопку сброса
                const replaceBtn = targetRow.querySelector('.replace-btn');
                if (replaceBtn) {
                    replaceBtn.innerHTML = '<i class="fas fa-undo-alt"></i>';
                    replaceBtn.classList.remove('hover:text-blue-600');
                    replaceBtn.classList.add('hover:text-red-600');
                    replaceBtn.title = 'Сбросить замену';
                    replaceBtn.dataset.replaced = 'true';
                }
            }

            if (replaceModal) replaceModal.classList.add('hidden');

            // Пересчитываем КБЖУ
            setTimeout(updateNutritionOnChange, 100);
        });
    }

    // Закрытие по клику на фон
    if (replaceModal) {
        replaceModal.addEventListener('click', function(e) {
            if (e.target === replaceModal) {
                replaceModal.classList.add('hidden');
            }
        });
    }

    // Закрытие модалки информации по клику на фон
    if (infoModal) {
        infoModal.addEventListener('click', function(e) {
            if (e.target === infoModal) {
                infoModal.classList.add('hidden');
            }
        });
    }

    // Настройка обработчиков для ссылок на вложенные рецепты
    setupSubrecipeLinks();

    // Восстанавливаем ratio из URL после инициализации
    setTimeout(restoreRatioFromURL, 100);

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
    document.getElementById('methodModalDesc').innerHTML = data.description || '';
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
}

function closeUtensilModal() {
    const modal = document.getElementById('utensilModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= ЗАМЕНА ИНГРЕДИЕНТА =======================

async function openReplaceModal(recipeIngredientId, ingredientName, unit) {
    console.log('openReplaceModal вызван:', { recipeIngredientId, ingredientName, unit });

    const modal = document.getElementById('replaceModal');
    if (!modal) {
        console.error('Модальное окно replaceModal не найдено!');
        return;
    }

    const replaceOriginalNameEl = document.getElementById('replaceOriginalName');
    const replaceOriginalUnitEl = document.getElementById('replaceOriginalUnit');
    const replaceNewUnitEl = document.getElementById('replaceNewUnit');
    const replaceRatioInput = document.getElementById('replaceRatio');
    const replaceWithSelectEl = document.getElementById('replaceWithSelect');

    if (replaceOriginalNameEl) replaceOriginalNameEl.innerText = ingredientName;
    if (replaceOriginalUnitEl) replaceOriginalUnitEl.innerText = unit;
    if (replaceNewUnitEl) replaceNewUnitEl.innerText = unit;
    if (replaceRatioInput) replaceRatioInput.value = 1;

    modal.classList.remove('hidden');

    if (replaceWithSelectEl) {
        replaceWithSelectEl.innerHTML = '<option value="">Загрузка вариантов замен...</option>';

        try {
            const response = await fetch(`/kitchen/api/substitutions/${recipeIngredientId}/`);
            if (response.ok) {
                const data = await response.json();

                replaceWithSelectEl.innerHTML = '<option value="custom">✏️ Другой ингредиент (ввести вручную)</option>';

                if (data.substitutions && data.substitutions.length > 0) {
                    data.substitutions.forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.name;
                        option.textContent = `${sub.name} (${sub.ratio} ${sub.unit} вместо 1 ${unit})`;
                        option.dataset.ratio = sub.ratio;
                        option.dataset.unit = sub.unit;
                        option.dataset.notes = sub.notes || '';
                        replaceWithSelectEl.appendChild(option);
                    });

                    replaceWithSelectEl.onchange = function() {
                        const selected = this.options[this.selectedIndex];
                        if (selected.value !== 'custom' && selected.dataset.ratio) {
                            if (replaceRatioInput) replaceRatioInput.value = selected.dataset.ratio;
                            if (replaceNewUnitEl) replaceNewUnitEl.innerText = selected.dataset.unit;
                        } else {
                            if (replaceRatioInput) replaceRatioInput.value = 1;
                            if (replaceNewUnitEl) replaceNewUnitEl.innerText = unit;
                        }
                    };
                }
            } else {
                throw new Error('Ошибка загрузки замен');
            }
        } catch (error) {
            console.error('Ошибка загрузки замен:', error);
            replaceWithSelectEl.innerHTML = '<option value="custom">✏️ Другой ингредиент (ошибка загрузки)</option>';
        }
    }
}

function closeReplaceModal() {
    const modal = document.getElementById('replaceModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= ИНФОРМАЦИЯ ОБ ИНГРЕДИЕНТЕ =======================

function openInfoModal(ingredientId, ingredientName) {
    console.log('openInfoModal вызван:', { ingredientId, ingredientName });

    const modal = document.getElementById('infoModal');
    if (!modal) return;

    const nameElement = document.getElementById('infoModalName');
    if (nameElement) nameElement.innerText = ingredientName;

    const link = document.getElementById('fullIngredientInfoLink');
    if (link) {
        const context = getRecipeContext();

        let returnTo, returnTitle, returnImage, returnMode, returnPortions, ratio, returnStep, returnContext;

        if (context) {
            returnTo = context.path || window.location.pathname;
            returnTitle = context.title || document.querySelector('h1')?.innerText || 'Рецепт';
            returnImage = context.image || '';
            returnMode = context.mode || 'portions';
            returnPortions = context.portions || null;
            ratio = context.ratio || null;
            returnStep = null;
            returnContext = null;
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            returnTo = window.location.pathname;
            returnTitle = document.querySelector('h1')?.innerText || document.title || 'Рецепт';
            returnImage = document.querySelector('.relative img:first-child')?.src || '';
            returnMode = urlParams.get('mode') || 'portions';
            returnPortions = urlParams.get('portions') || null;
            ratio = urlParams.get('ratio') || null;
            returnStep = urlParams.get('step') || null;
            returnContext = urlParams.get('return_context') || null;
        }

        let url = `/kitchen/ingredient/${ingredientId}/`;
        const params = new URLSearchParams();

        if (returnTo) params.set('return_to', returnTo);
        if (returnTitle) params.set('return_title', returnTitle);
        if (returnImage) params.set('return_image', returnImage);
        if (returnStep) params.set('return_step', returnStep);
        if (returnContext) params.set('return_context', returnContext);
        if (returnMode) params.set('return_mode', returnMode);
        if (returnPortions) params.set('return_portions', returnPortions);
        if (ratio) params.set('ratio', ratio);

        const queryString = params.toString();
        if (queryString) {
            url += '?' + queryString;
        }

        link.href = url;
    }

    modal.classList.remove('hidden');
}

function closeInfoModal() {
    const modal = document.getElementById('infoModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= ТОСТ-УВЕДОМЛЕНИЕ =======================
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

    toastTimeout = setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

function closeToast() {
    const toast = document.getElementById('toastNotification');
    if (toast) {
        toast.classList.add('hidden');
        if (toastTimeout) clearTimeout(toastTimeout);
    }
}

// ======================= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =======================

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

// ======================= ПЕРЕСЧЕТ КБЖУ =======================

const nutritionCache = {};

async function fetchIngredientNutrition(ingredientId) {
    if (nutritionCache[ingredientId]) return nutritionCache[ingredientId];

    try {
        const response = await fetch(`/kitchen/api/ingredient/${ingredientId}/`);
        if (response.ok) {
            const data = await response.json();
            nutritionCache[ingredientId] = {
                calories: data.calories || 0,
                protein: data.protein || 0,
                fat: data.fat || 0,
                carbohydrates: data.carbohydrates || 0
            };
            return nutritionCache[ingredientId];
        }
    } catch (error) {
        console.error(`Ошибка загрузки данных для ингредиента ${ingredientId}:`, error);
    }
    return { calories: 0, protein: 0, fat: 0, carbohydrates: 0 };
}

async function recalculateNutrition() {
    const rows = document.querySelectorAll('#ingredientsList .ingredient-row');

    if (rows.length === 0) {
        console.log('Нет ингредиентов для расчета КБЖУ');
        return;
    }

    let totalCalories = 0;
    let totalProtein = 0;
    let totalFat = 0;
    let totalCarbs = 0;

    // Собираем все промисы для параллельной загрузки
    const nutritionPromises = Array.from(rows).map(async (row) => {
        const infoBtn = row.querySelector('.info-btn');
        const ingredientId = infoBtn?.dataset.id;
        if (!ingredientId) return null;

        const amountSpan = row.querySelector('.ingredient-amount');
        const amountText = amountSpan?.innerText || '';
        const amountMatch = amountText.match(/^([\d\.]+)/);
        if (!amountMatch) return null;

        const amount = parseFloat(amountMatch[1]);
        const unit = row.dataset.unit || 'г';

        // Проверяем кэш перед запросом
        if (nutritionCache[ingredientId]) {
            const nutrition = nutritionCache[ingredientId];
            let multiplier = 1;
            if (unit === 'г' || unit === 'мл') {
                multiplier = amount / 100;
            } else if (unit === 'кг' || unit === 'л') {
                multiplier = (amount * 1000) / 100;
            } else if (unit === 'шт' || unit === 'ст.л.' || unit === 'ч.л.' || unit === 'зубч.') {
                let estimatedWeight = 0;
                if (unit === 'шт') estimatedWeight = 100;
                else if (unit === 'ст.л.') estimatedWeight = 15;
                else if (unit === 'ч.л.') estimatedWeight = 5;
                else if (unit === 'зубч.') estimatedWeight = 10;
                multiplier = (amount * estimatedWeight) / 100;
            }
            return {
                calories: nutrition.calories * multiplier,
                protein: nutrition.protein * multiplier,
                fat: nutrition.fat * multiplier,
                carbs: nutrition.carbohydrates * multiplier
            };
        }

        try {
            const response = await fetch(`/kitchen/api/ingredient/${ingredientId}/`);
            if (response.ok) {
                const data = await response.json();
                const nutrition = {
                    calories: data.calories || 0,
                    protein: data.protein || 0,
                    fat: data.fat || 0,
                    carbohydrates: data.carbohydrates || 0
                };

                // Сохраняем в кэш
                nutritionCache[ingredientId] = nutrition;

                // Применяем множитель
                let multiplier = 1;
                if (unit === 'г' || unit === 'мл') {
                    multiplier = amount / 100;
                } else if (unit === 'кг' || unit === 'л') {
                    multiplier = (amount * 1000) / 100;
                } else if (unit === 'шт' || unit === 'ст.л.' || unit === 'ч.л.' || unit === 'зубч.') {
                    let estimatedWeight = 0;
                    if (unit === 'шт') estimatedWeight = 100;
                    else if (unit === 'ст.л.') estimatedWeight = 15;
                    else if (unit === 'ч.л.') estimatedWeight = 5;
                    else if (unit === 'зубч.') estimatedWeight = 10;
                    multiplier = (amount * estimatedWeight) / 100;
                }

                return {
                    calories: nutrition.calories * multiplier,
                    protein: nutrition.protein * multiplier,
                    fat: nutrition.fat * multiplier,
                    carbs: nutrition.carbohydrates * multiplier
                };
            }
        } catch (error) {
            console.error(`Ошибка загрузки данных для ингредиента ${ingredientId}:`, error);
        }
        return null;
    });

    const results = await Promise.all(nutritionPromises);

    for (const result of results) {
        if (result) {
            totalCalories += result.calories;
            totalProtein += result.protein;
            totalFat += result.fat;
            totalCarbs += result.carbs;
        }
    }

    let servings = parseInt(document.getElementById('portionsSlider')?.value) || 4;

    const perServingCalories = totalCalories / servings;
    const perServingProtein = totalProtein / servings;
    const perServingFat = totalFat / servings;
    const perServingCarbs = totalCarbs / servings;

    // Обновляем отображение
    const kcalSpan = document.querySelector('.kcal-value');
    const proteinSpan = document.querySelector('.protein-value');
    const fatSpan = document.querySelector('.fat-value');
    const carbsSpan = document.querySelector('.carbs-value');

    if (kcalSpan) kcalSpan.innerText = Math.round(perServingCalories);
    if (proteinSpan) proteinSpan.innerText = Math.round(perServingProtein);
    if (fatSpan) fatSpan.innerText = Math.round(perServingFat);
    if (carbsSpan) carbsSpan.innerText = Math.round(perServingCarbs);

    console.log(`КБЖУ пересчитано: ${Math.round(perServingCalories)} ккал, ${Math.round(perServingProtein)}г белков, ${Math.round(perServingFat)}г жиров, ${Math.round(perServingCarbs)}г углеводов на ${servings} порций`);
}

async function updateNutritionOnChange() {
    await recalculateNutrition();
}

let nutritionInitDone = false;

async function initNutrition() {
    if (nutritionInitDone) return;
    nutritionInitDone = true;

    console.log('Инициализация КБЖУ...');
    setTimeout(async () => {
        await recalculateNutrition();
    }, 500);
}

// ======================= КНОПКА СОХРАНЕНИЯ РЕЦЕПТА =======================

document.addEventListener('DOMContentLoaded', function() {
    const saveRecipeBtn = document.getElementById('saveRecipeBtn');
    if (saveRecipeBtn) {
        saveRecipeBtn.addEventListener('click', function() {
            const recipeId = window.location.pathname.match(/\/recipe\/(\d+)\//)?.[1] || null;
            if (!recipeId) {
                showToast('Ошибка: ID рецепта не найден', 'Ошибка', 'error');
                return;
            }

            const name = prompt('Введите название для сохраненного рецепта:',
                document.querySelector('h1')?.innerText + ' (моя версия)' || 'Сохраненный рецепт');

            if (name === null) return;

            const notes = prompt('Добавьте заметки (опционально):', '');

            fetch('/kitchen/api/save-recipe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    recipe_id: parseInt(recipeId),
                    name: name,
                    notes: notes || '',
                    is_favorite: false
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    showToast('✅ ' + data.message, 'Успешно сохранено!', 'success');
                    if (data.nutrition) {
                        const kcalSpan = document.querySelector('.kcal-value');
                        const proteinSpan = document.querySelector('.protein-value');
                        const fatSpan = document.querySelector('.fat-value');
                        const carbsSpan = document.querySelector('.carbs-value');
                        if (kcalSpan) kcalSpan.innerText = data.nutrition.calories || 0;
                        if (proteinSpan) proteinSpan.innerText = data.nutrition.protein || 0;
                        if (fatSpan) fatSpan.innerText = data.nutrition.fat || 0;
                        if (carbsSpan) carbsSpan.innerText = data.nutrition.carbs || 0;
                    }
                } else {
                    showToast('❌ Ошибка: ' + data.error, 'Ошибка', 'error');
                }
            })
            .catch(error => {
                showToast('❌ Ошибка при сохранении', 'Ошибка', 'error');
                console.error('Error:', error);
            });
        });
    }
});

// ======================= ГЛОБАЛЬНЫЕ ФУНКЦИИ =======================

// Делаем функции глобальными для доступа из HTML
window.showMethodDetails = showMethodDetails;
window.closeMethodModal = closeMethodModal;
window.showPreparationDetails = showPreparationDetails;
window.closePreparationModal = closePreparationModal;
window.showUtensilDetails = showUtensilDetails;
window.closeUtensilModal = closeUtensilModal;
window.openInfoModal = openInfoModal;
window.closeInfoModal = closeInfoModal;
window.openReplaceModal = openReplaceModal;
window.closeReplaceModal = closeReplaceModal;
window.updateNutritionOnChange = updateNutritionOnChange;
window.initNutrition = initNutrition;
window.showToast = showToast;
window.closeToast = closeToast;
window.saveRecipeContext = saveRecipeContext;
window.getRecipeContext = getRecipeContext;
window.clearRecipeContext = clearRecipeContext;
window.updateRecipeContext = updateRecipeContext;

// Инициализируем КБЖУ после загрузки страницы
setTimeout(initNutrition, 1000);