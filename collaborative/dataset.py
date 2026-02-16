from pathlib import Path
import numpy as np


def load(max_size: int) -> tuple[np.ndarray, dict[str, int], dict[str, int]]:
    """
    Loads the max_size first triplets of `../train_triplets`.
    """
    # Maps users and songs to their unique index for further referencing as matrix index
    USER_MAPPING: dict[str, int] = {}
    SONG_MAPPING: dict[str, int] = {}

    # It's a list of tuples (user, song, listening count)
    dataset_triplet_dtype = np.dtype(
        [
            ("User index", np.uint32),
            ("Song index", np.uint32),
            ("Listening count", np.float64),
        ]
    )
    dataset_raw: list[tuple[int, int, int]] = []
    with open(
        (Path(__file__).parent / "../train_triplets.txt").resolve(), "r"
    ) as dataset_file:
        for line in dataset_file:
            user_id, song_id, listening_count = line.split("\t")

            dataset_raw.append(
                (
                    USER_MAPPING.setdefault(user_id, len(USER_MAPPING)),
                    SONG_MAPPING.setdefault(song_id, len(SONG_MAPPING)),
                    int(listening_count),
                )
            )

            if len(dataset_raw) >= max_size:
                break

    dataset = np.array(dataset_raw, dtype=dataset_triplet_dtype)

    # print(
    #     f"Parsed {len(SONG_MAPPING)} and {len(USER_MAPPING)} users, for a total of {len(dataset)} triplets."
    # )

    return (dataset, USER_MAPPING, SONG_MAPPING)


def normalize(dataset: np.ndarray) -> np.ndarray:
    """
    Modifies the dataset in place (and returns it too).
    """
    dataset["Listening count"] = (
        dataset["Listening count"] - dataset["Listening count"].mean()
    ) / dataset["Listening count"].std()

    # print(dataset.dtype, dataset.shape)
    # print(dataset["Listening count"])

    return dataset