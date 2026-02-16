# Content-Based Recommendation System

## Overview

A semantic music recommendation engine using transformer embeddings and k-Nearest Neighbors. Recommends songs based on metadata similarity (artist, title, genre, tempo) using the Million Song Dataset.

**Key Feature:** Works for new users with minimal listening history (cold start problem solution).

## Files

- **`data_cleaning_script.ipynb`** - Loads and processes Million Song Dataset HDF5 files, extracts metadata, generates pickle files
- **`embedding_generator.py`** - Converts song metadata to 384-dimensional semantic vectors using SentenceTransformer
- **`recommender.py`** - KNN-based recommendation engine with cosine similarity
- **`test_recommender.ipynb`** - Demo notebook showing end-to-end recommendation workflow

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Process data:
```bash
jupyter notebook data_cleaning_script.ipynb
# Run all cells to generate: ../data/taste_profile.pkl and ../data/songs_metadata.pkl
```

3. Generate embeddings:
```bash
python embedding_generator.py
# Creates: ../data/song_embeddings.pkl
```

## Usage

```python
from recommender import ContentBasedRecommender

# Initialize
recommender = ContentBasedRecommender(
    embeddings_path='../data/song_embeddings.pkl',
    metadata_path='../data/songs_metadata.pkl'
)

# User listening history
user_history = [
    {'song_id': 'SOXXXXX', 'play_count': 10},
    {'song_id': 'SOYYYYY', 'play_count': 5}
]

# Calculate user profile
user_embedding = recommender.calculate_user_embedding(user_history)

# Get recommendations
recommendations = recommender.recommend(user_embedding, n_recommendations=5)

for rec in recommendations:
    print(f"{rec['title']} by {rec['artist_name']} (similarity: {rec['similarity']:.3f})")
```

## How It Works

1. Song metadata → Natural language description
2. SentenceTransformer → Dense embeddings
3. User history → Weighted average embedding
4. KNN cosine search → Similar songs
