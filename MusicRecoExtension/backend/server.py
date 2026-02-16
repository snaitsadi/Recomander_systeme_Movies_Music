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