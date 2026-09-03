class RiskEngine:

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=100.0):

        return max(
            minimum,
            min(
                float(value),
                maximum
            )
        )

    def calculate(
        self,
        features,
        anomaly_score,
        prediction
    ):

        risk = 0.0

        # =================================================
        # CPU RISK
        # =================================================

        cpu_mean = features["cpu_mean"]
        cpu_max = features["cpu_max"]
        cpu_slope = features["cpu_slope"]

        if cpu_mean >= 80:
            risk += 25

        elif cpu_mean >= 60:
            risk += 18

        elif cpu_mean >= 40:
            risk += 10

        elif cpu_mean >= 25:
            risk += 5

        # Very high instantaneous CPU.
        if cpu_max >= 90:
            risk += 15

        elif cpu_max >= 75:
            risk += 8

        # Sustained CPU growth.
        if cpu_slope >= 5:
            risk += 15

        elif cpu_slope >= 2:
            risk += 8

        # =================================================
        # MEMORY RISK
        # =================================================

        memory_mean = features["memory_mean"]
        memory_max = features["memory_max"]
        memory_slope = features["memory_slope"]

        # Memory thresholds are deliberately conservative.
        if memory_mean >= 1000:
            risk += 20

        elif memory_mean >= 500:
            risk += 12

        elif memory_mean >= 250:
            risk += 5

        if memory_max >= 2000:
            risk += 15

        elif memory_max >= 1000:
            risk += 8

        # Memory growth is particularly important.
        if memory_slope >= 10:
            risk += 20

        elif memory_slope >= 5:
            risk += 12

        elif memory_slope >= 2:
            risk += 5

        # =================================================
        # THREAD RISK
        # =================================================

        thread_slope = features["thread_slope"]

        if thread_slope >= 10:
            risk += 15

        elif thread_slope >= 5:
            risk += 10

        elif thread_slope >= 2:
            risk += 5

        # =================================================
        # ML ANOMALY
        # =================================================

        if prediction == -1:

            # Convert Isolation Forest's score
            # into a bounded contribution.
            #
            # More negative = more unusual.

            anomaly_strength = (
                max(
                    0.0,
                    min(
                        1.0,
                        (-anomaly_score) / 0.20
                    )
                )
            )

            risk += (
                anomaly_strength * 20
            )

        # =================================================
        # Final normalization
        # =================================================

        risk = self._clamp(
            risk
        )

        # =================================================
        # Risk level
        # =================================================

        if risk >= 80:

            level = "CRITICAL"

        elif risk >= 60:

            level = "HIGH"

        elif risk >= 40:

            level = "MEDIUM"

        elif risk >= 20:

            level = "LOW"

        else:

            level = "NORMAL"

        return {
            "risk": round(risk, 2),
            "level": level
        }