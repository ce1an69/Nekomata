/** Deck & drawing logic — client-side state management only. */

export class Deck {
    constructor(cards) {
        this._originals = cards;
        this.remaining = [];
        this.reset();
    }

    reset() {
        this.remaining = [...this._originals];
    }

    shuffle() {
        const a = this.remaining;
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
    }
}
