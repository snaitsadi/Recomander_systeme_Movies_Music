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
    /**
     * Toggle sidebar visibility.
     */
    toggleSidebar() {
        const isHidden = (this.ui.container.style.display === 'none');
        this.ui.container.style.display = isHidden ? 'block' : 'none';
    }

    /**
     * Change application state and update UI accordingly.
     * 
     * @param {string} newState - New state ('idle', 'loading', 'playing')
     */
    changeState(newState) {
        this.state.status = newState;
        if (newState === 'idle') this.ui.showView('initial');
        if (newState === 'loading') this.ui.showView('loader', { algo: this.state.algoType });
        if (newState === 'playing') this.ui.showView('playing');
    }

    /**
     * Stop the current listening session and send feedback.
     */
    stopSession() {
        console.log("[Controller] Stopping session...");
        
        // Send feedback before stopping if we have listening data
        if (this.state.listeningTime > 0 && this.state.currentTrackId) {
            console.log(`[Controller] Sending feedback: ${this.state.currentTrackId}, listened ${this.state.listeningTime}s`);
            this.api.sendFeedback(
                this.state.userId,
                this.state.currentTrackId,
                this.state.listeningTime
            ).then(result => {
                console.log('[Feedback] Result:', result);
            }).catch(err => {
                console.error('[Feedback] Error:', err);
            });
        }
        
        // Reset state
        this.changeState('idle');
        this.state.listeningTime = 0;
        this.state.monitoredUrl = null;
        this.state.currentTrackSignature = null;
        this.state.currentTrackId = null;
        chrome.storage.local.set({ 
            'listeningTime': 0, 
            'music_reco_state': 'idle',
            'currentTrackId': null 
        });
        this.ui.updateTimer(0);
    }

    /**
     * Trigger a new recommendation request and navigate to the recommended track.
     */
    async triggerRecommendation() {
        console.log("[Controller] Triggering recommendation...");
        
        // Send feedback for previous session if any
        if (this.state.listeningTime > 0 && this.state.currentTrackId) {
            console.log(`[Controller] Ending previous session: ${this.state.currentTrackId}, ${this.state.listeningTime}s`);
            try {
                const feedbackResult = await this.api.sendFeedback(
                    this.state.userId,
                    this.state.currentTrackId,
                    this.state.listeningTime
                );
                console.log('[Feedback] Result:', feedbackResult);
            } catch (err) {
                console.error('[Feedback] Error:', err);
            }
            
            this.state.listeningTime = 0;
            chrome.storage.local.set({ 'listeningTime': 0 });
            this.ui.updateTimer(0);
        }

        // Reset state for new recommendation
        this.changeState('loading');
        this.state.monitoredUrl = null;
        this.state.currentTrackSignature = null;
        this.state.currentTrackId = null;

        try {
            // Get recommendation from API
            const recommendation = await this.api.getRecommendation(
                this.state.userId, 
                this.state.algoType
            );
            
            if (this.state.status !== 'loading') {
                console.log("[Controller] Recommendation ignored - loading cancelled");
                return;
            }

            console.log("[Controller] Recommended:", recommendation.song_title, "via", recommendation.algorithm);
            
            const recommendedTrack = recommendation.song_title;
            // Prefer song_id if available, otherwise use title only as fallback (backend will try to resolve it)
            const recommendedId = recommendation.song_id || recommendation.song_title;
            
            // Store flags for autoplay after navigation
            chrome.storage.local.set({ 
                'music_reco_autoplay': true, 
                'music_reco_state': 'playing',
                'currentTrackId': recommendedId // Now holding the best identifier we have
            }, () => {
                // Navigate to search results using TITLE
                this.adapter.search(recommendedTrack);
                
                // Handle SPA navigation (page doesn't reload)
                this.adapter.waitForUrl('/search')
                    .then(() => {
                        console.log("[Controller] URL changed, triggering autoplay logic for SPA");
                        // Wait for DOM to update before searching for play buttons
                        return new Promise(r => setTimeout(r, 1000));
                    })
                    .then(() => this.handleAutoplay())
                    .catch(err => console.log("[Controller] SPA navigation check timeout/error:", err));
            });
        } catch (error) {
            console.error("[Controller] Failed to get recommendation:", error);
            this.ui.showNotification("Failed to get recommendation. Please try again.");
            this.changeState('idle');
        }
    }

    /**
     * Handle autoplay logic after navigation to search results.
     */
    async handleAutoplay() {
        this.changeState('loading');
        
        const success = await this.adapter.playFirstResult();
        
        if (success) {
            this.changeState('playing');
            chrome.storage.local.set({ 'music_reco_autoplay': false });
            
            // Wait for player update
            setTimeout(() => {
                this.state.currentTrackSignature = this.adapter.getCurrentTrackDetails();
                
                chrome.storage.local.get(['currentTrackId'], (res) => {
                    if (res.currentTrackId) {
                        this.state.currentTrackId = res.currentTrackId;
                    }
                });
            }, 2000);
            
        } else {
            this.ui.showNotification("Content unavailable, skipping...");
            
            setTimeout(() => {
                this.triggerRecommendation();
            }, 1000);
        }
    }

    /**
     * Start monitoring playback state and track changes.
     * Uses event-driven approach with minimal polling for performance.
     */
    startMonitoring() {
        let monitoringInterval = null;
        
        // Setup history API listener for navigation changes
        this.adapter.onUrlChange((newUrl) => {
            console.log("[Controller] URL changed via SPA navigation:", newUrl);
            if (this.state.status === 'playing') {
                // Check if user navigated away from playback context
                if (!newUrl.includes('/you/') && !newUrl.includes('/search')) {
                    console.log("[Controller] Navigated away from playback context");
                }
            }
        });


        
        // Polling: Only tick when playing to update UI timer and detect track changes
        let wasPlayingBefore = false;
        
        const startTickingInterval = () => {
            if (monitoringInterval) return; // Already running
            
            monitoringInterval = setInterval(() => {
                const isCurrentlyPlaying = this.adapter.isPlaying();

                // Handle pause/resume
                if (!isCurrentlyPlaying && wasPlayingBefore) {
                    // Just paused - keep ticking but don't increment time
                    wasPlayingBefore = false;
                    return;
                }
                
                if (isCurrentlyPlaying && !wasPlayingBefore) {
                    // Just resumed - continue ticking
                    wasPlayingBefore = true;
                }

                if (!isCurrentlyPlaying) {
                    // Not playing (paused or stopped)
                    return;
                }

                if (this.state.status === 'playing') {
                    // Check for track changes (user manually changed song)
                    const currentSig = this.adapter.getCurrentTrackDetails();
                    if (this.state.currentTrackSignature && currentSig) {
                        if (currentSig !== this.state.currentTrackSignature) {
                            console.log("[Controller] Track changed manually! Stopping session.");
                            
                            // Send feedback before stopping
                            if (this.state.listeningTime > 0 && this.state.currentTrackId) {
                                this.api.sendFeedback(
                                    this.state.userId,
                                    this.state.currentTrackId,
                                    this.state.listeningTime
                                ).then(result => {
                                    console.log('[Feedback] Manual stop result:', result);
                                }).catch(err => {
                                    console.error('[Feedback] Manual stop error:', err);
                                });
                            }
                            
                            this.ui.showNotification("Track changed! Stopping recommendation session.");
                            this.stopSession();
                            return;
                        }
                    } else if (!this.state.currentTrackSignature && currentSig) {
                        this.state.currentTrackSignature = currentSig;
                    }

                    // Increment listening time
                    this.state.listeningTime++;
                    this.ui.updateTimer(this.state.listeningTime);
                    
                    // Periodically backup to storage (every 5 seconds)
                    if (this.state.listeningTime % 5 === 0) {
                        chrome.storage.local.set({ 'listeningTime': this.state.listeningTime });
                    }

                    // Check for end of track (auto-advance)
                    const progress = this.adapter.getProgress();
                    if (progress && progress.max > 0) {
                        // If less than 2 seconds remaining
                        if (progress.current >= progress.max - 2 && progress.current > 1) {
                            if (!this.state.isChangingTrack) {
                                this.state.isChangingTrack = true;
                                console.log("[Controller] Track finished. Auto-playing next...");
                                this.triggerRecommendation();
                            }
                        } else {
                            this.state.isChangingTrack = false;
                        }
                    }
                }
            }, 1000); // Tick every second
        };

        // Hook into state changes to start/stop monitoring interval
        const originalChangeState = this.changeState.bind(this);
        this.changeState = (newState) => {
            originalChangeState(newState);
            if (newState === 'playing') {
                wasPlayingBefore = true;
                startTickingInterval();
            } else if (monitoringInterval) {
                clearInterval(monitoringInterval);
                monitoringInterval = null;
                wasPlayingBefore = false;
            }
        };
    }
}

// Initialize controller when script loads
new RecoController();
