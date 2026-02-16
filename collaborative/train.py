from collections.abc import Iterable
import numpy as np
from typing import TypedDict, cast

from .model import Model


class LearningStats(TypedDict):
    """
    Learning stats (losses: train & validation) for each epoch.
    """

    losses_train: list[np.float64 | float]
    losses_validation: list[np.float64 | float]
    accuracy_train: list[np.float64 | float]
    accuracy_validation: list[np.float64 | float]


def train(
    l: int,
    lbd: float,
    gamma: float,
    n_epochs: int,
    train_set: np.ndarray,
    validation_set: np.ndarray,
    model: Model,
) -> tuple[Model, LearningStats]:
    (q, p, b_song, b_user) = model

    learning_stats: LearningStats = {
        "losses_train": [np.nan] * n_epochs,
        "losses_validation": [np.nan] * n_epochs,
        "accuracy_train": [np.nan] * n_epochs,
        "accuracy_validation": [np.nan] * n_epochs,
    }

    print(f"Training with l={l}, lambda={lbd}, gamma={gamma} for {n_epochs} epochs.")

    average_listening_count = train_set["Listening count"].mean()

    for epoch in range(n_epochs):
        print(f"Epoch {epoch+1}")
        loss_sum: float = 0
        accuracy_sum: float = 0

        np.random.shuffle(train_set)  # Reorder each epoch
        # user \in [0, #USERS - 1]
        # song \in [0, #SONGS - 1]
        # listenings \in N (r_ui, "true" value)
        for i, (user, song, listening_count) in enumerate(
            cast(Iterable[tuple[np.uint32, np.uint32, np.float64]], train_set)
        ):

            # Predicted value
            p_u = p[user].copy()
            q_i = q[song].copy()
            b_u = b_user[user].copy()
            b_i = b_song[song].copy()

            listenings_hat = (p_u.T @ q_i) + average_listening_count + b_u + b_i

            # Prediction error
            e_ui = listening_count - listenings_hat

            # This is the learning part
            q[song] += gamma * (e_ui * p_u - lbd * q_i)
            p[user] += gamma * (e_ui * q_i - lbd * p_u)
            b_user[user] += gamma * (e_ui - lbd * b_u)
            b_song[song] += gamma * (e_ui - lbd * b_i)

            # Loss
            loss = e_ui**2 + lbd * (np.linalg.norm(q_i) ** 2 + np.linalg.norm(p_u) ** 2)
            loss_sum += loss

            # Accuracy
            accuracy = e_ui**2
            accuracy_sum += accuracy

        learning_stats["losses_train"][epoch] = loss_sum
        learning_stats["accuracy_train"][epoch] = np.sqrt(accuracy_sum / len(train_set))

        # Now evaluating on validation data
        loss_validation_sum = 0
        accuracy_validation_sum = 0
        for user, song, listening_count in validation_set:
            listenings_hat = (
                (p[user].T @ q[song])
                + average_listening_count
                + b_user[user]
                + b_song[song]
            )

            e_ui = listening_count - listenings_hat

            # Loss
            loss = e_ui**2 + lbd * (
                np.linalg.norm(q[song]) ** 2 + np.linalg.norm(p[user]) ** 2
            )
            loss_validation_sum += loss

            # Accuracy
            accuracy = e_ui**2
            accuracy_validation_sum += accuracy

        learning_stats["losses_validation"][epoch] = loss_validation_sum
        learning_stats["accuracy_validation"][epoch] = np.sqrt(
            accuracy_validation_sum / len(validation_set)
        )

        print(
            f"Loss (train): {learning_stats['losses_train'][epoch]}, loss (validation): {learning_stats['losses_validation'][epoch]}"
        )
        print(
            f"Accuracy (train): {learning_stats['accuracy_train'][epoch]}, Accuracy (validation): {learning_stats['accuracy_validation'][epoch]}"
        )

    return (q, p, b_song, b_user), learning_stats
    