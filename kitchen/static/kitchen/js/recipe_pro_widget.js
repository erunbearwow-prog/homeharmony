// static/kitchen/js/recipe_pro_widget.js

document.addEventListener('DOMContentLoaded', function() {
    // DOM элементы
    const portionsSlider = document.getElementById('proPortionsSlider');
    const portionsValue = document.getElementById('proPortionsValue');
    const portionsRatioInfo = document.getElementById('proPortionsRatioInfo');
    const resetPortionsBtn = document.getElementById('proResetPortionsBtn');

    const modePortionsBtn = document.getElementById('proModePortionsBtn');
    const modeProductsBtn = document.getElementById('proModeProductsBtn');
    const portionsPanel = document.getElementById('proPortionsPanel');
    const productsPanel = document.getElementById('proProductsPanel');

    const baseIngredientRow = document.getElementById('proBaseIngredientRow');
    const baseIngredientWeight = document.getElementById('proBaseIngredientWeight');
    const baseIngredientUnit = document.getElementById('proBaseIngredientUnit');
    const baseIngredientName = document.getElementById('proBaseIngredientName');
    const applyBaseBtn = document.getElementById('proApplyBaseBtn');
    const resetBaseBtn = document.getElementById('proResetBaseBtn');
    const baseRatioInfo = document.getElementById('proBaseRatioInfo');

    const ingredientsTable = document.getElementById('proIngredientsTable');
    const totalNetValue = document.getElementById('totalNetValue');
    const totalYieldSpan = document.getElementById('totalYield');

    // Данные
    let currentMode = 'portions';
    let currentRatio = 1;
    let baseServings = parseInt(portionsSlider?.value) || 4;
    let currentBaseIngredient = null;
    let ingredients = [];
    let previousRatio = 1;  // Сохраняем последний коэффициент

    // Сбор данных об ингредиентах
    if (ingredientsTable) {
        document.querySelectorAll('#proIngredientsTable tr[data-id]').forEach(row => {
            const grossCell = row.querySelector('.gross-cell');
            const netCell = row.querySelector('.net-cell');
            ingredients.push({
                id: row.dataset.id,
                name: row.cells[0]?.innerText || '',
                gross: parseFloat(row.dataset.gross),
                net: parseFloat(row.dataset.net),
                unit: row.dataset.unit || 'г',
                lossFactor: parseFloat(row.dataset.loss) || (parseFloat(row.dataset.gross) / parseFloat(row.dataset.net)),
                grossCell: grossCell,
                netCell: netCell,
                row: row,
                originalGross: parseFloat(row.dataset.gross),
                originalNet: parseFloat(row.dataset.net)
            });
        });
    }

    // Обновление всех ингредиентов
    function updateAllIngredients(ratio) {
        currentRatio = ratio;

        ingredients.forEach(ing => {
            const newNet = ing.originalNet * ratio;
            const newGross = newNet * ing.lossFactor;

            if (ing.netCell) {
                ing.netCell.innerText = `${Math.round(newNet)} ${ing.unit}`;
            }
            if (ing.grossCell) {
                ing.grossCell.innerText = `${Math.round(newGross)} ${ing.unit}`;
            }
        });

        // Обновляем итого
        const total = ingredients.reduce((sum, ing) => sum + (ing.originalNet * currentRatio), 0);
        const totalText = `${Math.round(total)} г`;

        // Обновляем все элементы с итоговым весом
        if (totalNetValue) totalNetValue.innerText = totalText;
        if (totalYieldSpan) totalYieldSpan.innerText = totalText;

        // ========== ДОБАВИТЬ ЭТУ СТРОКУ ==========
        const totalYieldHeader = document.getElementById('totalYieldHeader');
        if (totalYieldHeader) totalYieldHeader.innerText = Math.round(total);

        updateSubrecipeLinks();
        updateURL();
    }

    // ======================= ОБНОВЛЕНИЕ ССЫЛОК НА ВЛОЖЕННЫЕ РЕЦЕПТЫ =======================
    function updateSubrecipeLinks() {
        const currentParams = new URLSearchParams(window.location.search);
        const ratio = currentRatio.toFixed(3);
        const portions = portionsSlider ? parseInt(portionsSlider.value) : baseServings;
        const mode = currentMode;

        document.querySelectorAll('.subrecipe-link-pro a, .subrecipe-link a, a.subrecipe-link').forEach(link => {
            try {
                let url = new URL(link.href, window.location.origin);

                // Основные параметры
                url.searchParams.set('ratio', ratio);
                url.searchParams.set('mode', mode);

                if (currentMode === 'products' && currentBaseIngredient) {
                    url.searchParams.set('base_ingredient', currentBaseIngredient.id);
                    url.searchParams.set('base_value', currentBaseIngredient.currentNet);
                    url.searchParams.delete('portions');
                } else {
                    url.searchParams.set('portions', portions);
                    url.searchParams.delete('base_ingredient');
                    url.searchParams.delete('base_value');
                }

                link.href = url.toString();
            } catch(e) {
                console.error('Ошибка обновления ссылки:', e);
            }
        });
    }

    // ======================= ОБНОВЛЕНИЕ URL В АДРЕСНОЙ СТРОКЕ =======================
    function updateURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const portions = portionsSlider ? parseInt(portionsSlider.value) : baseServings;

        if (currentMode === 'products' && currentBaseIngredient) {
            urlParams.set('mode', 'products');
            urlParams.set('base_ingredient', currentBaseIngredient.id);
            urlParams.set('base_value', currentBaseIngredient.currentNet);
            urlParams.set('ratio', currentRatio.toFixed(3));
            urlParams.delete('portions');
        } else {
            urlParams.set('mode', 'portions');
            urlParams.set('portions', portions);
            urlParams.set('ratio', currentRatio.toFixed(3));
            urlParams.delete('base_ingredient');
            urlParams.delete('base_value');
        }

        const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
        window.history.pushState({}, '', newUrl);
    }

    // Обновить информацию о базовом ингредиенте в UI
    function updateBaseIngredientUI() {
        if (currentBaseIngredient) {
            baseIngredientName.innerText = currentBaseIngredient.name;
            baseIngredientWeight.value = currentBaseIngredient.currentNet;
            baseIngredientUnit.innerText = 'г';
            baseIngredientRow.classList.remove('hidden');

            // Подсветка кнопки цепи
            document.querySelectorAll('.chain-btn-pro').forEach(btn => {
                const btnRow = btn.closest('tr');
                if (btnRow && btnRow.dataset.id == currentBaseIngredient.id) {
                    btn.classList.remove('text-gray-400');
                    btn.classList.add('text-amber-600');
                } else {
                    btn.classList.remove('text-amber-600');
                    btn.classList.add('text-gray-400');
                }
            });
        } else {
            baseIngredientRow.classList.add('hidden');
            baseIngredientName.innerText = '—';
            baseRatioInfo.innerText = '';

            // Убираем подсветку со всех кнопок
            document.querySelectorAll('.chain-btn-pro').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });
        }
    }

    // Переключение режимов
    function setMode(mode) {
        const previousMode = currentMode;
        currentMode = mode;

        if (mode === 'portions') {
            // Переключаем видимость панелей
            portionsPanel.classList.remove('hidden');
            productsPanel.classList.add('hidden');
            modePortionsBtn.classList.add('bg-amber-600', 'text-white');
            modePortionsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
            modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
            modeProductsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

            if (previousMode === 'products' && currentBaseIngredient) {
                // Пересчитываем порции из текущего коэффициента
                const ratioFromProducts = currentRatio;
                const newPortions = Math.round(ratioFromProducts * baseServings);

                if (portionsSlider && newPortions >= 1 && newPortions <= 50) {
                    portionsSlider.value = newPortions;
                    if (portionsValue) portionsValue.innerText = newPortions;
                    currentRatio = ratioFromProducts;
                    updateAllIngredients(currentRatio);
                    if (portionsRatioInfo) {
                        portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newPortions} порций)`;
                    }
                }
            } else {
                // Обычный режим порций
                const portions = parseInt(portionsSlider.value);
                currentRatio = portions / baseServings;
                updateAllIngredients(currentRatio);
                if (portionsRatioInfo) {
                    portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${portions} порций)`;
                }
            }
        }
        else { // mode === 'products'
            // Переключаем видимость панелей
            portionsPanel.classList.add('hidden');
            productsPanel.classList.remove('hidden');
            modeProductsBtn.classList.add('bg-amber-600', 'text-white');
            modeProductsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
            modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
            modePortionsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

            if (previousMode === 'portions') {
                // Берём текущий коэффициент из режима порций
                const ratioFromPortions = currentRatio;

                // Находим первый ингредиент для создания базового
                if (ingredients.length > 0) {
                    const firstIngredient = ingredients[0];
                    const newBaseValue = firstIngredient.originalNet * ratioFromPortions;

                    // Создаём базовый ингредиент
                    currentBaseIngredient = {
                        id: firstIngredient.id,
                        name: firstIngredient.name,
                        originalNet: firstIngredient.originalNet,
                        currentNet: newBaseValue,
                        unit: firstIngredient.unit
                    };

                    // Обновляем UI
                    updateBaseIngredientUI();

                    // Обновляем ингредиенты
                    currentRatio = ratioFromPortions;
                    updateAllIngredients(currentRatio);

                    if (baseRatioInfo) {
                        baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${newBaseValue.toFixed(1)} ${firstIngredient.unit} ${firstIngredient.name})`;
                    }
                } else {
                    updateAllIngredients(currentRatio);
                }
            }
            else if (currentBaseIngredient) {
                // Уже есть базовый ингредиент
                const ratio = currentBaseIngredient.currentNet / currentBaseIngredient.originalNet;
                currentRatio = ratio;
                updateAllIngredients(currentRatio);
                updateBaseIngredientUI();
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentNet} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
                }
            }
        }
    }

    // Обработчики кнопок режимов
    if (modePortionsBtn) modePortionsBtn.addEventListener('click', () => setMode('portions'));
    if (modeProductsBtn) modeProductsBtn.addEventListener('click', () => setMode('products'));

    // Обработчик ползунка порций
    if (portionsSlider) {
        portionsSlider.addEventListener('input', function() {
            const val = parseInt(this.value);
            if (portionsValue) portionsValue.innerText = val;
            currentRatio = val / baseServings;
            updateAllIngredients(currentRatio);
            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${val} порций)`;
            }
        });
    }

    // Сброс порций
    if (resetPortionsBtn) {
        resetPortionsBtn.addEventListener('click', function() {
            portionsSlider.value = baseServings;
            if (portionsValue) portionsValue.innerText = baseServings;
            currentRatio = 1;
            updateAllIngredients(1);
            if (portionsRatioInfo) portionsRatioInfo.innerText = '';
        });
    }

    // Обработчик кликов по 🔗 в таблице (сделать базовым)
    if (ingredientsTable) {
        ingredientsTable.addEventListener('click', function(e) {
            const chainBtn = e.target.closest('.chain-btn-pro');
            if (!chainBtn) return;

            const row = chainBtn.closest('tr');
            const id = row.dataset.id;
            const name = row.cells[0]?.innerText;
            const originalNet = parseFloat(row.dataset.net);
            const unit = row.dataset.unit || 'г';

            // Находим текущее значение нетто из ячейки
            const netCell = row.querySelector('.net-cell');
            let currentNet = originalNet * currentRatio;
            if (netCell) {
                const match = netCell.innerText.match(/^[\d\.]+/);
                if (match) currentNet = parseFloat(match[0]);
            }

            // Сохраняем базовый ингредиент
            currentBaseIngredient = {
                id: id,
                name: name,
                originalNet: originalNet,
                currentNet: currentNet,
                unit: unit
            };

            // Обновляем UI
            updateBaseIngredientUI();

            // Обновляем информацию о коэффициенте
            const ratio = currentNet / originalNet;
            currentRatio = ratio;

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentNet} ${unit} ${name})`;
            }

            // Переключаемся в режим продуктов
            setMode('products');

            // обновляем ссылки на вложенный рецепт
            updateSubrecipeLinks();
            updateURL();
        });
    }

    // Применить базовый ингредиент
    if (applyBaseBtn) {
        applyBaseBtn.addEventListener('click', function() {
            if (!currentBaseIngredient) return;

            let newValue = parseFloat(baseIngredientWeight.value);
            if (isNaN(newValue) || newValue <= 0) newValue = currentBaseIngredient.originalNet;

            const ratio = newValue / currentBaseIngredient.originalNet;
            currentBaseIngredient.currentNet = newValue;
            currentRatio = ratio;

            updateAllIngredients(ratio);
            updateBaseIngredientUI();

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${newValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
            }
        });
    }

    // Сброс базового ингредиента
    if (resetBaseBtn) {
        resetBaseBtn.addEventListener('click', function() {
            currentBaseIngredient = null;
            updateBaseIngredientUI();
            setMode('portions');
        });
    }

    // Калькуляция себестоимости
    const costBtn = document.getElementById('proCalculateCostBtn');
    const costModal = document.getElementById('proCostModal');
    const costContent = document.getElementById('proCostContent');

    if (costBtn && costContent) {
        costBtn.addEventListener('click', async function() {
            costContent.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i> Загрузка цен...</div>';
            costModal.classList.remove('hidden');

            // Заглушка для калькуляции
            costContent.innerHTML = `
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span>Общий вес нетто:</span>
                        <span class="font-bold">${totalNetValue?.innerText || '0 г'}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Порций:</span>
                        <span>${portionsSlider?.value || baseServings}</span>
                    </div>
                    <div class="border-t pt-2 mt-2">
                        <div class="flex justify-between text-lg font-bold">
                            <span>Себестоимость порции:</span>
                            <span class="text-amber-700">-- ₽</span>
                        </div>
                        <div class="text-xs text-gray-400 mt-2">* Для расчёта добавьте цены ингредиентов</div>
                    </div>
                </div>
            `;
        });
    }

    // Закрытие модалки по клику на фон
    if (costModal) {
        costModal.addEventListener('click', function(e) {
            if (e.target === costModal) {
                costModal.classList.add('hidden');
            }
        });
    }

    // Инициализация: обновляем итого при загрузке
    updateAllIngredients(1);

    // ======================= ВОССТАНОВЛЕНИЕ ПАРАМЕТРОВ ИЗ URL =======================
    function restoreFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const mode = urlParams.get('mode');
        const ratioParam = urlParams.get('ratio');
        const portionsParam = urlParams.get('portions');
        const baseIngredientId = urlParams.get('base_ingredient');
        const baseValue = urlParams.get('base_value');

        if (ratioParam && !isNaN(parseFloat(ratioParam))) {
            currentRatio = parseFloat(ratioParam);
        } else {
            currentRatio = 1;
        }

        if (mode === 'products' && baseIngredientId && baseValue) {
            const ingredient = ingredients.find(ing => ing.id == baseIngredientId);
            if (ingredient) {
                currentBaseIngredient = {
                    id: ingredient.id,
                    name: ingredient.name,
                    originalNet: ingredient.originalNet,
                    currentNet: parseFloat(baseValue),
                    unit: ingredient.unit
                };
                updateBaseIngredientUI();

                // Устанавливаем режим без вызова setMode (чтобы избежать двойного обновления)
                currentMode = 'products';
                portionsPanel.classList.add('hidden');
                productsPanel.classList.remove('hidden');
                modeProductsBtn.classList.add('bg-amber-600', 'text-white');
                modeProductsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
                modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
                modePortionsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

                currentRatio = parseFloat(baseValue) / ingredient.originalNet;
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${baseValue} ${ingredient.unit} ${ingredient.name})`;
                }
            } else {
                currentMode = 'portions';
            }
        } else if (portionsParam && !isNaN(parseInt(portionsParam))) {
            const portions = parseInt(portionsParam);
            if (portionsSlider && portions >= 1 && portions <= 50) {
                portionsSlider.value = portions;
                if (portionsValue) portionsValue.innerText = portions;
                currentRatio = portions / baseServings;
                currentMode = 'portions';
            }
        } else if (ratioParam && !isNaN(parseFloat(ratioParam))) {
            currentRatio = parseFloat(ratioParam);
            const portions = Math.round(currentRatio * baseServings);
            if (portionsSlider && portions >= 1 && portions <= 50) {
                portionsSlider.value = portions;
                if (portionsValue) portionsValue.innerText = portions;
                currentMode = 'portions';
            }
        } else {
            currentMode = 'portions';
        }

        // Применяем видимость панелей для обычного режима (если не products)
        if (currentMode !== 'products') {
            portionsPanel.classList.remove('hidden');
            productsPanel.classList.add('hidden');
            modePortionsBtn.classList.add('bg-amber-600', 'text-white');
            modePortionsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
            modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
            modeProductsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

            if (portionsRatioInfo && currentMode === 'portions') {
                const portions = parseInt(portionsSlider.value);
                portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${portions} порций)`;
            }
        }

        updateAllIngredients(currentRatio);
    }

    // Инициализация: восстанавливаем состояние из URL (НЕ вызываем updateAllIngredients отдельно)
    restoreFromURL();
});