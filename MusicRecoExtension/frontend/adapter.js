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