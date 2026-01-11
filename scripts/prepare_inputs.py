import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

def main():
    essays = pd.read_csv(DATA_DIR / "essays.csv")

    refs = []
    for i in range(1, 9):  # 1..8 включительно
        refs.append(pd.read_csv(DATA_DIR / f"reference_text{i}.csv"))
    refs = pd.concat(refs, ignore_index=True)

    df = essays.merge(refs, on="reference_text_id", how="left")

    df = df.rename(columns={
        "task": "task_text",
        "reference_text": "reference_text_essay",
    })

    need_cols = ["essay_id", "essay_type", "task_text", "reference_text_essay", "essay_text"]
    df = df[need_cols]

    out = DATA_DIR / "inputs_for_scoring.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    print(f"Saved: {out} rows={len(df)}")

if __name__ == "__main__":
    main()
