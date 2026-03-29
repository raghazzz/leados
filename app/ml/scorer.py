import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)
MODEL_PATH = Path("app/ml/models/lead_scorer.pkl")

# ── Score tables ──────────────────────────────────────────
# Higher number = better lead quality for that value

INDUSTRY_SCORES = {
    "saas": 1.0,
    "software": 0.95,
    "technology": 0.9,
    "fintech": 0.9,
    "b2b": 0.88,
    "marketing": 0.85,
    "lead generation": 0.85,
    "consulting": 0.8,
    "e-commerce": 0.75,
    "healthcare": 0.7,
    "education": 0.65,
    "real estate": 0.6,
    "retail": 0.5,
    "other": 0.4,
}

TITLE_SCORES = {
    "ceo": 1.0,
    "founder": 1.0,
    "co-founder": 1.0,
    "cro": 0.95,
    "vp sales": 0.95,
    "head of sales": 0.9,
    "vp marketing": 0.9,
    "director of sales": 0.88,
    "cmo": 0.85,
    "head of marketing": 0.85,
    "growth": 0.8,
    "sales manager": 0.75,
    "business development": 0.7,
    "account executive": 0.65,
    "marketing manager": 0.65,
    "manager": 0.5,
    "analyst": 0.35,
    "intern": 0.1,
}

COMPANY_SIZE_SCORES = {
    "1-10": 0.5,
    "11-50": 0.75,
    "50-200": 0.9,
    "51-200": 0.9,
    "201-500": 0.95,
    "500-1000": 0.85,
    "1000+": 0.7,
    "1001-5000": 0.65,
    "5001-10000": 0.55,
    "10001+": 0.45,
}


# ── Data classes ──────────────────────────────────────────

@dataclass
class LeadFeatures:
    """All the information we have about a lead."""
    name: str = ""
    email: str = ""
    company: Optional[str] = None
    title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None


@dataclass
class ScoreResult:
    """The output of scoring a lead."""
    score: float                  # 0 to 100
    is_qualified: bool
    breakdown: dict = field(default_factory=dict)
    recommendation: str = ""
    model_used: str = "heuristic"


# ── Helper functions ──────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase and strip whitespace."""
    return text.lower().strip() if text else ""


def _lookup_score(value: Optional[str], lookup: dict, default: float = 0.4) -> float:
    """Find the score for a value in a lookup table.
    Tries exact match first, then partial match."""
    if not value:
        return default
    v = _normalize(value)
    if v in lookup:
        return lookup[v]
    # Partial match — e.g. "VP of Sales" matches "vp sales"
    for key, score in lookup.items():
        if key in v or v in key:
            return score
    return default


def _data_completeness(features: LeadFeatures) -> float:
    """What percentage of optional fields are filled in?
    More data = more serious lead."""
    fields = [
        features.company,
        features.title,
        features.industry,
        features.company_size,
        features.website,
        features.phone,
        features.linkedin_url,
    ]
    filled = sum(1 for f in fields if f)
    return filled / len(fields)


def _email_quality(email: str) -> float:
    """Business email = real company. Gmail = could be anyone."""
    if not email:
        return 0.0
    domain = email.split("@")[-1].lower()
    free_providers = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}
    return 0.5 if domain in free_providers else 1.0


# ── Main scoring function ─────────────────────────────────

def heuristic_score(features: LeadFeatures, threshold: float = 60.0) -> ScoreResult:
    """Score a lead using weighted rules. No training data needed."""

    industry_s    = _lookup_score(features.industry, INDUSTRY_SCORES)
    title_s       = _lookup_score(features.title, TITLE_SCORES)
    size_s        = _lookup_score(features.company_size, COMPANY_SIZE_SCORES)
    completeness_s = _data_completeness(features)
    email_s       = _email_quality(features.email)

    # Weighted average — these weights add up to 1.0
    raw = (
        industry_s      * 0.30 +   # 30% — what industry are they in?
        title_s         * 0.30 +   # 30% — can they make a buying decision?
        size_s          * 0.20 +   # 20% — is the company the right size?
        completeness_s  * 0.12 +   # 12% — how much do we know about them?
        email_s         * 0.08     # 8%  — is it a real business email?
    )

    score = round(raw * 100, 1)
    is_qualified = score >= threshold

    breakdown = {
        "industry_score": round(industry_s, 3),
        "title_score": round(title_s, 3),
        "company_size_score": round(size_s, 3),
        "data_completeness": round(completeness_s, 3),
        "email_quality": round(email_s, 3),
        "overall": score,
    }

    # Human readable recommendation
    if score >= 80:
        rec = "Hot lead. Send personalised email immediately."
    elif score >= 60:
        rec = "Qualified lead. Reach out within 24 hours."
    elif score >= 40:
        rec = "Marginal lead. Add to nurture sequence."
    else:
        rec = "Low priority. Deprioritise or archive."

    return ScoreResult(
        score=score,
        is_qualified=is_qualified,
        breakdown=breakdown,
        recommendation=rec,
        model_used="heuristic_v1",
    )


def score_lead(features: LeadFeatures, threshold: float = 60.0) -> ScoreResult:
    """
    Main entry point for scoring.
    Uses ML model if one has been trained, otherwise uses heuristic scorer.
    """
    if not MODEL_PATH.exists():
        return heuristic_score(features, threshold)

    try:
        import pickle
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)

        X = np.array([
            _lookup_score(features.industry, INDUSTRY_SCORES),
            _lookup_score(features.title, TITLE_SCORES),
            _lookup_score(features.company_size, COMPANY_SIZE_SCORES),
            _data_completeness(features),
            _email_quality(features.email),
        ]).reshape(1, -1)

        prob = model.predict_proba(X)[0][1]
        score = round(prob * 100, 1)

        return ScoreResult(
            score=score,
            is_qualified=score >= threshold,
            breakdown={"probability": prob, "overall": score},
            recommendation="Based on trained ML model.",
            model_used="random_forest_v1",
        )
    except Exception as e:
        logger.warning(f"ML scoring failed ({e}), falling back to heuristic.")
        return heuristic_score(features, threshold)


def train_model(leads_data: list[dict]) -> dict:
    """
    Train a Random Forest on your real historical lead data.
    Call this once you have 200+ leads with known outcomes.
    Each lead dict needs a 'converted' field set to True or False.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score
    import pickle

    X, y = [], []
    for row in leads_data:
        features = LeadFeatures(**{
            k: row.get(k) for k in LeadFeatures.__dataclass_fields__
        })
        X.append([
            _lookup_score(features.industry, INDUSTRY_SCORES),
            _lookup_score(features.title, TITLE_SCORES),
            _lookup_score(features.company_size, COMPANY_SIZE_SCORES),
            _data_completeness(features),
            _email_quality(features.email),
        ])
        y.append(int(row.get("converted", False)))

    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(X_train, y_train)

    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    logger.info(f"Model trained and saved. AUC score: {auc:.3f}")
    return {"auc": round(auc, 3), "samples": len(X)}
