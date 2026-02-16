from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import pandas as pd
import os
import random
import math
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from collaborative
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import Recommenders
try:
    from collaborative_recommender import get_collaborative_recommendations, is_collaborative_available
    print("[COLLABORATIVE] ✓ Wrapper loaded successfully")
except ImportError as e:
    print(f"[COLLABORATIVE] ⚠ Could not import wrapper: {e}")
    def is_collaborative_available(): return False
    def get_collaborative_recommendations(*args, **kwargs): return []

try:
    from content_recommender_utils import load_content_recommender, get_content_based_recommendation
    CONTENT_RECOMMENDER_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Could not import content_recommender_utils: {e}")
    CONTENT_RECOMMENDER_AVAILABLE = False

try:
    from mix_recommender import get_mix_recommendation
    MIX_RECOMMENDER_AVAILABLE = True
except ImportError as e:
     print(f"[WARNING] Could not import mix_recommender: {e}")
     MIX_RECOMMENDER_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variable to hold the preloaded content-based recommender
content_recommender = None

# =============================================================================
# CONFIGURATION
# =============================================================================

DB_NAME = "music_reco.db"
DEFAULT_SONG_DURATION = 210  # Default duration in seconds (3m 30s)
MAX_SCORE = 10
COLD_START_THRESHOLD = 5  # Minimum tracks needed before using collaborative filtering

# =============================================================================
# HELPER FUNCTIONS
# ============================================================================

ef compute_score(listened_seconds, total_duration=None):
    """
    Calculate an engagement score between 0 and 10 based on completion ratio.
    
    Formula: ceil(completion_ratio * 10)
    
    Examples:
        - 10% listened  -> 1 point
        - 50% listened  -> 5 points
        - 100% listened -> 10 points
    
    Args:
        listened_seconds (float): Number of seconds the user listened to the track
        total_duration (float, optional): Total duration of the track in seconds.
                                         Defaults to 210s (3m 30s) if not provided.
    
    Returns:
        int: Engagement score between 0 and 10
    """
    duration = total_duration if (total_duration and total_duration > 0) else DEFAULT_SONG_DURATION
    
    # Cap listened time at total duration (max 100% completion)
    actual_listened = min(listened_seconds, duration)
    
    # Calculate completion ratio (0.0 to 1.0)
    completion_ratio = actual_listened / duration
    
    # Linear formula: ratio * max_score, rounded up
    score = math.ceil(completion_ratio * MAX_SCORE)
    
    return int(score)

def init_db():
    """
    Initialize SQLite database if it doesn't exist.
    
    Creates two tables:
        - songs: Store song metadata (title, artist, duration)
        - listening_history: Track user listening sessions and engagement scores
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Songs metadata table (stores duration and track information)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            song_id TEXT PRIMARY KEY,
            title TEXT,
            artist TEXT,
            duration REAL,
            release TEXT,
            year INTEGER,
            tempo REAL
        )
    ''')

    # Listening history table (tracks user engagement)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listening_history (
            user_id TEXT NOT NULL,
            song_id TEXT NOT NULL,
            listening_time INTEGER,
            algo_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, song_id)
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized successfully.")


    def init_content_recommender():
    """
    Initialize the content-based recommender system.
    Loads embeddings and metadata on server startup.
    """
    global content_recommender
    
    if not CONTENT_RECOMMENDER_AVAILABLE:
        print("[CONTENT-BASED] Skipping initialization - module not available")
        return
    
    try:
        content_recommender = load_content_recommender()
        print("[CONTENT-BASED] ✓ Recommender initialized successfully")
    except FileNotFoundError as e:
        print(f"[CONTENT-BASED] ⚠ Could not load recommender: {e}")
        content_recommender = None
    except Exception as e:
        print(f"[CONTENT-BASED] ⚠ Error initializing recommender: {e}")
        content_recommender = None


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/')
def home():
    """Root endpoint - API status check."""
    return jsonify({
        "service": "SoundCloud Music Recommender API",
        "status": "running",
        "version": "1.0"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "music-reco-api"
    })

@app.route('/recommend/next', methods=['GET'])
def recommend_next_track():
    """
    Get next recommended track for a user.
    
    Supports both query parameters (preferred) and JSON body.
    
    Query Parameters:
        userId (str): Unique user identifier
        algoType (str): Algorithm type - 'matriciel', 'content', or 'mix'
                       Defaults to 'matriciel'
    
    Returns:
        JSON: {
            "song_title": str,
            "algorithm": str,
            "status": "success"
        }
    
    Example:
        GET /recommend/next?userId=user123&algoType=matriciel
    """
    # Support both query parameters and JSON body
    user_id = request.args.get('userId') or (request.json.get('userId') if request.json else None)
    algo_type = request.args.get('algoType') or (request.json.get('algoType') if request.json else 'matriciel')
    
    print(f"[RECOMMENDATION] User: {user_id} | Algorithm: {algo_type}")

    suggestion = "Default Track"
    algo_used = algo_type
    track_details = {}

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check for cold start: Does user have sufficient listening history?
        cursor.execute("SELECT COUNT(*) FROM listening_history WHERE user_id = ?", (user_id,))
        history_count = cursor.fetchone()[0]

        # Cold start scenario: Less than required tracks in history
        if history_count < COLD_START_THRESHOLD:
            algo_used = "cold_start_top50"
            
            # Get top 50 most popular tracks with metadata
            cursor.execute('''
                SELECT s.song_id, s.title, s.artist, s.duration, s.release, s.year, s.tempo 
                FROM listening_history lh
                LEFT JOIN songs s ON lh.song_id = s.song_id
                GROUP BY lh.song_id
                ORDER BY SUM(lh.listening_time) DESC
                LIMIT 50
            ''')
            
            rows = cursor.fetchall()
            valid_rows = [row for row in rows if row[1] and row[2]]  # Ensure title and artist exist
            
            if valid_rows:
                selected = random.choice(valid_rows)
                suggestion = f"{selected[1]} - {selected[2]}"
                track_details = {
                    "song_id": selected[0],
                    "title": selected[1],
                    "artist": selected[2],
                    "duration": selected[3],
                    "release": selected[4],
                    "year": selected[5],
                    "tempo": selected[6]
                }
            else:
                # No tracks in database at all - use fallback
                suggestion = "Bohemian Rhapsody - Queen"
                algo_used = "fallback_default"
        else:
            # User has sufficient history - use algorithm-specific logic
            selected_track_obj = None
            
            if algo_type == 'content':
                if CONTENT_RECOMMENDER_AVAILABLE and content_recommender:
                    try:
                        recs = get_content_based_recommendation(content_recommender, user_id, conn)
                        if recs:
                            # Content recommender returns list of dicts
                            selected_track_obj = random.choice(recs)
                            algo_used = "content_v1"
                        else:
                             algo_used = "content_empty"
                    except Exception as e:
                        print(f"[CONTENT] Error: {e}")
                        algo_used = "content_error"
                else:
                    algo_used = "content_na"
                    
            elif algo_type == 'matriciel':
                if is_collaborative_available():
                    try:
                        # Wrapper handles DB lookup
                        recs = get_collaborative_recommendations(user_id, conn, limit=10)
                        if recs:
                            selected_track_obj = random.choice(recs)
                            algo_used = "matriciel_v1"
                        else:
                            algo_used = "matriciel_empty"
                    except Exception as e:
                        print(f"[COLLAB] Error: {e}")
                        algo_used = "matriciel_error"
                else:
                    algo_used = "matriciel_na"
                    
            elif algo_type == 'mix':
                 if MIX_RECOMMENDER_AVAILABLE:
                     try:
                         # mix recommender handles scoring and returns single winner
                         rec, reason = get_mix_recommendation(user_id, conn, content_recommender)
                         if rec:
                             selected_track_obj = rec
                             algo_used = reason
                         else:
                             algo_used = reason
                     except Exception as e:
                         print(f"[MIX] Error: {e}")
                         algo_used = "mix_error"
                 else:
                     algo_used = "mix_na"
            
            # Fallback if no track selected
            if selected_track_obj:
               # Ensure we have required keys
               title = selected_track_obj.get('title', 'Unknown Title')
               artist = selected_track_obj.get('artist') or selected_track_obj.get('artist_name') or 'Unknown Artist'
               suggestion = f"{title} - {artist}"
               
               track_details = {
                    "song_id": selected_track_obj.get('song_id'),
                    "title": title,
                    "artist": artist,
                    "duration": selected_track_obj.get('duration', DEFAULT_SONG_DURATION),
                    "release": selected_track_obj.get('release'),
                    "year": selected_track_obj.get('year', 0),
                    "tempo": selected_track_obj.get('tempo', 0)
                }
            else:
                 suggestion = "Hotel California - The Eagles"
                 algo_used += "_fallback"

        conn.close()

    except Exception as e:
        print(f"[ERROR] Database error in /recommend/next: {e}")
        suggestion = "Bohemian Rhapsody - Queen"  # Fallback track
        algo_used = "error_fallback"

    response_data = {
        "song_title": suggestion,
        "algorithm": algo_used,
        "status": "success",
        **track_details
    }

    return jsonify(response_data)