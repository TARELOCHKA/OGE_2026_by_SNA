import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import os
print("TOKEN LOADED:", bool(os.getenv("GIGACHAT_TOKEN")))


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import os
import pandas as pd

from app import create_app
from app.schemas import ScoreRequest
from app.scoring import score_essay


DATA_DIR = Path("data")
IN_PATH = DATA_DIR / "inputs_for_scoring.csv"
OUT_PATH = DATA_DIR / "submission.csv"

def main():
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Not found: {IN_PATH}. Run scripts/prepare_inputs.py first.")

    # Обычно валидатору нужны только баллы
    only_scores = os.getenv("SUBMISSION_ONLY_SCORES", "1") == "1"

    df = pd.read_csv(IN_PATH, encoding="utf-8")

    app = create_app()
    rows = []

    with app.app_context():
        for _, r in df.iterrows():
            req = ScoreRequest(
                essay_id=str(r["essay_id"]),
                essay_text=str(r["essay_text"]),
                reference_text_essay=str(r["reference_text_essay"]),
                task_text=str(r["task_text"]),
                essay_type=int(r["essay_type"]),
            )

            out = score_essay(req)

            row = {
                "essay_id": str(out["essay_id"]),
                "K1": int(out["K1"]),
                "K2": int(out["K2"]),
                "K3": int(out["K3"]),
                "K4": int(out["K4"]),
            }

            if not only_scores:
                row.update({
                    "K1_explanation": out["K1_explanation"],
                    "K2_explanation": out["K2_explanation"],
                    "K3_explanation": out["K3_explanation"],
                    "K4_explanation": out["K4_explanation"],
                })

            rows.append(row)

    sub = pd.DataFrame(rows)
    sub.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"Saved: {OUT_PATH} rows={len(sub)}")

if __name__ == "__main__":
    main()
