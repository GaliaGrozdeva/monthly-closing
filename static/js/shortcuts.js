// Клавишите са активни само когато съответното действие е на страницата.
(() => {
    const saveButton = document.querySelector('[data-shortcut="save"]');
    const form = saveButton ? saveButton.form : null;
    const values = () => form ? JSON.stringify(Array.from(new FormData(form).entries())) : "";
    const initialValues = values();
    let submitting = false;

    if (form) {
        form.addEventListener("submit", () => { submitting = true; });
    }

    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[href]");
        if (!link || !form || submitting || values() === initialValues) return;
        if (link.target === "_blank" || link.getAttribute("href").startsWith("#")) return;
        if (!window.confirm("Има незапазени промени. Да напуснем ли страницата без запис?")) {
            event.preventDefault();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.defaultPrevented || event.isComposing || event.repeat || event.metaKey) return;
        let action = "";
        if (!event.altKey && !event.ctrlKey && !event.shiftKey) {
            if (event.key === "F1") action = "new";
            if (event.key === "F2") action = "save";
            if (event.key === "F3") action = "search";
            if (event.key === "Escape") {
                action = "back";
            }
        }
        if (event.altKey && !event.ctrlKey && !event.shiftKey) {
            // code разпознава същите клавиши и при включена кирилица.
            if (event.code === "KeyE") action = "edit";
            if (event.code === "KeyD") action = "delete";
        }
        if (!action) return;
        const target = document.querySelector('[data-shortcut="' + action + '"]');
        if (!target || target.disabled || target.hidden) return;
        event.preventDefault();
        if (action === "search") {
            target.focus();
            target.select();
        } else {
            target.click();
        }
    });
})();
