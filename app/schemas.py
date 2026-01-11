from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ScoreRequest:
    essay_id: Optional[str]
    essay_text: str
    reference_text_essay: str
    task_text: str
    essay_type: int

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "ScoreRequest":
        # минимальная “ручная” валидация, без pydantic (проще для старта)
        missing = [k for k in ["essay_text", "reference_text_essay", "task_text", "essay_type"] if k not in data]
        if missing:
            raise ValueError(f"Missing fields: {missing}")

        essay_type = data["essay_type"]
        if not isinstance(essay_type, int):
            raise ValueError("essay_type must be int")

        if essay_type not in (2, 3):
            raise ValueError("essay_type must be 2 or 3")

        return ScoreRequest(
            essay_id=str(data.get("essay_id")) if data.get("essay_id") is not None else None,
            essay_text=str(data["essay_text"]),
            reference_text_essay=str(data["reference_text_essay"]),
            task_text=str(data["task_text"]),
            essay_type=essay_type,
        )


def validate_score_output(out: Dict[str, Any]) -> None:
    # Диапазоны из задания:
    # K1: 0..1, K2: 0..3, K3: 0..2, K4: 0..1
    ranges = {"K1": (0, 1), "K2": (0, 3), "K3": (0, 2), "K4": (0, 1)}

    for k, (lo, hi) in ranges.items():
        if k not in out:
            raise ValueError(f"Missing field: {k}")
        if not isinstance(out[k], int):
            raise ValueError(f"{k} must be int")
        if not (lo <= out[k] <= hi):
            raise ValueError(f"{k} must be in [{lo}, {hi}]")

        exp_key = f"{k}_explanation"
        if exp_key not in out:
            raise ValueError(f"Missing field: {exp_key}")
        if not isinstance(out[exp_key], str) or not out[exp_key].strip():
            raise ValueError(f"{exp_key} must be non-empty string")


def validate_batch_input(items: Any, max_batch_size: int) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    if len(items) == 0:
        raise ValueError("items must be non-empty")
    if len(items) > max_batch_size:
        raise ValueError(f"batch too large: {len(items)} > {max_batch_size}")
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{i}] must be an object")
    return items
