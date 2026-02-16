/**
 * Music Recommendation API Service
 * 
 * Handles communication with the backend recommendation server.
 * Supports both real backend and mock mode for development/testing.
 * 
 * @class MusicRecoAPI
 */
class MusicRecoAPI {
    constructor() {
        // Backend configuration
        this.baseUrl = 'http://localhost:5000';
        this.useMockData = false; // Set to true to use mock data instead of backend
        
        // Mock song collection for testing without backend
        this.mockSongs = [
            "Hello - Cardi B",
            "Blinding Lights - The Weeknd",
            "Bad Guy - Billie Eilish",
            "Shape of You - Ed Sheeran",
            "Levitating - Dua Lipa",
            "Watermelon Sugar - Harry Styles",
            "Peaches - Justin Bieber",
            "Save Your Tears - The Weeknd",
            "Good 4 U - Olivia Rodrigo",
            "Montero - Lil Nas X"
        ];
    }
