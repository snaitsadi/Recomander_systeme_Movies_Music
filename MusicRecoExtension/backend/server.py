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

def compute_score(listened_seconds, total_duration=None):
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




@app.route('/user/history', methods=['GET'])
def get_user_history():
    """
    Get user's listening history with engagement scores.
    
    Query Parameters:
        userId (str, required): User identifier
    
    Returns:
        JSON: {
            "status": "success",
            "user_id": str,
            "total_songs_listened": int,
            "unique_songs": int,
            "total_score": int,
            "history": [list of listening sessions]
        }
    
    Example:
        GET /user/history?userId=user_abc123
    """
    user_id = request.args.get('userId')
    
    if not user_id:
        return jsonify({"error": "userId parameter is required"}), 400
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Retrieve listening history with scores
        cursor.execute('''
            SELECT 
                lh.song_id,
                lh.listening_time as score,
                lh.algo_type,
                lh.timestamp,
                s.title,
                s.artist,
                s.duration
            FROM listening_history lh
            LEFT JOIN songs s ON lh.song_id = s.song_id
            WHERE lh.user_id = ?
            ORDER BY lh.timestamp DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        
        # Format results
        history = []
        for row in rows:
            history.append({
                "song_id": row[0],
                "score": row[1],
                "algo_type": row[2],
                "timestamp": row[3],
                "title": row[4],
                "artist": row[5],
                "duration": row[6]
            })
        
        # Calculate statistics
        total_score = sum(item['score'] for item in history)
        unique_songs = len(set(item['song_id'] for item in history))
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "user_id": user_id,
            "total_songs_listened": len(history),
            "unique_songs": unique_songs,
            "total_score": total_score,
            "history": history
        })
        
    except Exception as e:
        print(f"[ERROR] Error in /user/history: {e}")
        return jsonify({"error": str(e)}), 500





@app.route('/feedback/update', methods=['POST', 'GET'])
def update_user_feedback():
    """
    Record user listening session feedback.
    
    Called when user finishes listening to a track (or skips).
    Calculates engagement score based on listening duration.
    
    Request Body (JSON) or Query Parameters:
        userId (str): User identifier
        musicId (str): Track identifier (PREFERRED: songId)
        listeningTime (float): Seconds listened
    
    Returns:
        JSON: {
            "status": "success",
            "message": str,
            "score_computed": int
        }
    """
    data = request.json if request.is_json else {}
    
    user_id = data.get('userId') or request.args.get('userId')
    
    # Prioritize 'songId' if provided, then 'musicId' (which might be ID or title)
    # We strictly want song_id format (e.g. SOxxxxx)
    raw_id_input = data.get('songId') or request.args.get('songId') or data.get('musicId') or request.args.get('musicId')
    
    # Additional fallback: if client sends 'songTitle' separately
    song_title_input = data.get('songTitle') or request.args.get('songTitle')
    
    time_listened = float(data.get('listeningTime') or request.args.get('listeningTime') or 0)
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        final_song_id = None
        
        # 1. Check if raw_id_input is a valid song_id in our DB
        if raw_id_input:
             cursor.execute("SELECT song_id FROM songs WHERE song_id = ?", (raw_id_input,))
             if cursor.fetchone():
                 final_song_id = raw_id_input
        
        # 2. If valid ID not found, check if raw_id_input or song_title_input match a title/artist combination
        if not final_song_id:
             # Try to match by title
             search_term = song_title_input if song_title_input else raw_id_input
             if search_term:
                 print(f"[FEEDBACK] '{search_term}' is not a known song_id. Searching by title...")
                 # Try exact title match first
                 cursor.execute("SELECT song_id FROM songs WHERE title = ? OR title || ' - ' || artist = ?", (search_term, search_term))
                 row = cursor.fetchone()
                 if row:
                     final_song_id = row[0]
                     print(f"[FEEDBACK] Resolved '{search_term}' to song_id: {final_song_id}")
                 else:
                     # Very loose search (risky but helps find something)
                     cursor.execute("SELECT song_id FROM songs WHERE ? LIKE '%' || title || '%'", (search_term,))
                     row = cursor.fetchone()
                     if row:
                        final_song_id = row[0]
                        print(f"[FEEDBACK] Fuzzy resolved '{search_term}' to song_id: {final_song_id}")
        
        if not final_song_id:
             print(f"[FEEDBACK] ERROR: Could not resolve '{raw_id_input or song_title_input}' to a valid song_id. Feedback ignored.")
             conn.close()
             return jsonify({
                 "status": "error",
                 "message": "Could not verify song_id. Only valid song_ids are stored."
             }), 400

        # Retrieve track duration for score logic using the FINAL song_id
        cursor.execute("SELECT duration FROM songs WHERE song_id = ?", (final_song_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            total_duration = row[0]
        else:
            total_duration = DEFAULT_SONG_DURATION

        print(f"[FEEDBACK] User {user_id} listened to '{final_song_id}' (Duration: {total_duration}s) for {time_listened}s")

        # Calculate engagement score
        interest_score = compute_score(time_listened, total_duration)

        # Insert or update listening history (cumulative score)
        cursor.execute('''
            INSERT INTO listening_history (user_id, song_id, listening_time) 
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, song_id) 
            DO UPDATE SET 
                listening_time = listening_history.listening_time + excluded.listening_time,
                timestamp = CURRENT_TIMESTAMP
        ''', (user_id, final_song_id, interest_score))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success", 
            "message": "Feedback recorded successfully",
            "score_computed": interest_score,
            "resolved_song_id": final_song_id
        })
        
    except Exception as e:
        print(f"[ERROR] SQL error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sync', methods=['POST', 'GET'])
def sync_data():
    """
    Import data into SQLite database from pickle files.
    Two separate steps:
    1. Import full song catalog from songs_metadata.pkl
    2. Import user listening history from merged_data.pkl
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, '..', '..', 'data')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        results = {
            "status": "success",
            "songs_loaded": 0,
            "history_loaded": 0,
            "messages": []
        }

        # --- STEP 1: LOAD SONGS METADATA ---
        metadata_path = os.path.join(data_dir, 'songs_metadata.pkl')
        if os.path.exists(metadata_path):
            print(f"[SYNC] Loading Songs Metadata from {metadata_path}...")
            meta_df = pd.read_pickle(metadata_path)
            print(f"[SYNC] Found {len(meta_df)} songs in metadata.")
            
            # Ensure required columns exist
            if 'song_id' in meta_df.columns:
                # Fill missing optional columns with defaults
                if 'duration' not in meta_df.columns: meta_df['duration'] = DEFAULT_SONG_DURATION
                if 'release' not in meta_df.columns: meta_df['release'] = None
                if 'year' not in meta_df.columns: meta_df['year'] = 0
                if 'tempo' not in meta_df.columns: meta_df['tempo'] = 0.0
                if 'title' not in meta_df.columns: meta_df['title'] = "Unknown Title"
                if 'artist_name' not in meta_df.columns: meta_df['artist_name'] = "Unknown Artist"

                # Clean numeric types
                meta_df['year'] = pd.to_numeric(meta_df['year'], errors='coerce').fillna(0).astype(int)
                meta_df['tempo'] = pd.to_numeric(meta_df['tempo'], errors='coerce').fillna(0.0)
                meta_df['duration'] = pd.to_numeric(meta_df['duration'], errors='coerce').fillna(DEFAULT_SONG_DURATION)
                
                # Prepare for insertion
                # Columns: song_id, title, artist, duration, release, year, tempo
                # Note: pickle has 'artist_name', db has 'artist'
                song_records = meta_df[['song_id', 'title', 'artist_name', 'duration', 'release', 'year', 'tempo']].to_records(index=False).tolist()
                
                cursor.executemany('''
                    INSERT OR REPLACE INTO songs (song_id, title, artist, duration, release, year, tempo)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', song_records)
                
                results["songs_loaded"] = len(song_records)
                results["messages"].append(f"Imported {len(song_records)} from songs_metadata.pkl")
            else:
                 results["messages"].append("songs_metadata.pkl missing 'song_id' column")
        else:
            results["messages"].append("songs_metadata.pkl not found")

        # --- STEP 2: LOAD LISTENING HISTORY ---
        history_path = os.path.join(data_dir, 'merged_data.pkl')
        # Fallback
        if not os.path.exists(history_path):
            history_path = os.path.join(data_dir, 'mixed_data.pkl')

        if os.path.exists(history_path):
            print(f"[SYNC] Loading User History from {history_path}...")
            hist_df = pd.read_pickle(history_path)
            print(f"[SYNC] Found {len(hist_df)} history records.")
            
            required_hist_cols = ['user_id', 'song_id', 'play_count']
            if all(c in hist_df.columns for c in required_hist_cols):
                # If we have no songs loaded yet (meta file missing), we must extract basic song info from history to satisfy eventual consistency
                if results["songs_loaded"] == 0:
                     print("[SYNC] Extracting basic song info from history (metadata missing)...")
                     unique_songs = hist_df[['song_id', 'title', 'artist_name']].drop_duplicates(subset=['song_id']).copy()
                     unique_songs['duration'] = DEFAULT_SONG_DURATION
                     unique_songs['release'] = None
                     unique_songs['year'] = 0
                     unique_songs['tempo'] = 0
                     
                     fallback_songs = unique_songs.to_records(index=False).tolist()
                     cursor.executemany('''
                        INSERT OR IGNORE INTO songs (song_id, title, artist, duration, release, year, tempo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', fallback_songs)
                     results["messages"].append(f"Extracted {len(fallback_songs)} songs from history file")

                # Prepare history data
                hist_df['listening_time'] = hist_df['play_count'].fillna(0).astype(int)
                hist_df['algo_type'] = 'import_msd'
                
                history_records = hist_df[['user_id', 'song_id', 'listening_time', 'algo_type']].to_records(index=False).tolist()
                
                cursor.executemany('''
                    INSERT INTO listening_history (user_id, song_id, listening_time, algo_type) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, song_id) 
                    DO UPDATE SET 
                        listening_time = listening_history.listening_time + excluded.listening_time
                ''', history_records)
                
                results["history_loaded"] = len(history_records)
                results["messages"].append(f"Imported {len(history_records)} from {os.path.basename(history_path)}")
            else:
                 results["messages"].append("History file missing required columns")
        else:
            results["messages"].append("History pickle file not found")

        conn.commit()
        conn.close()
        
        print(f"[SYNC] Complete. {results}")
        return jsonify(results)

    except Exception as e:
        print(f"[SYNC ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =============================================================================
# APPLICATION STARTUP
# =============================================================================

if __name__ == '__main__':
    init_db()
    init_content_recommender()
    print("\n" + "="*60)
    print(" SoundCloud Music Recommender API")
    print(" Server starting on http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
