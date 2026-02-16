import sqlite3
import random
import sys
from pathlib import Path

# Add project root to sys.path to allow importing from collaborative
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

COLLABORATIVE_AVAILABLE = False
get_api_recommendations = None

try:
    from collaborative.api import get_recommendations as _get_recs
    get_api_recommendations = _get_recs
    COLLABORATIVE_AVAILABLE = True
    print("[COLLABORATIVE] ✓ Module loaded successfully in wrapper")
except Exception as e:
    print(f"[COLLABORATIVE] ⚠ Could not import module or load models: {e}")
    COLLABORATIVE_AVAILABLE = False

def is_collaborative_available():
    return COLLABORATIVE_AVAILABLE

def get_collaborative_recommendations(user_id, conn, limit=10):
    """
    Get collaborative recommendations for a user.
    
    Args:
        user_id (str): User identifier
        conn (sqlite3.Connection): Database connection
        limit (int): Number of recommendations to retrieve (default: 10)
        
    Returns:
        list: List of dicts with song details
    """
    if not COLLABORATIVE_AVAILABLE:
        print("[COLLABORATIVE] collaborative module not available")
        return []

    try:
        cursor = conn.cursor()
        # Get user history
        cursor.execute("SELECT song_id, listening_time FROM listening_history WHERE user_id = ?", (user_id,))
        history = cursor.fetchall()
        
        if not history:
            print(f"[COLLABORATIVE] No history for user {user_id}")
            return []
            
        print(f"[COLLABORATIVE] Found {len(history)} history items for {user_id}")
        # collaborative api expects list[tuple[str, int]]
        user_listenings = [(row[0], int(row[1])) for row in history]
        
        # Get raw recommendations (list of song_ids)
        print(f"[COLLABORATIVE] Calling API with {len(user_listenings)} listenings")
        raw_recs = get_api_recommendations(user_listenings)
        
        if not raw_recs:
            print("[COLLABORATIVE] No raw recommendations returned")
            return []
        
        print(f"[COLLABORATIVE] API returned {len(raw_recs)} raw IDs")
        # Get metadata for the top recommendations
        top_n = raw_recs[:limit]
        placeholders = ','.join(['?'] * len(top_n))
        
        query = f"SELECT song_id, title, artist, duration, release, year, tempo FROM songs WHERE song_id IN ({placeholders})"
        cursor.execute(query, top_n)
        found_songs = cursor.fetchall()
        
        if not found_songs:
            print("[COLLABORATIVE] No matching songs found in DB")
            return []
            
        # Map back to preserve order of recommendation (since SQL IN doesn't preserve order)
        songs_map = {
            row[0]: {
                "song_id": row[0],
                "title": row[1],
                "artist": row[2],
                "duration": row[3],
                "release": row[4],
                "year": row[5],
                "tempo": row[6]
            } 
            for row in found_songs
        }
        
        # Reconstruct ordered list
        ordered_recs = []
        for song_id in top_n:
            if song_id in songs_map:
                ordered_recs.append(songs_map[song_id])
                
        return ordered_recs
        
    except Exception as e:
        print(f"[COLLABORATIVE] Error generating recommendation: {e}")
        return []
