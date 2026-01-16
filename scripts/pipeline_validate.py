import os
import json
from pathlib import Path
import subprocess
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


import pandas as pd
import requests
from dotenv import load_dotenv
from clearml import Task

# Подтягиваем .env (важно для токенов/параметров)
load_dotenv()

URL_VALIDATOR = "https://edu.loginom.dev/lgi/rest/hackathone_service/hackathon01"

DATA_DIR = Path("data")
SUBMISSION_PATH = DATA_DIR / "submission.csv"
VALIDATOR_RESPONSE_PATH = DATA_DIR / "validator_response.json"


def score_to_mae(score: float) -> float:
    # score = 1/(1+MAE) => MAE = 1/score - 1
    return (1.0 / score) - 1.0




def generate_submission():
    """
    Генерит data/submission.csv, вызывая ваш скрипт как отдельную команду.
    Это надёжнее, чем импортировать scripts.make_submission как модуль.
    """
    cmd = [sys.executable, "scripts/make_submission.py"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        raise RuntimeError(f"make_submission failed with code={res.returncode}")



def send_to_validator(submission_path: Path) -> dict:
    user_id = os.getenv("VALIDATOR_USER_ID", "")
    if not user_id:
        raise RuntimeError("VALIDATOR_USER_ID is not set in .env")

    df = pd.read_csv(submission_path, encoding="utf-8")

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

    # --- Session + Retry ---
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.0,  # 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=1, pool_maxsize=1)
    session.mount("https://", adapter)

    headers = {
        "Content-Type": "application/json",
        "Connection": "close",  # часто лечит EOF
        "User-Agent": "OGE-Scoring/1.0",
    }

    # Иногда EOF решается verify=False (как у вас с GigaChat)
    verify_ssl = os.getenv("VALIDATOR_VERIFY_SSL", "1") == "1"

    last_err = None
    for attempt in range(1, 6):
        try:
            resp = session.post(
                URL_VALIDATOR,
                json=payload,
                headers=headers,
                timeout=180,
                verify=verify_ssl,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            # маленькая пауза и повтор
            time.sleep(1.5 * attempt)

    raise RuntimeError(f"Validator request failed after retries: {last_err}")



def main():
    # --- параметры эксперимента ---
    prompt_version = os.getenv("PROMPT_VERSION", "unknown")
    model = os.getenv("GIGACHAT_MODEL", "GigaChat")
    temperature = float(os.getenv("TEMPERATURE", "0.0"))

    # Важно: попытки ограничены. Не запускайте лишний раз.
    # --- стартуем ClearML task ---
    task = Task.init(
        project_name="OGE Essay Scoring",
        task_name=f"Pipeline validation {prompt_version}"
    )
    task.connect({
        "prompt_version": prompt_version,
        "model": model,
        "temperature": temperature,
    })
    logger = task.get_logger()

    # --- 1) генерим submission ---
    generate_submission()

    if not SUBMISSION_PATH.exists():
        raise FileNotFoundError(f"submission not found: {SUBMISSION_PATH}")

    # --- 2) отправляем в валидатор ---
    response = send_to_validator(SUBMISSION_PATH)

    # сохраним ответ валидатора как файл
    VALIDATOR_RESPONSE_PATH.write_text(
        json.dumps(response, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # --- 3) достаём score/attempts ---
    score = response.get("DataSet", {}).get("Rows", [{}])[0].get("Score", None)
    attempts_msg = response.get("DataSet", {}).get("Rows", [{}])[0].get("AttemptsMessage", "")

    if score is None:
        raise RuntimeError(f"Validator response has no Score: {response}")

    score = float(score)
    mae = score_to_mae(score)

    # --- 4) логируем метрики ---
    logger.report_scalar("external", "Score", score, iteration=0)
    logger.report_scalar("external", "MAE", mae, iteration=0)

    # attempts как текст в параметрах
    task.connect({"attempts_message": attempts_msg})

    # --- 5) прикладываем артефакты ---
    task.upload_artifact("submission.csv", str(SUBMISSION_PATH))
    task.upload_artifact("validator_response.json", str(VALIDATOR_RESPONSE_PATH))

    print("✅ DONE")
    print("Score =", score)
    print("MAE   =", mae)
    if attempts_msg:
        print("Attempts:", attempts_msg)


if __name__ == "__main__":
    main()
