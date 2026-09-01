(function () {
    function root() {
        return (typeof gradioApp === 'function') ? gradioApp() : document;
    }

    function byId(id) {
        return root().querySelector(`#${id}`);
    }

    function getNativePromptRow(tab) {
        return byId(`${tab}_prompt_row`);
    }

    function getTopRow(tab) {
        return byId(`${tab}_toprow`);
    }

    function findGenerateColumn(tab) {
        const app = root();
        const generate = app.querySelector(`#${tab}_generate`);
        const topRow = getTopRow(tab);
        if (!generate) return null;

        // Preferred: direct child of top row that owns the Generate button.
        if (topRow) {
            let node = generate;
            while (node && node.parentElement && node.parentElement !== topRow) {
                node = node.parentElement;
            }
            if (node && node.parentElement === topRow) return node;
        }

        // Fallback for alternative prompt layouts: use a reasonably sized column ancestor.
        let node = generate.parentElement;
        while (node && node !== app) {
            if (node.classList && (node.classList.contains('column') || node.classList.contains('gradio-column'))) {
                return node;
            }
            node = node.parentElement;
        }
        return generate.parentElement;
    }

    function moveExtraAbovePrompt(tab) {
        const panel = byId(`${tab}_prompt_prepend_extra_panel`);
        const promptRow = getNativePromptRow(tab);
        if (!panel || !promptRow || !promptRow.parentElement) return false;

        if (panel.nextElementSibling !== promptRow) {
            promptRow.parentElement.insertBefore(panel, promptRow);
        }
        panel.style.display = '';
        return true;
    }

    function moveControlsToGenerateColumn(tab) {
        const panel = byId(`${tab}_prompt_prepend_controls`);
        const column = findGenerateColumn(tab);
        if (!panel || !column) return false;

        // Keep it below the native Generate/style controls, in the free right-side area.
        if (panel.parentElement !== column || panel !== column.lastElementChild) {
            column.appendChild(panel);
        }
        panel.style.display = '';
        return true;
    }

    function apply() {
        for (const tab of ['txt2img', 'img2img']) {
            moveExtraAbovePrompt(tab);
            moveControlsToGenerateColumn(tab);
        }
    }

    function start() {
        apply();
        const target = root();
        if (!target || target.dataset.promptPrependObserver === '2') return;
        target.dataset.promptPrependObserver = '2';
        const obs = new MutationObserver(() => apply());
        obs.observe(target, { childList: true, subtree: true });
        [150, 400, 800, 1500, 3000].forEach(ms => setTimeout(apply, ms));
    }

    if (typeof onUiLoaded === 'function') {
        onUiLoaded(start);
    } else {
        window.addEventListener('load', start);
    }
})();
