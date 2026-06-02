// ======================= ВИДЖЕТ ИНГРЕДИЕНТОВ =======================

document.addEventListener('DOMContentLoaded', function() {
    // Данные ингредиентов
    const ingredients = [];
    let currentRatio = 1;
    let currentBaseIngredient = null;
    let currentReplaceIngredient = null;

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

    // Функция обновления всех ингредиентов
    function updateAllIngredients(ratio) {
        ingredients.forEach(ing => {
            let newValue = ing.baseQuantity * ratio;
            let displayValue;

            if (ing.unit === 'шт.' || ing.unit === 'зубч.' || ing.unit === 'ст. л.') {
                displayValue = Math.ceil(newValue);
            } else if (ing.unit === 'г' || ing.unit === 'мл') {
                displayValue = Math.round(newValue);
            } else {
                displayValue = Math.round(newValue * 10) / 10;
            }

            ing.element.innerText = `${displayValue} ${ing.unit}`;
            ing.currentQuantity = displayValue;
        });
    }

    // ======================= ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ =======================
    function setMode(mode) {
        console.log('Switching to mode:', mode);

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
        localStorage.setItem('recipe_mode', mode);
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
            const response = await fetch(`/api/substitutions/${recipeIngredientId}/`);
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
    function openInfoModal(ingredientId, ingredientName) {
        document.getElementById('infoModalName').innerText = ingredientName;
        infoModal.classList.remove('hidden');
    }

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

    // Копировать отмеченное
    if (copyCheckedBtn) {
        copyCheckedBtn.addEventListener('click', () => {
            const items = [];
            document.querySelectorAll('.ingredient-row').forEach(row => {
                const cb = row.querySelector('.ingredient-checkbox');
                const label = row.querySelector('label');
                const amount = row.querySelector('.ingredient-amount')?.innerText;
                if (cb && cb.checked && label) {
                    items.push(`${label.innerText} — ${amount}`);
                }
            });
            if (items.length === 0) alert('Ничего не отмечено');
            else navigator.clipboard.writeText(items.join('\n')).then(() => alert(`Скопировано ${items.length} ингредиентов`));
        });
    }

    // Восстановление режима
    const savedMode = localStorage.getItem('recipe_mode');
    if (savedMode === 'products') {
        setMode('products');
    } else {
        setMode('portions');
    }

    // ======================= ШАГИ ПРИГОТОВЛЕНИЯ =======================
    function updateStepsProgress() {
        const stepCheckboxes = document.querySelectorAll('.step-checkbox');
        const total = stepCheckboxes.length;
        const completed = Array.from(stepCheckboxes).filter(cb => cb.checked).length;
        const percent = total ? (completed / total) * 100 : 0;
        document.getElementById('stepsProgress').innerText = `${completed}/${total}`;
        document.getElementById('stepsProgressBar').style.width = `${percent}%`;

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
            // Если кликнули на чекбокс или на его label — ничего не делаем
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

    console.log('Виджет инициализирован');
});

// ======================= МЕТОДЫ ПРИГОТОВЛЕНИЯ =======================
let methodsCache = {};

async function showMethodDetails(button) {
    const methodId = button.dataset.methodId;
    const methodName = button.dataset.methodName;

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

        const response = await fetch(`/api/method/${methodId}/`);
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
    document.getElementById('methodModalIcon').className = `fas ${data.icon || 'fa-fire'} text-amber-600`;
    document.getElementById('methodModalShortDesc').innerText = data.short_description || '';
    document.getElementById('methodModalDesc').innerHTML = data.description || '';

    const scienceBlock = document.getElementById('methodModalScience');
    const scienceText = document.getElementById('methodModalScienceText');
    if (data.scientific_background) {
        scienceText.innerText = data.scientific_background;
        scienceBlock.classList.remove('hidden');
    } else {
        scienceBlock.classList.add('hidden');
    }

    const tempBlock = document.getElementById('methodModalTemp');
    const tempText = document.getElementById('methodModalTempText');
    if (data.typical_temperature) {
        tempText.innerText = data.typical_temperature;
        tempBlock.classList.remove('hidden');
    } else {
        tempBlock.classList.add('hidden');
    }

    const durationBlock = document.getElementById('methodModalDuration');
    const durationText = document.getElementById('methodModalDurationText');
    if (data.typical_duration) {
        durationText.innerText = data.typical_duration;
        durationBlock.classList.remove('hidden');
    } else {
        durationBlock.classList.add('hidden');
    }

    const tipsBlock = document.getElementById('methodModalTips');
    const tipsText = document.getElementById('methodModalTipsText');
    if (data.tips) {
        tipsText.innerText = data.tips;
        tipsBlock.classList.remove('hidden');
    } else {
        tipsBlock.classList.add('hidden');
    }

    const mistakesBlock = document.getElementById('methodModalMistakes');
    const mistakesText = document.getElementById('methodModalMistakesText');
    if (data.common_mistakes) {
        mistakesText.innerText = data.common_mistakes;
        mistakesBlock.classList.remove('hidden');
    } else {
        mistakesBlock.classList.add('hidden');
    }

    const advancedBlock = document.getElementById('methodModalAdvanced');
    const advancedText = document.getElementById('methodModalAdvancedText');
    if (data.advanced_notes) {
        advancedText.innerText = data.advanced_notes;
        advancedBlock.classList.remove('hidden');
    } else {
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

        const response = await fetch(`/api/preparation/${preparationId}/`);
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
    if (data.tips) {
        tipsText.innerText = data.tips;
        tipsBlock.classList.remove('hidden');
    } else {
        tipsBlock.classList.add('hidden');
    }

    const timeBlock = document.getElementById('preparationModalTime');
    const timeText = document.getElementById('preparationModalTimeText');
    if (data.time_factor) {
        timeText.innerText = `Увеличивает время приготовления в ${data.time_factor} раз`;
        timeBlock.classList.remove('hidden');
    } else {
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

        const response = await fetch(`/api/utensil/${utensilId}/`);
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

    const altBlock = document.getElementById('utensilModalAlternative');
    const altText = document.getElementById('utensilModalAlternativeText');
    if (data.alternative) {
        altText.innerText = data.alternative;
        altBlock.classList.remove('hidden');
    } else {
        altBlock.classList.add('hidden');
    }

    const careBlock = document.getElementById('utensilModalCare');
    const careText = document.getElementById('utensilModalCareText');
    if (data.care_instructions) {
        careText.innerText = data.care_instructions;
        careBlock.classList.remove('hidden');
    } else {
        careBlock.classList.add('hidden');
    }
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

// ======================= ГЛОБАЛЬНЫЕ ПРИВЯЗКИ =======================
window.showMethodDetails = showMethodDetails;
window.closeMethodModal = closeMethodModal;
window.showPreparationDetails = showPreparationDetails;
window.closePreparationModal = closePreparationModal;
window.showUtensilDetails = showUtensilDetails;
window.closeUtensilModal = closeUtensilModal;