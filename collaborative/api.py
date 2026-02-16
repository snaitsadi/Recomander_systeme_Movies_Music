import numpy as np
from pathlib import Path
import pickle

from .dataset import load as load_dataset, normalize
from .model import load as load_model
from .test_train import DATASET_SIZE, l

# Should load full dataset!
dataset, USER_MAPPING, SONG_MAPPING = load_dataset(DATASET_SIZE)
average_listening_count = dataset["Listening count"].mean()
dataset = normalize(dataset)

#load songs_metadata.pkl
with open(Path(__file__).parent / "../data/songs_metadata.pkl", "rb") as f:
    songs_metadata = pickle.load(f)

songs_metadata_indices = set((SONG_MAPPING[song_id] for song_id in songs_metadata["song_id"] if song_id in SONG_MAPPING))

print("[COLLABORATIVE] Dataset ready")
