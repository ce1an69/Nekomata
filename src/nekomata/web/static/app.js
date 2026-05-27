/** Nekomata Web — main application entry. */

import { Starfield } from './particles.js';
import { state } from './state.js';
import { showScreen, showToast, showModal, resumeHome, needsInit, onShow, t, applyI18n } from './utils.js';
import { showBrowserScreen } from './browser.js';
import { showDrawScreen, initDrawKeyboard } from './draw.js';

let starfield = null;

// Expose state globally for utils.t()
window.__nekoState = state;

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
    const canvas = document.getElementById('stars-canvas');
    if (canvas) {
        starfield = new Starfield(canvas);
        starfield.start();
    }

    await Promise.all([loadConfig(), loadCards(), loadSpreads(), loadStrings()]);

    if (state.cards.length === 0) {
        document.body.innerHTML = '<div style="padding:2em;color:var(--red);text-align:center">' +
            '<h2>Load failed</h2><p>Unable to load card data. Please refresh the page.</p></div>';
        return;
    }

    applyI18n();

    if (!state.config.has_api_key) {
        showScreen('setup');
    } else {
        showScreen('home');
    }

    initDrawKeyboard();
});

async function loadConfig() {
    try {
        const r = await fetch('/api/config');
        if (!r.ok) throw new Error(`${r.status}`);
        state.config = await r.json();
    } catch (e) {
        console.warn('Failed to load config:', e);
    }
}

async function loadCards() {
    try {
        const r = await fetch('/api/cards');
        if (!r.ok) throw new Error(`${r.status}`);
        state.cards = await r.json();
    } catch (e) {
        console.error('Failed to load card data:', e);
    }
}

async function loadSpreads() {
    try {
        const r = await fetch('/api/spreads');
        if (!r.ok) throw new Error(`${r.status}`);
        state.spreads = await r.json();
    } catch (e) {
        console.error('Failed to load spreads:', e);
    }
}

async function loadStrings() {
    try {
        const r = await fetch('/api/strings');
        if (!r.ok) throw new Error(`${r.status}`);
        state.strings = await r.json();
    } catch (e) {
        console.warn('Failed to load UI strings:', e);
    }
}

// ---------------------------------------------------------------------------
// Setup Screen
// ---------------------------------------------------------------------------

document.querySelector('#setup-save')?.addEventListener('click', saveSetup);
document.querySelector('#setup-back')?.addEventListener('click', () => { showScreen('home'); resumeHome(); });

function initSetupScreen() {
    const urlInput = document.getElementById('setup-url');
    const keyInput = document.getElementById('setup-key');
    const modelInput = document.getElementById('setup-model');
    const langSelect = document.getElementById('setup-lang');

    if (state.config.api_url) urlInput.value = state.config.api_url;
    if (state.config.api_key) keyInput.value = state.config.api_key;
    else if (state.config.has_api_key) { keyInput.value = ''; keyInput.placeholder = '•••••••• (configured)'; }
    if (state.config.model) modelInput.value = state.config.model;
    if (state.config.lang) langSelect.value = state.config.lang;
    document.getElementById('setup-error').classList.add('hidden');

    if (!needsInit('setup')) return;

    modelInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') saveSetup(); });
    keyInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') modelInput.focus(); });
    urlInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') keyInput.focus(); });
}

async function saveSetup() {
    const api_url = document.getElementById('setup-url').value.trim();
    const api_key = document.getElementById('setup-key').value.trim();
    const model = document.getElementById('setup-model').value.trim();
    const lang = document.getElementById('setup-lang').value;
    const errEl = document.getElementById('setup-error');

    if (!api_url) {
        errEl.textContent = t('setup.error_url_required', 'API URL is required');
        errEl.classList.remove('hidden');
        return;
    }
    if (!model) {
        errEl.textContent = t('setup.error_model_required', 'Model is required');
        errEl.classList.remove('hidden');
        return;
    }
    if (!api_key && !state.config.has_api_key) {
        errEl.textContent = t('setup.error_key_required', 'Please enter an API Key');
        errEl.classList.remove('hidden');
        return;
    }

    errEl.classList.add('hidden');
    try {
        const r = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_url, api_key, model, lang }),
        });
        if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error(errBody.detail || `Save failed (${r.status})`);
        }
        state.config = await r.json();
        await loadStrings();
        applyI18n();
        showScreen('home');
    } catch (e) {
        errEl.textContent = e.message;
        errEl.classList.remove('hidden');
    }
}

// ---------------------------------------------------------------------------
// Home Screen
// ---------------------------------------------------------------------------

function slashDesc(cmd) {
    switch (cmd) {
        case '/browse': return `${t('home.commands./browse_short.1', 'Browse all')} ${state.cards.length || 78} ${t('home.commands./browse_cards.1', 'cards')}`;
        case '/config': return t('home.commands./config.1', 'Edit API settings');
    }
}

const SLASH_COMMANDS = ['/browse', '/config'];

export function initHomeScreen() {
    const input = document.getElementById('home-input');
    const sugBox = document.getElementById('home-suggestions');

    if (!needsInit('home')) return;

    function _sugItems() { return sugBox.querySelectorAll('.suggestion-item'); }
    function _sugActive() { return sugBox.querySelector('.suggestion-item.active'); }
    function _sugSetActive(item) {
        sugBox.querySelectorAll('.suggestion-item').forEach(i => i.classList.remove('active'));
        if (item) item.classList.add('active');
    }

    input.addEventListener('input', () => {
        const val = input.value;
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
        if (!val.startsWith('/')) {
            sugBox.classList.add('hidden');
            return;
        }
        const matches = SLASH_COMMANDS.filter(cmd => cmd.startsWith(val));
        if (matches.length === 0 || (matches.length === 1 && matches[0] === val)) {
            sugBox.classList.add('hidden');
            return;
        }
        sugBox.innerHTML = matches.map(cmd => {
            const desc = slashDesc(cmd);
            return `<div class="suggestion-item" data-cmd="${cmd}">` +
            `<span class="cmd">${cmd}</span><span class="desc">${desc}</span></div>`;
        }).join('');
        sugBox.classList.remove('hidden');

        sugBox.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.dataset.cmd;
                sugBox.classList.add('hidden');
                input.focus();
            });
        });
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            const items = _sugItems();
            if (!items.length) return;
            e.preventDefault();
            const cur = _sugActive();
            const arr = [...items];
            const idx = cur ? arr.indexOf(cur) : -1;
            const next = e.key === 'ArrowDown'
                ? arr[(idx + 1) % arr.length]
                : arr[(idx - 1 + arr.length) % arr.length];
            _sugSetActive(next);
            if (next) { input.value = next.dataset.cmd; next.scrollIntoView({ block: 'nearest' }); }
            return;
        }
        if (e.key === 'Enter') {
            const val = input.value.trim();
            sugBox.classList.add('hidden');
            if (!val) return;
            if (val.startsWith('/')) {
                handleSlashCommand(val);
            } else {
                state.question = val;
                input.value = '';
                showSpreadSelect();
            }
        }
        if (e.key === 'Tab') {
            e.preventDefault();
            const val = input.value;
            if (val.startsWith('/')) {
                const match = SLASH_COMMANDS.find(c => c.startsWith(val) && c !== val);
                if (match) input.value = match;
            }
        }
    });
}

function handleSlashCommand(cmd) {
    const input = document.getElementById('home-input');
    input.value = '';
    switch (cmd) {
        case '/browse':
            showBrowserScreen();
            break;
        case '/config':
            showScreen('setup');
            break;
    }
}

// ---------------------------------------------------------------------------
// Spread Select Screen
// ---------------------------------------------------------------------------

function showSpreadSelect() {
    showScreen('spread-select');
    initSpreadSelect();
}

function initSpreadSelect() {
    const qBar = document.getElementById('spread-question-bar');
    if (state.question) {
        qBar.textContent = `> ${state.question}`;
        qBar.classList.remove('hidden');
    } else {
        qBar.classList.add('hidden');
    }

    const btnContainer = document.getElementById('spread-buttons');
    btnContainer.innerHTML = '';

    state.spreads.forEach((sp) => {
        const opt = document.createElement('div');
        opt.className = 'spread-option';
        opt.dataset.key = sp.key;
        opt.innerHTML = `<span class="sname">${sp.name}</span>` +
            `<span class="scount">${sp.card_count}</span>`;
        opt.addEventListener('mouseenter', () => showSpreadPreview(sp));
        opt.addEventListener('click', () => selectSpread(sp.key));
        btnContainer.appendChild(opt);
    });

    const back = document.createElement('button');
    back.className = 'spread-back';
    back.textContent = '← Back';
    back.addEventListener('click', () => {
        showScreen('home');
        resumeHome();
    });
    btnContainer.appendChild(back);

    if (state.spreads.length > 0) showSpreadPreview(state.spreads[0]);

    if (!initSpreadSelect._kbd) {
        initSpreadSelect._kbd = true;
        document.getElementById('screen-spread-select').addEventListener('keydown', (e) => {
            const opts = btnContainer.querySelectorAll('.spread-option');
            if (!opts.length) return;
            const arr = [...opts];
            const cur = btnContainer.querySelector('.spread-option.active');
            const idx = cur ? arr.indexOf(cur) : -1;

            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                const next = e.key === 'ArrowDown'
                    ? arr[(idx + 1) % arr.length]
                    : arr[(idx - 1 + arr.length) % arr.length];
                opts.forEach(o => o.classList.remove('active'));
                next.classList.add('active');
                const sp = state.spreads.find(s => s.key === next.dataset.key);
                if (sp) showSpreadPreview(sp);
                next.scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter' && idx >= 0) {
                selectSpread(arr[idx].dataset.key);
            } else if (e.key === 'Enter' && idx < 0 && arr.length) {
                arr[0].classList.add('active');
                const sp = state.spreads.find(s => s.key === arr[0].dataset.key);
                if (sp) showSpreadPreview(sp);
            }
        });
    }
}

function showSpreadPreview(sp) {
    const preview = document.getElementById('spread-preview');
    const cardsLabel = state.config.lang === 'zh' ? '张牌' : 'cards';
    preview.innerHTML = `<h3>${sp.name}</h3>` +
        `<p class="subtext">${sp.description} · ${sp.card_count} ${cardsLabel}</p>` +
        `<ul class="pos-list">${sp.positions.map((p, i) =>
            `<li>${p.name} — ${p.description}</li>`
        ).join('')}</ul>`;
}

function selectSpread(key) {
    state.spreadKey = key;
    showDrawScreen();
}

// ---------------------------------------------------------------------------
// Screen init hooks
// ---------------------------------------------------------------------------

onShow('setup', initSetupScreen);
onShow('home', () => {
    initHomeScreen();
    document.getElementById('home-input').focus();
});
