import pickle
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import os

class ContentBasedRecommender:
    """
    Recommends songs based on content similarity.
    """
    def __init__(self, embeddings_path="../data/song_embeddings.pkl", metadata_path="../data/songs_metadata.pkl"):
        """
        Initialize the recommender.
        
        Args:
            embeddings_path (str): Path to the song embeddings pickle.
            metadata_path (str): Path to the song metadata pickle.
        """
        self.embeddings_path = embeddings_path
        self.metadata_path = metadata_path
        
        self.embedding_map = None
        self.metadata_df = None
        self.song_ids = None
        self.embedding_matrix = None
        self.knn_model = None
        
        self._load_data()
        self._build_index()


def _load_data(self):
        """Loads embeddings and metadata."""
        if not os.path.exists(self.embeddings_path):
            raise FileNotFoundError(f"Embeddings file not found at {self.embeddings_path}. Run embedding_generator.py first.")
        
        print(f"Loading embeddings from {self.embeddings_path}...")
        with open(self.embeddings_path, 'rb') as f:
            self.embedding_map = pickle.load(f)
            
        if os.path.exists(self.metadata_path):
            print(f"Loading metadata from {self.metadata_path}...")
            self.metadata_df = pd.read_pickle(self.metadata_path)
            # Create a quick lookup for details
            self.song_details = self.metadata_df.set_index('song_id')[['title', 'artist_name']].to_dict('index')
        else:
            print("Warning: Metadata file not found. Recommendations will return IDs only.")
            self.song_details = {}
