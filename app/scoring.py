from typing import Dict
from flask import current_app

from .schemas import ScoreRequest, validate_score_output
from .prompting import build_prompt, PROMPT_VERSION
from .json_utils import extract_json
from .gigachat_client import GigaChatClient


def _get_client() -> GigaChatClient:
    cfg = current_app.config
    return GigaChatClient(
        auth_token=cfg.get("GIGACHAT_TOKEN", ""),
        timeout=cfg.get("REQUEST_TIMEOUT_SEC", 60),
        verify_ssl=False,
    )


def score_essay(req: ScoreRequest) -> Dict:
    """
    Реальный скоринг:
    - строим промпт
    - вызываем GigaChat
    - парсим JSON
    - валидируем диапазоны/поля
    - 1 ретрай если формат сломан
    """
    client = _get_client()
    prompt = build_prompt(req)

    model_name = current_app.config.get("GIGACHAT_MODEL", "GigaChat")  # можно поменять на Lite/Max и т.п.
    temperature = float(current_app.config.get("TEMPERATURE", 0.2))
    max_tokens = int(current_app.config.get("MAX_TOKENS", 900))

    last_err = None
    for attempt in range(2):  # 0 — основной, 1 — ретрай
        try:
            raw = client.chat_completion(
                model=model_name,
                prompt=prompt if attempt == 0 else (
                    prompt + "\n\nВажно: твой прошлый ответ был невалидным. Верни только JSON строго по схеме."
                ),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            data = extract_json(raw)

            out = {
                "essay_id": req.essay_id,
                "K1": int(data["K1"]),
                "K1_explanation": str(data["K1_explanation"]),
                "K2": int(data["K2"]),
                "K2_explanation": str(data["K2_explanation"]),
                "K3": int(data["K3"]),
                "K3_explanation": str(data["K3_explanation"]),
                "K4": int(data["K4"]),
                "K4_explanation": str(data["K4_explanation"]),
                "meta": {
                    "model": model_name,
                    "prompt_version": PROMPT_VERSION,
                    "attempt": attempt,
                    "essay_type": req.essay_type,
                }
            }

            validate_score_output(out)
            return out

        except Exception as e:
            last_err = e

    raise RuntimeError(f"LLM scoring failed after retry: {last_err}")
