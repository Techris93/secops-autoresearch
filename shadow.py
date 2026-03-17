"""
SecOps Autoresearch — Shadow Evaluation  [SCAFFOLD — Item 7]
Runs candidate detection rules alongside production rules without surfacing
alerts to analysts. Allows safe validation of new thresholds or rules in a
production-like event stream before enforcement.

MOTIVATION:
  Tightening a rule (lower threshold) can dramatically increase FP volume.
  Shadow mode lets engineers measure the real-world FP rate of a candidate
  ruleset against live or replay traffic before flipping it on, eliminating
  big-bang rule changes that flood the alert queue.

DESIGN:
  shadow.py maintains two parallel rule sets:
    "production"  → current detect.py RULE_THRESHOLDS (enforced, creates alerts)
    "candidate"   → modified thresholds / new rules under test (silent, logged only)

  On each event batch:
    1. Run production ruleset → emit real alerts.
    2. Run candidate ruleset  → log delta (alerts in candidate but not production,
       and vice versa) to data/shadow_log.jsonl.
    3. After a soak period (e.g. 24 h), compute:
         candidate_fp_rate, candidate_recall, candidate_precision
       and compare to production baselines.
    4. If candidate is strictly better (lower FP AND equal/higher recall),
       promote it by overwriting RULE_THRESHOLDS in detect.py.
    5. If candidate is worse on any dimension, reject it and file a finding.

TODO — implement the following:

  def start_shadow_session(
      candidate_thresholds: Dict[str, Dict],
      session_id: str,
      soak_hours: int = 24,
  ) -> str:
      \"\"\"
      Persist candidate config to data/shadow_sessions/{session_id}.json.
      Returns session_id.
      \"\"\"
      ...

  def run_shadow_batch(
      events: List[Dict],
      session_id: str,
  ) -> Dict[str, Any]:
      \"\"\"
      Run both rulesets on `events`. Write delta to shadow_log.jsonl.
      Returns {
        "production_ids": [...],
        "candidate_ids": [...],
        "candidate_only": [...],   # potential FP candidates
        "production_only": [...],  # FNs in candidate (regressions)
      }
      \"\"\"
      ...

  def evaluate_shadow_session(session_id: str, labeled: List[Dict]) -> Dict:
      \"\"\"
      After soak period ends, compute full precision/recall/F1/FPR for
      both production and candidate rulesets over all logged events.
      \"\"\"
      ...

  def promote_candidate(session_id: str) -> bool:
      \"\"\"
      If candidate is strictly better, patch RULE_THRESHOLDS in detect.py
      via AST rewrite and publish a finding. Returns True if promoted.
      \"\"\"
      ...

  def list_sessions() -> List[Dict]:
      \"\"\"Return all shadow sessions with status and soak progress.\"\"\"
      ...

INTEGRATION POINTS:
  - swarm.py --spawn should optionally open a shadow session instead of a
    git branch so candidate rules are tested before committing.
  - benchmark.yml should run shadow evaluation on PRs that modify detect.py
    thresholds, blocking merge if candidate_only / total_candidate > 0.15.
  - tune.py --promote param should call promote_candidate() instead of
    printing manual instructions.

STORAGE:
  data/shadow_sessions/{id}.json     — session config and status
  data/shadow_log.jsonl              — append-only event/delta log
  data/shadow_evaluations.jsonl      — soak-period evaluation results
"""

import os

SHADOW_SESSIONS_DIR = os.path.join("data", "shadow_sessions")
SHADOW_LOG_FILE = os.path.join("data", "shadow_log.jsonl")
SHADOW_EVALUATIONS_FILE = os.path.join("data", "shadow_evaluations.jsonl")


def _not_implemented(*_args, **_kwargs):
    raise NotImplementedError(
        "shadow.py is a scaffold. See TODO comments for the implementation plan."
    )


start_shadow_session = _not_implemented
run_shadow_batch = _not_implemented
evaluate_shadow_session = _not_implemented
promote_candidate = _not_implemented
list_sessions = _not_implemented
