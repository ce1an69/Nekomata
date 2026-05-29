/** Shared UI helpers. */

const _screenHooks = {};

/** Get a localized string from state.strings by dot-path (e.g. "setup.title"). */
export function t(path, fallback = '') {
    const s = window.__nekoState?.strings || {};
    const parts = path.split('.');
    let val = s;
    for (const p of parts) {
        if (val == null || typeof val !== 'object') return fallback;
        val = val[p];
    }
    return val != null ? val : fallback;
}

/** Apply i18n to all elements with data-i18n / data-i18n-placeholder attributes. */
export function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const path = el.getAttribute('data-i18n');
        const val = t(path);
        if (val) el.textContent = val;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const path = el.getAttribute('data-i18n-placeholder');
        const val = t(path);
        if (val) el.placeholder = val;
    });
}

export function onShow(screenId, fn) {
    _screenHooks[screenId] = _screenHooks[screenId] || [];
    _screenHooks[screenId].push(fn);
}

export function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    const el = document.getElementById(`screen-${id}`);
    if (el) {
        el.classList.remove('hidden');
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = '';
    }
    const hooks = _screenHooks[id];
    if (hooks) hooks.forEach(fn => fn());
}

export function showToast(title, body, duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    const titleEl = document.createElement('div');
    titleEl.className = 'toast-title';
    titleEl.textContent = title;
    toast.appendChild(titleEl);
    if (body) {
        const bodyEl = document.createElement('div');
        bodyEl.className = 'toast-body';
        bodyEl.textContent = body;
        toast.appendChild(bodyEl);
    }
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('exiting');
        toast.addEventListener('animationend', () => toast.remove());
    }, duration);
}

export function showModal(title, bodyHtml) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const box = document.createElement('div');
    box.className = 'modal-box';
    const h3 = document.createElement('h3');
    h3.textContent = title;
    box.appendChild(h3);
    box.insertAdjacentHTML('beforeend', bodyHtml);
    const actions = document.createElement('div');
    actions.className = 'modal-actions';
    const btn = document.createElement('button');
    btn.className = 'btn btn-primary modal-close';
    btn.textContent = t('common.ok', 'OK');
    actions.appendChild(btn);
    box.appendChild(actions);
    overlay.appendChild(box);
    const close = () => {
        overlay.classList.add('closing');
        overlay.addEventListener('animationend', () => overlay.remove());
    };
    btn.addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    document.body.appendChild(overlay);
}

function escapeAttr(s) {
    return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function cardImgUrl(card, reversed = false) {
    const style = reversed ? ' style="transform: rotate(180deg)"' : '';
    return `<div class="detail-card-img"><img src="/assets/cards/${escapeAttr(card.arcana)}/${escapeAttr(card.id)}_detail.png" alt="${escapeAttr(card.name)}"${style}></div>`;
}

export function makeBtn(label, cls, onClick) {
    const btn = document.createElement('button');
    btn.className = `btn ${cls}`;
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    return btn;
}

export function resumeHome() {
    const input = document.getElementById('home-input');
    input.value = '';
    input.style.height = 'auto';
    input.focus();
}

const _inited = new Set();
export function needsInit(key) {
    if (_inited.has(key)) return false;
    _inited.add(key);
    return true;
}

// -- Card data helpers (locale-aware) --

export function isEn() {
    return window.__nekoState?.config?.lang === 'en';
}

export function cardName(c) {
    return isEn() ? c.name : (c.name_zh || c.name);
}

export function arcanaName(c) {
    return isEn() ? (c.arcana.charAt(0).toUpperCase() + c.arcana.slice(1)) : (c.arcana_zh || c.arcana);
}

export function cardKeywords(c, reversed) {
    if (isEn() && c.keywords_upright_en?.length) {
        return reversed ? c.keywords_reversed_en : c.keywords_upright_en;
    }
    return reversed ? c.keywords_reversed : c.keywords_upright;
}

export function cardMeaning(c, reversed) {
    if (isEn() && c.meaning_upright_en) {
        return reversed ? c.meaning_reversed_en : c.meaning_upright_en;
    }
    return reversed ? c.meaning_reversed : c.meaning_upright;
}

export function statusLabel(reversed) {
    const cd = window.__nekoState?.strings?.card_detail || {};
    return reversed ? (cd.reversed || 'Reversed') : (cd.upright || 'Upright');
}
