import random
from content_recommender_utils import get_content_based_recommendation
from collaborative_recommender import get_collaborative_recommendations

def get_mix_recommendation(user_id, conn, content_recommender_instance):
    """
    Get a recommendation using a mix of Content-Based and Collaborative Filtering.
    
    Algorithm:
    1. Get top 5 recommendations from Content-Based (if available)
    2. Get top 5 recommendations from Collaborative (if available)
    3. Assign scores: 1st place = 5 pts, 2nd = 4 pts, ..., 5th = 1 pt.
    4. Sum scores for each unique song.
    5. Return the song with the highest score (random tie-breaking).
    
    Args:
        user_id (str): User identifier
        conn (sqlite3.Connection): Database connection
        content_recommender_instance: Loaded ContentBasedRecommender object
        
    Returns:
        dict: The winning song object (or None if no recs)
        str: explanation/algo_type details
    """
    
    # Storage for scores
    # key: song_id, value: {points: int, song_obj: dict}
    candidates = {}



    def add_votes(recommendations, max_points=5, source="unknown"):
        if not recommendations:
            print(f"[MIX] No recommendations from {source}")
            return
        
        # Take up to top 5
        top_recs = recommendations[:5]
        print(f"[MIX] Processing top {len(top_recs)} from {source}")
        
        for i, rec in enumerate(top_recs):
            points = max_points - i  # 5, 4, 3, 2, 1
            song_id = rec.get('song_id')
            title = rec.get('title', 'Unknown')
            
            if not song_id:
                continue
                
            if song_id not in candidates:
                candidates[song_id] = {
                    'points': 0,
                    'song_details': rec
                }
            
            candidates[song_id]['points'] += points
            print(f"[MIX] Vote from {source}: {title} (+{points} pts). Total: {candidates[song_id]['points']}")
            # Prefer to keep details that might be more complete (e.g. from DB) if collision
            
    # 1. Content Based
    content_recs = []
    if content_recommender_instance:
        try:
            print("[MIX] Fetching Content-Based recommendations...")
            content_recs = get_content_based_recommendation(content_recommender_instance, user_id, conn)
            # content_recs is a list of dicts: {'song_id', 'title', 'artist_name', 'similarity'}
            # Normalize keys to match collaborative (title, artist without _name)
            for rec in (content_recs or []):
                if 'artist_name' in rec:
                    rec['artist'] = rec.pop('artist_name')
        except Exception as e:
            print(f"[MIX] Content-based failed: {e}")
    else:
        print("[MIX] Content recommender not available")

    add_votes(content_recs, source="content-based")
    
    # 2. Collaborative
    collab_recs = []
    try:
        print("[MIX] Fetching Collaborative recommendations...")
        collab_recs = get_collaborative_recommendations(user_id, conn, limit=5)
    except Exception as e:
        print(f"[MIX] Collaborative failed: {e}")

    add_votes(collab_recs, source="collaborative")
    
    print(f"[MIX] Total unique candidates: {len(candidates)}")
    
    if not candidates:
        return None, "mix_no_candidates"

    # Find max score
    max_score = -1
    winners = []
    
    for song_id, data in candidates.items():
        score = data['points']
        if score > max_score:
            max_score = score
            winners = [data['song_details']]
        elif score == max_score:
            winners.append(data['song_details'])
            
    if not winners:
        return None, "mix_error"
        
    print(f"[MIX] Max Score: {max_score}, Winners count: {len(winners)}")
    
    # Random tie-break
    final_choice = random.choice(winners)
    return final_choice, "mix_hybrid"
