from typing import Dict
from flask import current_app

from .schemas import ScoreRequest, validate_score_output
from .prompting import build_prompt, PROMPT_VERSION
from .json_utils import extract_json
from .gigachat_client import GigaChatClient
from .repair import build_repair_prompt

def normalize_keys(data: dict) -> dict:
    """
    Нормализует ключи JSON: кириллица -> латиница, различные варианты написания.
    Также нормализует вложенные структуры и explanation ключи.
    """
    if not isinstance(data, dict):
        return data

    # Маппинг кириллических символов на латинские для ключей
    cyrillic_to_latin = {
        "К": "K", "к": "k",
    }

    # Расширенный маппинг: кириллица -> латиница + варианты написания
    key_mapping = {
        "К1": "K1", "к1": "K1",
        "К2": "K2", "к2": "K2",
        "К3": "K3", "к3": "K3",
        "К4": "K4", "к4": "K4",
        "К1_explanation": "K1_explanation", "к1_explanation": "K1_explanation",
        "К1 explanation": "K1_explanation", "к1 explanation": "K1_explanation",
        "К2_explanation": "K2_explanation", "к2_explanation": "K2_explanation",
        "К2 explanation": "K2_explanation", "к2 explanation": "K2_explanation",
        "К3_explanation": "K3_explanation", "к3_explanation": "K3_explanation",
        "К3 explanation": "K3_explanation", "к3 explanation": "K3_explanation",
        "К4_explanation": "K4_explanation", "к4_explanation": "K4_explanation",
        "К4 explanation": "K4_explanation", "к4 explanation": "K4_explanation",
    }

    out = {}
    for k, v in data.items():
        # Сначала проверяем точное совпадение
        normalized_key = key_mapping.get(k, k)

        # Если не нашли точное совпадение, пытаемся нормализовать через замену кириллицы
        if normalized_key == k:
            # Заменяем кириллические буквы на латинские в ключе
            temp_key = k
            for cyr, lat in cyrillic_to_latin.items():
                temp_key = temp_key.replace(cyr, lat)

            # Если после замены ключ изменился и соответствует паттерну K1-K4, используем его
            if temp_key != k:
                # Проверяем, соответствует ли ключ паттерну
                import re
                if re.match(r'^K[1-4](_explanation| explanation)?$', temp_key, re.IGNORECASE):
                    # Нормализуем регистр
                    if '_explanation' in temp_key.lower() or ' explanation' in temp_key.lower():
                        num = re.search(r'[1-4]', temp_key)
                        if num:
                            normalized_key = f"K{num.group()}_explanation"
                    else:
                        num = re.search(r'[1-4]', temp_key)
                        if num:
                            normalized_key = f"K{num.group()}"

        # Если это объяснение, но ключ неправильный, пытаемся найти правильный
        if normalized_key == k and ("_explanation" in k.lower() or "explanation" in k.lower()):
            # Проверяем, какой это K (1-4)
            import re
            match = re.search(r'[кКkK][1-4]', k, re.IGNORECASE)
            if match:
                num = match.group()[-1]  # Берем цифру
                normalized_key = f"K{num}_explanation"

        # Нормализуем значение, если это словарь (рекурсивно)
        if isinstance(v, dict):
            v = normalize_keys(v)
        elif isinstance(v, list):
            v = [normalize_keys(item) if isinstance(item, dict) else item for item in v]

        out[normalized_key] = v

    return out



NEEDED_KEYS = {
    "K1", "K1_explanation",
    "K2", "K2_explanation",
    "K3", "K3_explanation",
    "K4", "K4_explanation",
}


def _get_client() -> GigaChatClient:
    cfg = current_app.config
    return GigaChatClient(
        auth_token=cfg.get("GIGACHAT_TOKEN", ""),
        timeout=cfg.get("REQUEST_TIMEOUT_SEC", 60),
        verify_ssl=False,
    )


def _has_all_keys(data: dict) -> bool:
    return isinstance(data, dict) and NEEDED_KEYS.issubset(set(data.keys()))


def score_essay(req: ScoreRequest) -> Dict:
    """
    Реальный скоринг:
    - строим промпт
    - вызываем GigaChat
    - парсим JSON
    - если JSON сломан ИЛИ нет ключей -> делаем repair-запрос
    - валидируем диапазоны/поля
    - 1 ретрай если всё равно плохо
    """
    client = _get_client()
    prompt = build_prompt(req)

    model_name = current_app.config.get("GIGACHAT_MODEL", "GigaChat")
    temperature = float(current_app.config.get("TEMPERATURE", 0.0))
    max_tokens = int(current_app.config.get("MAX_TOKENS", 900))

    last_err = None

    for attempt in range(2):
        try:
            repaired = False

            raw = client.chat_completion(
                model=model_name,
                prompt=prompt if attempt == 0 else (
                    prompt
                    + "\n\nВАЖНО: прошлый ответ был невалидным/неполным. "
                      "Верни ТОЛЬКО валидный JSON строго по схеме, все поля обязательны."
                ),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # 1) Пытаемся распарсить
            data = None
            try:
                data = normalize_keys(extract_json(raw))
            except Exception:
                data = None

            # 2) Если не распарсилось ИЛИ распарсилось, но не хватает ключей -> repair
            if not _has_all_keys(data):
                repaired = True

                # REPAIR #1: починить прошлый ответ
                fixed_raw = client.chat_completion(
                    model=model_name,
                    prompt=build_repair_prompt(raw),
                    temperature=0.0,
                    max_tokens=600,
                )

                try:
                    data = normalize_keys(extract_json(fixed_raw))
                except Exception:
                    data = None

                # REPAIR #2: ультра-жёсткий формат (если repair #1 не помог)
                if not _has_all_keys(data):
                    hard_repair_prompt = (
                        "Верни ТОЛЬКО валидный JSON-объект. "
                        "Ключи и строки только в двойных кавычках. "
                        "Никакого текста, только JSON.\n"
                        "Схема:\n"
                        "{"
                        "\"K1\": <int>, \"K1_explanation\": \"...\", "
                        "\"K2\": <int>, \"K2_explanation\": \"...\", "
                        "\"K3\": <int>, \"K3_explanation\": \"...\", "
                        "\"K4\": <int>, \"K4_explanation\": \"...\""
                        "}\n\n"
                        "Твой предыдущий ответ (исправь его в JSON):\n"
                        f"{raw}"
                    )
                    fixed_raw2 = client.chat_completion(
                        model=model_name,
                        prompt=hard_repair_prompt,
                        temperature=0.0,
                        max_tokens=600,
                    )

                    try:
                        data = normalize_keys(extract_json(fixed_raw2))
                    except Exception:
                        data = None



            # 3) Если даже после repair нет ключей — отдаём понятную ошибку
            if not _has_all_keys(data):
                missing = sorted(list(NEEDED_KEYS - set(data.keys()))) if isinstance(data, dict) else sorted(list(NEEDED_KEYS))
                raise ValueError(
                    f"LLM JSON missing keys: {missing}. "
                    f"Raw (truncated)={str(raw)[:300]}"
                )

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
