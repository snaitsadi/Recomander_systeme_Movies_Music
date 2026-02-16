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