/** Card browser screen. */

import { state } from './state.js';
import { showScreen, cardImgUrl, resumeHome, needsInit, t, isEn, cardName, arcanaName, cardKeywords, cardMeaning, statusLabel as cardStatusLabel } from './utils.js';

export function showBrowserScreen() {
    state.browserReversed = false;
    showScreen('browser');
    initBrowser();

    const revBtn = document.getElementById('browser-reverse-btn');
    revBtn.classList.remove('active');

    if (needsInit('browser')) {

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
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const filterBtns = [...document.querySelectorAll('.filter-btn')];
                const activeBtn = document.querySelector('.filter-btn.active');
                const curIdx = activeBtn ? filterBtns.indexOf(activeBtn) : 0;
                const nextIdx = e.key === 'ArrowRight'
                    ? (curIdx + 1) % filterBtns.length
                    : (curIdx - 1 + filterBtns.length) % filterBtns.length;
                filterBtns.forEach(b => b.classList.remove('active'));
                filterBtns[nextIdx].classList.add('active');
                renderCardList(filterBtns[nextIdx].dataset.suit);
                return;
            }

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
        all: 'All', major: 'Major Arcana', cups: 'Cups', wands: 'Wands', swords: 'Swords', pentacles: 'Pentacles'
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
            `<span class="item-name">${numStr} ${cardName(c)}</span>` +
            `<span class="item-suit">${arcanaName(c)}</span></div>`;
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
    const keywords = cardKeywords(card, reversed);
    const sl = cardStatusLabel(reversed);
    const revBadge = reversed ? `<span class="browser-reversed-badge">${sl}</span>` : '';
    const suitLabel = t('card_browser.suit', 'Suit');
    const elemAstroLabel = `${t('card_detail.element', 'Element')} · ${t('card_detail.astrology', 'Astrology')}`;
    const kwLabel = `${t('card_browser.select_placeholder', 'Keywords')} (${sl})`;
    const upMeaningLabel = `${t('card_detail.upright', 'Upright')} ${t('card_browser.select_placeholder', 'Meaning')}`;
    const revMeaningLabel = `${t('card_detail.reversed', 'Reversed')} ${t('card_browser.select_placeholder', 'Meaning')}`;

    detail.innerHTML = imgHtml +
        `<div class="detail-field"><div class="label">${cardName(card)} ${card.name}${revBadge}</div></div>` +
        `<div class="detail-field"><div class="label">${suitLabel}</div><div class="value">${arcanaName(card)}</div></div>` +
        `<div class="detail-field"><div class="label">${elemAstroLabel}</div><div class="value sub">${card.element} · ${card.astrology}</div></div>` +
        `<div class="detail-field"><div class="label">${kwLabel}</div><div class="value sub">${keywords.join(', ')}</div></div>` +
        `<div class="detail-field"><div class="label">${upMeaningLabel}</div><div class="value sub">${cardMeaning(card, false)}</div></div>` +
        `<div class="detail-field"><div class="label">${revMeaningLabel}</div><div class="value sub">${cardMeaning(card, true)}</div></div>`;
}

const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI','XXII'];

function toRoman(num) {
    return ROMAN[num - 1] || String(num);
}
