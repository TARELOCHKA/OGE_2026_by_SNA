# app/routes.py
import json
from flask import Blueprint, jsonify, request, render_template

from .schemas import (
    ScoreRequest,
    validate_score_output,
    validate_batch_input,
)
from .scoring import score_essay
from .data_store import get_by_essay_id  # <-- добавили

bp = Blueprint("api", __name__)


def pretty_json(obj) -> str:
    """Красивый JSON для UI (русский без unicode-escape)."""
    return json.dumps(obj, ensure_ascii=False, indent=2)


# -------------------------
# API endpoints (для интеграций/скриптов)
# -------------------------

@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/score_one")
def score_one():
    data = request.get_json(silent=True) or {}
    try:
        req_obj = ScoreRequest.from_json(data)
        out = score_essay(req_obj)
        validate_score_output(out)
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/score_batch")
def score_batch():
    data = request.get_json(silent=True) or {}
    items = data.get("items", None)

    try:
        items = validate_batch_input(items, max_batch_size=request.app.config["MAX_BATCH_SIZE"])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    results = []
    errors = []

    for item in items:
        try:
            req_obj = ScoreRequest.from_json(item)
            out = score_essay(req_obj)
            validate_score_output(out)
            results.append(out)
        except Exception as e:
            errors.append({"essay_id": item.get("essay_id"), "error": str(e)})

    return jsonify({"results": results, "errors": errors})


# -------------------------
# UI endpoints (одна страница, табы: one/batch)
# -------------------------

def _one_defaults():
    return {
        "essay_id": "1",
        "essay_type": 2,
        "task_text": "",
        "reference_text_essay": "",
        "essay_text": "",
    }


def _sample_batch():
    return {
        "items": [
            {
                "essay_id": "1",
                "essay_type": 1,
                "task_text": "t",
                "reference_text_essay": "r",
                "essay_text": "text text text"
            },
            {
                "essay_id": "2",
                "essay_type": 2,
                "task_text": "t2",
                "reference_text_essay": "r2",
                "essay_text": "ещё один текст"
            }
        ]
    }


@bp.get("/ui")
def ui_app():
    return render_template(
        "app.html",
        active_tab="one",
        one_form=_one_defaults(),
        batch_payload=json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
        result_pretty=None,
        batch_pretty=None,
        error=None,
    )


@bp.post("/ui/load_one")
def ui_load_one():
    """
    Подтягиваем данные для одного эссе по essay_id из data/inputs_for_scoring.csv
    """
    essay_id = (request.form.get("essay_id") or "").strip()
    batch_payload = request.form.get("batch_payload", "")

    try:
        loaded = get_by_essay_id(essay_id)
        if not loaded:
            raise ValueError(f"essay_id={essay_id} не найден в data/inputs_for_scoring.csv (запусти scripts/prepare_inputs.py)")

        return render_template(
            "app.html",
            active_tab="one",
            one_form=loaded,
            batch_payload=batch_payload or json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
            result_pretty=None,
            batch_pretty=None,
            error=None,
        )
    except Exception as e:
        # возвращаем форму и ошибку
        one_form = _one_defaults()
        one_form["essay_id"] = essay_id

        return render_template(
            "app.html",
            active_tab="one",
            one_form=one_form,
            batch_payload=batch_payload or json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
            result_pretty=None,
            batch_pretty=None,
            error=str(e),
        ), 400


@bp.post("/ui/score_one")
def ui_score_one():
    try:
        one_form = {
            "essay_id": request.form.get("essay_id", "").strip() or None,
            "essay_type": int(request.form.get("essay_type", "1")),
            "task_text": request.form.get("task_text", ""),
            "reference_text_essay": request.form.get("reference_text_essay", ""),
            "essay_text": request.form.get("essay_text", ""),
        }

        req_obj = ScoreRequest.from_json(one_form)
        out = score_essay(req_obj)
        validate_score_output(out)

        return render_template(
            "app.html",
            active_tab="one",
            one_form=one_form,
            batch_payload=request.form.get("batch_payload", "") or json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
            result_pretty=pretty_json(out),
            batch_pretty=None,
            error=None,
        )

    except Exception as e:
        # Важно: essay_type может быть строкой — оставим как есть, чтобы пользователь увидел введённое
        one_form = {
            "essay_id": request.form.get("essay_id", "").strip(),
            "essay_type": request.form.get("essay_type", "1"),
            "task_text": request.form.get("task_text", ""),
            "reference_text_essay": request.form.get("reference_text_essay", ""),
            "essay_text": request.form.get("essay_text", ""),
        }

        return render_template(
            "app.html",
            active_tab="one",
            one_form=one_form,
            batch_payload=request.form.get("batch_payload", "") or json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
            result_pretty=None,
            batch_pretty=None,
            error=str(e),
        ), 400


@bp.post("/ui/score_batch")
def ui_score_batch():
    try:
        payload = request.form.get("batch_payload", "")
        data = json.loads(payload)

        items = data.get("items", None)
        items = validate_batch_input(items, max_batch_size=request.app.config["MAX_BATCH_SIZE"])

        results = []
        errors = []

        for item in items:
            try:
                req_obj = ScoreRequest.from_json(item)
                out = score_essay(req_obj)
                validate_score_output(out)
                results.append(out)
            except Exception as e:
                errors.append({"essay_id": item.get("essay_id"), "error": str(e)})

        batch_result = {"results": results, "errors": errors}

        return render_template(
            "app.html",
            active_tab="batch",
            one_form=_one_defaults(),
            batch_payload=payload,
            result_pretty=None,
            batch_pretty=pretty_json(batch_result),
            error=None,
        )

    except Exception as e:
        return render_template(
            "app.html",
            active_tab="batch",
            one_form=_one_defaults(),
            batch_payload=request.form.get("batch_payload", "") or json.dumps(_sample_batch(), ensure_ascii=False, indent=2),
            result_pretty=None,
            batch_pretty=None,
            error=str(e),
        ), 400
