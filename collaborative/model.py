from typing import Any
import numpy as np

# Model is a tuple (q,p,b_song,b_user) of shapes (#SONGS, l), (#USERS, l) and (#SONGS), (#USERS)
Model = tuple[
    np.ndarray[tuple[Any, ...], np.dtype[np.float64]],
    np.ndarray[tuple[Any, ...], np.dtype[np.float64]],
    np.ndarray[tuple[Any, ...], np.dtype[np.float64]],
    np.ndarray[tuple[Any, ...], np.dtype[np.float64]],
]


def init(n_songs: int, n_users: int) -> Model:
    l = 100
    # Initial (random) values
    # Shape: (#SONGS, l)
    q = np.random.random_sample((n_songs, l))
    # Shape: (#USERS, l)
    p = np.random.random_sample((n_users, l))
    b_song = np.random.random_sample(n_songs)
    b_user = np.random.random_sample(n_users)

    return q, p, b_song, b_user



def save(prefix: str, model: Model):
    q, p, b_song, b_user = model
    np.save(prefix + "_q.npy", q)
    np.save(prefix + "_p.npy", p)
    np.save(prefix + "_b_song.npy", b_song)
    np.save(prefix + "_b_user.npy", b_user)


def load(prefix: str) -> Model:
    q = np.load(prefix + "_q.npy")
    p = np.load(prefix + "_p.npy")
    b_song = np.load(prefix + "_b_song.npy")
    b_user = np.load(prefix + "_b_user.npy")

    return (q, p, b_song, b_user)
