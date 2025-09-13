from __future__ import annotations

# Standard / third-party imports
from pathlib import Path
from typing import List, Optional, Any, Dict

import joblib
from flask import Flask, request, jsonify, render_template
from pydantic import BaseModel, ValidationError, field_validator

# Local imports
from engine import recommend
from universe import SUPPORTED_GOALS
from data_sources import get_quote_snapshot  # live stats

# -----------------------------------------------------------------------------
# Flask app
# -----------------------------------------------------------------------------
app = Flask(__name__)

# -----------------------------------------------------------------------------
# Intent model loader (single, robust)
# -----------------------------------------------------------------------------
INTENT_PIPE = None  # scikit pipeline saved to models/intent.pipe
pipe_path = Path("models/intent.pipe")
if pipe_path.exists():
    try:
        INTENT_PIPE = joblib.load(pipe_path)
        print("Loaded intent model.")
    except Exception as e:
        print("Failed to load intent model:", e)
        INTENT_PIPE = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _split_list(value: Any) -> List[str]:
    """
    Normalize include/exclude inputs from either JSON or Form.
    Accepts list[str] or comma-separated string, returns trimmed list[str].
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def _safe_int(v: Any, default: int = 10) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _enrich_with_quotes(tickers: List[Dict[str, Any]]) -> None:
    """
    Mutates each ticker dict, adding price, ret_1y_pct, div_yield_pct.
    """
    for t in tickers:
        try:
            snap = get_quote_snapshot(t["symbol"])
        except Exception:
            snap = {}
        t["price"] = snap.get("price")
        t["ret_1y_pct"] = snap.get("ret_1y_pct")
        t["div_yield_pct"] = snap.get("div_yield_pct")


# -----------------------------------------------------------------------------
# Request Schemas (pydantic v2)
# -----------------------------------------------------------------------------
class RecommendRequest(BaseModel):
    goal: str
    risk: str = "medium"                       # "low" | "medium" | "high"
    include: Optional[List[str]] = []
    exclude: Optional[List[str]] = []
    max: int = 10

    @field_validator("risk")
    @classmethod
    def _risk_ok(cls, v: str) -> str:
        v = (v or "").lower()
        if v not in {"low", "medium", "high"}:
            raise ValueError("risk must be low|medium|high")
        return v

    @field_validator("goal")
    @classmethod
    def _goal_ok(cls, v: str) -> str:
        if v not in SUPPORTED_GOALS:
            raise ValueError(f"goal must be one of: {', '.join(SUPPORTED_GOALS)}")
        return v

    @field_validator("max")
    @classmethod
    def _max_ok(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("max must be between 1 and 100")
        return v


class SmartRequest(BaseModel):
    query: str
    risk: str = "medium"
    include: Optional[List[str]] = []
    exclude: Optional[List[str]] = []
    max: int = 10

    @field_validator("risk")
    @classmethod
    def _risk_ok(cls, v: str) -> str:
        v = (v or "").lower()
        if v not in {"low", "medium", "high"}:
            raise ValueError("risk must be low|medium|high")
        return v

    @field_validator("max")
    @classmethod
    def _max_ok(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("max must be between 1 and 100")
        return v


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return "OK", 200


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html", goals=SUPPORTED_GOALS)


# -----------------------------------------------------------------------------
# Core recommend (form + JSON)
# -----------------------------------------------------------------------------
@app.post("/recommend")
def recommend_route():
    # Parse payload
    if request.is_json:
        body = request.get_json(silent=True) or {}
        payload = {
            "goal": (body.get("goal") or ""),
            "risk": (body.get("risk") or "medium"),
            "include": _split_list(body.get("include")),
            "exclude": _split_list(body.get("exclude")),
            "max": _safe_int(body.get("max"), 10),
        }
    else:
        payload = {
            "goal": request.form.get("goal", ""),
            "risk": request.form.get("risk", "medium"),
            "include": _split_list(request.form.get("include", "")),
            "exclude": _split_list(request.form.get("exclude", "")),
            "max": _safe_int(request.form.get("max", "10"), 10),
        }

    # Validate
    try:
        req = RecommendRequest(**payload)
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": e.errors()}), 400
        return render_template("index.html", goals=SUPPORTED_GOALS, result={"error": "Invalid inputs."}), 400

    # Compute
    tickers, note = recommend(req.goal, req.risk, req.include or [], req.exclude or [], req.max)

    # Enrich with live stats
    _enrich_with_quotes(tickers)

    result = {
        "tickers": tickers,
        "note": note,
        "disclaimer": "Educational demo. Not investment advice.",
    }

    if request.is_json:
        return jsonify(result), 200
    return render_template("index.html", goals=SUPPORTED_GOALS, result=result, form=req.model_dump())


# -----------------------------------------------------------------------------
# Smart recommend (free-text → predicted goal)
# -----------------------------------------------------------------------------
@app.post("/recommend_smart")
def recommend_smart():
    # Parse payload (JSON or form)
    if request.is_json:
        body = request.get_json(silent=True) or {}
        payload = {
            "query": (body.get("query") or ""),
            "risk": (body.get("risk") or "medium"),
            "include": _split_list(body.get("include")),
            "exclude": _split_list(body.get("exclude")),
            "max": _safe_int(body.get("max"), 10),
        }
    else:
        payload = {
            "query": request.form.get("query", ""),
            "risk": request.form.get("risk", "medium"),
            "include": _split_list(request.form.get("include", "")),
            "exclude": _split_list(request.form.get("exclude", "")),
            "max": _safe_int(request.form.get("max", "10"), 10),
        }

    # Friendly guard for empty query *before* validation
    q = (payload.get("query") or "").strip()
    if not q:
        if request.is_json:
            return jsonify({"error": "query required"}), 400
        msg = "Type a query (e.g., 'AI chips', 'automotive EVs', or 'dividend healthcare') before using Smart Recommend."
        return render_template("index.html", goals=SUPPORTED_GOALS, result={"error": msg}), 200

    # Validate rest of inputs
    try:
        sreq = SmartRequest(**payload)
    except ValidationError as e:
        if request.is_json:
            return jsonify({"error": e.errors()}), 400
        return render_template("index.html", goals=SUPPORTED_GOALS, result={"error": "Invalid inputs."}), 400

    # Require model
    if not INTENT_PIPE:
        if request.is_json:
            return jsonify({"error": "intent model not loaded"}), 500
        return render_template("index.html", goals=SUPPORTED_GOALS, result={"error": "Intent model not loaded."}), 500

    # Predict goal
    try:
        predicted_goal = INTENT_PIPE.predict([sreq.query])[0]
    except Exception as e:
        if request.is_json:
            return jsonify({"error": f"intent prediction failed: {e}"}), 500
        return render_template("index.html", goals=SUPPORTED_GOALS, result={"error": "Intent prediction failed."}), 500

    # Recommend & enrich
    tickers, note = recommend(predicted_goal, sreq.risk, sreq.include or [], sreq.exclude or [], sreq.max)
    _enrich_with_quotes(tickers)

    result = {
        "predicted_goal": predicted_goal,
        "tickers": tickers,
        "note": note,
        "disclaimer": "Educational demo. Not investment advice.",
    }

    if request.is_json:
        return jsonify(result), 200

    # Persist form state into the page
    form_state = {
        "goal": predicted_goal,
        "risk": sreq.risk,
        "include": sreq.include,
        "exclude": sreq.exclude,
        "max": sreq.max,
        "query": sreq.query,
    }
    return render_template("index.html", goals=SUPPORTED_GOALS, result=result, form=form_state)


# -----------------------------------------------------------------------------
# Dev server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Host 0.0.0.0 for container friendliness; keep debug during local dev.
    app.run(host="0.0.0.0", port=3000, debug=True)
