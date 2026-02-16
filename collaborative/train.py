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