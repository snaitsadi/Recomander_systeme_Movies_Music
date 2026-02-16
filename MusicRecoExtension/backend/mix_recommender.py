import random
from content_recommender_utils import get_content_based_recommendation
from collaborative_recommender import get_collaborative_recommendations

def get_mix_recommendation(user_id, conn, content_recommender_instance):
    """
    Get a recommendation using a mix of Content-Based and Collaborative Filtering.
    
    Algorithm:
    1. Get top 5 recommendations from Content-Based (if available)
    2. Get top 5 recommendations from Collaborative (if available)
    3. Assign scores: 1st place = 5 pts, 2nd = 4 pts, ..., 5th = 1 pt.
    4. Sum scores for each unique song.
    5. Return the song with the highest score (random tie-breaking).
    
    Args:
        user_id (str): User identifier
        conn (sqlite3.Connection): Database connection
        content_recommender_instance: Loaded ContentBasedRecommender object
        
    Returns:
        dict: The winning song object (or None if no recs)
        str: explanation/algo_type details
    """
    
    # Storage for scores
    # key: song_id, value: {points: int, song_obj: dict}
    candidates = {}