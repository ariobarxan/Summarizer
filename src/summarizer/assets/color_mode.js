const root = element.closest('.gradio-container');
const toggle = element.querySelector('#color-mode-toggle');
const storageKey = 'summarizer-color-mode';
let saved = null;
try { saved = localStorage.getItem(storageKey); } catch (_) {}
const initial = saved === 'light' || saved === 'dark'
    ? saved : (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
function applyMode(mode) {
    root.dataset.colorMode = mode;
    toggle.setAttribute('aria-checked', String(mode === 'dark'));
    // Keep Gradio's built-in surfaces consistent with our custom palette.
    document.body.classList.toggle('dark', mode === 'dark');
}
applyMode(initial);
toggle.addEventListener('click', () => {
    const mode = root.dataset.colorMode === 'dark' ? 'light' : 'dark';
    applyMode(mode);
    try { localStorage.setItem(storageKey, mode); } catch (_) {}
});
