def build_repair_prompt(bad_text: str) -> str:
    return f"""
Сделай из текста валидный JSON строго по схеме.

Правила:
- Верни ТОЛЬКО JSON-объект, без markdown.
- Двойные кавычки для ключей и строк.
- Поля ровно: K1, K1_explanation, K2, K2_explanation, K3, K3_explanation, K4, K4_explanation
- K1..K4 — целые числа.

Текст для исправления:
{bad_text}
""".strip()
