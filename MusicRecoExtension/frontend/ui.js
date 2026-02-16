class MusicRecoUI {
    constructor() {
        this.container = null;
        this.shadowRoot = null;
        this.panel = null;
        this.views = {};
        this.elements = {};
        this.handlers = {};
    }

    init() {
        this.createSidebar();
        this.attachDragAndDrop();
    }

    createSidebar() {
        // Create host container
        const host = document.createElement('div');
        host.id = 'music-reco-host';
        document.body.appendChild(host);

        // Attach Shadow DOM
        this.shadowRoot = host.attachShadow({ mode: 'open' });

        // Create styles for Shadow DOM
        const style = document.createElement('style');
        style.textContent = this.getShadowStyles();
        this.shadowRoot.appendChild(style);

        // Create HTML structure inside Shadow DOM
        const wrapper = document.createElement('div');
        wrapper.innerHTML = this.getShadowHTML();
        this.shadowRoot.appendChild(wrapper);

        // Store references to key elements
        this.container = host;
        this.panel = this.shadowRoot.querySelector('#reco-panel');
        this.views.initial = this.shadowRoot.querySelector('#initial-view');
        this.views.playing = this.shadowRoot.querySelector('#playing-view');
        this.views.loader = this.shadowRoot.querySelector('#temp-loader');

        this.elements.header = this.shadowRoot.querySelector('#reco-header');
        this.elements.settingsPanel = this.shadowRoot.querySelector('#reco-settings-panel');
        this.elements.algoButtons = this.shadowRoot.querySelectorAll('.algo-btn');
        this.elements.userIdDisplay = this.shadowRoot.querySelector('#user-id-display');
        this.elements.timer = this.shadowRoot.querySelector('#reco-timer');
        this.elements.loaderText = this.shadowRoot.querySelector('#loader-algo-text');

        // Attach event listeners
        this.attachEventListeners();
    }
