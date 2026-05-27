/** Shared application state. */

export const state = {
    question: '',
    spreadKey: '',
    config: { api_url: '', api_key: '', model: '', lang: 'en' },
    cards: [],
    spreads: [],
    strings: {},
    spread: null,
    phase: 'pick',
    deck: null,
    carousel: null,
    pickIndex: 0,
    flipIndex: 0,
    selectedSlotIdx: -1,
    showDetail: true,
    showInterp: false,
    spreadHidden: false,
    interpCtrl: null,
    reversalProb: 0.5,
    browserReversed: false,
};
