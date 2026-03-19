from random import Random

from app.modeling.types import CausalRecord


def train_validation_split(
    records: list[CausalRecord],
    *,
    test_ratio: float,
    seed: int,
) -> tuple[list[CausalRecord], list[CausalRecord]]:
    if not records:
        return [], []

    grouped = {
        0: [record for record in records if record.treatment == 0],
        1: [record for record in records if record.treatment == 1],
    }
    rng = Random(seed)
    train_records: list[CausalRecord] = []
    validation_records: list[CausalRecord] = []

    for group_records in grouped.values():
        rng.shuffle(group_records)
        split_index = max(1, int(len(group_records) * (1 - test_ratio)))
        split_index = min(split_index, max(len(group_records) - 1, 1))
        train_records.extend(group_records[:split_index])
        validation_records.extend(group_records[split_index:])

    if not validation_records and len(train_records) > 4:
        validation_records.append(train_records.pop())

    return train_records, validation_records

