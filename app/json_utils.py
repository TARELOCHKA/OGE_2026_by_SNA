import json

def extract_json(text: str) -> dict:
    """
    Пытаемся распарсить как JSON.
    Если модель прислала лишний текст — вырезаем по первой '{' и последней '}'.
    """
    text = text.strip()

    # 1) пробуем напрямую
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) вырезаем по скобкам
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    candidate = text[start:end+1]
    return json.loads(candidate)
