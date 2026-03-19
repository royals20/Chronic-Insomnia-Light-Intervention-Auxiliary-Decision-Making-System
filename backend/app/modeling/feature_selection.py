from statistics import mean

from app.modeling.types import FeatureSpec, RawCausalRow


def _variance(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    avg = mean(values)
    return sum((value - avg) ** 2 for value in values) / len(values)


def summarize_feature_coverage(
    raw_rows: list[RawCausalRow],
    candidate_features: list[FeatureSpec],
) -> list[dict]:
    total = max(len(raw_rows), 1)
    summary: list[dict] = []
    for spec in candidate_features:
        values = [
            row.features.get(spec.name)
            for row in raw_rows
            if row.features.get(spec.name) is not None
        ]
        available_count = len(values)
        summary.append(
            {
                "feature_name": spec.name,
                "feature_label": spec.label,
                "available_count": available_count,
                "missing_count": total - available_count,
                "coverage_rate": round(available_count / total * 100, 2),
                "variance": round(_variance([float(value) for value in values]), 6),
            }
        )
    return summary


def select_features(
    raw_rows: list[RawCausalRow],
    candidate_features: list[FeatureSpec],
    *,
    max_features: int,
    min_feature_coverage: float,
) -> tuple[list[FeatureSpec], list[dict]]:
    coverage_summary = summarize_feature_coverage(raw_rows, candidate_features)
    coverage_by_name = {
        item["feature_name"]: item
        for item in coverage_summary
    }
    selected = [
        spec
        for spec in candidate_features
        if coverage_by_name[spec.name]["coverage_rate"] >= min_feature_coverage * 100
        and coverage_by_name[spec.name]["variance"] > 0
    ]

    if not selected:
        selected = [
            spec
            for spec in candidate_features
            if coverage_by_name[spec.name]["coverage_rate"] >= 40
            and coverage_by_name[spec.name]["variance"] > 0
        ]

    selected = selected[:max_features]
    selected_names = {spec.name for spec in selected}
    for item in coverage_summary:
        item["selected"] = item["feature_name"] in selected_names
    return selected, coverage_summary

