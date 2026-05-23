/** Shared UI helpers. */

export function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    const el = document.getElementById(`screen-${id}`);
    if (el) {
        el.classList.remove('hidden');
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = '';
    }
}

export function showToast(title, body, duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<div class="toast-title">${title}</div>` +
        (body ? `<div class="toast-body">${body}</div>` : '');
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('exiting');
        toast.addEventListener('animationend', () => toast.remove());
    }, duration);
}

export function showModal(title, bodyHtml) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `<div class="modal-box">` +
        `<h3>${title}</h3>` +
        bodyHtml +
        `<div class="modal-actions"><button class="btn btn-primary modal-close">OK</button></div></div>`;
    const close = () => {
        overlay.classList.add('closing');
        overlay.addEventListener('animationend', () => overlay.remove());
    };
    overlay.querySelector('.modal-close').addEventListener('click', close);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) close(); });
    document.body.appendChild(overlay);
}

export function cardImgUrl(card, reversed = false) {
    const style = reversed ? ' style="transform: rotate(180deg)"' : '';
    return `<div class="detail-card-img"><img src="/assets/cards/${card.arcana}/${card.id}_detail.png" alt="${card.name}"${style}></div>`;
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
    input.focus();
}
