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
