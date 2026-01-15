import os, json
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://edu.loginom.dev/lgi/rest/hackathone_service/hackathon01"

def main():
    user_id = os.getenv("VALIDATOR_USER_ID", "")
    if not user_id:
        raise RuntimeError("Нет VALIDATOR_USER_ID. Добавь в .env строку: VALIDATOR_USER_ID=...")

    sub_path = os.getenv("SUBMISSION_PATH", "data/submission.csv")
    df = pd.read_csv(sub_path, encoding="utf-8")

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "essay_id": str(r["essay_id"]),
            "K1": int(r["K1"]),
            "K2": int(r["K2"]),
            "K3": int(r["K3"]),
            "K4": int(r["K4"]),
        })

    payload = {
        "DataSet": {"Rows": rows},
        "Variables2": {"UserID": user_id},
    }

    resp = requests.post(URL, json=payload, timeout=180)
    print("HTTP:", resp.status_code)
    resp.raise_for_status()

    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # достаём Score
    score = data.get("DataSet", {}).get("Rows", [{}])[0].get("Score", None)
    msg = data.get("DataSet", {}).get("Rows", [{}])[0].get("AttemptsMessage", None)
    print("\nSCORE =", score)
    if msg:
        print("AttemptsMessage =", msg)

if __name__ == "__main__":
    main()
