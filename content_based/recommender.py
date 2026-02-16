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


    def _build_index(self):
        """Prepares the KNN index for fast retrieval."""
        # Convert map to matrix for sklearn
        self.song_ids = list(self.embedding_map.keys())
        self.embedding_matrix = np.array([self.embedding_map[sid] for sid in self.song_ids])
        
        print(f"Building NearestNeighbors index for {len(self.song_ids)} songs...")
        self.knn_model = NearestNeighbors(n_neighbors=5, metric='cosine', algorithm='brute')
        self.knn_model.fit(self.embedding_matrix)

    def calculate_user_embedding(self, user_history):
        """
        Calculates a user's embedding vector based on their listening history.
        
        Args:
            user_history (list): A list of dictionaries or tuples containing song_id and play_count.
                                 Format: [{'song_id': '...', 'play_count': 5}, ...] 
                                 or list of (song_id, count).
        
        Returns:
            np.array: The weighted mean embedding for the user.
        """
        if not user_history:
            return None
            
        weighted_sum = np.zeros(self.embedding_matrix.shape[1])
        total_weight = 0
        
        for item in user_history:
            if isinstance(item, dict):
                song_id = item.get('song_id')
                count = item.get('play_count', 1)
            else:
                song_id, count = item
                
            if song_id in self.embedding_map:
                embedding = self.embedding_map[song_id]
                weighted_sum += embedding * count
                total_weight += count
        
        if total_weight == 0:
            return None
            
        return weighted_sum / total_weight
    

    def recommend(self, user_embedding, n_recommendations=5):
        """
        Finds the nearest songs to the user's embedding.
        
        Args:
            user_embedding (np.array): The user's accumulated vector.
            n_recommendations (int): Number of songs to recommend.
            
        Returns:
            list: List of recommended songs with metadata.
        """
        if user_embedding is None:
            return []
            
        # Reshape for sklearn (1, n_features)
        query = user_embedding.reshape(1, -1)
        
        distances, indices = self.knn_model.kneighbors(query, n_neighbors=n_recommendations)
        
        recommendations = []
        for i, idx in enumerate(indices[0]):
            song_id = self.song_ids[idx]
            dist = distances[0][i]
            
            details = self.song_details.get(song_id, {'title': 'Unknown', 'artist_name': 'Unknown'})
            
            rec = {
                'song_id': song_id,
                'distance': float(dist),
                'similarity': 1.0 - float(dist), # cosine distance to similarity
                **details
            }
            recommendations.append(rec)
            
        return recommendations

