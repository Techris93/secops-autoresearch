"""
SecOps Autoresearch — Analyst Feedback Loop  [SCAFFOLD — Item 4]
Closes the loop between analyst dispositions and detection rule quality.

WORKFLOW:
  1. An analyst reviews a finding in `data/findings/` and marks it
     as TP / FP / FN / benign-explain.
  2. feedback.py ingests those dispositions and writes structured
     records to `data/feedback.jsonl`.
  3. evaluate.py (or tune.py) reads feedback records to:
       - Automatically promote events confirmed as TPs into a
         "golden set" for regression tests.
       - Flag rules that generate many analyst-confirmed FPs for
         threshold relaxation (raise thresholds) or allowlist expansion.
       - Increase weighting of confirmed FN attack types in the
         benchmark so the tuner prioritises recall for those classes.

TODO — implement the following:

  class Disposition(Enum):
      TRUE_POSITIVE   = "tp"
      FALSE_POSITIVE  = "fp"
      FALSE_NEGATIVE  = "fn"      # analyst spotted something the rules missed
      BENIGN_EXPLAIN  = "benign"  # FP with root-cause note

  def record_disposition(
      event_id: str,
      rule_id: str,
      disposition: Disposition,
      analyst: str,
      note: str = "",
  ) -> None:
      \"\"\"Append a signed disposition to data/feedback.jsonl.\"\"\"
      ...

  def load_dispositions(since: datetime = None) -> List[Dict]:
      \"\"\"Return all (or recent) analyst dispositions.\"\"\"
      ...

  def fp_rate_by_rule(dispositions: List[Dict]) -> Dict[str, float]:
      \"\"\"Return FP rate per rule_id from analyst records.\"\"\"
      ...

  def promote_golden_set(dispositions: List[Dict]) -> int:
      \"\"\"
      Move analyst-confirmed TP events into data/golden_set.json.
      These are used in benchmark.yml as a must-catch regression set.
      Returns the number of events promoted.
      \"\"\"
      ...

  def suggest_allowlist_entries(dispositions: List[Dict]) -> List[Dict]:
      \"\"\"
      For each analyst-confirmed FP, extract features that distinguish
      it from true positives (src_ip subnet, user patterns, domain TLDs)
      and suggest allowlist entries for detect.py.
      \"\"\"
      ...

INTEGRATION POINTS:
  - evaluate.py main() should call load_dispositions() and log a warning
    when any rule's analyst FP rate exceeds 20%.
  - tune.py should accept --weight-fn-classes to up-weight attack types
    with analyst-confirmed FNs.
  - swarm.py research directions should include "fp-reduction" hints
    derived from suggest_allowlist_entries().

STORAGE FORMAT (data/feedback.jsonl):
  {
    "event_id":    "EVT-00123",
    "rule_id":     "RULE-001",
    "disposition": "fp",
    "analyst":     "alice",
    "note":        "CI/CD runner — add to svc_deploy allowlist",
    "timestamp":   "2026-03-17T14:22:00Z"
  }

SECURITY NOTE:
  Validate `analyst` field against an allowlist of authorized reviewers
  before writing to prevent poisoning of the feedback corpus.
"""

# Placeholder so the module is importable by other scripts.
FEEDBACK_FILE = "data/feedback.jsonl"
GOLDEN_SET_FILE = "data/golden_set.json"


def _not_implemented(*_args, **_kwargs):
    raise NotImplementedError(
        "feedback.py is a scaffold. See TODO comments for the implementation plan."
    )


record_disposition = _not_implemented
load_dispositions = _not_implemented
fp_rate_by_rule = _not_implemented
promote_golden_set = _not_implemented
suggest_allowlist_entries = _not_implemented
