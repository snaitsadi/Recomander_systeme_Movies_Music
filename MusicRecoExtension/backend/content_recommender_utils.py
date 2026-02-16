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