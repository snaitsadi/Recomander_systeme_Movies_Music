import pandas as pd
import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

class SongEmbeddingGenerator:
    """
    Generates embeddings for songs based on their metadata using SentenceTransformer.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2", data_path="../data/songs_metadata.pkl", output_path="../data/song_embeddings.pkl"):
        """
        Initialize the generator.
        
        Args:
            model_name (str): The name of the SentenceTransformer model to use.
            data_path (str): Path to the pickle file containing song metadata.
            output_path (str): Path where the generated embeddings will be saved.
        """
        self.model_name = model_name
        self.data_path = data_path
        self.output_path = output_path
        self.model = SentenceTransformer(model_name)
        


    def _create_text_representation(self, row):
        """
        Creates a textual representation of a song from its metadata.
        Features used: title, artist_name, release, year, tempo, artist_terms, genre.
        """
        parts = []
        
        # specific to Million Song Dataset columns
        title = row.get('title', 'Unknown Title')
        artist = row.get('artist_name', 'Unknown Artist')
        parts.append(f"Song: {title}")
        parts.append(f"Artist: {artist}")
        
        album = row.get('release')
        if pd.notna(album) and album != title:
            parts.append(f"Album: {album}")
            
        year = row.get('year')
        if pd.notna(year) and year != 0:
            parts.append(f"Year: {int(year)}")
            
        # Add audio features if available and meaningful
        # MSD often has these
        tempo = row.get('tempo')
        if pd.notna(tempo) and tempo > 0:
            parts.append(f"Tempo: {int(tempo)} BPM")
            
        # Add genre context using artist terms (tags)
        # MSD uses 'artist_terms' instead of a single genre field
        terms = row.get('artist_terms')
        if isinstance(terms, (list, np.ndarray)) and len(terms) > 0:
            # Take top 5 terms
            top_terms = ", ".join(terms[:5])
            parts.append(f"Tags: {top_terms}")
        elif pd.notna(row.get('genre')):
             parts.append(f"Genre: {row.get('genre')}")
             
        # Create a sentence
        return ". ".join(parts) + "."
    


    def generate(self):
        """
        Loads data, generates embeddings, and saves them.
        """
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found at {self.data_path}. Please run data_cleaning_script.ipynb first.")
            
        print(f"Loading songs metadata from {self.data_path}...")
        df = pd.read_pickle(self.data_path)
        
        print(f"Generating textual descriptions for {len(df)} songs...")
        descriptions = df.apply(self._create_text_representation, axis=1).tolist()
        
        print(f"Encoding descriptions with {self.model_name}...")
        # Encode in batches to show progress
        embeddings = self.model.encode(descriptions, show_progress_bar=True, convert_to_numpy=True)
        
        # Create a dictionary mapping song_id to embedding
        # This assumes song_id is unique and present
        if 'song_id' not in df.columns:
            raise ValueError("DataFrame missing required 'song_id' column.")
            
        embedding_map = {
            song_id: emb 
            for song_id, emb in zip(df['song_id'], embeddings)
        }
        
        print(f"Saving embeddings to {self.output_path}...")
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'wb') as f:
            pickle.dump(embedding_map, f)
            
        print("Done.")

if __name__ == "__main__":
    generator = SongEmbeddingGenerator()
    generator.generate()
