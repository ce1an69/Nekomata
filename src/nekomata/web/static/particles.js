/** Starfield canvas background — animated twinkling stars. */

export class Starfield {
    constructor(canvas, opts = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.count = opts.count || 200;
        this.stars = [];
        this._raf = null;
        this._onResize = () => this._resize();
    }

    start() {
        this._resize();
        window.addEventListener('resize', this._onResize);
        this._loop();
    }

    stop() {
        cancelAnimationFrame(this._raf);
        window.removeEventListener('resize', this._onResize);
    }

    _resize() {
        const { canvas } = this;
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        if (this.stars.length === 0) {
            for (let i = 0; i < this.count; i++) {
                this.stars.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    r: Math.random() * 1.8 + 0.2,
                    a: Math.random(),
                    speed: Math.random() * 0.4 + 0.1,
                });
            }
        }
    }

    _loop = () => {
        const { ctx, canvas } = this;
        const w = canvas.width;
        const h = canvas.height;

        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = 'white';

        for (const s of this.stars) {
            ctx.globalAlpha = s.a;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fill();

            s.y -= s.speed;
            if (s.y < -2) {
                s.y = h + 2;
                s.x = Math.random() * w;
            }
            if (Math.random() > 0.95) s.a = Math.random();
        }

        ctx.globalAlpha = 1;
        this._raf = requestAnimationFrame(this._loop);
    };
}
