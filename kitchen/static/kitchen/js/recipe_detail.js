// ======================= ШАГИ ПРИГОТОВЛЕНИЯ =======================
function saveStepStates() {
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        localStorage.setItem(`subrecipe_step_${cb.id}`, cb.checked);
    });
}

function restoreStepStates() {
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        const saved = localStorage.getItem(`subrecipe_step_${cb.id}`);
        if (saved !== null) cb.checked = saved === 'true';
    });
}

function updateStepsProgress() {
    const stepCheckboxes = document.querySelectorAll('.step-checkbox');
    const total = stepCheckboxes.length;
    const completed = Array.from(stepCheckboxes).filter(cb => cb.checked).length;
    const percent = total ? (completed / total) * 100 : 0;
    const progressBar = document.getElementById('stepsProgressBar');
    const progressText = document.getElementById('stepsProgress');

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

// ======================= ИНИЦИАЛИЗАЦИЯ =======================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Recipe detail JS загружен');

    // Прогресс-бар
    const stepsContainer = document.querySelector('.space-y-6');
    if (stepsContainer && !document.getElementById('stepsProgress')) {
        const progressHtml = `
            <div class="mb-6 no-print">
                <div class="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Прогресс приготовления</span>
                    <span id="stepsProgress">0/0</span>
                </div>
                <div class="progress-bar">
                    <div id="stepsProgressBar" class="progress-fill" style="width: 0%"></div>
                </div>
            </div>
        `;
        stepsContainer.insertAdjacentHTML('beforebegin', progressHtml);
    }

    restoreStepStates();
    document.querySelectorAll('.step-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            saveStepStates();
            updateStepsProgress();
        });
    });
    makeStepCardsClickable();
    updateStepsProgress();

    // Авто-прокрутка к шагу из URL (для возврата)
    const urlParams = new URLSearchParams(window.location.search);
    const stepParam = urlParams.get('step');
    if (stepParam) {
        const targetStep = document.querySelector(`.step-card[data-step-id="${parseInt(stepParam) - 1}"]`);
        if (targetStep) {
            setTimeout(() => {
                targetStep.scrollIntoView({ behavior: 'smooth', block: 'center' });
                targetStep.classList.add('highlight-step');
                setTimeout(() => {
                    targetStep.classList.remove('highlight-step');
                }, 3000);
            }, 500);
        }
    }
});