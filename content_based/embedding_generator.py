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