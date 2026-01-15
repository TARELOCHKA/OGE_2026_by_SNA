import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def main():
    score_str = os.getenv("EXTERNAL_SCORE", "")
    if not score_str:
        raise RuntimeError("Set EXTERNAL_SCORE env var, e.g. EXTERNAL_SCORE=0.60215")

    score = float(score_str)
    mae = (1.0 / score) - 1.0  # score = 1/(1+MAE)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "score": score,
        "mae": mae,
        "prompt_version": os.getenv("PROMPT_VERSION", "unknown"),
        "temperature": float(os.getenv("TEMPERATURE", "0.0")),
        "model": os.getenv("GIGACHAT_MODEL", "GigaChat"),
        "submission_file": os.getenv("SUBMISSION_PATH", "data/submission.csv"),
        "attempts_note": os.getenv("ATTEMPTS_NOTE", ""),
    }

    out_dir = Path("experiments")
    out_dir.mkdir(exist_ok=True)

    name = f"exp_{record['prompt_version']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out_path = out_dir / name
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Saved:", out_path)
    print("Score =", score)
    print("MAE   =", mae)

if __name__ == "__main__":
    main()
