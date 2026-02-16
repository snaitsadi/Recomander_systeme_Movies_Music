/**
 * SoundCloud Platform Adapter
 * 
 * Provides integration with SoundCloud's web interface.
 * Handles navigation, playback control, and DOM element detection.
 * 
 * @class SoundCloudAdapter
 */
class SoundCloudAdapter {
    constructor() {
        this.observers = [];
        this.historyListeners = [];
        this.setupHistoryTracking();
    }

    /**
     * Setup history API tracking to detect SPA (Single Page App) navigation.
     * SoundCloud uses client-side routing, so we need to intercept history changes.
     */
    setupHistoryTracking() {
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;

        const notifyListeners = (newUrl) => {
            this.historyListeners.forEach(callback => callback(newUrl));
        };

        history.pushState = function(...args) {
            const result = originalPushState.apply(history, args);
            notifyListeners(window.location.href);
            return result;
        };

        history.replaceState = function(...args) {
            const result = originalReplaceState.apply(history, args);
            notifyListeners(window.location.href);
            return result;
        };
    }


    /**
     * Register a callback for URL changes (SPA navigation events).
     * 
     * @param {Function} callback - Function to call when URL changes
     */
    onUrlChange(callback) {
        this.historyListeners.push(callback);
    }

    /**
     * Navigate to a search query using SoundCloud's internal routing.
     * 
     * @param {string} query - Search query string
     */
    search(query) {
        const url = `/search/sounds?q=${encodeURIComponent(query)}`;
        
        // SoundCloud is an SPA. Create a link and click it to trigger internal router
        const link = document.createElement('a');
        link.href = url;
        link.style.display = 'none';
        document.body.appendChild(link);
        
        link.click();
        
        // Cleanup after a short delay
        setTimeout(() => link.remove(), 100);
    }

    /**
     * Wait for a specific element to appear in the DOM using MutationObserver.
     * More efficient than polling with setInterval.
     * 
     * @param {string} selector - CSS selector for the element
     * @param {number} timeout - Maximum time to wait in milliseconds
     * @returns {Promise<Element>} Resolves with the element when found
     */
    waitForElement(selector, timeout = 10000) {
        return new Promise((resolve, reject) => {
            const el = document.querySelector(selector);
            if (el) return resolve(el);

            const observer = new MutationObserver((mutations) => {
                const element = document.querySelector(selector);
                if (element) {
                    observer.disconnect();
                    this.observers = this.observers.filter(o => o !== observer);
                    resolve(element);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            this.observers.push(observer);

            setTimeout(() => {
                observer.disconnect();
                this.observers = this.observers.filter(o => o !== observer);
                reject(new Error(`Timeout waiting for ${selector}`));
            }, timeout);
        });
    }

    /**
     * Wait for the URL to contain a specific string.
     * Useful for detecting page navigation completion.
     * 
     * @param {string} part - String to search for in URL
     * @param {number} timeout - Maximum time to wait in milliseconds
     * @returns {Promise<void>} Resolves when URL matches
     */
    waitForUrl(part, timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (window.location.href.includes(part)) return resolve();

            const checkUrl = (newUrl) => {
                if (newUrl.includes(part)) {
                    this.historyListeners = this.historyListeners.filter(cb => cb !== checkUrl);
                    resolve();
                }
            };

            this.onUrlChange(checkUrl);

            setTimeout(() => {
                this.historyListeners = this.historyListeners.filter(cb => cb !== checkUrl);
                reject(new Error(`Timeout waiting for URL to contain ${part}`));
            }, timeout);
        });
    }

    /**
     * Find and click the play button of the first search result. 
     * Handles "Go+" restrictions and disabled buttons.
     * 
     * @returns {Promise<boolean>} True if successful, false otherwise
     */
    async playFirstResult() {
        // Brief wait for DOM stability
        await new Promise(resolve => setTimeout(resolve, 200));

        try {
            const resultSelector = '.searchList__item';
            await this.waitForElement(resultSelector, 500);

            const firstItem = document.querySelector(resultSelector);
            if (!firstItem) throw new Error("No search results found");

            const goPlusIndicator = firstItem.querySelector('.tierIndicator__smallGoPlus');
            if (goPlusIndicator && !goPlusIndicator.classList.contains('sc-hidden')) {
                return false;
            }

            const playBtn = firstItem.querySelector('.sc-button-play');
            
            if (!playBtn) throw new Error("Play button not found");

            if (playBtn.classList.contains('sc-button-disabled') || playBtn.getAttribute('title') === 'Non disponible') {
                return false;
            }
            
            playBtn.click();
            return true;
        } catch (e) {
            console.error("[Adapter] Failed to autoplay:", e);
            return false;
        }
    }

    /**
     * Check if music is currently playing.
     * 
     * @returns {boolean} True if a track is currently playing
     */
    isPlaying() {
        const playControl = document.querySelector('.playControl');
        return playControl && playControl.classList.contains('playing');
    }

    /**
     * Get playback progress of the current track.
     * 
     * @returns {{current: number, max: number} | null} Progress object or null if not available
     */
    getProgress() {
        const progress = document.querySelector('.playbackTimeline__progressWrapper');
        if (!progress) return null;

        return {
            current: parseInt(progress.getAttribute('aria-valuenow'), 10) || 0,
            max: parseInt(progress.getAttribute('aria-valuemax'), 10) || 0
        };
    }

    /**
     * Get details of the currently playing track from the player footer.
     * 
     * @returns {string | null} Track details in format "Artist - Title", or null if not available
     */
    getCurrentTrackDetails() {
        const titleEl = document.querySelector('.playControls .playbackSoundBadge__titleLink');
        const artistEl = document.querySelector('.playControls .playbackSoundBadge__lightLink');
        
        if (!titleEl) return null;

        const title = titleEl.getAttribute('title') || titleEl.innerText;
        const artist = artistEl ? (artistEl.getAttribute('title') || artistEl.innerText) : '';
        
        return `${artist} - ${title}`;
    }

    /**
     * Clean up all mutation observers.
     * Call this when disposing of the adapter.
     */
    dispose() {
        this.observers.forEach(obs => obs.disconnect());
        this.observers = [];
        this.historyListeners = [];
    }
}

// Expose to global scope for other content scripts
window.SoundCloudAdapter = SoundCloudAdapter;
