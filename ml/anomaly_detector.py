from sklearn.ensemble import IsolationForest


class AnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(
            n_estimators=200,
            contamination="auto",
            random_state=42
        )

    def train(self, features):

        self.model.fit(features)

    def predict(self, features):

        predictions = self.model.predict(
            features
        )

        scores = self.model.decision_function(
            features
        )

        return predictions, scores