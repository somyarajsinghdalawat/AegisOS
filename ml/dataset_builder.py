from pathlib import Path
import json

import numpy as np


class DatasetBuilder:

    DATASET_PATH = Path("ml/models/process_dataset.npz")
    METADATA_PATH = Path("ml/models/process_dataset_metadata.json")

    def __init__(self, feature_names):
        self.feature_names = list(feature_names)
        self.samples = []

    def add(self, feature_vector):
        vector = np.asarray(
            feature_vector,
            dtype=float
        )

        if vector.ndim != 1:
            raise ValueError(
                "Feature vector must be one-dimensional."
            )

        if len(vector) != len(self.feature_names):
            raise ValueError(
                f"Expected {len(self.feature_names)} features, "
                f"got {len(vector)}."
            )

        if not np.all(np.isfinite(vector)):
            return False

        self.samples.append(vector)

        return True

    def add_many(self, feature_vectors):

        added = 0

        for vector in feature_vectors:

            if self.add(vector):
                added += 1

        return added

    def size(self):
        return len(self.samples)

    def build(self):

        if not self.samples:
            raise ValueError(
                "Dataset is empty."
            )

        return np.asarray(
            self.samples,
            dtype=float
        )

    def save(self, path=None):

        if path is None:
            path = self.DATASET_PATH

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        matrix = self.build()

        np.savez_compressed(
            path,
            X=matrix
        )

        metadata = {
            "feature_names": self.feature_names,
            "samples": int(matrix.shape[0]),
            "features": int(matrix.shape[1])
        }

        metadata_path = (
            path.parent /
            f"{path.stem}_metadata.json"
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4
            )

        print(
            f"Dataset saved to: {path}"
        )

        return path

    @classmethod
    def load(
        cls,
        path=None
    ):

        if path is None:
            path = cls.DATASET_PATH

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"Dataset not found: {path}"
            )

        data = np.load(
            path
        )

        if "X" not in data:

            raise ValueError(
                "Dataset does not contain X."
            )

        matrix = np.asarray(
            data["X"],
            dtype=float
        )

        metadata_path = (
            path.parent /
            f"{path.stem}_metadata.json"
        )

        feature_names = []

        if metadata_path.exists():

            with open(
                metadata_path,
                "r",
                encoding="utf-8"
            ) as file:

                metadata = json.load(file)

                feature_names = metadata.get(
                    "feature_names",
                    []
                )

        builder = cls(
            feature_names
        )

        builder.samples = [
            row.copy()
            for row in matrix
        ]

        return builder