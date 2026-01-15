Создай `README.md` в корне проекта и вставь:

````md
# OGE Essay Scoring (GigaChat + Flask)

Сервис для автоматической проверки сочинений ОГЭ по русскому языку.
Поддерживает оценивание:
- одного эссе (`/score_one`)
- пачки эссе (`/score_batch`)
- веб-интерфейс для демонстрации (`/ui`)

Качество оценивается внешним валидатором Loginom (score = 1/(1+MAE)).

---

## Содержание
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Как пользоваться UI](#как-пользоваться-ui)
- [Как прогнать все эссе и получить submission.csv](#как-прогнать-все-эссе-и-получить-submissioncsv)
- [Как отправить submission в валидатор Loginom и получить Score/MAE](#как-отправить-submission-в-валидатор-loginom-и-получить-scoremae)
- [Локальный логер экспериментов](#локальный-логер-экспериментов)
- [API](#api)
- [Структура проекта](#структура-проекта)
- [Частые проблемы](#частые-проблемы)

---

## Требования
- Python 3.10+ (рекомендуется 3.11/3.12)
- Windows PowerShell / Git Bash
- Доступ к токену GigaChat

---

## Быстрый старт

### 1) Установка зависимостей
Создать и активировать виртуальное окружение:

**PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
````

### 2) Создать `.env` (в корне проекта)

Файл `.env` НЕ коммитится (он в `.gitignore`).

Пример `.env`:

```env
GIGACHAT_TOKEN=YOUR_TOKEN_HERE
GIGACHAT_MODEL=GigaChat
TEMPERATURE=0.0
PROMPT_VERSION=v2

# для валидатора Loginom
VALIDATOR_USER_ID=YOUR_USER_ID
```

### 3) Запустить сервер

```powershell
python -c "from app import create_app; create_app().run(host='0.0.0.0', port=8080, debug=True)"
```

Открыть:

* UI: [http://localhost:8080/ui](http://localhost:8080/ui)
* Health: [http://localhost:8080/health](http://localhost:8080/health)

---

## Переменные окружения

Основные параметры (берутся из `.env`):

* `GIGACHAT_TOKEN` — токен для доступа к GigaChat
* `GIGACHAT_MODEL` — название модели (например `GigaChat`)
* `TEMPERATURE` — температура (для оценивания лучше `0.0`)
* `PROMPT_VERSION` — версия промпта (`v1`, `v2`, `v3`)
* `VALIDATOR_USER_ID` — UserID для Loginom валидатора

---

## Как пользоваться UI

1. Перейти на [http://localhost:8080/ui](http://localhost:8080/ui)
2. Вкладка **Одно эссе** — оценка одного текста
3. Вкладка **Batch** — оценка пачки (`{"items":[...]}`)

---

## Как прогнать все эссе и получить submission.csv

### 1) Подготовить входной файл `inputs_for_scoring.csv`

```powershell
python scripts/prepare_inputs.py
```

Результат:

* `data/inputs_for_scoring.csv`

### 2) Сгенерировать `submission.csv`

```powershell
python scripts/make_submission.py
```

Результат:

* `data/submission.csv`

Формат `submission.csv`:

```csv
essay_id,K1,K2,K3,K4
...
```

---

## Как отправить submission в валидатор Loginom и получить Score/MAE

URL валидатора:
`https://edu.loginom.dev/lgi/rest/hackathone_service/hackathon01`

### 1) Убедиться, что в `.env` указан `VALIDATOR_USER_ID`

```env
VALIDATOR_USER_ID=YOUR_USER_ID
```

### 2) Отправить `submission.csv`

```powershell
python scripts/send_to_validator.py
```

Сервис вернёт `Score` и сообщение о попытках (например `Потрачено 1/5 попыток`).

### 3) Перевод Score -> MAE

Формула:
`Score = 1 / (1 + MAE)`
то есть:
`MAE = (1 / Score) - 1`

---

## Локальный логер экспериментов

Если ClearML недоступен, мы сохраняем результаты экспериментов локально в папку `experiments/`.

После получения Score с валидатора:

```env
EXTERNAL_SCORE=0.6021505376344086
ATTEMPTS_NOTE=Потрачено 1/5 попыток

powershell:
python scripts/log_experiment_local.py
```

Скрипт создаст файл:

* `experiments/exp_<prompt_version>_<datetime>.json`

Там хранится:

* score, mae
* prompt_version, temperature, model
* отметка о попытках

---

## API

### GET /health

Ответ:

```json
{"status":"ok"}
```

### POST /score_one

Тело запроса:

```json
{
  "essay_id": "1",
  "essay_type": 2,
  "task_text": "...",
  "reference_text_essay": "...",
  "essay_text": "..."
}
```

### POST /score_batch

Тело запроса:

```json
{
  "items": [
    { "essay_id":"1", "essay_type":2, "task_text":"...", "reference_text_essay":"...", "essay_text":"..." },
    { "essay_id":"2", "essay_type":3, "task_text":"...", "reference_text_essay":"...", "essay_text":"..." }
  ]
}
```

---

## Структура проекта

* `app/` — Flask приложение

  * `routes.py` — API + UI endpoints
  * `scoring.py` — вызов GigaChat, парсинг JSON, retry/repair
  * `gigachat_client.py` — клиент к GigaChat API
  * `prompting.py` — промпты (v1/v2/v3)
  * `schemas.py` — валидация входа/выхода
  * `json_utils.py` — извлечение JSON из ответа модели
  * `templates/app.html` — UI страница

* `scripts/`

  * `prepare_inputs.py` — сборка `inputs_for_scoring.csv` из исходных CSV
  * `make_submission.py` — прогон всех эссе и генерация `submission.csv`
  * `send_to_validator.py` — отправка сабмита в Loginom и получение Score
  * `log_experiment_local.py` — локальный логер экспериментов (Score/MAE)

* `data/`

  * `essays.csv`, `reference_text*.csv` — исходные данные
  * `inputs_for_scoring.csv` — подготовленный вход для скоринга
  * `submission.csv` — результат (K1..K4) для валидатора

---

## Частые проблемы

### `GIGACHAT_TOKEN is not set`

Проверь `.env` и что он загружается (в скриптах используется `load_dotenv()`).

### Ошибки парсинга JSON от модели

В `scoring.py` включён retry и JSON-repair через дополнительный запрос.

### PowerShell `curl` не работает как в Linux

В PowerShell используйте `Invoke-RestMethod` или наши скрипты в `scripts/`.
