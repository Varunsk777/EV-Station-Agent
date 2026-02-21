class WeightNormalizer:

    @staticmethod
    def normalize(weights: dict) -> dict:
        total = sum(weights.values())

        if total == 0:
            equal = 1 / len(weights)
            return {k: equal for k in weights}

        return {k: v / total for k, v in weights.items()}

    @staticmethod
    def enforce_floor(weights: dict, min_weight: float) -> dict:
        adjusted = {
            k: max(v, min_weight) for k, v in weights.items()
        }

        return WeightNormalizer.normalize(adjusted)