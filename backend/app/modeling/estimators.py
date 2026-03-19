from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from statistics import mean

from app.modeling.types import CausalRecord


class BaseCausalEstimator(ABC):
    backend_name = "base"

    @abstractmethod
    def fit(self, records: list[CausalRecord], feature_names: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def effect(self, records: list[CausalRecord]) -> list[float]:
        raise NotImplementedError

    def average_treatment_effect(self, records: list[CausalRecord]) -> float:
        effects = self.effect(records)
        if not effects:
            return 0.0
        return round(mean(effects), 4)


class FallbackNearestNeighborCausalEstimator(BaseCausalEstimator):
    backend_name = "fallback_nearest_neighbor"

    def __init__(self, *, neighbor_count: int = 5) -> None:
        self.neighbor_count = neighbor_count
        self.feature_names: list[str] = []
        self.train_records: list[CausalRecord] = []
        self.feature_means: dict[str, float] = {}
        self.feature_stds: dict[str, float] = {}

    def fit(self, records: list[CausalRecord], feature_names: list[str]) -> None:
        if len(records) < 6:
            raise ValueError("可用于训练的样本过少，无法完成演示级因果评估。")

        treated_count = sum(1 for record in records if record.treatment == 1)
        control_count = len(records) - treated_count
        if treated_count == 0 or control_count == 0:
            raise ValueError("处理组或对照组为空，无法进行因果获益评估。")

        self.train_records = records
        self.feature_names = feature_names
        for feature_name in feature_names:
            values = [record.features[feature_name] for record in records]
            avg = mean(values)
            variance = sum((value - avg) ** 2 for value in values) / max(len(values), 1)
            self.feature_means[feature_name] = avg
            self.feature_stds[feature_name] = sqrt(variance) or 1.0

    def _distance(self, left: CausalRecord, right: CausalRecord) -> float:
        total = 0.0
        for feature_name in self.feature_names:
            scale = self.feature_stds.get(feature_name, 1.0) or 1.0
            total += ((left.features[feature_name] - right.features[feature_name]) / scale) ** 2
        return sqrt(total)

    def _weighted_outcome(
        self,
        target: CausalRecord,
        *,
        treatment_group: int,
    ) -> float:
        pool = [
            record
            for record in self.train_records
            if record.treatment == treatment_group and record.patient_id != target.patient_id
        ]
        if not pool:
            pool = [
                record
                for record in self.train_records
                if record.treatment == treatment_group
            ]
        if not pool:
            return mean(record.outcome for record in self.train_records)

        ranked = sorted(pool, key=lambda record: self._distance(target, record))
        selected = ranked[: self.neighbor_count]
        numerator = 0.0
        denominator = 0.0
        for record in selected:
            distance = self._distance(target, record)
            weight = 1.0 / (distance + 1e-6)
            numerator += record.outcome * weight
            denominator += weight
        return numerator / denominator if denominator else mean(record.outcome for record in selected)

    def effect(self, records: list[CausalRecord]) -> list[float]:
        if not records:
            return []

        effects: list[float] = []
        for record in records:
            treated_outcome = self._weighted_outcome(record, treatment_group=1)
            control_outcome = self._weighted_outcome(record, treatment_group=0)
            effects.append(round(treated_outcome - control_outcome, 4))
        return effects


class EconmlCausalForestAdapter(BaseCausalEstimator):
    backend_name = "econml_causal_forest"

    def __init__(self) -> None:
        import numpy as np
        from econml.dml import CausalForestDML
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

        self.np = np
        self.model = CausalForestDML(
            model_y=RandomForestRegressor(
                n_estimators=80,
                min_samples_leaf=5,
                random_state=20260319,
            ),
            model_t=RandomForestClassifier(
                n_estimators=80,
                min_samples_leaf=5,
                random_state=20260319,
            ),
            n_estimators=120,
            min_samples_leaf=5,
            discrete_treatment=True,
            random_state=20260319,
        )
        self.feature_names: list[str] = []

    def fit(self, records: list[CausalRecord], feature_names: list[str]) -> None:
        self.feature_names = feature_names
        X = self.np.array(
            [[record.features[name] for name in feature_names] for record in records],
            dtype=float,
        )
        T = self.np.array([record.treatment for record in records], dtype=int)
        Y = self.np.array([record.outcome for record in records], dtype=float)
        self.model.fit(Y, T, X=X)

    def effect(self, records: list[CausalRecord]) -> list[float]:
        if not records:
            return []
        X = self.np.array(
            [[record.features[name] for name in self.feature_names] for record in records],
            dtype=float,
        )
        return [round(float(value), 4) for value in self.model.effect(X)]


def build_causal_estimator() -> BaseCausalEstimator:
    try:
        return EconmlCausalForestAdapter()
    except Exception:
        return FallbackNearestNeighborCausalEstimator()

