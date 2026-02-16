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