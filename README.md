# Recomander_systeme_Movies_Music
# SoundCloud Music Recommendation System

This project is a music recommendation system designed to enhance the SoundCloud browsing experience. It consists of a Google Chrome Extension that integrates directly into the SoundCloud interface and a backend server that powers the recommendation logic.

## Project Concept

The main goal is to provide intelligent music suggestions to users as they listen on SoundCloud. The system analyzes user listening habits and song characteristics to recommend new tracks that match their taste.

### Key Components

*   **Chrome Extension**: A browser extension that acts as the frontend. It adds a sidebar to SoundCloud, tracks the songs you listen to, and plays recommended tracks automatically.
*   **Recommendation Engine**: A Python-based backend that processes data and generates recommendations using two main approaches:
    *   **Content-Based Filtering**: Recommends songs similar to what you like based on audio features and metadata (using the Million Song Dataset).
    *   **Collaborative Filtering**: Suggests new music based on the listening patterns of similar users.

### How It Works

1.  **Track**: The extension monitors your listening duration and history on SoundCloud.
2.  **Analyze**: The backend server processes this data against a database of songs and user profiles.
3.  **Recommend**: The system generates a personalized list of songs and displays them in the extension sidebar, ready to play.
