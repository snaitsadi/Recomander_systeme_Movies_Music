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

    getShadowHTML() {
        return `
            <div id="reco-panel">
                <div id="reco-header">
                    <div class="reco-header-title">
                        <svg class="header-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 18V5l12-2v13M9 18c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3zm12-3c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3z"/>
                        </svg>
                    </div>
                    <div class="reco-header-actions">
                        <button class="reco-icon-btn" id="settings-btn" title="Settings">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12.22 2h-.44a2 2 0 00-2 2v.18a2 2 0 01-1 1.73l-.43.25a2 2 0 01-2 0l-.15-.08a2 2 0 00-2.73.73l-.22.38a2 2 0 00.73 2.73l.15.1a2 2 0 011 1.72v.51a2 2 0 01-1 1.74l-.15.09a2 2 0 00-.73 2.73l.22.38a2 2 0 002.73.73l.15-.08a2 2 0 012 0l.43.25a2 2 0 011 1.73V20a2 2 0 002 2h.44a2 2 0 002-2v-.18a2 2 0 011-1.73l.43-.25a2 2 0 012 0l.15.08a2 2 0 002.73-.73l.22-.39a2 2 0 00-.73-2.73l-.15-.08a2 2 0 01-1-1.74v-.5a2 2 0 011-1.74l.15-.09a2 2 0 00.73-2.73l-.22-.38a2 2 0 00-2.73-.73l-.15.08a2 2 0 01-2 0l-.43-.25a2 2 0 01-1-1.73V4a2 2 0 00-2-2z"/>
                                <circle cx="12" cy="12" r="3"/>
                            </svg>
                        </button>
                        <button class="reco-icon-btn" id="close-btn" title="Close">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 6L6 18M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <div id="reco-settings-panel">
                    <label class="setting-label">Algorithm</label>
                    <div class="algo-buttons">
                        <button class="algo-btn active" data-algo="matriciel">Collaborative</button>
                        <button class="algo-btn" data-algo="content">Content</button>
                        <button class="algo-btn" data-algo="mix">Hybrid</button>
                    </div>
                    <div class="user-id-info"><span id="user-id-display">...</span></div>
                </div>

                <div id="reco-content">
                    <div id="initial-view" class="view-section active">
                        <div class="icon-wrapper">
                            <svg class="main-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 18v-6a9 9 0 0118 0v6"/>
                                <path d="M21 19a2 2 0 01-2 2h-1a2 2 0 01-2-2v-3a2 2 0 012-2h3zM3 19a2 2 0 002 2h1a2 2 0 002-2v-3a2 2 0 00-2-2H3z"/>
                            </svg>
                        </div>
                        <h3 class="view-title">Music Recommender</h3>
                        <p class="view-description">Discover new tracks based on your listening preferences using AI-powered recommendations.</p>
                        <button class="primary-btn" id="start-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M8 5v14l11-7z"/>
                            </svg>
                            Start Listening
                        </button>
                    </div>

                    <div id="playing-view" class="view-section">
                        <div class="status-indicator">
                            <svg class="listening-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                                <path class="wave-bar" d="M12 4v16"/>
                                <path class="wave-bar" d="M8 7v10"/>
                                <path class="wave-bar" d="M16 7v10"/>
                                <path class="wave-bar" d="M4 10v4"/>
                                <path class="wave-bar" d="M20 10v4"/>
                            </svg>
                        </div>
                        <div id="reco-timer" style="display: none;">00:00</div>
                        <p class="listening-text">Listening & analyzing...</p>
                        <div class="action-buttons">
                            <button class="icon-btn" id="next-btn" title="Next track">
                                <svg viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M4 4l12 8-12 8V4zm13 0v16h3V4h-3z"/>
                                </svg>
                            </button>
                            <button class="icon-btn stop-btn" id="stop-btn" title="Stop">
                                <svg viewBox="0 0 24 24" fill="currentColor">
                                    <rect x="6" y="6" width="12" height="12" rx="2"/>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div id="temp-loader" class="view-section">
                        <div class="loader-spinner">
                            <svg viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <span class="loader-text" id="loader-algo-text">Analyzing...</span>
                        <button id="cancel-loading-btn" style="margin-top: 15px; background: var(--bg-elevated); border: 1px solid var(--border); color: var(--text-secondary); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; transition: all 0.2s ease;">
                            Stop Loading
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getShadowStyles() {
        return `
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            :host {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                font-size: 13px;
                --z-index: 2147483647;
                --primary: #FF5500;
                --primary-dark: #E04D00;
                --primary-light: #FF6B1A;
                --bg-main: #0A0A0A;
                --bg-secondary: #1A1A1A;
                --bg-elevated: #242424;
                --text-primary: #FFFFFF;
                --text-secondary: #AAAAAA;
                --text-muted: #666666;
                --border: #2A2A2A;
                --accent: #00D9FF;
            }
            #reco-panel {
                position: fixed;
                top: 80px;
                right: 20px;
                width: 280px;
                background: linear-gradient(145deg, rgba(20, 20, 20, 0.98) 0%, rgba(10, 10, 10, 0.98) 100%);
                border: 2px solid var(--primary);
                box-shadow: 0 0 30px rgba(255, 85, 0, 0.5), 0 10px 50px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 85, 0, 0.2);
                border-radius: 16px;
                color: var(--text-primary);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                z-index: var(--z-index);
                backdrop-filter: blur(20px);
            }

            #reco-header {
                padding: 12px 16px;
                background: linear-gradient(135deg, rgba(255, 85, 0, 0.15) 0%, rgba(255, 85, 0, 0.05) 100%);
                border-bottom: 2px solid rgba(255, 85, 0, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: grab;
                user-select: none;
                box-shadow: 0 2px 10px rgba(255, 85, 0, 0.2);
            }

            #reco-header:active {
                cursor: grabbing;
            }

            .reco-header-title {
                display: flex;
                align-items: center;
            }

            .header-icon {
                width: 24px;
                height: 24px;
                color: var(--primary);
                filter: drop-shadow(0 0 12px rgba(255, 85, 0, 0.8));
                animation: iconGlow 3s ease-in-out infinite;
            }

            @keyframes iconGlow {
                0%, 100% { filter: drop-shadow(0 0 12px rgba(255, 85, 0, 0.8)); }
                50% { filter: drop-shadow(0 0 20px rgba(255, 85, 0, 1)); }
            }

            .reco-header-actions {
                display: flex;
                gap: 6px;
                align-items: center;
            }

            .reco-icon-btn {
                background: transparent;
                border: none;
                color: var(--text-muted);
                cursor: pointer;
                padding: 4px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                width: 28px;
                height: 28px;
            }

            .reco-icon-btn svg {
                width: 16px;
                height: 16px;
            }    
            .reco-icon-btn:hover {
                background: var(--bg-elevated);
                color: var(--text-primary);
                transform: scale(1.05);
            }

            .reco-icon-btn:active {
                transform: scale(0.95);
            }

            #reco-settings-panel {
                display: none;
                background: var(--bg-secondary);
                padding: 12px;
                border-bottom: 1px solid var(--border);
                animation: slideDown 0.2s ease;
            }

            #reco-settings-panel.visible {
                display: block;
            }

            @keyframes slideDown {
                from {
                    opacity: 0;
                    max-height: 0;
                }
                to {
                    opacity: 1;
                    max-height: 200px;
                }
            }

            .setting-label {
                color: var(--text-secondary);
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                display: block;
                margin-bottom: 6px;
            }

            .algo-buttons {
                display: flex;
                gap: 6px;
                width: 100%;
            }

            .algo-btn {
                flex: 1;
                padding: 8px 10px;
                background: var(--bg-elevated);
                color: var(--text-secondary);
                border: 1px solid var(--border);
                border-radius: 6px;
                outline: none;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-weight: 500;
            }

            .algo-btn:hover {
                border-color: var(--primary);
                color: var(--text-primary);
                background: var(--bg-secondary);
            }

            .algo-btn.active {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                border-color: var(--primary);
                color: var(--text-primary);
                box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
            }

            .user-id-info {
                color: var(--text-muted);
                font-size: 9px;
                margin-top: 8px;
                text-align: center;
                font-family: monospace;
            }

            #reco-content {
                padding: 24px 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 220px;
                background: transparent;
            }

            .view-section {
                width: 100%;
                text-align: center;
                display: none;
            }

            .view-section.active {
                display: flex;
                flex-direction: column;
                align-items: center;
                animation: fadeIn 0.3s ease;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Initial View */
            .icon-wrapper {
                margin-bottom: 16px;
            }

            .main-icon {
                width: 56px;
                height: 56px;
                color: var(--primary);
                filter: drop-shadow(0 4px 16px rgba(255, 85, 0, 0.6));
            }

            .view-title {
                font-size: 18px;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }

            .view-description {
                font-size: 12px;
                line-height: 1.5;
                color: var(--text-secondary);
                margin-bottom: 20px;
                padding: 0 8px;
                text-align: center;
            }

            .primary-btn {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                color: var(--text-primary);
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 600;
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                transition: all 0.2s ease;
                box-shadow: 0 4px 12px rgba(255, 85, 0, 0.3);
            }

            .primary-btn svg {
                width: 16px;
                height: 16px;
            }

            .primary-btn:hover {
                background: linear-gradient(135deg, var(--primary-light) 0%, var(--primary) 100%);
                box-shadow: 0 6px 20px rgba(255, 85, 0, 0.4);
                transform: translateY(-1px);
            }

            .primary-btn:active {
                transform: translateY(0);
                box-shadow: 0 2px 8px rgba(255, 85, 0, 0.3);
            }

            /* Playing View */
            .status-indicator {
                margin-bottom: 20px;
            }

            .listening-icon {
                width: 64px;
                height: 64px;
                color: var(--primary);
            }

            .listening-icon .wave-bar {
                animation: waveform 1.2s ease-in-out infinite;
            }

            .listening-icon .wave-bar:nth-child(1) { animation-delay: 0s; }
            .listening-icon .wave-bar:nth-child(2) { animation-delay: 0.1s; }
            .listening-icon .wave-bar:nth-child(3) { animation-delay: 0.2s; }
            .listening-icon .wave-bar:nth-child(4) { animation-delay: 0.3s; }
            .listening-icon .wave-bar:nth-child(5) { animation-delay: 0.4s; }

            @keyframes waveform {
                0%, 100% {
                    opacity: 0.3;
                    transform: scaleY(0.5);
                }
                50% {
                    opacity: 1;
                    transform: scaleY(1);
                }
            }


