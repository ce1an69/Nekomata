/** Nekomata Web — main application entry. */

import { Starfield } from './particles.js';
import { state } from './state.js';
import { showScreen, showToast, showModal, resumeHome } from './utils.js';
import { showBrowserScreen } from './browser.js';
import { showDrawScreen, initDrawKeyboard } from './draw.js';

let starfield = null;

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
            '<h2>加载失败</h2><p>无法加载卡牌数据，请刷新页面重试。</p></div>';
        return;
    }

    if (!state.config.api_key) {
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

function initSetupScreen() {
    const urlInput = document.getElementById('setup-url');
    const keyInput = document.getElementById('setup-key');
    const modelInput = document.getElementById('setup-model');

    if (state.config.api_url) urlInput.value = state.config.api_url;
    if (state.config.api_key) keyInput.value = state.config.api_key;
    if (state.config.model) modelInput.value = state.config.model;

    if (initSetupScreen._done) return;
    initSetupScreen._done = true;

    modelInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') saveSetup(); });
    keyInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') modelInput.focus(); });
    urlInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') keyInput.focus(); });
}

async function saveSetup() {
    const api_url = document.getElementById('setup-url').value.trim();
    const api_key = document.getElementById('setup-key').value.trim();
    const model = document.getElementById('setup-model').value.trim();
    const errEl = document.getElementById('setup-error');

    if (!api_url || !api_key || !model) {
        errEl.textContent = '所有字段均为必填';
        errEl.classList.remove('hidden');
        return;
    }

    errEl.classList.add('hidden');
    try {
        const r = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_url, api_key, model }),
        });
        if (!r.ok) {
            const errBody = await r.json().catch(() => ({}));
            throw new Error(errBody.detail || `保存失败 (${r.status})`);
        }
        state.config = await r.json();
        showScreen('home');
    } catch (e) {
        errEl.textContent = e.message;
        errEl.classList.remove('hidden');
    }
}

// ---------------------------------------------------------------------------
// Home Screen
// ---------------------------------------------------------------------------

const SLASH_COMMANDS = {
    '/browse': '浏览全部 78 张牌',
    '/help': '帮助',
    '/status': '当前配置',
    '/quit': '退出',
};

export function initHomeScreen() {
    const input = document.getElementById('home-input');
    const sugBox = document.getElementById('home-suggestions');

    if (initHomeScreen._done) return;
    initHomeScreen._done = true;

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
        const matches = Object.entries(SLASH_COMMANDS)
            .filter(([cmd]) => cmd.startsWith(val));
        if (matches.length === 0 || (matches.length === 1 && matches[0][0] === val)) {
            sugBox.classList.add('hidden');
            return;
        }
        sugBox.innerHTML = matches.map(([cmd, desc]) =>
            `<div class="suggestion-item" data-cmd="${cmd}">` +
            `<span class="cmd">${cmd}</span><span class="desc">${desc}</span></div>`
        ).join('');
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
                const match = Object.keys(SLASH_COMMANDS).find(c => c.startsWith(val) && c !== val);
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
        case '/help':
            showModal('帮助',
                '<p>输入你的问题开始占卜</p>' +
                '<p>/browse — 浏览全部 78 张牌</p>' +
                '<p>/status — 查看当前配置</p>' +
                '<p>/quit — 退出</p>');
            break;
        case '/status':
            showToast('当前配置', `API: ${state.config.api_url}  Model: ${state.config.model}`);
            break;
        case '/quit':
            window.close();
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
            `<span class="scount">${sp.card_count} 张</span>`;
        opt.addEventListener('mouseenter', () => showSpreadPreview(sp));
        opt.addEventListener('click', () => selectSpread(sp.key));
        btnContainer.appendChild(opt);
    });

    const back = document.createElement('button');
    back.className = 'spread-back';
    back.textContent = '← 返回';
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
    preview.innerHTML = `<h3>${sp.name}</h3>` +
        `<p class="subtext">${sp.description} · ${sp.card_count} 张牌</p>` +
        `<ul class="pos-list">${sp.positions.map((p, i) =>
            `<li><span class="pos-idx">${i + 1}.</span>${p.name} — ${p.description}</li>`
        ).join('')}</ul>`;
}

function selectSpread(key) {
    state.spreadKey = key;
    showDrawScreen();
}

// ---------------------------------------------------------------------------
// Lazy init on first show
// ---------------------------------------------------------------------------

const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
        if (m.target.id === 'screen-setup' && !m.target.classList.contains('hidden')) {
            initSetupScreen();
        }
        if (m.target.id === 'screen-home' && !m.target.classList.contains('hidden')) {
            initHomeScreen();
            document.getElementById('home-input').focus();
        }
    }
});

observer.observe(document.getElementById('screen-setup'), { attributes: true, attributeFilter: ['class'] });
observer.observe(document.getElementById('screen-home'), { attributes: true, attributeFilter: ['class'] });
