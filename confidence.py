"""
SecOps Autoresearch — Confidence Scoring & Calibration
Assigns a calibrated probability score to each detection instead of a binary flag.

Confidence tiers:
  ≥ 0.90  → "high"       — auto-escalate to Tier-2
  0.70–0.90 → "medium"   — Tier-1 review queue
  0.50–0.70 → "low"      — low-confidence queue / shadow mode
  < 0.50  → "suppressed" — quiet log only (no pager)

Usage:
    from confidence import score_event, confidence_tier, calibrate_scores

DO NOT MODIFY THIS FILE. The agent only modifies detect.py.
"""

import json
import math
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CALIBRATION_MODEL_FILE = os.path.join(DATA_DIR, "calibration_model.json")
CONFIDENCE_HISTORY_FILE = os.path.join(DATA_DIR, "confidence_history.jsonl")

CONFIDENCE_TIERS = {
    "high":       (0.90, 1.01),
    "medium":     (0.70, 0.90),
    "low":        (0.50, 0.70),
    "suppressed": (0.00, 0.50),
}

# Per-rule raw feature extractors map rule ID → scoring function.
# Each function receives the group of events for a single detection cluster
# and returns a raw score in [0, 1].

# ═══ Raw Feature Scorers ═════════════════════════════════════════════════════

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def _average(vals: List[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def score_brute_force_cluster(
    failures: List[Dict],
    successes: List[Dict],
    window_minutes: float,
) -> float:
    """
    Score a brute-force detection cluster.

    Signal weighting:
      - Volume: more failures → higher score, saturating at 20
      - Speed:  shorter window → higher score
      - Compromise: subsequent successful login is a strong multiplier
    """
    from detect import RULE_THRESHOLDS
    t = RULE_THRESHOLDS["brute_force"]
    threshold = t["RAPID_THRESHOLD"]
    window_cap = t["RAPID_WINDOW_MINUTES"]

    failure_count = len(failures)
    # Normalise failure count: 1.0 when count ≥ 3× threshold
    volume_score = _clamp(failure_count / (threshold * 3), 0.0, 1.0)

    # Speed: window_minutes=0 → 1.0 urgency, window_cap → 0.5, 2×cap → 0.25
    speed_score = _clamp(1 - (window_minutes / (window_cap * 2)), 0.0, 1.0)

    # Compromise bonus: following success within the window is high confidence
    compromise_bonus = 0.4 if successes else 0.0

    raw = (volume_score * 0.4) + (speed_score * 0.3) + compromise_bonus
    return _clamp(raw)


def score_dns_exfil_cluster(
    queries: List[Dict],
    avg_label_len: float,
    unique_ratio: float,
    max_entropy: float,
) -> float:
    """
    Score a DNS exfiltration detection cluster.

    Signal weighting:
      - query volume (more = more suspicious)
      - average label length (longer = more suspicious)
      - unique subdomain ratio (high = more suspicious)
      - entropy of labels (high = more suspicious)
    """
    query_score  = _clamp(len(queries) / 25.0)
    length_score = _clamp((avg_label_len - 10) / 30.0)    # normalise against 40-char ceiling
    ratio_score  = _clamp((unique_ratio - 0.5) / 0.5)
    entropy_score = _clamp((max_entropy - 2.5) / 2.5)     # entropy cap ~5 bits

    raw = (query_score * 0.25 + length_score * 0.25 +
           ratio_score * 0.25 + entropy_score * 0.25)
    return _clamp(raw)


def score_c2_beaconing_cluster(
    connections: List[Dict],
    interval_cv: float,
    max_bytes_out: float,
    _max_bytes_in: float,
) -> float:
    """
    Score a C2 beaconing detection cluster.

    Signal weighting:
      - Periodicity: lower coefficient of variation → more beacon-like
      - Volume: more connections → higher score
      - Payload size: smaller payloads → more suspicious (C2 keepalive)
    """
    from detect import RULE_THRESHOLDS
    t = RULE_THRESHOLDS["c2_beaconing"]

    conn_score = _clamp(len(connections) / 30.0)
    # CV near 0 = perfectly periodic = maximum suspicion
    periodicity_score = _clamp(1.0 - min(interval_cv, 1.0))
    # Small payload relative to threshold → more suspicious
    bytes_score = _clamp(1.0 - (max_bytes_out / (t["MAX_BYTES_OUT"] * 2)))

    raw = conn_score * 0.35 + periodicity_score * 0.45 + bytes_score * 0.20
    return _clamp(raw)


def score_lateral_movement_cluster(
    unique_dest_count: int,
    window_minutes: float,
    _avg_gap_seconds: float,
    max_bytes: float,
) -> float:
    """
    Score a lateral movement detection cluster.

    Signal weighting:
      - Breadth: more unique destinations → higher score
      - Speed: tighter timing → higher score
      - Volume: lower transfer bytes → more suspicious (probe vs. data copy)
    """
    from detect import RULE_THRESHOLDS
    t = RULE_THRESHOLDS["lateral_movement"]

    breadth_score = _clamp(unique_dest_count / (t["UNIQUE_DEST_THRESHOLD"] * 2))
    speed_score   = _clamp(1.0 - (window_minutes / (t["WINDOW_MINUTES"] * 2)))
    # Rapid, small transfers look like scanning
    probe_score   = _clamp(1.0 - (max_bytes / (t["MAX_TRANSFER_BYTES"] * 2)))

    raw = breadth_score * 0.4 + speed_score * 0.3 + probe_score * 0.3
    return _clamp(raw)


# ═══ Calibration (Platt Scaling) ═════════════════════════════════════════════

def _platt_transform(raw_score: float, a: float, b: float) -> float:
    """Apply Platt scaling: P(y=1|f) = 1 / (1 + exp(A*f + B))."""
    return _clamp(1.0 / (1.0 + math.exp(a * raw_score + b)))


def calibrate_scores(
    raw_scores: List[float],
    labels: List[int],
    method: str = "platt",
) -> Tuple[float, float]:
    """
    Fit a Platt calibration model (logistic regression on raw scores).
    Returns (A, B) parameters and saves them to data/calibration_model.json.

    Parameters
    ----------
    raw_scores : list of raw [0,1] scores from the scoring functions above
    labels     : list of ground-truth labels (1 = malicious, 0 = benign)
    method     : only "platt" supported currently

    Returns (A, B) — use _platt_transform(raw_score, A, B) at inference.
    """
    if len(raw_scores) != len(labels):
        raise ValueError("raw_scores and labels must have the same length")
    if len(raw_scores) < 10:
        raise ValueError("Need at least 10 samples to calibrate")

    # Simple gradient-descent Platt scaling
    A, B = 1.0, 0.0
    lr = 0.01
    for _ in range(200):
        dA = dB = 0.0
        for s, y in zip(raw_scores, labels):
            p = _platt_transform(s, A, B)
            err = p - y
            dA += err * s
            dB += err
        A -= lr * dA / len(raw_scores)
        B -= lr * dB / len(raw_scores)

    os.makedirs(DATA_DIR, exist_ok=True)
    model = {"A": A, "B": B, "method": method,
             "trained_at": datetime.now(tz=timezone.utc).isoformat(),
             "n_samples": len(raw_scores)}
    with open(CALIBRATION_MODEL_FILE, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2)

    return A, B


def load_calibration() -> Optional[Dict]:
    """Load calibration parameters from disk. Returns None if not yet trained."""
    if not os.path.exists(CALIBRATION_MODEL_FILE):
        return None
    with open(CALIBRATION_MODEL_FILE, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return None


def apply_calibration(raw_score: float) -> float:
    """
    Map a raw [0,1] score to a calibrated probability using the saved model.
    Returns raw_score unchanged if no calibration model exists yet.
    """
    model = load_calibration()
    if model is None:
        return raw_score
    return _platt_transform(raw_score, model["A"], model["B"])


# ═══ Tier Classification ═════════════════════════════════════════════════════

def confidence_tier(calibrated_prob: float) -> str:
    """Return 'high' | 'medium' | 'low' | 'suppressed' for a calibrated probability."""
    for tier, (lo, hi) in CONFIDENCE_TIERS.items():
        if lo <= calibrated_prob < hi:
            return tier
    return "suppressed"


def annotate_detections(
    rule_results: Dict[str, List[str]],
    _events: List[Dict],
    _rule_meta: List[Dict],
) -> List[Dict]:
    """
    For each detected event, compute a confidence score and tier.
    Returns list of {event_id, rule_id, raw_score, calibrated_score, tier}.

    This is a lightweight scoring pass — full per-cluster scoring requires
    explain.py's cluster extraction.  Here we fall back to a simple heuristic
    based on the number of co-detections across rules (more rules = higher conf).
    """
    # Count how many rules flagged each event_id
    detection_counts: Dict[str, int] = {}
    for _rule_id, ids in rule_results.items():
        for eid in ids:
            detection_counts[eid] = detection_counts.get(eid, 0) + 1

    max_rules = max(detection_counts.values()) if detection_counts else 1

    results = []
    for eid, count in detection_counts.items():
        raw = _clamp(count / max_rules)
        cal = apply_calibration(raw)
        results.append({
            "event_id":         eid,
            "rules_triggered":  count,
            "raw_score":        round(raw, 4),
            "calibrated_score": round(cal, 4),
            "tier":             confidence_tier(cal),
        })

    results.sort(key=lambda x: x["calibrated_score"], reverse=True)
    return results


def log_confidence_metrics(detections: List[Dict]) -> None:
    """Append aggregated confidence tier distribution to history log."""
    tier_counts = {t: 0 for t in CONFIDENCE_TIERS}
    for d in detections:
        tier = d.get("tier", "suppressed")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    entry = {
        "timestamp":   datetime.now(tz=timezone.utc).isoformat(),
        "total":       len(detections),
        "tier_counts": tier_counts,
        "avg_score":   round(_average([d["calibrated_score"] for d in detections]), 4),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CONFIDENCE_HISTORY_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
