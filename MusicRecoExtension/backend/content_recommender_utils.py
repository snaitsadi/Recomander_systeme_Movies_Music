"""
Content-Based Recommender Utilities

Handles loading and using the content-based recommendation model for the Flask backend.
Provides functions to format database data and generate recommendations.
"""

import os
import sys
import random

# Add parent directory to path to import from content_based module
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(backend_dir, '..', '..')
content_based_dir = os.path.join(project_root, 'content_based')
sys.path.insert(0, content_based_dir)

from recommender import ContentBasedRecommender


def load_content_recommender():
    """
    Load the ContentBasedRecommender with the appropriate data paths.
    
    Returns:
        ContentBasedRecommender: Initialized recommender instance
        
    Raises:
        FileNotFoundError: If required data files don't exist
    """
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(backend_dir, '..', '..')
    data_dir = os.path.join(project_root, 'data')
    
    embeddings_path = os.path.join(data_dir, 'song_embeddings.pkl')
    metadata_path = os.path.join(data_dir, 'songs_metadata.pkl')
    
    print(f"[CONTENT-BASED] Loading recommender...")
    print(f"  Embeddings: {embeddings_path}")
    print(f"  Metadata: {metadata_path}")
    
    if not os.path.exists(embeddings_path):
        raise FileNotFoundError(
            f"Embeddings file not found at {embeddings_path}. "
            "Run embedding_generator.py first."
        )
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(
            f"Metadata file not found at {metadata_path}. "
            "Run data_cleaning_script.ipynb first."
        )
    
    recommender = ContentBasedRecommender(
        embeddings_path=embeddings_path,
        metadata_path=metadata_path
    )
    
    print("[CONTENT-BASED] ✓ Recommender loaded successfully!")
    return recommender


def format_user_history_for_recommender(db_history_rows):
    """
    Format database listening history into the format expected by ContentBasedRecommender.
    
    The database now stores:
        - song_id: MSD song ID (SOxxxxx format)
        - listening_time: engagement score (0-10)
    
    The recommender expects:
        - song_id: MSD song ID (SOxxxxx format)
        - play_count: integer listening count
    
    Args:
        db_history_rows (list): List of tuples from database query
                               Format: [(song_id, listening_time), ...]
    
    Returns:
        list: Formatted history as [{'song_id': 'SOxxxxx', 'play_count': score}, ...]
              Returns empty list if no valid songs found
    """
    formatted_history = []
    
    for song_id, listening_time in db_history_rows:
        # Database now stores proper MSD song IDs
        if song_id and song_id.startswith('SO'):
            formatted_history.append({
                'song_id': song_id,
                'play_count': int(listening_time) if listening_time else 1
            })
    
    return formatted_history


def get_content_based_recommendation(recommender, user_id, conn):
    """
    Get a content-based recommendation for a user.
    
    Args:
        recommender (ContentBasedRecommender): Loaded recommender instance
        user_id (str): User identifier
        conn (sqlite3.Connection): Database connection
    
    Returns:
        str: Recommended track in "Title - Artist" format
        
    Raises:
        Exception: If recommendation fails
    """
    cursor = conn.cursor()
    
    # Fetch user's listening history from database
    cursor.execute('''
        SELECT song_id, listening_time 
        FROM listening_history 
        WHERE user_id = ?
        ORDER BY listening_time DESC
    ''', (user_id,))
    
    db_history = cursor.fetchall()
    
    if not db_history:
        print(f"[CONTENT-BASED] No history found for user {user_id}")
        return None
    
    print(f"[CONTENT-BASED] Found {len(db_history)} tracks in user history")
    
    # Format history for the recommender
    user_history = format_user_history_for_recommender(db_history)
    
    if not user_history:
        print("[CONTENT-BASED] No valid song IDs found in history")
        return None
    
    print(f"[CONTENT-BASED] Formatted {len(user_history)} tracks for recommender")
    
    # Calculate user embedding
    user_embedding = recommender.calculate_user_embedding(user_history)
    
    if user_embedding is None:
        print("[CONTENT-BASED] Could not calculate user embedding")
        return None
    
    # Get top 5 recommendations
    recommendations = recommender.recommend(user_embedding, n_recommendations=5)
    
    if not recommendations:
        print("[CONTENT-BASED] No recommendations generated")
        return []
    
    print(f"[CONTENT-BASED] Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['title']} - {rec['artist_name']} (similarity: {rec['similarity']:.3f})")
    
    return recommendations
