// ======================= СОХРАНЯЕМ ИСХОДНЫЕ ДАННЫЕ =======================
let originalValues = [];
let ingredientItems = [];
let caloriesSpan = null;

// DOM элементы для режимов
let modeProductsBtn, modePortionsBtn, modeProductsPanel, modePortionsPanel;
let meatInput, applyMeatBtn, resetProductsBtn, meatRatioInfo;
let portionsSlider, portionsValueSpan, resetPortionsBtn, portionsRatioInfo;

// Базовые значения по рецепту
const BASE_MEAT = 500;        // 500 г мяса по рецепту
const BASE_PORTIONS = 6;      // 6 порций по рецепту

// Текущий режим: 'products' или 'portions'
let currentMode = 'products';

// ======================= ФУНКЦИЯ ОБНОВЛЕНИЯ ИНГРЕДИЕНТОВ =======================
function updateIngredientsDisplay(ratio) {
    ingredientItems.forEach((item, idx) => {
        const amountSpan = item.querySelector('.ingredient-amount');
        if (!amountSpan) return;

        const unit = item.dataset.unit;
        let newVal = originalValues[idx] * ratio;

        // Умное округление в зависимости от единицы измерения
        if (unit === 'шт.' || unit === 'зубч.' || unit === 'ст. л.') {
            newVal = Math.ceil(newVal);  // штучные округляем вверх
        } else if (unit === 'г' || unit === 'мл') {
            newVal = Math.round(newVal);  // граммы и миллилитры — до целых
        } else {
            newVal = Math.round(newVal * 10) / 10;  // остальное — с одним знаком
        }

        amountSpan.innerText = `${newVal} ${unit}`;
    });

    // Обновляем калории
    if (caloriesSpan) {
        const baseCal = parseFloat(caloriesSpan.dataset.base) || 380;
        const newCal = Math.round(baseCal * ratio);
        caloriesSpan.innerText = newCal;
    }
}

// ======================= РЕЖИМ 1: ПО ПРОДУКТАМ (ПОД ВЕС МЯСА) =======================
function recalcByMeatWeight(meatGram) {
    let ratio = meatGram / BASE_MEAT;
    if (isNaN(ratio) || ratio <= 0) ratio = 1;
    updateIngredientsDisplay(ratio);

    if (meatRatioInfo) {
        meatRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${meatGram} г мяса)`;
    }
}

// ======================= РЕЖИМ 2: ПО ПОРЦИЯМ (КОЛИЧЕСТВО ГОСТЕЙ) =======================
function recalcByPortions(portions) {
    let ratio = portions / BASE_PORTIONS;
    if (isNaN(ratio) || ratio <= 0) ratio = 1;
    updateIngredientsDisplay(ratio);

    if (portionsRatioInfo) {
        portionsRatioInfo.innerText = `Коэффициент: ${ratio.toFixed(2)} (на ${portions} порций)`;
    }
}

// ======================= ПЕРЕКЛЮЧЕНИЕ МЕЖДУ РЕЖИМАМИ =======================
function setMode(mode) {
    currentMode = mode;

    if (mode === 'products') {
        // Показываем панель продуктов, скрываем порции
        if (modeProductsPanel) modeProductsPanel.classList.remove('hidden');
        if (modePortionsPanel) modePortionsPanel.classList.add('hidden');

        // Стили кнопок
        if (modeProductsBtn) {
            modeProductsBtn.classList.add('bg-amber-100', 'text-amber-800');
            modeProductsBtn.classList.remove('text-gray-500');
        }
        if (modePortionsBtn) {
            modePortionsBtn.classList.remove('bg-green-100', 'text-green-800');
            modePortionsBtn.classList.add('text-gray-500');
        }

        // Пересчитываем по текущему значению мяса
        const meatVal = meatInput ? parseFloat(meatInput.value) : BASE_MEAT;
        recalcByMeatWeight(isNaN(meatVal) ? BASE_MEAT : meatVal);
    } else {
        // Показываем панель порций, скрываем продукты
        if (modeProductsPanel) modeProductsPanel.classList.add('hidden');
        if (modePortionsPanel) modePortionsPanel.classList.remove('hidden');

        // Стили кнопок
        if (modePortionsBtn) {
            modePortionsBtn.classList.add('bg-green-100', 'text-green-800');
            modePortionsBtn.classList.remove('text-gray-500');
        }
        if (modeProductsBtn) {
            modeProductsBtn.classList.remove('bg-amber-100', 'text-amber-800');
            modeProductsBtn.classList.add('text-gray-500');
        }

        // Пересчитываем по текущему значению порций
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        recalcByPortions(isNaN(portionsVal) ? BASE_PORTIONS : portionsVal);
    }
}

// ======================= ФУНКЦИЯ ДЛЯ ШАРИНГА =======================
window.shareRecipe = function() {
    let url = new URL(window.location.href);
    url.searchParams.delete('meat');
    url.searchParams.delete('portions');

    if (currentMode === 'products') {
        const meatVal = meatInput ? parseFloat(meatInput.value) : BASE_MEAT;
        url.searchParams.set('meat', meatVal);
    } else {
        const portionsVal = portionsSlider ? parseInt(portionsSlider.value) : BASE_PORTIONS;
        url.searchParams.set('portions', portionsVal);
    }

    const recipeTitle = document.querySelector('h1')?.innerText || 'Рецепт';

    if (navigator.share) {
        navigator.share({
            title: recipeTitle,
            text: currentMode === 'products' ? 'Рецепт с пересчётом под мой вес мяса' : 'Рецепт с пересчётом на количество гостей',
            url: url.toString()
        }).catch(err => console.log('Ошибка шеринга:', err));
    } else {
        navigator.clipboard.writeText(url.toString()).then(() => {
            alert('Ссылка скопирована!');
        }).catch(() => alert('Не удалось скопировать ссылку'));
    }
};

// ======================= ИНИЦИАЛИЗАЦИЯ =======================
document.addEventListener('DOMContentLoaded', function() {
    // Находим элементы
    ingredientItems = document.querySelectorAll('#ingredientsList .ingredient-item');
    caloriesSpan = document.querySelector('.calories-value');

    // Сохраняем исходные значения ингредиентов
    ingredientItems.forEach(item => {
        const original = parseFloat(item.dataset.original);
        if (!isNaN(original)) {
            originalValues.push(original);
        } else {
            originalValues.push(0);
        }
    });

    // Находим DOM элементы режимов
    modeProductsBtn = document.getElementById('modeProductsBtn');
    modePortionsBtn = document.getElementById('modePortionsBtn');
    modeProductsPanel = document.getElementById('modeProductsPanel');
    modePortionsPanel = document.getElementById('modePortionsPanel');

    // Режим продуктов
    meatInput = document.getElementById('customMeatWeight');
    applyMeatBtn = document.getElementById('applyMeatBtn');
    resetProductsBtn = document.getElementById('resetProductsBtn');
    meatRatioInfo = document.getElementById('meatRatioInfo');

    // Режим порций
    portionsSlider = document.getElementById('portionsSlider');
    portionsValueSpan = document.getElementById('portionsValue');
    resetPortionsBtn = document.getElementById('resetPortionsBtn');
    portionsRatioInfo = document.getElementById('portionsRatioInfo');

    // Навешиваем обработчики для режима продуктов
    if (applyMeatBtn) {
        applyMeatBtn.addEventListener('click', () => {
            let val = parseFloat(meatInput.value);
            if (isNaN(val) || val <= 0) val = BASE_MEAT;
            meatInput.value = val;
            recalcByMeatWeight(val);
        });
    }

    if (resetProductsBtn) {
        resetProductsBtn.addEventListener('click', () => {
            meatInput.value = BASE_MEAT;
            recalcByMeatWeight(BASE_MEAT);
        });
    }

    // Навешиваем обработчики для режима порций
    if (portionsSlider) {
        portionsSlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            if (portionsValueSpan) portionsValueSpan.innerText = val;
            recalcByPortions(val);
        });
    }

    if (resetPortionsBtn) {
        resetPortionsBtn.addEventListener('click', () => {
            if (portionsSlider) portionsSlider.value = BASE_PORTIONS;
            if (portionsValueSpan) portionsValueSpan.innerText = BASE_PORTIONS;
            recalcByPortions(BASE_PORTIONS);
        });
    }

    // Обработчики переключения режимов
    if (modeProductsBtn) {
        modeProductsBtn.addEventListener('click', () => setMode('products'));
    }
    if (modePortionsBtn) {
        modePortionsBtn.addEventListener('click', () => setMode('portions'));
    }

    // ======================= ОБРАБОТКА ПАРАМЕТРОВ URL =======================
    const urlParams = new URLSearchParams(window.location.search);
    const meatParam = urlParams.get('meat');
    const portionsParam = urlParams.get('portions');

    if (portionsParam !== null && !isNaN(parseFloat(portionsParam))) {
        // Сначала переключаем режим, потом устанавливаем значение
        setMode('portions');
        const val = parseFloat(portionsParam);
        if (portionsSlider) {
            portionsSlider.value = val;
            if (portionsValueSpan) portionsValueSpan.innerText = val;
        }
        recalcByPortions(val);
    } else if (meatParam !== null && !isNaN(parseFloat(meatParam))) {
        setMode('products');
        const val = parseFloat(meatParam);
        if (meatInput) meatInput.value = val;
        recalcByMeatWeight(val);
    } else {
        // Режим по умолчанию — продукты с базовыми значениями
        setMode('products');
        if (meatInput) meatInput.value = BASE_MEAT;
        recalcByMeatWeight(BASE_MEAT);
    }
});