/** Card browser screen. */

import { state } from './state.js';
import { showScreen, cardImgUrl, resumeHome } from './utils.js';

export function showBrowserScreen() {
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

        document.getElementById('screen-browser').addEventListener('keydown', (e) => {
            const items = document.querySelectorAll('.card-list-item');
            if (!items.length) return;
            const cur = document.querySelector('.card-list-item.selected');
            const arr = [...items];
            const idx = cur ? arr.indexOf(cur) : -1;

            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                const next = e.key === 'ArrowDown'
                    ? arr[(idx + 1) % arr.length]
                    : arr[(idx - 1 + arr.length) % arr.length];
                arr.forEach(i => i.classList.remove('selected'));
                next.classList.add('selected');
                showBrowserDetail(next.dataset.id);
                next.scrollIntoView({ block: 'nearest' });
            }
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
        const numStr = c.arcana === 'major' ? toRoman(c.number) : String(c.number);
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
