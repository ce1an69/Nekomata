/** Draw screen — carousel picking, slot flipping, detail, and interpretation. */

import { Deck } from './cards.js';
import { InterpretationController } from './interpret.js';
import { CardCarousel } from './carousel.js';
import { state } from './state.js';
import { showScreen, cardImgUrl, makeBtn, resumeHome } from './utils.js';

// -- Keyboard handler for draw screen --

export function initDrawKeyboard() {
    document.addEventListener('keydown', (e) => {
        const draw = document.getElementById('screen-draw');
        if (!draw || draw.classList.contains('hidden')) return;
        if (document.activeElement?.tagName === 'TEXTAREA' || document.activeElement?.tagName === 'INPUT') return;

        if (state.phase === 'pick' && state.carousel) {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                state.carousel.idx = Math.max(0, state.carousel.idx - 1);
                state.carousel.vel = 0;
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                state.carousel.idx = Math.min(state.cards.length - 1, state.carousel.idx + 1);
                state.carousel.vel = 0;
            } else if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                const ci = Math.round(state.carousel.idx);
                if (ci >= 0 && ci < state.cards.length && state.cards[ci]) {
                    onCarouselSelect(ci);
                }
            }
        } else if (state.phase === 'flip') {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                const slot = document.querySelector('.spread-slot.face-down');
                if (slot) flipSlot(slot, parseInt(slot.dataset.index));
            }
        } else if (state.phase === 'done') {
            const slots = document.querySelectorAll('.spread-slot');
            if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && slots.length) {
                e.preventDefault();
                let idx = state.selectedSlotIdx;
                idx = e.key === 'ArrowLeft'
                    ? (idx - 1 + slots.length) % slots.length
                    : (idx + 1) % slots.length;
                selectSlot(idx);
            } else if (e.key === 'Enter' && !state.showInterp) {
                e.preventDefault();
                startInterpretation();
            }
        }
    });
}

// -- Draw screen lifecycle --

export function showDrawScreen() {
    const spDef = state.spreads.find(s => s.key === state.spreadKey);
    if (!spDef) return;

    state.deck = new Deck(state.cards);
    state.deck.shuffle();
    state.spread = { key: spDef.key, positions: spDef.positions, drawnCards: [] };
    state.phase = 'pick';
    state.pickIndex = 0;
    state.flipIndex = 0;
    state.selectedSlotIdx = -1;
    state.showDetail = true;
    state.showInterp = false;

    showScreen('draw');

    document.getElementById('draw-spread-name').textContent = spDef.name;
    document.getElementById('draw-question').textContent = state.question || '';
    document.getElementById('screen-draw').classList.remove('interpreting');
    syncDrawLayoutState();
    document.getElementById('detail-panel').classList.add('hidden');
    document.getElementById('interp-panel').classList.add('hidden');
    document.getElementById('interp-text').innerHTML = '';

    renderCarousel();
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

// -- Carousel --

function renderCarousel() {
    const section = document.getElementById('carousel-section');
    section.classList.remove('exiting');
    section.style.display = '';

    if (state.carousel) state.carousel.destroy();

    const scene = document.getElementById('carousel-scene');
    state.carousel = new CardCarousel(scene, {
        onSelect: onCarouselSelect,
        onReady: () => { updateDrawActions(); },
    });
    state.carousel.loadCards(state.deck.remaining);
    state.carousel.start();
}

function onCarouselSelect(carouselIdx) {
    if (state.phase !== 'pick') return;

    const card = state.deck.remaining[carouselIdx];
    if (!card) return;

    const isReversed = Math.random() < state.reversalProb;
    const posIdx = state.pickIndex;
    const position = state.spread.positions[posIdx];

    // Flying animation from carousel to slot
    const carouselEl = state.carousel.els[carouselIdx];
    const slot = document.querySelectorAll('.spread-slot')[posIdx];

    if (carouselEl && slot) {
        const fromRect = carouselEl.getBoundingClientRect();
        const toRect = slot.getBoundingClientRect();

        const flyEl = document.createElement('div');
        flyEl.className = 'cc-fly';
        flyEl.innerHTML = '<span class="cc-sym">✦</span>';
        flyEl.style.left = fromRect.left + 'px';
        flyEl.style.top = fromRect.top + 'px';
        flyEl.style.width = fromRect.width + 'px';
        flyEl.style.height = fromRect.height + 'px';
        document.body.appendChild(flyEl);

        requestAnimationFrame(() => {
            flyEl.style.left = toRect.left + 'px';
            flyEl.style.top = toRect.top + 'px';
            flyEl.style.width = toRect.width + 'px';
            flyEl.style.height = toRect.height + 'px';
            flyEl.style.opacity = '0.7';
        });

        setTimeout(() => flyEl.remove(), 500);
    }

    state.carousel.removeCard(carouselIdx);
    state.spread.drawnCards.push({ card, position, isReversed });

    if (slot) {
        slot.classList.remove('empty', 'waiting');
        slot.classList.add('face-down');
        slot.innerHTML = buildSlotFaceDown(state.spread.drawnCards[posIdx]);
        slot.style.opacity = '0';
        slot.style.transform = 'scale(0.8)';
        setTimeout(() => {
            slot.style.transition = 'opacity 0.3s, transform 0.3s';
            slot.style.opacity = '1';
            slot.style.transform = 'scale(1)';
        }, 300);
    }

    state.pickIndex++;
    if (state.pickIndex >= state.spread.positions.length) {
        setTimeout(() => transitionToFlip(), 600);
    } else {
        markWaitingSlot(state.pickIndex);
    }
    updateDrawActions();
}

// -- Spread slots --

function renderSpreadSlots() {
    const area = document.getElementById('spread-area');
    area.innerHTML = '';

    state.spread.positions.forEach((pos, idx) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'slot-wrapper';

        const slot = document.createElement('div');
        slot.className = 'spread-slot empty';
        slot.dataset.index = idx;
        slot.addEventListener('click', () => onSpreadSlotClicked(slot, idx));

        const label = document.createElement('span');
        label.className = 'slot-label';
        label.textContent = pos.name;

        wrapper.appendChild(slot);
        wrapper.appendChild(label);
        area.appendChild(wrapper);
    });

    if (state.spread.positions.length > 0) markWaitingSlot(0);
}

function markWaitingSlot(idx) {
    const slots = document.querySelectorAll('.spread-slot');
    slots.forEach(s => s.classList.remove('waiting'));
    if (idx < slots.length) slots[idx].classList.add('waiting');
}

function buildSlotFaceDown(drawnCard) {
    return `<div class="slot-inner">` +
        `<div class="slot-face slot-back"><span class="slot-back-pattern">✦</span></div>` +
        `<div class="slot-face slot-front">` +
        buildCardFaceInner(drawnCard) +
        `</div></div>`;
}

function buildCardFaceInner(drawnCard) {
    const c = drawnCard.card;
    if (!c.has_image) return '';
    const cls = drawnCard.isReversed ? 'reversed' : '';
    return `<img src="/assets/cards/${c.arcana}/${c.id}_detail.png" alt="${c.name}" class="${cls}">`;
}

function transitionToFlip() {
    state.phase = 'flip';
    const section = document.getElementById('carousel-section');
    section.classList.add('exiting');
    if (state.carousel) {
        state.carousel.destroy();
        state.carousel = null;
    }
    updateDrawActions();
}

function onSpreadSlotClicked(slotEl, idx) {
    if (state.phase === 'flip') {
        if (slotEl.classList.contains('face-down')) flipSlot(slotEl, idx);
    } else if (state.phase === 'done') {
        selectSlot(idx);
    }
}

function flipSlot(slotEl, idx) {
    slotEl.classList.add('flipped', 'flipping');
    slotEl.classList.remove('face-down');

    setTimeout(() => {
        slotEl.classList.remove('flipping');
        slotEl.classList.add('revealed');
        slotEl.classList.add('glow');
        setTimeout(() => slotEl.classList.remove('glow'), 400);
    }, 400);

    state.flipIndex++;
    if (state.flipIndex >= state.spread.positions.length) {
        setTimeout(() => completionShimmer(), 700);
    }
    updateDrawActions();
}

function completionShimmer() {
    state.phase = 'done';
    const slots = document.querySelectorAll('.spread-slot');

    slots.forEach((s, i) => {
        setTimeout(() => {
            s.classList.add('glow');
            setTimeout(() => s.classList.remove('glow'), 500);
        }, i * 150);
    });

    for (let i = 0; i < 15; i++) {
        setTimeout(() => spawnInterpParticle(), i * 80);
    }

    setTimeout(() => {
        showDetailPanel();
        selectSlot(0);
    }, slots.length * 150 + 300);

    updateDrawActions();
}

function spawnInterpParticle() {
    const p = document.createElement('div');
    p.className = 'cc-particle';
    p.style.left = (Math.random() * window.innerWidth) + 'px';
    p.style.top = (Math.random() * window.innerHeight) + 'px';
    const sz = 3 + Math.random() * 8;
    p.style.width = sz + 'px';
    p.style.height = sz + 'px';
    const gold = getComputedStyle(document.documentElement).getPropertyValue('--gold').trim();
    p.style.background = gold;
    p.style.boxShadow = `0 0 10px ${gold}`;
    p.style.zIndex = '9999';
    p.animate([
        { transform: 'translateY(0) scale(1)', opacity: 0.8 },
        { transform: `translateY(-100px) scale(0)`, opacity: 0 },
    ], { duration: 1000 + Math.random() * 1000, easing: 'ease-out' });
    document.body.appendChild(p);
    setTimeout(() => p.remove(), 2000);
}

// -- Detail panel --

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
    if (state.showDetail) panel.classList.remove('hidden');
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

// -- Action buttons --

function updateDrawActions() {
    const hintEl = document.getElementById('draw-hint-text');
    const btnsEl = document.getElementById('draw-buttons');
    btnsEl.innerHTML = '';

    if (state.phase === 'pick') {
        hintEl.textContent = `点击选牌 (${state.pickIndex}/${state.spread.positions.length}) · 拖拽浏览`;
        btnsEl.appendChild(makeBtn('← 返回', '', () => {
            if (state.carousel) state.carousel.destroy();
            showScreen('home');
            resumeHome();
        }));
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

// -- Interpretation --

async function startInterpretation() {
    state.showInterp = true;
    document.getElementById('screen-draw').classList.add('interpreting');
    syncDrawLayoutState();
    document.getElementById('interp-panel').classList.remove('hidden');
    updateDrawActions();
    await state.interpCtrl.start(state.spread.drawnCards, state.question, state.strings, state.spreadKey);
}
