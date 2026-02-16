/**
 * Music Recommendation Controller
 * 
 * Main controller that coordinates the recommendation system.
 * Manages state, UI updates, and communication between components.
 * 
 * @class RecoController
 */
class RecoController {
    constructor() {
        this.ui = new window.MusicRecoUI();
        this.adapter = new window.SoundCloudAdapter();
        this.api = new window.MusicRecoAPI();
        
        this.state = {
            userId: null,
            algoType: 'matriciel',
            listeningTime: 0,
            status: 'idle',
            isChangingTrack: false,
            monitoredUrl: null,
            currentTrackSignature: null,
            currentTrackId: null
        };

        this.init();
    }

    /**
     * Initialize the controller and set up all components.
     */
    init() {
        this.ui.init();
        this.bindEvents();
        this.loadStorage();
        this.startMonitoring();
    }



    /**
     * Bind UI event handlers and Chrome runtime message listeners.
     */
    bindEvents() {
        // UI event handlers
        this.ui.setEventHandler('onStart', () => this.triggerRecommendation());
        this.ui.setEventHandler('onNext', () => this.triggerRecommendation());
        this.ui.setEventHandler('onStop', () => this.stopSession());
        
        this.ui.setEventHandler('onCancelLoading', () => {
             console.log("[Controller] Loading cancelled by user");
             this.state.status = 'idle';
             this.ui.showView('initial');
             this.ui.showNotification("Loading cancelled");
        });

        this.ui.setEventHandler('onClose', () => {
             // Hide sidebar for current session (doesn't persist)
             this.ui.toggleVisibility(false);
        });

        this.ui.setEventHandler('onAlgoChange', (newAlgo) => {
            this.state.algoType = newAlgo;
            chrome.storage.local.set({ 'algoType': newAlgo });
            console.log("[Controller] Algorithm changed to:", newAlgo);
        });

        this.ui.setEventHandler('onPositionChange', (pos) => {
            chrome.storage.local.set({ 'sidebarPos': pos });
        });

        // Chrome extension message listener (from background script or popup)
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.action === 'toggleSidebar') {
                this.toggleSidebar();
            }
        });
    }

    /**
     * Load persisted data from Chrome storage and initialize state.
     */
    loadStorage() {
        chrome.storage.local.get([
            'userId', 'algoType', 'sidebarPos', 
            'listeningTime', 'music_reco_autoplay', 'music_reco_state'
        ], (res) => {
            // User ID: Generate if doesn't exist
            if (res.userId) {
                this.state.userId = res.userId;
            } else {
                this.state.userId = 'user_' + Math.random().toString(36).substr(2, 9);
                chrome.storage.local.set({ 'userId': this.state.userId });
            }
            this.ui.setUserId(this.state.userId);

            // Algorithm selection
            if (res.algoType) {
                this.state.algoType = res.algoType;
                this.ui.setAlgo(res.algoType);
            }

            // Sidebar position
            this.ui.restorePosition(res.sidebarPos);

            // Always show sidebar by default on page load
            this.ui.toggleVisibility(true);

            // Autoplay logic: Handle pending recommendation playback
            if (res.music_reco_autoplay) {
                this.handleAutoplay();
            } else {
                 this.changeState('idle');
            }
        });
    }