import json
import re


def _normalize_quotes(s: str) -> str:
    # "умные" кавычки -> обычные
    s = s.replace("“", '"').replace("”", '"').replace("„", '"').replace("«", '"').replace("»", '"')
    s = s.replace("’", "'").replace("‘", "'")
    return s


def _try_load(candidate: str) -> dict:
    return json.loads(candidate)


def extract_json(text: str) -> dict:
    """
    Устойчивый извлекатель JSON из ответа модели:
    - нормализует кавычки
    - пытается json.loads целиком
    - если не вышло: ищет JSON-объекты по { ... } и пытается распарсить каждый
      (берём самый длинный валидный объект)
    """
    if text is None:
        raise ValueError("Empty text")

    text = _normalize_quotes(text.strip())

    # 1) напрямую
    try:
        return _try_load(text)
    except Exception:
        pass

    # 2) поиск всех кандидатов { ... } (не только от первой до последней)
    # Берём все подстроки, которые начинаются с { и заканчиваются на }
    # Попытаемся распарсить каждую, начиная с самых длинных
    candidates = []

    starts = [m.start() for m in re.finditer(r"\{", text)]
    ends = [m.start() for m in re.finditer(r"\}", text)]

    for i in starts:
        for j in ends:
            if j > i:
                candidates.append(text[i:j+1])

    # сортируем по длине (длиннее — вероятнее полный JSON)
    candidates.sort(key=len, reverse=True)

    last_err = None
    for cand in candidates[:50]:  # ограничим, чтобы не было квадратичной боли
        cand2 = cand.strip()

        # иногда модель оборачивает JSON в тройные кавычки/код-блоки — чистим слегка
        cand2 = cand2.replace("```json", "").replace("```", "").strip()

        try:
            obj = _try_load(cand2)
            if isinstance(obj, dict):
                return obj
        except Exception as e:
            last_err = e

    raise ValueError(f"Could not extract valid JSON. Last error: {last_err}")
