/**
 * 3D card carousel with click-to-select.
 *
 * Mouse controls:
 *   - Drag to scroll
 *   - Click center-area card to select
 *   - Click off-center card to center it first
 *   - Wheel to scroll
 */

export class CardCarousel {
    constructor(scene, opts = {}) {
        this.scene = scene;
        this.onSelect = opts.onSelect || (() => {});
        this.onReady = opts.onReady || (() => {});

        this.cards = [];
        this.els = [];
        this.idx = 0;
        this.vel = 0;
        this.dragging = false;
        this._dead = false;
        this._intro = true;
        this._introTarget = 0;
        this._centering = false;
        this._centerTarget = 0;
        this._dragX0 = 0;
        this._dragIdx0 = 0;
        this._dragMoved = false;
        this._raf = null;

        this.friction = 0.85;
        this.maxVel = 0.15;

        this._md = this._onDown.bind(this);
        this._mm = this._onMove.bind(this);
        this._mu = this._onUp.bind(this);
        this._wh = this._onWheel.bind(this);
        this._onTouchStart = this._handleTouchStart.bind(this);
        this._onTouchMove = this._handleTouchMove.bind(this);
        this._onTouchEnd = this._handleTouchEnd.bind(this);
    }

    loadCards(cards) {
        this.cards = [...cards];
        this.els = new Array(cards.length).fill(null);
        this.idx = 0;
        this._introTarget = Math.floor(cards.length / 2);
        this.scene.innerHTML = '';

        for (let i = 0; i < cards.length; i++) {
            const el = document.createElement('div');
            el.className = 'cc-card';
            el.dataset.i = i;
            el.innerHTML = `<div class="cc-inner"><div class="cc-back"><span class="cc-sym">✦</span></div></div>`;
            this.scene.appendChild(el);
            this.els[i] = el;
        }

        this.scene.addEventListener('mousedown', this._md);
        this.scene.addEventListener('wheel', this._wh, { passive: true });
        window.addEventListener('mousemove', this._mm);
        window.addEventListener('mouseup', this._mu);

        this.scene.addEventListener('touchstart', this._onTouchStart, { passive: false });
        this.scene.addEventListener('touchmove', this._onTouchMove, { passive: false });
        this.scene.addEventListener('touchend', this._onTouchEnd);
    }

    start() {
        this._intro = true;
        this._loop();
    }

    destroy() {
        this._dead = true;
        cancelAnimationFrame(this._raf);
        this.scene.removeEventListener('mousedown', this._md);
        this.scene.removeEventListener('wheel', this._wh);
        window.removeEventListener('mousemove', this._mm);
        window.removeEventListener('mouseup', this._mu);
        this.scene.removeEventListener('touchstart', this._onTouchStart);
        this.scene.removeEventListener('touchmove', this._onTouchMove);
        this.scene.removeEventListener('touchend', this._onTouchEnd);
        this.scene.innerHTML = '';
    }

    removeCard(i) {
        const el = this.els[i];
        if (!el) return;
        el.classList.add('cc-picked-out');
        setTimeout(() => el.remove(), 500);
        this.els[i] = null;
        this.cards[i] = null;
    }

    /* ---- loop ---- */

    _startLoop() {
        if (this._raf != null) return;
        this._raf = requestAnimationFrame(this._loop);
    }

    _loop = () => {
        if (this._dead) return;
        this._raf = null;

        if (this._intro) {
            const d = this._introTarget - this.idx;
            this.idx += d * 0.05;
            if (Math.abs(d) < 0.1) {
                this.idx = this._introTarget;
                this._intro = false;
                this.onReady();
            }
            this._pos();
            this._startLoop();
        } else {
            if (this._centering) {
                const d = this._centerTarget - this.idx;
                this.idx += d * 0.12;
                if (Math.abs(d) < 0.05) {
                    this.idx = this._centerTarget;
                    this._centering = false;
                }
                this._pos();
                this._startLoop();
            } else if (!this.dragging) {
                this.idx += this.vel;
                this.vel *= this.friction;
                if (Math.abs(this.vel) < 0.0001) this.vel = 0;
                const mx = this._maxIdx();
                if (this.idx < 0) { this.idx = 0; this.vel = -this.vel * 0.5; }
                if (this.idx > mx) { this.idx = mx; this.vel = -this.vel * 0.5; }
                this._pos();
                if (this.vel !== 0) this._startLoop();
            } else {
                this._pos();
                this._startLoop();
            }
        }
    };

    /* ---- positioning ---- */

    _pos() {
        const W = window.innerWidth;
        const cw = this._cw();
        const mob = W <= 768;
        const gap = Math.min(
            Math.max(cw * (mob ? 0.85 : 1.15), W * (mob ? 0.12 : 0.18)),
            cw * (mob ? 1.25 : 2),
        );
        const vis = Math.ceil((W / 2) / (gap * 0.5)) + 3;

        for (let i = 0; i < this.els.length; i++) {
            const el = this.els[i];
            if (!el) continue;
            const d = i - this.idx;

            if (Math.abs(d) > vis) { el.style.display = 'none'; continue; }
            el.style.display = '';

            const x = d * gap;
            const z = -Math.pow(Math.abs(d), 1.3) * 50;
            let ry = d * 5;
            if (ry > 45) ry = 45;
            if (ry < -45) ry = -45;

            let sc = 1;
            const sel = Math.round(this.idx) === i;

            if (Math.abs(d) < 0.5) {
                sc = (mob ? 1.06 : 1.2) - Math.abs(d) * (mob ? 0.22 : 0.4);
                el.style.zIndex = 1000;
            } else {
                sc = 1 - Math.min(Math.abs(d) * 0.08, 0.4);
                el.style.zIndex = 1000 - Math.floor(Math.abs(d) * 10);
            }

            el.style.transform = `translateX(${x}px) translateZ(${z}px) rotateY(${ry}deg) scale(${sc})`;
            el.classList.toggle('cc-active', sel);
        }
    }

    /* ---- mouse ---- */

    _onDown(e) {
        if (this._intro || this._centering) return;
        this.dragging = true;
        this._dragMoved = false;
        this._dragX0 = e.clientX;
        this._dragIdx0 = this.idx;
        this.vel = 0;
        this.scene.style.cursor = 'grabbing';
        this._startLoop();
    }

    _onMove(e) {
        if (!this.dragging) return;
        const dx = e.clientX - this._dragX0;
        if (Math.abs(dx) > 5) this._dragMoved = true;
        this.idx = this._dragIdx0 - dx / this._cw();
    }

    _onUp(e) {
        if (!this.dragging) return;
        this.dragging = false;
        this.scene.style.cursor = '';

        const dx = e.clientX - this._dragX0;

        if (!this._dragMoved && Math.abs(dx) < 5) {
            const ci = this._cardAtPoint(e.clientX, e.clientY);
            if (ci !== null && this.cards[ci] !== null) {
                if (Math.abs(ci - this.idx) < 0.6) {
                    this._fireSelect(ci);
                } else {
                    this._centerTarget = ci;
                    this._centering = true;
                    this._startLoop();
                }
            }
        } else {
            this.vel = Math.max(-this.maxVel, Math.min(this.maxVel, -dx / this._cw() * 0.06));
            this._startLoop();
        }
    }(e) {
        if (this._intro || this._centering) return;
        this.vel = Math.max(-this.maxVel, Math.min(this.maxVel, this.vel + e.deltaY * 0.001));
        this._startLoop();
    }

    /* ---- touch ---- */

    _handleTouchStart(e) {
        if (this._intro || this._centering) return;
        e.preventDefault();
        const t = e.touches[0];
        this.dragging = true;
        this._dragMoved = false;
        this._dragX0 = t.clientX;
        this._dragIdx0 = this.idx;
        this.vel = 0;
        this._startLoop();
    }

    _handleTouchMove(e) {
        if (!this.dragging) return;
        e.preventDefault();
        const t = e.touches[0];
        const dx = t.clientX - this._dragX0;
        if (Math.abs(dx) > 5) this._dragMoved = true;
        this.idx = this._dragIdx0 - dx / this._cw();
    }

    _handleTouchEnd(e) {
        if (!this.dragging) return;
        this.dragging = false;
        const t = e.changedTouches[0];
        const dx = t.clientX - this._dragX0;

        if (!this._dragMoved && Math.abs(dx) < 5) {
            const ci = this._cardAtPoint(t.clientX, t.clientY);
            if (ci !== null && this.cards[ci] !== null) {
                if (Math.abs(ci - this.idx) < 0.6) {
                    this._fireSelect(ci);
                } else {
                    this._centerTarget = ci;
                    this._centering = true;
                }
            }
        } else {
            this.vel = Math.max(-this.maxVel, Math.min(this.maxVel, -dx / this._cw() * 0.06));
        }
    }

    /* ---- helpers ---- */

    _cw() {
        const vw = window.innerWidth;
        if (vw <= 480) return Math.max(80, Math.min(130, vw * 0.22));
        if (vw <= 768) return Math.max(90, Math.min(140, vw * 0.20));
        return Math.max(100, Math.min(160, vw * 0.16));
    }

    _maxIdx() {
        let last = this.cards.length - 1;
        while (last >= 0 && this.cards[last] === null) last--;
        return Math.max(0, last);
    }

    _cardAtPoint(x, y) {
        for (let i = 0; i < this.els.length; i++) {
            const el = this.els[i];
            if (!el) continue;
            const r = el.getBoundingClientRect();
            if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return i;
        }
        return null;
    }

    _fireSelect(i) {
        const el = this.els[i];
        if (el) {
            const r = el.getBoundingClientRect();
            const ring = document.createElement('div');
            ring.className = 'cc-ring';
            ring.style.left = (r.left + r.width / 2) + 'px';
            ring.style.top = (r.top + r.height / 2) + 'px';
            document.body.appendChild(ring);
            setTimeout(() => ring.remove(), 600);
        }
        this.onSelect(i);
    }
}
