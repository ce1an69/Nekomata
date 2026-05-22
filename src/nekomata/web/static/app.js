/** Nekomata Web — main application entry, screen management, all UI logic. */

import { Deck } from './cards.js';
import { InterpretationController } from './interpret.js';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
    question: '',
    spreadKey: '',
    config: { api_url: '', api_key: '', model: '' },
    cards: [],
    spreads: [],
    strings: {},
    spread: null,
    phase: 'pick',   // pick | flip | done
    deck: null,
    pickIndex: 0,
    flipIndex: 0,
    selectedSlotIdx: -1,
    showDetail: true,
    showInterp: false,
    interpCtrl: null,
    reversalProb: 0.5,
    browserReversed: false,
};

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
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
// Screen management
// ---------------------------------------------------------------------------

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    const el = document.getElementById(`screen-${id}`);
    if (el) {
        el.classList.remove('hidden');
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = '';
    }
}

function getVisibleScreen() {
    for (const s of document.querySelectorAll('.screen')) {
        if (!s.classList.contains('hidden')) {
            return s.id.replace('screen-', '');
        }
    }
    return '';
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function cardImgUrl(card, reversed = false) {
    const style = reversed ? ' style="transform: rotate(180deg)"' : '';
    return `<div class="detail-card-img"><img src="/assets/cards/${card.arcana}/${card.id}_detail.png" alt="${card.name}"${style}></div>`;
}

function makeBtn(label, cls, onClick) {
    const btn = document.createElement('button');
    btn.className = `btn ${cls}`;
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    return btn;
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

    modelInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') saveSetup();
    });
    keyInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') modelInput.focus();
    });
    urlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') keyInput.focus();
    });
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

function initHomeScreen() {
    const input = document.getElementById('home-input');
    const sugBox = document.getElementById('home-suggestions');

    if (initHomeScreen._done) return;
    initHomeScreen._done = true;

    input.addEventListener('input', () => {
        const val = input.value;
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

const SLASH_COMMANDS = {
    '/browse': '浏览全部 78 张牌',
    '/help': '帮助',
    '/status': '当前配置',
    '/quit': '退出',
};

function handleSlashCommand(cmd) {
    const input = document.getElementById('home-input');
    input.value = '';
    switch (cmd) {
        case '/browse':
            showBrowserScreen();
            break;
        case '/help':
            alert('输入你的问题开始占卜，或使用 /browse 浏览牌面');
            break;
        case '/status':
            alert(`API: ${state.config.api_url}\nModel: ${state.config.model}`);
            break;
        case '/quit':
            window.close();
            break;
    }
}

function resumeHome() {
    const input = document.getElementById('home-input');
    input.value = '';
    input.focus();
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
        opt.innerHTML = `<span class="sname">${sp.name}</span>` +
            `<span class="scount">${sp.card_count} 张</span>`;
        opt.addEventListener('mouseenter', () => showSpreadPreview(sp));
        opt.addEventListener('click', () => selectSpread(sp.key));
        btnContainer.appendChild(opt);
    });

    // Back button
    const back = document.createElement('button');
    back.className = 'spread-back';
    back.textContent = '← 返回';
    back.addEventListener('click', () => {
        showScreen('home');
        resumeHome();
    });
    btnContainer.appendChild(back);

    // Show first preview
    if (state.spreads.length > 0) showSpreadPreview(state.spreads[0]);
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
// Draw Screen
// ---------------------------------------------------------------------------

function showDrawScreen() {
    const spDef = state.spreads.find(s => s.key === state.spreadKey);
    if (!spDef) return;

    state.deck = new Deck(state.cards);
    state.deck.shuffle();
    state.spread = {
        key: spDef.key,
        positions: spDef.positions,
        drawnCards: [],
        plannedCards: [],
    };
    state.phase = 'pick';
    state.pickIndex = 0;
    state.flipIndex = 0;
    state.selectedSlotIdx = -1;
    state.showDetail = true;
    state.showInterp = false;

    for (let i = 0; i < spDef.positions.length; i++) {
        const draw = state.deck.draw(state.reversalProb);
        if (draw) {
            state.spread.plannedCards.push({
                card: draw.card,
                position: spDef.positions[i],
                isReversed: draw.isReversed,
            });
        }
    }

    showScreen('draw');

    document.getElementById('draw-spread-name').textContent = spDef.name;
    document.getElementById('draw-question').textContent = state.question || '';

    document.getElementById('screen-draw').classList.remove('interpreting');
    syncDrawLayoutState();
    document.getElementById('detail-panel').classList.add('hidden');
    document.getElementById('interp-panel').classList.add('hidden');
    document.getElementById('interp-text').innerHTML = '';

    renderDeck();
    renderSpreadSlots();
    updateDrawActions();

    state.interpCtrl?.abort();
    state.interpCtrl = new InterpretationController(
        document.getElementById('interp-text'),
        document.getElementById('interp-loading'),
        document.getElementById('interp-spinner'),
        document.getElementById('interp-load-msg'),
    );
}

function renderDeck() {
    const grid = document.getElementById('deck-grid');
    const section = document.getElementById('deck-section');
    section.classList.remove('exiting');
    section.style.maxHeight = '300px';
    grid.innerHTML = '';

    const count = 24;
    for (let i = 0; i < count; i++) {
        const card = document.createElement('div');
        card.className = 'deck-card';
        card.textContent = '✦';
        card.dataset.index = i;
        card.addEventListener('click', () => onDeckCardPicked(card));
        grid.appendChild(card);

        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, i * 30);
    }
}

function renderSpreadSlots() {
    const area = document.getElementById('spread-area');
    area.innerHTML = '';

    state.spread.positions.forEach((pos, idx) => {
        const slot = document.createElement('div');
        slot.className = 'spread-slot empty';
        slot.dataset.index = idx;
        slot.innerHTML = `<span class="slot-label">${pos.name}</span>`;
        slot.addEventListener('click', () => onSpreadSlotClicked(slot, idx));
        area.appendChild(slot);
    });

    if (state.spread.positions.length > 0) {
        markWaitingSlot(0);
    }
}

function markWaitingSlot(idx) {
    const slots = document.querySelectorAll('.spread-slot');
    slots.forEach(s => s.classList.remove('waiting'));
    if (idx < slots.length) slots[idx].classList.add('waiting');
}

function onDeckCardPicked(deckCardEl) {
    if (state.phase !== 'pick') return;
    if (deckCardEl.classList.contains('picked')) return;

    const planned = state.spread.plannedCards[state.pickIndex];
    if (!planned) return;

    deckCardEl.classList.add('picked');

    state.spread.drawnCards.push(planned);
    const slotIdx = state.pickIndex;
    const slot = document.querySelectorAll('.spread-slot')[slotIdx];

    slot.classList.remove('empty', 'waiting');
    slot.classList.add('face-down');
    slot.innerHTML = buildSlotFaceDown(planned);

    slot.style.opacity = '0';
    slot.style.transform = 'translateY(-12px)';
    requestAnimationFrame(() => {
        slot.style.opacity = '1';
        slot.style.transform = 'translateY(0)';
    });

    state.pickIndex++;

    if (state.pickIndex >= state.spread.positions.length) {
        setTimeout(() => transitionToFlip(), 400);
    } else {
        markWaitingSlot(state.pickIndex);
    }

    updateDrawActions();
}

function buildSlotFaceDown(drawnCard) {
    return `<div class="slot-inner">` +
        `<div class="slot-face slot-back"><span class="slot-back-pattern">✦</span></div>` +
        `<div class="slot-face slot-front">` +
        buildCardFaceInner(drawnCard) +
        `</div></div>` +
        `<span class="slot-label">${drawnCard.position.name}</span>`;
}

function buildCardFaceInner(drawnCard) {
    const c = drawnCard.card;
    const imgHtml = c.has_image
        ? cardImgUrl(c).replace('detail-card-img', 'slot-card-img')
        : `<div style="font-size:0.75em;color:var(--text);padding:4px;">${c.name_zh}</div>`;
    const revMark = drawnCard.isReversed
        ? `<div class="reversed-mark">reversed</div>` : '';
    return imgHtml + revMark +
        `<div class="card-name">${c.name_zh}</div>`;
}

function transitionToFlip() {
    state.phase = 'flip';
    const section = document.getElementById('deck-section');
    const deckCards = section.querySelectorAll('.deck-card');

    deckCards.forEach((dc, i) => {
        setTimeout(() => dc.classList.add('exiting'), i * 25);
    });

    setTimeout(() => {
        section.classList.add('exiting');
    }, deckCards.length * 25 + 200);

    updateDrawActions();
}

function onSpreadSlotClicked(slotEl, idx) {
    if (state.phase === 'flip') {
        if (slotEl.classList.contains('face-down')) {
            flipSlot(slotEl, idx);
        }
    } else if (state.phase === 'done') {
        selectSlot(idx);
    }
}

function flipSlot(slotEl, idx) {
    slotEl.classList.add('flipped');
    slotEl.classList.remove('face-down');

    setTimeout(() => {
        slotEl.classList.add('revealed');
        slotEl.classList.add('glow');
        setTimeout(() => slotEl.classList.remove('glow'), 300);
    }, 400);

    state.flipIndex++;

    if (state.flipIndex >= state.spread.positions.length) {
        setTimeout(() => completionShimmer(), 500);
    }

    updateDrawActions();
}

function completionShimmer() {
    state.phase = 'done';
    const slots = document.querySelectorAll('.spread-slot');

    slots.forEach((s, i) => {
        setTimeout(() => {
            s.classList.add('glow');
            setTimeout(() => s.classList.remove('glow'), 400);
        }, i * 120);
    });

    setTimeout(() => {
        showDetailPanel();
        selectSlot(0);
    }, slots.length * 120 + 200);

    updateDrawActions();
}

function selectSlot(idx) {
    const slots = document.querySelectorAll('.spread-slot');
    slots.forEach(s => s.classList.remove('selected'));
    if (idx >= 0 && idx < slots.length) {
        slots[idx].classList.add('selected');
        state.selectedSlotIdx = idx;
        updateDetailContent();
    }
}

function showDetailPanel() {
    const panel = document.getElementById('detail-panel');
    if (state.showDetail) {
        panel.classList.remove('hidden');
    }
    syncDrawLayoutState();
}

function syncDrawLayoutState() {
    document.getElementById('screen-draw')?.classList.toggle('detail-hidden', !state.showDetail);
}

function updateDetailContent() {
    const dc = state.spread.drawnCards[state.selectedSlotIdx];
    if (!dc) return;

    const c = dc.card;
    const panel = document.getElementById('detail-content');

    const imgHtml = c.has_image ? cardImgUrl(c) : '';

    const keywords = dc.isReversed ? c.keywords_reversed : c.keywords_upright;
    const meaning = dc.isReversed ? c.meaning_reversed : c.meaning_upright;
    const statusLabel = dc.isReversed ? '逆位' : '正位';

    panel.innerHTML = imgHtml +
        `<div class="detail-field"><div class="label">${c.name_zh} ${c.name}</div></div>` +
        `<div class="detail-field"><div class="label">位置</div><div class="value">${dc.position.name} — ${dc.position.description}</div></div>` +
        `<div class="detail-field"><div class="label">状态</div><div class="value">${statusLabel}</div></div>` +
        `<div class="detail-field"><div class="label">关键词</div><div class="value sub">${keywords.join(', ')}</div></div>` +
        `<div class="detail-field"><div class="label">牌义</div><div class="value sub">${meaning}</div></div>` +
        `<div class="detail-field"><div class="label">元素 · 星座</div><div class="value sub">${c.element} · ${c.astrology}</div></div>`;
}

function updateDrawActions() {
    const hintEl = document.getElementById('draw-hint-text');
    const btnsEl = document.getElementById('draw-buttons');
    btnsEl.innerHTML = '';

    if (state.phase === 'pick') {
        hintEl.textContent = `点击牌堆抽牌 (${state.pickIndex}/${state.spread.positions.length})`;
        btnsEl.appendChild(makeBtn('← 返回', '', () => { showScreen('home'); resumeHome(); }));
    } else if (state.phase === 'flip') {
        hintEl.textContent = `点击牌面翻开 (${state.flipIndex}/${state.spread.positions.length})`;
        btnsEl.appendChild(makeBtn('← 返回', '', () => { showScreen('home'); resumeHome(); }));
    } else {
        hintEl.textContent = '点击牌面查看详情';
        btnsEl.appendChild(makeBtn(
            state.showDetail ? '隐藏详情' : '详情',
            state.showDetail ? 'active' : '',
            () => {
                state.showDetail = !state.showDetail;
                document.getElementById('detail-panel').classList.toggle('hidden', !state.showDetail);
                syncDrawLayoutState();
                updateDrawActions();
            },
        ));
        if (!state.showInterp) {
            btnsEl.appendChild(makeBtn('解读', 'btn-primary', () => startInterpretation()));
        }
        btnsEl.appendChild(makeBtn('← 返回', '', () => { showScreen('home'); resumeHome(); }));
    }
}

async function startInterpretation() {
    state.showInterp = true;
    document.getElementById('screen-draw').classList.add('interpreting');
    syncDrawLayoutState();
    document.getElementById('interp-panel').classList.remove('hidden');
    updateDrawActions();

    await state.interpCtrl.start(state.spread.drawnCards, state.question, state.strings, state.spreadKey);
}

// ---------------------------------------------------------------------------
// Browser Screen
// ---------------------------------------------------------------------------

function showBrowserScreen() {
    state.browserReversed = false;
    showScreen('browser');
    initBrowser();

    const revBtn = document.getElementById('browser-reverse-btn');
    revBtn.classList.remove('active');

    if (!showBrowserScreen._done) {
        showBrowserScreen._done = true;

        document.getElementById('browser-back-btn').addEventListener('click', () => {
            showScreen('home');
            resumeHome();
        });

        revBtn.addEventListener('click', () => {
            state.browserReversed = !state.browserReversed;
            revBtn.classList.toggle('active', state.browserReversed);
            const current = document.querySelector('.card-list-item.selected');
            if (current) showBrowserDetail(current.dataset.id);
        });
    }
}

function initBrowser() {
    const filterBar = document.getElementById('filter-bar');
    const labels = state.strings.arcana_labels || {
        all: '全部', major: '大阿卡纳', cups: '圣杯', wands: '权杖', swords: '宝剑', pentacles: '星币'
    };
    const suits = Object.entries(labels).map(([key, label]) => ({ key, label }));

    filterBar.innerHTML = suits.map(s =>
        `<button class="filter-btn${s.key === 'all' ? ' active' : ''}" data-suit="${s.key}">${s.label}</button>`
    ).join('');

    filterBar.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filterBar.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderCardList(btn.dataset.suit);
        });
    });

    renderCardList('all');
}

function renderCardList(filter) {
    const list = document.getElementById('card-list');
    const countEl = document.getElementById('browser-count');

    const filtered = filter === 'all'
        ? state.cards
        : state.cards.filter(c => c.arcana === filter);

    countEl.textContent = `${filtered.length}/78 cards`;

    list.innerHTML = filtered.map((c) => {
        const numStr = c.arcana === 'major'
            ? toRoman(c.number)
            : String(c.number);
        return `<div class="card-list-item" data-id="${c.id}">` +
            `<span class="item-name">${numStr} ${c.name_zh}</span>` +
            `<span class="item-suit">${c.arcana_zh}</span></div>`;
    }).join('');

    list.querySelectorAll('.card-list-item').forEach(item => {
        item.addEventListener('click', () => {
            list.querySelectorAll('.card-list-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            showBrowserDetail(item.dataset.id);
        });
    });

    const firstItem = list.querySelector('.card-list-item');
    if (firstItem) {
        firstItem.classList.add('selected');
        showBrowserDetail(firstItem.dataset.id);
    }
}

function showBrowserDetail(cardId) {
    const card = state.cards.find(c => c.id === cardId);
    if (!card) return;

    const detail = document.getElementById('browser-detail');
    const reversed = state.browserReversed;

    const imgHtml = card.has_image ? cardImgUrl(card, reversed) : '';

    const keywords = reversed ? card.keywords_reversed : card.keywords_upright;
    const statusLabel = reversed ? '逆位' : '正位';
    const revBadge = reversed ? '<span class="browser-reversed-badge">reversed</span>' : '';

    detail.innerHTML = imgHtml +
        `<div class="detail-field"><div class="label">${card.name_zh} ${card.name}${revBadge}</div></div>` +
        `<div class="detail-field"><div class="label">花色</div><div class="value">${card.arcana_zh}</div></div>` +
        `<div class="detail-field"><div class="label">元素 · 星座</div><div class="value sub">${card.element} · ${card.astrology}</div></div>` +
        `<div class="detail-field"><div class="label">关键词 (${statusLabel})</div><div class="value sub">${keywords.join(', ')}</div></div>` +
        `<div class="detail-field"><div class="label">正位牌义</div><div class="value sub">${card.meaning_upright}</div></div>` +
        `<div class="detail-field"><div class="label">逆位牌义</div><div class="value sub">${card.meaning_reversed}</div></div>`;
}

function toRoman(num) {
    const map = [
        [0, '0'], [1, 'I'], [2, 'II'], [3, 'III'], [4, 'IV'], [5, 'V'],
        [6, 'VI'], [7, 'VII'], [8, 'VIII'], [9, 'IX'], [10, 'X'],
        [11, 'XI'], [12, 'XII'], [13, 'XIII'], [14, 'XIV'], [15, 'XV'],
        [16, 'XVI'], [17, 'XVII'], [18, 'XVIII'], [19, 'XIX'], [20, 'XX'],
        [21, 'XXI'],
    ];
    return map.find(m => m[0] === num)?.[1] || String(num);
}

// ---------------------------------------------------------------------------
// Init screens on first show
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
