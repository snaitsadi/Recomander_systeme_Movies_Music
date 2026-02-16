import json
import numpy as np

from .dataset import load as load_dataset, normalize
from .model import init, save
from .train import train

DATASET_SIZE = 4_000_000
l = 40

if __name__ == "__main__":
    dataset, USER_MAPPING, SONG_MAPPING = load_dataset(DATASET_SIZE)
    dataset = normalize(dataset)

    print("Dataset ready")

    training_set_size = int(len(dataset) * 0.66)

    dataset_perm = np.random.permutation(len(dataset))
    dataset_shuffled = dataset[dataset_perm]

    train_set = dataset_shuffled[:training_set_size]
    validation_set = dataset_shuffled[training_set_size:]

    model, stats = train(
        l,
        0.001,
        0.0005,
        200,
        train_set,
        validation_set,
        init(len(SONG_MAPPING), len(USER_MAPPING)),
    )

    print("Training done")

    save(f"model-{DATASET_SIZE}-{l}", model)
    with open("model-{DATASET_SIZE}-{l}_stats.json", "w") as f:
        json.dump(stats, f)

    print("Model saved")
