import pandas as pd
from pathlib import Path

_DATA = None

def load_inputs(path: str = "data/inputs_for_scoring.csv"):
    global _DATA
    if _DATA is None:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Not found: {path}. Run scripts/prepare_inputs.py first.")
        _DATA = pd.read_csv(p)
        _DATA["essay_id"] = _DATA["essay_id"].astype(str)
    return _DATA

def get_by_essay_id(essay_id: str):
    df = load_inputs()
    row = df[df["essay_id"] == str(essay_id)]
    if row.empty:
        return None
    r = row.iloc[0].to_dict()
    # оставим только нужное
    return {
        "essay_id": str(r["essay_id"]),
        "essay_type": int(r["essay_type"]),
        "task_text": str(r["task_text"]),
        "reference_text_essay": str(r["reference_text_essay"]),
        "essay_text": str(r["essay_text"]),
    }
