from .schemas import ScoreRequest

PROMPT_VERSION = "v1.0"

def build_prompt(req: ScoreRequest) -> str:
    # Важно: требуем строгий JSON
    return f"""
Оцени ученическое сочинение ОГЭ по русскому языку по критериям K1-K4.

Входные данные:
essay_type: {req.essay_type}
task_text: {req.task_text}

reference_text_essay:
{req.reference_text_essay}

essay_text:
{req.essay_text}

Требования к ответу:
- Верни ТОЛЬКО валидный JSON без Markdown и без пояснений вне JSON.
- Поля строго такие: K1, K1_explanation, K2, K2_explanation, K3, K3_explanation, K4, K4_explanation.
- Баллы:
  - K1: 0..1
  - K2: 0..3
  - K3: 0..2
  - K4: 0..1
- Объяснения: 2-5 предложений, по делу, со ссылкой на признаки из текста.
- Если не уверен — ставь минимальный балл и объясни, чего не хватило.

Пример формата (не копируй текст, это только пример структуры):
{{
  "K1": 1,
  "K1_explanation": "...",
  "K2": 2,
  "K2_explanation": "...",
  "K3": 1,
  "K3_explanation": "...",
  "K4": 1,
  "K4_explanation": "..."
}}
""".strip()
