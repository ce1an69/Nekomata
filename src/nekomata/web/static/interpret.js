/** AI interpretation — SSE consumption & incremental rendering. */

export class InterpretationController {
    constructor(container, loadingEl, spinnerEl, loadMsgEl) {
        this._container = container;
        this._loadingEl = loadingEl;
        this._spinnerEl = spinnerEl;
        this._loadMsgEl = loadMsgEl;
        this._abortController = null;
        this._loadFrame = 0;
        this._loadTimer = null;
    }

    async start(drawnCards, question, strings, spreadKey = '') {
        this._container.innerHTML = '';
        this._showLoading(true, strings);
        this._abortController = new AbortController();

        try {
            const resp = await fetch('/api/interpret', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    spread_key: spreadKey,
                    cards: drawnCards.map(dc => ({
                        card_id: dc.card.id,
                        position_name: dc.position.name,
                        position_name_zh: dc.position.name_zh || '',
                        position_description: dc.position.description || '',
                        is_reversed: dc.isReversed,
                    })),
                }),
                signal: this._abortController.signal,
            });
            if (!resp.ok) throw new Error(`解读请求失败 (${resp.status})`);
            if (!resp.body) throw new Error('解读请求没有返回内容');

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let currentKind = null;
            let currentEl = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || trimmed === 'data: [DONE]') continue;
                    if (!trimmed.startsWith('data: ')) continue;

                    try {
                        const chunk = JSON.parse(trimmed.slice(6));
                        if (chunk.error) {
                            this._appendError(chunk.error);
                            this._showLoading(false);
                            return;
                        }
                        if (chunk.kind === 'thinking') continue;
                        if (chunk.kind !== currentKind) {
                            currentKind = chunk.kind;
                            currentEl = document.createElement('div');
                            currentEl.className = 'content';
                            this._container.appendChild(currentEl);
                        }
                        currentEl.innerHTML = renderMarkdown(currentEl._raw + chunk.text);
                        currentEl._raw = (currentEl._raw || '') + chunk.text;
                    } catch { /* skip malformed */ }
                }
            }

            this._showLoading(false);
            const doneEl = document.createElement('div');
            doneEl.className = 'interp-done';
            doneEl.textContent = '─── ✦ ───';
            this._container.appendChild(doneEl);

        } catch (e) {
            if (e.name !== 'AbortError') this._appendError(e.message);
            this._showLoading(false);
        }
    }

    abort() {
        if (this._abortController) this._abortController.abort();
        this._showLoading(false);
    }

    _showLoading(show, strings) {
        if (show) {
            this._loadingEl.classList.remove('hidden');
            this._loadFrame = 0;
            const s = strings || {};
            const frames = s.loading_frames || [];
            const msgs = s.loading_messages || [];
            const interval = s.loading_interval_ms || 80;
            const msgInterval = s.loading_message_interval_s || 2.0;
            this._loadTimer = setInterval(() => {
                if (frames.length) this._spinnerEl.textContent = frames[this._loadFrame % frames.length];
                if (msgs.length) {
                    const msgIdx = Math.floor(this._loadFrame * interval / (msgInterval * 1000)) % msgs.length;
                    this._loadMsgEl.textContent = msgs[msgIdx];
                }
                this._loadFrame++;
            }, interval);
        } else {
            if (this._loadTimer) clearInterval(this._loadTimer);
            this._loadingEl.classList.add('hidden');
        }
    }

    _appendError(msg) {
        const el = document.createElement('div');
        el.className = 'error-text';
        el.textContent = msg;
        this._container.appendChild(el);
    }
}

/** Markdown → HTML with block-level parsing. */
function renderMarkdown(text) {
    const html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    const lines = html.split('\n');
    const blocks = [];
    let current = [];

    for (const line of lines) {
        if (line.trim() === '') {
            if (current.length) { blocks.push(current); current = []; }
        } else {
            current.push(line);
        }
    }
    if (current.length) blocks.push(current);

    return blocks.map(renderBlock).join('');
}

function renderBlock(lines) {
    const first = lines[0].trim();

    if (lines.length === 1 && /^[-*_]{3,}$/.test(first)) return '<hr>';

    const h = first.match(/^(#{1,3})\s+(.+)$/);
    if (h && lines.length === 1) return `<h${h[1].length}>${fmt(h[2])}</h${h[1].length}>`;

    if (lines.every(l => /^\s*[-*]\s/.test(l)))
        return '<ul>' + lines.map(l => `<li>${fmt(l.replace(/^\s*[-*]\s+/, ''))}</li>`).join('') + '</ul>';

    if (lines.every(l => /^\s*\d+\.\s/.test(l)))
        return '<ol>' + lines.map(l => `<li>${fmt(l.replace(/^\s*\d+\.\s+/, ''))}</li>`).join('') + '</ol>';

    if (lines.every(l => /^&gt;\s?/.test(l)))
        return '<blockquote><p>' + lines.map(l => fmt(l.replace(/^&gt;\s?/, ''))).join('<br>') + '</p></blockquote>';

    return '<p>' + lines.map(l => fmt(l)).join('<br>') + '</p>';
}

function fmt(text) {
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>');
}
