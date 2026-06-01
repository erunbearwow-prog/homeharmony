// ======================= СОХРАНЯЕМ ИСХОДНЫЕ ДАННЫЕ =======================
let originalValues = [];
let ingredientItems = [];
let caloriesSpan = null;

// DOM элементы для режимов
let modeProductsBtn, modePortionsBtn, modeProductsPanel, modePortionsPanel;
let meatInput, applyMeatBtn, resetProductsBtn, meatRatioInfo;
let portionsSlider, portionsValueSpan, resetPortionsBtn, portionsRatioInfo;

// Базовые значения по рецепту
const BASE_MEAT = 500;
const BASE_PORTIONS = 6;

// Текущий режим: 'products' или 'portions'
let currentMode = 'products';

// Текущий базовый ингредиент для пересчёта
let currentBaseIngredient = {
    id: null,
    name: 'говядина',
    originalValue: BASE_MEAT,
    unit: 'г',
    currentValue: BASE_MEAT
};

// Хранилище замен ингредиентов
let ingredientReplacements = {};

// Кэш для методов приготовления
let methodsCache = {};

// ======================= БАЗА ЗНАНИЙ ЗАМЕН ИНГРЕДИЕНТОВ =======================
const REPLACEMENTS_DB = {
    'чеснок': {
        searchTerms: ['чеснок свежий', 'чеснок зубчик', 'чеснок долька', 'чеснок'],
        unit: 'зубч.',
        replacements: [
            { name: 'чеснок сушёный гранулы', ratio: 0.33, unit: 'ч. л.', displayName: 'чеснок сушёный (гранулы)', note: '1 зубчик = 1/3 ч.л. гранул' },
            { name: 'чеснок сушёный порошок', ratio: 0.25, unit: 'ч. л.', displayName: 'чеснок сушёный (порошок)', note: '1 зубчик = 1/4 ч.л. порошка' },
            { name: 'чесночная паста', ratio: 0.5, unit: 'ч. л.', displayName: 'чесночная паста', note: '1 зубчик = 1/2 ч.л. пасты' }
        ]
    },
    'томатная паста': {
        searchTerms: ['томатная паста', 'томат паста', 'т. паста', 'паста томатная'],
        unit: 'ст. л.',
        replacements: [
            { name: 'перетёртые помидоры', ratio: 2, unit: 'ст. л.', displayName: 'перетёртые помидоры', note: '1 ст.л. пасты = 2 ст.л. помидоров' },
            { name: 'томатный сок', ratio: 3, unit: 'ст. л.', displayName: 'томатный сок', note: '1 ст.л. пасты = 3 ст.л. сока' },
            { name: 'кетчуп', ratio: 1, unit: 'ст. л.', displayName: 'кетчуп', note: '1 ст.л. пасты = 1 ст.л. кетчупа' },
            { name: 'свежие помидоры (протёртые)', ratio: 2.5, unit: 'ст. л.', displayName: 'свежие помидоры', note: '1 ст.л. пасты = 2.5 ст.л. протёртых помидоров' }
        ]
    },
    'петрушка': {
        searchTerms: ['петрушка свежая', 'петрушка', 'зелень петрушки'],
        unit: 'ст. л.',
        replacements: [
            { name: 'петрушка сушёная', ratio: 0.33, unit: 'ч. л.', displayName: 'петрушка сушёная', note: '1 ст.л. свежей = 1 ч.л. сушёной' }
        ]
    },
    'укроп': {
        searchTerms: ['укроп свежий', 'укроп', 'зелень укропа'],
        unit: 'ст. л.',
        replacements: [
            { name: 'укроп сушёный', ratio: 0.33, unit: 'ч. л.', displayName: 'укроп сушёный', note: '1 ст.л. свежего = 1 ч.л. сушёного' }
        ]
    },
    'лук репчатый': {
        searchTerms: ['лук репчатый', 'лук', 'репчатый лук', 'луковица'],
        unit: 'шт.',
        replacements: [
            { name: 'лук сушёный гранулы', ratio: 0.25, unit: 'ч. л.', displayName: 'лук сушёный (гранулы)', note: '1 средняя луковица = 1/4 ч.л. гранул' },
            { name: 'лук-порей', ratio: 1.5, unit: 'шт.', displayName: 'лук-порей', note: '1 луковица = 1.5 стебля порея' }
        ]
    },
    'яйцо': {
        searchTerms: ['яйцо куриное', 'яйцо', 'куриное яйцо', 'яйца'],
        unit: 'шт.',
        replacements: [
            { name: 'льняное семя молотое', ratio: 3, unit: 'ст. л.', displayName: 'льняное семя (молотое) + вода 1:1', note: '1 яйцо = 3 ст.л. льняной муки + 3 ст.л. воды' },
            { name: 'банан (пюре)', ratio: 0.5, unit: 'шт.', displayName: 'банан (пюре)', note: '1 яйцо = 1/2 банана' }
        ]
    }
};

// Функция поиска замен для ингредиента
function findReplacementsForIngredient(ingredientName) {
    const normalizedName = ingredientName.toLowerCase().trim();

    for (const [key, data] of Object.entries(REPLACEMENTS_DB)) {
        for (const term of data.searchTerms) {
            if (normalizedName.includes(term.toLowerCase()) || term.toLowerCase().includes(normalizedName)) {
                return {
                    originalKey: key,
                    unit: data.unit,
                    replacements: data.replacements
                };
            }
        }
    }
    return null;
}

// ======================= ОБНОВЛЕНИЕ URL =======================
function updateURL() {
    const params = new URLSearchParams();
    params.set('mode', currentMode);

    if (currentMode === 'products') {
        if (currentBaseIngredient.id !== null && currentBaseIngredient.name !== 'говядина') {
            params.set('base_ingredient', currentBaseIngredient.id);
            params.set('base_value', currentBaseIngredient.currentValue);
        } else {
            params.set('meat', currentBaseIngredient.currentValue);
        }
    } else {
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        params.set('portions', portionsVal);
    }

    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.pushState({}, '', newUrl);
}

// ======================= ОБНОВЛЕНИЕ ИНГРЕДИЕНТОВ =======================
function updateIngredientsDisplay(ratio, skipReplacements = false) {
    ingredientItems.forEach((item, idx) => {
        const amountSpan = item.querySelector('.ingredient-amount');
        if (!amountSpan) return;

        let newVal = originalValues[idx] * ratio;
        const unit = item.dataset.unit;

        if (!skipReplacements && ingredientReplacements[item.dataset.ingredientId]) {
            const replacement = ingredientReplacements[item.dataset.ingredientId];
            newVal = newVal * replacement.ratio;
        }

        if (unit === 'шт.' || unit === 'зубч.' || unit === 'ст. л.') {
            newVal = Math.ceil(newVal);
        } else if (unit === 'г' || unit === 'мл') {
            newVal = Math.round(newVal);
        } else {
            newVal = Math.round(newVal * 10) / 10;
        }

        amountSpan.innerText = `${newVal} ${unit}`;
    });

    if (caloriesSpan) {
        const baseCal = parseFloat(caloriesSpan.dataset.base) || 380;
        caloriesSpan.innerText = Math.round(baseCal * ratio);
    }
}

// ======================= ПЕРЕСЧЁТ ПО БАЗОВОМУ ИНГРЕДИЕНТУ =======================
function recalcByBaseIngredient(newValue) {
    if (!currentBaseIngredient.originalValue) return;
    const ratio = newValue / currentBaseIngredient.originalValue;
    updateIngredientsDisplay(ratio);
    currentBaseIngredient.currentValue = newValue;

    if (meatRatioInfo) {
        meatRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${newValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
    }
    updateURL();
    updateIngredientLinks();
}

function recalcByMeatWeight(meatGram) {
    let ratio = meatGram / BASE_MEAT;
    if (isNaN(ratio) || ratio <= 0) ratio = 1;
    updateIngredientsDisplay(ratio);

    if (meatRatioInfo) {
        meatRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${meatGram} г мяса)`;
    }

    currentBaseIngredient = {
        id: null,
        name: 'говядина',
        originalValue: BASE_MEAT,
        unit: 'г',
        currentValue: meatGram
    };

    updateURL();
    updateIngredientLinks();
}

function recalcByPortions(portions) {
    let ratio = portions / BASE_PORTIONS;
    if (isNaN(ratio) || ratio <= 0) ratio = 1;
    updateIngredientsDisplay(ratio);

    if (portionsRatioInfo) {
        portionsRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${portions} порций)`;
    }
    updateURL();
    updateIngredientLinks();
}

// ======================= УСТАНОВКА БАЗОВОГО ИНГРЕДИЕНТА (🔗) =======================
function setBaseIngredient(ingredientId, ingredientName, originalValue, unit, currentAmountSpan) {
    document.querySelectorAll('.ingredient-chain-btn').forEach(btn => {
        btn.classList.remove('text-amber-600', 'bg-amber-50');
        btn.classList.add('text-gray-400');
    });

    const activeBtn = document.querySelector(`.ingredient-chain-btn[data-ingredient-id="${ingredientId}"]`);
    if (activeBtn) {
        activeBtn.classList.remove('text-gray-400');
        activeBtn.classList.add('text-amber-600', 'bg-amber-50', 'rounded');
    }

    let currentValue = originalValue;
    if (currentAmountSpan) {
        const match = currentAmountSpan.innerText.match(/^[\d\.]+/);
        if (match) currentValue = parseFloat(match[0]);
    }

    currentBaseIngredient = { id: ingredientId, name: ingredientName, originalValue, unit, currentValue };

    if (currentMode !== 'products') setMode('products');
    else {
        updateProductsPanelForBaseIngredient();
        recalcByBaseIngredient(currentValue);
    }
}

function updateProductsPanelForBaseIngredient() {
    const panel = document.querySelector('#modeProductsPanel .p-3');
    if (!panel) return;

    const titleSpan = panel.querySelector('.font-medium.text-sm');
    if (titleSpan) {
        titleSpan.innerHTML = `<i class="fas fa-link text-amber-700 mr-1"></i> Пересчитать по <span id="baseIngredientName" class="font-bold text-amber-700">${currentBaseIngredient.name}</span>`;
    }

    let inputRow = panel.querySelector('#baseIngredientRow');
    if (!inputRow) {
        inputRow = document.createElement('div');
        inputRow.id = 'baseIngredientRow';
        inputRow.className = 'flex flex-wrap items-center gap-2 mt-3';
        panel.appendChild(inputRow);
    }

    inputRow.innerHTML = `
        <span class="text-sm font-medium">${currentBaseIngredient.name}:</span>
        <span class="text-sm text-gray-500 line-through">${currentBaseIngredient.originalValue} ${currentBaseIngredient.unit}</span>
        <input type="number" id="customBaseWeight" value="${currentBaseIngredient.currentValue}" step="${currentBaseIngredient.unit === 'шт.' ? 1 : 10}"
               class="w-24 px-2 py-1 border border-gray-300 rounded-lg text-center">
        <span class="text-sm">${currentBaseIngredient.unit}</span>
        <button id="applyBaseBtn" class="bg-amber-700 text-white px-3 py-1 rounded-lg text-sm">Пересчитать</button>
        <button id="resetBaseBtn" class="text-gray-500 text-sm underline ml-auto">Сбросить</button>
    `;

    const baseInput = document.getElementById('customBaseWeight');
    const applyBaseBtn = document.getElementById('applyBaseBtn');
    const resetBaseBtn = document.getElementById('resetBaseBtn');

    if (applyBaseBtn) {
        applyBaseBtn.addEventListener('click', () => {
            let val = parseFloat(baseInput.value);
            if (isNaN(val) || val <= 0) val = currentBaseIngredient.originalValue;
            currentBaseIngredient.currentValue = val;
            recalcByBaseIngredient(val);
        });
    }
    if (resetBaseBtn) {
        resetBaseBtn.addEventListener('click', () => {
            currentBaseIngredient.currentValue = currentBaseIngredient.originalValue;
            if (baseInput) baseInput.value = currentBaseIngredient.originalValue;
            recalcByBaseIngredient(currentBaseIngredient.originalValue);
        });
    }
    if (baseInput) {
        baseInput.addEventListener('change', () => {
            let val = parseFloat(baseInput.value);
            if (isNaN(val) || val <= 0) val = currentBaseIngredient.originalValue;
            currentBaseIngredient.currentValue = val;
            recalcByBaseIngredient(val);
        });
    }

    const ratio = currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
    if (meatRatioInfo) meatRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${currentBaseIngredient.currentValue} ${currentBaseIngredient.unit} ${currentBaseIngredient.name})`;
}

function resetBaseIngredient() {
    currentBaseIngredient = { id: null, name: 'говядина', originalValue: BASE_MEAT, unit: 'г', currentValue: BASE_MEAT };
    document.querySelectorAll('.ingredient-chain-btn').forEach(btn => {
        btn.classList.remove('text-amber-600', 'bg-amber-50');
        btn.classList.add('text-gray-400');
    });

    const panel = document.querySelector('#modeProductsPanel .p-3');
    if (panel) {
        const titleSpan = panel.querySelector('.font-medium.text-sm');
        if (titleSpan) titleSpan.innerHTML = `<i class="fas fa-link text-amber-700 mr-1"></i> Пересчитать по <span id="baseIngredientName" class="font-bold text-amber-700">говядине</span>`;

        let inputRow = panel.querySelector('#baseIngredientRow');
        if (inputRow) {
            inputRow.innerHTML = `
                <span class="text-sm font-medium">🥩 Говядина:</span>
                <span class="text-sm text-gray-500 line-through">500 г</span>
                <input type="number" id="customMeatWeight" value="500" step="10" class="w-24 px-2 py-1 border border-gray-300 rounded-lg text-center">
                <span class="text-sm">г</span>
                <button id="applyMeatBtn" class="bg-amber-700 text-white px-3 py-1 rounded-lg text-sm">Пересчитать</button>
                <button id="resetProductsBtn" class="text-gray-500 text-sm underline ml-auto">Сбросить</button>
            `;

            const newMeatInput = document.getElementById('customMeatWeight');
            const newApplyMeatBtn = document.getElementById('applyMeatBtn');
            const newResetProductsBtn = document.getElementById('resetProductsBtn');

            if (newApplyMeatBtn) newApplyMeatBtn.addEventListener('click', () => {
                let val = parseFloat(newMeatInput.value);
                if (isNaN(val) || val <= 0) val = BASE_MEAT;
                newMeatInput.value = val;
                recalcByMeatWeight(val);
            });
            if (newResetProductsBtn) newResetProductsBtn.addEventListener('click', () => {
                newMeatInput.value = BASE_MEAT;
                recalcByMeatWeight(BASE_MEAT);
            });
        }
    }
    recalcByMeatWeight(BASE_MEAT);
}

// ======================= ЗАМЕНА ИНГРЕДИЕНТОВ (⟳) =======================
let activeReplaceIngredient = null;
let activeSelectedReplacement = null;

function showReplaceModal(ingredientId, ingredientName, originalValue, unit) {
    activeReplaceIngredient = { id: ingredientId, name: ingredientName, originalValue, unit };

    const modal = document.getElementById('replaceModal');
    const originalNameSpan = document.getElementById('replaceOriginalName');
    const originalUnitSpan = document.getElementById('replaceOriginalUnit');
    const replaceSelect = document.getElementById('replaceWithSelect');
    const ratioInput = document.getElementById('replaceRatio');
    const newUnitSpan = document.getElementById('replaceNewUnit');
    const newNameSpan = document.getElementById('replaceNewName');
    const autoNote = document.getElementById('autoRatioNote');
    const replacementNote = document.getElementById('replacementNote');

    if (originalNameSpan) originalNameSpan.innerText = ingredientName;
    if (originalUnitSpan) originalUnitSpan.innerText = unit;

    const replacementsData = findReplacementsForIngredient(ingredientName);

    replaceSelect.innerHTML = '';

    if (replacementsData && replacementsData.replacements.length > 0) {
        if (replacementNote) {
            replacementNote.innerHTML = `💡 Для <strong>${ingredientName}</strong> найдены рекомендованные замены:`;
            replacementNote.classList.remove('hidden');
        }

        replacementsData.replacements.forEach(rep => {
            const option = document.createElement('option');
            option.value = rep.name;
            option.textContent = `${rep.displayName || rep.name} — ${rep.note}`;
            option.dataset.ratio = rep.ratio;
            option.dataset.unit = rep.unit;
            option.dataset.note = rep.note;
            option.dataset.displayName = rep.displayName || rep.name;
            replaceSelect.appendChild(option);
        });

        const customOption = document.createElement('option');
        customOption.value = 'custom';
        customOption.textContent = '✏️ Другой ингредиент (ввести вручную)';
        replaceSelect.appendChild(customOption);

    } else {
        if (replacementNote) {
            replacementNote.innerHTML = `❓ Для <strong>${ingredientName}</strong> нет рекомендованных замен. Вы можете ввести коэффициент вручную.`;
            replacementNote.classList.remove('hidden');
        }

        const customOption = document.createElement('option');
        customOption.value = 'custom';
        customOption.textContent = '✏️ Другой ингредиент (ввести вручную)';
        replaceSelect.appendChild(customOption);
    }

    replaceSelect.onchange = () => {
        const selected = replaceSelect.options[replaceSelect.selectedIndex];

        if (selected && selected.value !== 'custom' && selected.dataset.ratio) {
            const ratio = parseFloat(selected.dataset.ratio);
            ratioInput.value = ratio;
            newUnitSpan.innerText = selected.dataset.unit;
            if (newNameSpan) newNameSpan.innerText = selected.dataset.displayName || selected.value;
            if (autoNote) autoNote.classList.remove('hidden');

            activeSelectedReplacement = {
                name: selected.value,
                displayName: selected.dataset.displayName || selected.value,
                ratio: ratio,
                unit: selected.dataset.unit,
                note: selected.dataset.note
            };
        } else {
            ratioInput.value = '';
            newUnitSpan.innerText = unit;
            if (newNameSpan) newNameSpan.innerText = '';
            if (autoNote) autoNote.classList.add('hidden');
            activeSelectedReplacement = null;
        }
    };

    if (replaceSelect.options.length > 0) {
        replaceSelect.selectedIndex = 0;
        replaceSelect.dispatchEvent(new Event('change'));
    }

    modal.classList.remove('hidden');
}

function applyReplacement() {
    if (!activeReplaceIngredient) return;

    const replaceSelect = document.getElementById('replaceWithSelect');
    const selectedOption = replaceSelect.options[replaceSelect.selectedIndex];
    const ratioInput = document.getElementById('replaceRatio');
    const newUnitSpan = document.getElementById('replaceNewUnit');

    let newName, ratio, newUnit;

    if (selectedOption && selectedOption.value !== 'custom' && selectedOption.dataset.ratio) {
        newName = selectedOption.dataset.displayName || selectedOption.value;
        ratio = parseFloat(selectedOption.dataset.ratio);
        newUnit = selectedOption.dataset.unit;
    } else {
        newName = prompt('Введите название ингредиента-заменителя:', activeReplaceIngredient.name);
        if (!newName) return;

        ratio = parseFloat(ratioInput.value);
        if (isNaN(ratio) || ratio <= 0) {
            alert('Пожалуйста, введите коэффициент пересчёта (больше 0)');
            return;
        }
        newUnit = newUnitSpan.innerText || activeReplaceIngredient.unit;
    }

    const ingredientItem = document.querySelector(`.ingredient-item[data-ingredient-id="${activeReplaceIngredient.id}"]`);
    if (!ingredientItem) return;

    ingredientReplacements[activeReplaceIngredient.id] = {
        originalName: activeReplaceIngredient.name,
        replacementName: newName,
        ratio: ratio,
        unit: newUnit
    };

    const label = ingredientItem.querySelector('label');
    if (label) {
        const oldText = label.innerText;
        label.innerText = oldText.replace(activeReplaceIngredient.name, newName);
    }

    const currentRatio = getCurrentGlobalRatio();
    const newAmount = activeReplaceIngredient.originalValue * currentRatio * ratio;
    const amountSpan = ingredientItem.querySelector('.ingredient-amount');
    if (amountSpan) {
        let displayAmount = newUnit === 'шт.' ? Math.ceil(newAmount) : Math.round(newAmount * 10) / 10;
        amountSpan.innerText = `${displayAmount} ${newUnit}`;
    }

    const replaceBtn = ingredientItem.querySelector('.ingredient-replace-btn');
    if (replaceBtn) {
        replaceBtn.innerHTML = '<i class="fas fa-undo-alt"></i>';
        replaceBtn.classList.remove('hover:text-blue-600');
        replaceBtn.classList.add('hover:text-red-600');
        replaceBtn.title = 'Сбросить замену';

        const newBtn = replaceBtn.cloneNode(true);
        replaceBtn.parentNode.replaceChild(newBtn, replaceBtn);
        newBtn.addEventListener('click', (e) => {
            e.preventDefault();
            resetReplacement(activeReplaceIngredient.id);
        });
    }

    document.getElementById('replaceModal').classList.add('hidden');
    saveReplacementsToLocal();
    activeReplaceIngredient = null;
}

function getCurrentGlobalRatio() {
    if (currentMode === 'products') {
        return currentBaseIngredient.currentValue / currentBaseIngredient.originalValue;
    } else {
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        return portionsVal / BASE_PORTIONS;
    }
}

function resetReplacement(ingredientId) {
    const ingredientItem = document.querySelector(`.ingredient-item[data-ingredient-id="${ingredientId}"]`);
    if (!ingredientItem || !ingredientReplacements[ingredientId]) return;

    const replacement = ingredientReplacements[ingredientId];
    const label = ingredientItem.querySelector('label');
    const amountSpan = ingredientItem.querySelector('.ingredient-amount');

    if (label) {
        label.innerText = label.innerText.replace(replacement.replacementName, replacement.originalName);
    }

    const currentRatio = getCurrentGlobalRatio();
    const originalAmount = replacement.originalValue * currentRatio;
    if (amountSpan) {
        let displayAmount = replacement.unit === 'шт.' ? Math.ceil(originalAmount) : Math.round(originalAmount * 10) / 10;
        amountSpan.innerText = `${displayAmount} ${replacement.unit}`;
    }

    delete ingredientReplacements[ingredientId];
    saveReplacementsToLocal();

    const replaceBtn = ingredientItem.querySelector('.ingredient-replace-btn');
    if (replaceBtn) {
        replaceBtn.innerHTML = '<i class="fas fa-exchange-alt"></i>';
        replaceBtn.classList.remove('hover:text-red-600');
        replaceBtn.classList.add('hover:text-blue-600');
        replaceBtn.title = 'Заменить ингредиент';

        const newBtn = replaceBtn.cloneNode(true);
        replaceBtn.parentNode.replaceChild(newBtn, replaceBtn);
        newBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showReplaceModal(ingredientId, replacement.originalName, replacement.originalValue, replacement.unit);
        });
    }
}

function saveReplacementsToLocal() {
    localStorage.setItem('recipe_replacements', JSON.stringify(ingredientReplacements));
}

function restoreReplacementsFromLocal() {
    const saved = localStorage.getItem('recipe_replacements');
    if (saved) {
        try {
            ingredientReplacements = JSON.parse(saved);
        } catch(e) { console.log('Ошибка восстановления замен'); }
    }
}

function applyStoredReplacements() {
    for (const [id, replacement] of Object.entries(ingredientReplacements)) {
        const ingredientItem = document.querySelector(`.ingredient-item[data-ingredient-id="${id}"]`);
        if (!ingredientItem) continue;

        const label = ingredientItem.querySelector('label');
        const amountSpan = ingredientItem.querySelector('.ingredient-amount');

        if (label) {
            label.innerText = label.innerText.replace(replacement.originalName, replacement.replacementName);
        }

        const currentRatio = getCurrentGlobalRatio();
        const newAmount = replacement.originalValue * currentRatio * replacement.ratio;
        if (amountSpan) {
            let displayAmount = replacement.unit === 'шт.' ? Math.ceil(newAmount) : Math.round(newAmount * 10) / 10;
            amountSpan.innerText = `${displayAmount} ${replacement.unit}`;
        }

        const replaceBtn = ingredientItem.querySelector('.ingredient-replace-btn');
        if (replaceBtn) {
            replaceBtn.innerHTML = '<i class="fas fa-undo-alt"></i>';
            replaceBtn.classList.remove('hover:text-blue-600');
            replaceBtn.classList.add('hover:text-red-600');
            replaceBtn.title = 'Сбросить замену';

            const newBtn = replaceBtn.cloneNode(true);
            replaceBtn.parentNode.replaceChild(newBtn, replaceBtn);
            newBtn.addEventListener('click', (e) => {
                e.preventDefault();
                resetReplacement(id);
            });
        }
    }
}

// ======================= НАВИГАЦИЯ ПО ИНГРЕДИЕНТАМ =======================
function getCurrentStateParams() {
    const params = new URLSearchParams();
    params.set('mode', currentMode);
    if (currentMode === 'products') {
        if (currentBaseIngredient.id !== null && currentBaseIngredient.name !== 'говядина') {
            params.set('base_ingredient', currentBaseIngredient.id);
            params.set('base_value', currentBaseIngredient.currentValue);
        } else {
            params.set('meat', currentBaseIngredient.currentValue);
        }
    } else {
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        params.set('portions', portionsVal);
    }
    return params.toString();
}

function updateIngredientLinks() {
    const stateParams = getCurrentStateParams();
    const currentPath = window.location.pathname;
    const returnUrl = encodeURIComponent(`${currentPath}?${stateParams}`);
    document.querySelectorAll('.ingredient-link').forEach(link => {
        const ingredientSlug = link.dataset.ingredient;
        if (ingredientSlug) link.href = `/ingredients/${ingredientSlug}/?return_to=${returnUrl}`;
    });
}

// ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ =======================
function setMode(mode) {
    currentMode = mode;
    if (mode === 'products') {
        if (modeProductsPanel) modeProductsPanel.classList.remove('hidden');
        if (modePortionsPanel) modePortionsPanel.classList.add('hidden');
        if (modeProductsBtn) modeProductsBtn.classList.add('bg-amber-100', 'text-amber-800');
        if (modePortionsBtn) modePortionsBtn.classList.remove('bg-green-100', 'text-green-800');
        updateProductsPanelForBaseIngredient();
        recalcByBaseIngredient(currentBaseIngredient.currentValue);
    } else {
        if (modeProductsPanel) modeProductsPanel.classList.add('hidden');
        if (modePortionsPanel) modePortionsPanel.classList.remove('hidden');
        if (modePortionsBtn) modePortionsBtn.classList.add('bg-green-100', 'text-green-800');
        if (modeProductsBtn) modeProductsBtn.classList.remove('bg-amber-100', 'text-amber-800');
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        recalcByPortions(portionsVal);
    }
    updateURL();
}

// ======================= ЧЕКБОКСЫ ИНГРЕДИЕНТОВ =======================
function saveCheckboxStates() {
    document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
        localStorage.setItem(`recipe_checkbox_${cb.id}`, cb.checked);
    });
}

function restoreCheckboxStates() {
    document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
        const saved = localStorage.getItem(`recipe_checkbox_${cb.id}`);
        if (saved !== null) cb.checked = saved === 'true';
    });
}

// ======================= ШАГИ ПРИГОТОВЛЕНИЯ =======================
function saveStepStates() {
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        localStorage.setItem(`recipe_step_${cb.id}`, cb.checked);
    });
    updateStepsProgress();
}

function restoreStepStates() {
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        const saved = localStorage.getItem(`recipe_step_${cb.id}`);
        if (saved !== null) cb.checked = saved === 'true';
    });
    updateStepsProgress();
}

function updateStepsProgress() {
    const stepCheckboxes = document.querySelectorAll('.step-checkbox');
    const total = stepCheckboxes.length;
    const completed = Array.from(stepCheckboxes).filter(cb => cb.checked).length;
    const percent = total ? (completed / total) * 100 : 0;
    const progressText = document.getElementById('stepsProgress');
    const progressBar = document.getElementById('stepsProgressBar');
    if (progressText) progressText.innerText = `${completed}/${total}`;
    if (progressBar) progressBar.style.width = `${percent}%`;
    document.querySelectorAll('.step-card').forEach((card, idx) => {
        const cb = stepCheckboxes[idx];
        if (cb && cb.checked) card.classList.add('completed');
        else if (cb) card.classList.remove('completed');
    });
}

function makeStepCardsClickable() {
    document.querySelectorAll('.step-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (e.target.closest('a') || e.target.closest('button')) return;
            const checkbox = card.querySelector('.step-checkbox');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    });
}

// ======================= МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================
async function showMethodDetails(button) {
    const methodId = button.dataset.methodId;
    const methodName = button.dataset.methodName;

    const modal = document.getElementById('methodModal');
    if (!modal) return;

    const demoData = {
        name: methodName,
        icon: 'fa-utensils',
        short_description: `Метод приготовления "${methodName}"`,
        description: `Подробное описание метода "${methodName}". Здесь будет информация о технике, советы и рекомендации.`,
        scientific_background: 'Научное обоснование метода будет добавлено позже.',
        typical_temperature: 'По ситуации',
        typical_duration: 'По ситуации',
        tips: '• Совет 1\n• Совет 2\n• Совет 3',
        common_mistakes: '• Типичная ошибка 1\n• Типичная ошибка 2',
        advanced_notes: 'Для опытных кулинаров: дополнительные нюансы.'
    };

    document.getElementById('methodModalName').innerText = demoData.name;
    document.getElementById('methodModalIcon').className = `fas ${demoData.icon} text-amber-600`;
    document.getElementById('methodModalShortDesc').innerText = demoData.short_description;
    document.getElementById('methodModalDesc').innerHTML = demoData.description;

    const scienceBlock = document.getElementById('methodModalScience');
    const scienceText = document.getElementById('methodModalScienceText');
    if (demoData.scientific_background) {
        scienceText.innerText = demoData.scientific_background;
        scienceBlock.classList.remove('hidden');
    } else {
        scienceBlock.classList.add('hidden');
    }

    const tempBlock = document.getElementById('methodModalTemp');
    const tempText = document.getElementById('methodModalTempText');
    if (demoData.typical_temperature) {
        tempText.innerText = demoData.typical_temperature;
        tempBlock.classList.remove('hidden');
    } else {
        tempBlock.classList.add('hidden');
    }

    const durationBlock = document.getElementById('methodModalDuration');
    const durationText = document.getElementById('methodModalDurationText');
    if (demoData.typical_duration) {
        durationText.innerText = demoData.typical_duration;
        durationBlock.classList.remove('hidden');
    } else {
        durationBlock.classList.add('hidden');
    }

    const tipsBlock = document.getElementById('methodModalTips');
    const tipsText = document.getElementById('methodModalTipsText');
    if (demoData.tips) {
        tipsText.innerText = demoData.tips;
        tipsBlock.classList.remove('hidden');
    } else {
        tipsBlock.classList.add('hidden');
    }

    const mistakesBlock = document.getElementById('methodModalMistakes');
    const mistakesText = document.getElementById('methodModalMistakesText');
    if (demoData.common_mistakes) {
        mistakesText.innerText = demoData.common_mistakes;
        mistakesBlock.classList.remove('hidden');
    } else {
        mistakesBlock.classList.add('hidden');
    }

    const advancedBlock = document.getElementById('methodModalAdvanced');
    const advancedText = document.getElementById('methodModalAdvancedText');
    if (demoData.advanced_notes) {
        advancedText.innerText = demoData.advanced_notes;
        advancedBlock.classList.remove('hidden');
    } else {
        advancedBlock.classList.add('hidden');
    }

    modal.classList.remove('hidden');
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

    const modal = document.getElementById('preparationModal');
    if (!modal) return;

    const demoData = {
        name: preparationName,
        description: 'Подробное описание техники подготовки продуктов.',
        tips: '• Полезный совет 1\n• Полезный совет 2',
        time_factor: 'Увеличивает время приготовления на 10%'
    };

    document.getElementById('preparationModalName').innerText = demoData.name;
    document.getElementById('preparationModalDesc').innerHTML = demoData.description;

    const tipsBlock = document.getElementById('preparationModalTips');
    const tipsText = document.getElementById('preparationModalTipsText');
    if (demoData.tips) {
        tipsText.innerText = demoData.tips;
        tipsBlock.classList.remove('hidden');
    } else {
        tipsBlock.classList.add('hidden');
    }

    const timeBlock = document.getElementById('preparationModalTime');
    const timeText = document.getElementById('preparationModalTimeText');
    if (demoData.time_factor) {
        timeText.innerText = demoData.time_factor;
        timeBlock.classList.remove('hidden');
    } else {
        timeBlock.classList.add('hidden');
    }

    modal.classList.remove('hidden');
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

    const modal = document.getElementById('utensilModal');
    if (!modal) return;

    const demoData = {
        name: utensilName,
        description: 'Описание рекомендуемой утвари и её назначения.',
        alternative: 'Можно заменить обычным ножом',
        care: 'Мыть в тёплой воде, сушить в вертикальном положении'
    };

    document.getElementById('utensilModalName').innerText = demoData.name;
    document.getElementById('utensilModalDesc').innerHTML = demoData.description;

    const altBlock = document.getElementById('utensilModalAlternative');
    const altText = document.getElementById('utensilModalAlternativeText');
    if (demoData.alternative) {
        altText.innerText = demoData.alternative;
        altBlock.classList.remove('hidden');
    } else {
        altBlock.classList.add('hidden');
    }

    const careBlock = document.getElementById('utensilModalCare');
    const careText = document.getElementById('utensilModalCareText');
    if (demoData.care) {
        careText.innerText = demoData.care;
        careBlock.classList.remove('hidden');
    } else {
        careBlock.classList.add('hidden');
    }

    modal.classList.remove('hidden');
}

function closeUtensilModal() {
    const modal = document.getElementById('utensilModal');
    if (modal) modal.classList.add('hidden');
}

// ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ ОТОБРАЖЕНИЯ =======================
const modeNormalBtn = document.getElementById('modeNormalBtn');
const modeCompactBtn = document.getElementById('modeCompactBtn');
const stepsContainer = document.getElementById('stepsList');

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

// ======================= ВОССТАНОВЛЕНИЕ ИЗ URL =======================
function restoreStateFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    const modeParam = urlParams.get('mode');
    const meatParam = urlParams.get('meat');
    const portionsParam = urlParams.get('portions');
    const baseIngredientId = urlParams.get('base_ingredient');
    const baseValue = urlParams.get('base_value');

    if (modeParam === 'portions' && portionsParam && !isNaN(parseFloat(portionsParam))) {
        const val = parseFloat(portionsParam);
        if (portionsSlider) portionsSlider.value = val;
        if (portionsValueSpan) portionsValueSpan.innerText = val;
        setMode('portions');
    } else if (modeParam === 'products' && baseIngredientId !== null && baseValue !== null) {
        const targetIngredient = document.querySelector(`.ingredient-item[data-ingredient-id="${baseIngredientId}"]`);
        if (targetIngredient) {
            const amountSpan = targetIngredient.querySelector('.ingredient-amount');
            const name = targetIngredient.dataset.ingredientName;
            const originalValue = parseFloat(targetIngredient.dataset.original);
            const unit = targetIngredient.dataset.unit;
            const val = parseFloat(baseValue);
            currentBaseIngredient = { id: baseIngredientId, name, originalValue, unit, currentValue: val };
            setMode('products');
        }
    } else if (modeParam === 'products' && meatParam && !isNaN(parseFloat(meatParam))) {
        if (meatInput) meatInput.value = parseFloat(meatParam);
        setMode('products');
        recalcByMeatWeight(parseFloat(meatParam));
    } else {
        if (meatInput) meatInput.value = BASE_MEAT;
        setMode('products');
    }
}

// ======================= ШАРИНГ =======================
window.shareRecipe = function() {
    let url = new URL(window.location.href);
    url.search = '';
    if (currentMode === 'products') {
        if (currentBaseIngredient.id !== null && currentBaseIngredient.name !== 'говядина') {
            url.searchParams.set('mode', 'products');
            url.searchParams.set('base_ingredient', currentBaseIngredient.id);
            url.searchParams.set('base_value', currentBaseIngredient.currentValue);
        } else {
            url.searchParams.set('mode', 'products');
            url.searchParams.set('meat', currentBaseIngredient.currentValue);
        }
    } else {
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        url.searchParams.set('mode', 'portions');
        url.searchParams.set('portions', portionsVal);
    }

    if (navigator.share) {
        navigator.share({ title: 'Борщ сибирский', url: url.toString() });
    } else {
        navigator.clipboard.writeText(url.toString()).then(() => alert('Ссылка скопирована!'));
    }
};

// ======================= ИНИЦИАЛИЗАЦИЯ =======================
document.addEventListener('DOMContentLoaded', function() {
    console.log('JS загружен');

    ingredientItems = document.querySelectorAll('#ingredientsList .ingredient-item');
    caloriesSpan = document.querySelector('.calories-value');
    ingredientItems.forEach(item => {
        const original = parseFloat(item.dataset.original);
        originalValues.push(isNaN(original) ? 0 : original);
    });

    modeProductsBtn = document.getElementById('modeProductsBtn');
    modePortionsBtn = document.getElementById('modePortionsBtn');
    modeProductsPanel = document.getElementById('modeProductsPanel');
    modePortionsPanel = document.getElementById('modePortionsPanel');
    meatInput = document.getElementById('customMeatWeight');
    applyMeatBtn = document.getElementById('applyMeatBtn');
    resetProductsBtn = document.getElementById('resetProductsBtn');
    meatRatioInfo = document.getElementById('meatRatioInfo');
    portionsSlider = document.getElementById('portionsSlider');
    portionsValueSpan = document.getElementById('portionsValue');
    resetPortionsBtn = document.getElementById('resetPortionsBtn');
    portionsRatioInfo = document.getElementById('portionsRatioInfo');

    if (applyMeatBtn) applyMeatBtn.addEventListener('click', () => resetBaseIngredient());
    if (resetProductsBtn) resetProductsBtn.addEventListener('click', () => resetBaseIngredient());
    if (portionsSlider) portionsSlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        if (portionsValueSpan) portionsValueSpan.innerText = val;
        recalcByPortions(val);
    });
    if (resetPortionsBtn) resetPortionsBtn.addEventListener('click', () => {
        if (portionsSlider) portionsSlider.value = BASE_PORTIONS;
        if (portionsValueSpan) portionsValueSpan.innerText = BASE_PORTIONS;
        recalcByPortions(BASE_PORTIONS);
    });
    if (modeProductsBtn) modeProductsBtn.addEventListener('click', () => setMode('products'));
    if (modePortionsBtn) modePortionsBtn.addEventListener('click', () => setMode('portions'));

    document.querySelectorAll('.ingredient-chain-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const amountSpan = btn.closest('.ingredient-item')?.querySelector('.ingredient-amount');
            setBaseIngredient(btn.dataset.ingredientId, btn.dataset.ingredientName,
                parseFloat(btn.dataset.originalValue), btn.dataset.unit, amountSpan);
        });
    });

    document.querySelectorAll('.ingredient-replace-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            showReplaceModal(btn.dataset.ingredientId, btn.dataset.ingredientName,
                parseFloat(btn.dataset.originalValue), btn.dataset.unit);
        });
    });

    document.getElementById('cancelReplaceBtn')?.addEventListener('click', () => {
        document.getElementById('replaceModal').classList.add('hidden');
        activeReplaceIngredient = null;
    });
    document.getElementById('confirmReplaceBtn')?.addEventListener('click', () => applyReplacement());

    // Закрытие модальных окон по клику вне области
    document.getElementById('methodModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('methodModal')) closeMethodModal();
    });
    document.getElementById('preparationModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('preparationModal')) closePreparationModal();
    });
    document.getElementById('utensilModal')?.addEventListener('click', (e) => {
        if (e.target === document.getElementById('utensilModal')) closeUtensilModal();
    });

    restoreCheckboxStates();
    document.querySelectorAll('.ingredient-checkbox').forEach(cb => {
        cb.addEventListener('change', saveCheckboxStates);
    });

    document.getElementById('checkAllBtn')?.addEventListener('click', () => {
        document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = true);
        saveCheckboxStates();
    });
    document.getElementById('uncheckAllBtn')?.addEventListener('click', () => {
        document.querySelectorAll('.ingredient-checkbox').forEach(cb => cb.checked = false);
        saveCheckboxStates();
    });
    document.getElementById('copyCheckedBtn')?.addEventListener('click', () => {
        const items = [];
        document.querySelectorAll('.ingredient-item').forEach(item => {
            const cb = item.querySelector('.ingredient-checkbox');
            const label = item.querySelector('label');
            const amountSpan = item.querySelector('.ingredient-amount');
            if (cb && cb.checked && label) {
                items.push(`${label.innerText.trim()} — ${amountSpan ? amountSpan.innerText : ''}`);
            }
        });
        if (items.length === 0) alert('Ничего не отмечено');
        else navigator.clipboard.writeText(items.join('\n')).then(() => alert(`Скопировано ${items.length} ингредиентов`));
    });

    restoreStepStates();
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        cb.addEventListener('change', saveStepStates);
    });
    makeStepCardsClickable();

    restoreReplacementsFromLocal();
    restoreStateFromURL();
    applyStoredReplacements();
    updateIngredientLinks();

    // Привязываем функции к window
    window.showMethodDetails = showMethodDetails;
    window.closeMethodModal = closeMethodModal;
    window.showPreparationDetails = showPreparationDetails;
    window.closePreparationModal = closePreparationModal;
    window.showUtensilDetails = showUtensilDetails;
    window.closeUtensilModal = closeUtensilModal;

    console.log('Инициализация завершена');
    console.log('Глобальные функции:', {
        showMethodDetails: typeof window.showMethodDetails,
        showPreparationDetails: typeof window.showPreparationDetails,
        showUtensilDetails: typeof window.showUtensilDetails,
    });
});

// Дублируем привязку на всякий случай
window.showMethodDetails = showMethodDetails;
window.closeMethodModal = closeMethodModal;
window.showPreparationDetails = showPreparationDetails;
window.closePreparationModal = closePreparationModal;
window.showUtensilDetails = showUtensilDetails;
window.closeUtensilModal = closeUtensilModal;