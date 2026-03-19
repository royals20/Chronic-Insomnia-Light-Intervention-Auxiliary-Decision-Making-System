from dataclasses import dataclass, field


@dataclass(slots=True)
class FeatureSpec:
    name: str
    label: str


@dataclass(slots=True)
class RawCausalRow:
    patient_id: int
    patient_code: str
    anonymized_code: str
    treatment: int
    treatment_label: str
    outcome: float
    features: dict[str, float | None]


@dataclass(slots=True)
class CausalRecord:
    patient_id: int
    patient_code: str
    anonymized_code: str
    treatment: int
    treatment_label: str
    outcome: float
    features: dict[str, float]
    observed_feature_count: int


@dataclass(slots=True)
class CausalDataset:
    total_patients: int
    records: list[CausalRecord]
    selected_features: list[FeatureSpec]
    feature_coverage: list[dict]
    treatment_name: str
    control_name: str
    outcome_name: str
    dropped_records: list[dict]
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

