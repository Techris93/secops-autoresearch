"""
SecOps Autoresearch — Confidence Scoring & Calibration  [SCAFFOLD — Item 6]
Assigns a calibrated probability score to each detection instead of a binary flag.

MOTIVATION:
  Binary detection (flag / no-flag) forces analysts to triage all alerts equally.
  A calibrated confidence score lets the SOC tier alerts by severity:
    ≥ 0.90  → auto-escalate to Tier-2
    0.70–0.90 → Tier-1 review queue
    0.50–0.70 → low-confidence queue / shadow mode
    < 0.50  → suppressed (but logged for audit)

DESIGN:
  Each detection rule emits a raw score in [0, 1] reflecting the strength of
  the signal. A lightweight calibration layer (Platt scaling or isotonic
  regression) maps raw scores to calibrated probabilities.

TODO — implement the following:

  def score_event(
      event: Dict,
      rule_id: str,
      raw_features: Dict[str, float],
  ) -> float:
      \"\"\"
      Return a raw confidence score in [0, 1] for a single event.

      Feature ideas per rule:
        brute_force:
          - failure_count / RAPID_THRESHOLD  (normalised burst ratio)
          - span_minutes / RAPID_WINDOW_MINUTES
          - is_external_ip(src_ip) → 0.0 or 1.0
          - has_subsequent_success → 0.8 bonus
        dns_exfiltration:
          - shannon_entropy(label) / 4.0  (normalised)
          - unique_label_ratio
          - query_count / MIN_QUERIES_PER_DOMAIN
        c2_beaconing:
          - coefficient_of_variation of inter-arrival times (lower = more periodic)
          - connection_count / 15
          - bytes_out / MAX_BYTES_OUT (inverted: smaller = more suspicious)
        lateral_movement:
          - unique_dest_count / UNIQUE_DEST_THRESHOLD
          - average_gap_seconds / MAX_AVERAGE_GAP_SECONDS (inverted)
      \"\"\"
      ...

  def calibrate(
      raw_scores: List[float],
      labels: List[int],
      method: str = "platt",       # "platt" | "isotonic"
  ) -> "CalibrationModel":
      \"\"\"
      Fit a calibration model on raw scores vs ground-truth labels.
      Writes model parameters to data/calibration_model.json.
      \"\"\"
      ...

  def load_calibration() -> "CalibrationModel":
      \"\"\"Load calibration parameters from data/calibration_model.json.\"\"\"
      ...

  def apply_calibration(raw_score: float) -> float:
      \"\"\"Map a raw score to a calibrated probability.\"\"\"
      ...

  def confidence_tier(calibrated_prob: float) -> str:
      \"\"\"Return 'high' | 'medium' | 'low' | 'suppressed'.\"\"\"
      ...

INTEGRATION POINTS:
  - run_detection() in detect.py should return per-event scores alongside IDs.
  - evaluate.py should compute reliability diagrams (calibration curves) and
    log expected calibration error (ECE) alongside F1 metrics.
  - findings.py should include confidence tier in each finding record.
  - benchmark.yml should fail if ECE > 0.10 (poorly calibrated model).

CALIBRATION DATA:
  Train on analyst-confirmed dispositions from feedback.py plus the labeled
  events in data/events.json. Recalibrate whenever analyst FP rate diverges
  from predicted confidence by more than 15%.

STORAGE:
  data/calibration_model.json — Platt/isotonic parameters
  data/confidence_history.jsonl — per-run calibration metrics
"""

CALIBRATION_MODEL_FILE = "data/calibration_model.json"
CONFIDENCE_HISTORY_FILE = "data/confidence_history.jsonl"

CONFIDENCE_TIERS = {
    "high":       (0.90, 1.01),
    "medium":     (0.70, 0.90),
    "low":        (0.50, 0.70),
    "suppressed": (0.00, 0.50),
}


def _not_implemented(*_args, **_kwargs):
    raise NotImplementedError(
        "confidence.py is a scaffold. See TODO comments for the implementation plan."
    )


score_event = _not_implemented
calibrate = _not_implemented
load_calibration = _not_implemented
apply_calibration = _not_implemented


def confidence_tier(calibrated_prob: float) -> str:
    for tier, (lo, hi) in CONFIDENCE_TIERS.items():
        if lo <= calibrated_prob < hi:
            return tier
    return "suppressed"
