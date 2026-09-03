from ml.dataset import DatasetLoader
from ml.features import FeatureEngineer
from ml.anomaly_detector import AnomalyDetector


loader = DatasetLoader()

data = loader.load_system_metrics()

print("Loaded records:", len(data))

features = FeatureEngineer.system_features(
    data
)

print("Feature records:", len(features))

detector = AnomalyDetector()

detector.train(features)

predictions, scores = detector.predict(
    features
)

print()
print("Anomaly results")
print("----------------")

for prediction, score in zip(
    predictions[-20:],
    scores[-20:]
):

    if prediction == -1:
        status = "ANOMALY"
    else:
        status = "NORMAL"

    print(
        f"{status:8} | score={score:.4f}"
    )