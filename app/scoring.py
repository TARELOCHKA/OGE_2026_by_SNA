from typing import Dict
from flask import current_app

from .schemas import ScoreRequest, validate_score_output
from .prompting import build_prompt, PROMPT_VERSION
from .json_utils import extract_json
from .gigachat_client import GigaChatClient
from .repair import build_repair_prompt


def _get_client() -> GigaChatClient:
    cfg = current_app.config
    return GigaChatClient(
        auth_token=cfg.get("GIGACHAT_TOKEN", ""),
        timeout=cfg.get("REQUEST_TIMEOUT_SEC", 60),
        verify_ssl=False,  # у вас так надо из-за SSL
    )


def score_essay(req: ScoreRequest) -> Dict:
    """
    Реальный скоринг:
    - строим промпт
    - вызываем GigaChat
    - парсим JSON
    - если JSON сломан -> делаем отдельный repair-запрос
    - валидируем диапазоны/поля
    - 1 ретрай если всё равно плохо
    """
    client = _get_client()
    prompt = build_prompt(req)

    model_name = current_app.config.get("GIGACHAT_MODEL", "GigaChat")
    temperature = float(current_app.config.get("TEMPERATURE", 0.0))  # для метрик лучше 0.0
    max_tokens = int(current_app.config.get("MAX_TOKENS", 900))

    last_err = None

    for attempt in range(2):  # 0 — основной, 1 — ретрай
        try:
            repaired = False

            raw = client.chat_completion(
                model=model_name,
                prompt=prompt if attempt == 0 else (
                    prompt
                    + "\n\nВАЖНО: прошлый ответ был невалидным JSON. "
                      "Верни ТОЛЬКО валидный JSON по схеме (двойные кавычки, без markdown)."
                ),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 1) Пытаемся распарсить как есть
            try:
                data = extract_json(raw)
            except Exception:
                # 2) Если не получилось — просим модель “починить” свой же ответ
                repaired = True
                fixed_raw = client.chat_completion(
                    model=model_name,
                    prompt=build_repair_prompt(raw),
                    temperature=0.0,
                    max_tokens=600,
                )
                data = extract_json(fixed_raw)

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
                    "json_repair": repaired,
                },
            }

            validate_score_output(out)
            return out

        except Exception as e:
            last_err = e

    raise RuntimeError(f"LLM scoring failed after retry: {last_err}")
