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


from pathlib import Path

SONG_MAPPING_REVERT = {
    song_index: song_id for song_id, song_index in SONG_MAPPING.items()
}

model_path = Path(__file__).parent / f"model-{DATASET_SIZE}-{l}"
q, p, b_song, b_user = load_model(str(model_path))

print("[COLLABORATIVE] Model loaded")


def get_recommendations(users_listenings: list[tuple[str, int]]) -> list[str]:
    print(f"[COLLAB_API] Analyzing {len(users_listenings)} input songs")
    # User songs as indexes w.r.t. song mapping
    user_song_indexes = {
        SONG_MAPPING[song_id]: listening_count
        for song_id, listening_count in users_listenings
        if song_id in SONG_MAPPING
    }

    if not user_song_indexes:
        print("[COLLAB_API] No valid known songs in input")
        return []
    
    print(f"[COLLAB_API] Found {len(user_song_indexes)} known songs in input")
