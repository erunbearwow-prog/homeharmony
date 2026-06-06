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

    // Сбор данных об ингредиентах
    if (ingredientsTable) {
        document.querySelectorAll('#proIngredientsTable tr[data-id]').forEach(row => {
            ingredients.push({
                id: row.dataset.id,
                name: row.cells[0]?.innerText || '',
                gross: parseFloat(row.dataset.gross),
                net: parseFloat(row.dataset.net),
                lossFactor: parseFloat(row.dataset.loss),
                grossCell: row.querySelector('.gross-cell'),
                netCell: row.querySelector('.net-cell'),
                row: row
            });
        });
    }

    // Обновление всех ингредиентов
    function updateAllIngredients(ratio) {
        ingredients.forEach(ing => {
            const newNet = ing.net * ratio;
            const newGross = newNet * ing.lossFactor;

            ing.netCell.innerText = `${Math.round(newNet)} ${ing.unit || 'г'}`;
            ing.grossCell.innerText = `${Math.round(newGross)} ${ing.unit || 'г'}`;
        });

        // Обновляем итого
        const total = ingredients.reduce((sum, ing) => sum + (ing.net * currentRatio), 0);
        if (totalNetValue) totalNetValue.innerText = `${Math.round(total)} г`;
        if (totalYieldSpan) totalYieldSpan.innerText = `${Math.round(total)} г`;
    }

    // Переключение режимов
    function setMode(mode) {
        currentMode = mode;

        if (mode === 'portions') {
            portionsPanel.classList.remove('hidden');
            productsPanel.classList.add('hidden');
            modePortionsBtn.classList.add('bg-amber-600', 'text-white');
            modePortionsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
            modeProductsBtn.classList.remove('bg-amber-600', 'text-white');
            modeProductsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

            const portions = parseInt(portionsSlider.value);
            currentRatio = portions / baseServings;
            updateAllIngredients(currentRatio);
            if (portionsRatioInfo) {
                portionsRatioInfo.innerText = `Коэффициент: ${currentRatio.toFixed(2)} (на ${portions} порций)`;
            }
        } else {
            portionsPanel.classList.add('hidden');
            productsPanel.classList.remove('hidden');
            modeProductsBtn.classList.add('bg-amber-600', 'text-white');
            modeProductsBtn.classList.remove('bg-white', 'text-gray-600', 'border-gray-200');
            modePortionsBtn.classList.remove('bg-amber-600', 'text-white');
            modePortionsBtn.classList.add('bg-white', 'text-gray-600', 'border-gray-200');

            if (currentBaseIngredient) {
                const ratio = currentBaseIngredient.currentNet / currentBaseIngredient.originalNet;
                updateAllIngredients(ratio);
                if (baseRatioInfo) {
                    baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentNet} г ${currentBaseIngredient.name})`;
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
            portionsValue.innerText = baseServings;
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
            const netCell = row.querySelector('.net-cell');
            const currentNet = parseFloat(netCell?.innerText) || 0;
            const originalNet = parseFloat(row.dataset.net);

            // Убираем выделение со всех
            document.querySelectorAll('.chain-btn-pro').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });
            chainBtn.classList.remove('text-gray-400');
            chainBtn.classList.add('text-amber-600');

            currentBaseIngredient = {
                id: id,
                name: name,
                originalNet: originalNet,
                currentNet: currentNet
            };

            baseIngredientName.innerText = name;
            baseIngredientWeight.value = currentNet;
            baseIngredientUnit.innerText = 'г';
            baseIngredientRow.classList.remove('hidden');

            setMode('products');
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

            updateAllIngredients(ratio);

            if (baseRatioInfo) {
                baseRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${newValue} г ${currentBaseIngredient.name})`;
            }
        });
    }

    // Сброс базового ингредиента
    if (resetBaseBtn) {
        resetBaseBtn.addEventListener('click', function() {
            currentBaseIngredient = null;
            baseIngredientRow.classList.add('hidden');
            baseRatioInfo.innerText = '';
            baseIngredientName.innerText = '—';

            document.querySelectorAll('.chain-btn-pro').forEach(btn => {
                btn.classList.remove('text-amber-600');
                btn.classList.add('text-gray-400');
            });

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

            // Здесь будет запрос к API для получения цен ингредиентов
            // Пока заглушка
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
});