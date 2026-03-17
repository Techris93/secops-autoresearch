"""
SecOps Autoresearch — Analyst Feedback Loop
Closes the loop between analyst dispositions and detection rule quality.

Analysts review findings (alerts) and record whether each is:
  - tp  (True Positive)  — genuine attack, rule fired correctly
  - fp  (False Positive) — benign event, rule fired incorrectly
  - fn  (False Negative) — attack the rules missed, analyst spotted manually
  - benign (FP with root-cause explanation)

Dispositions flow into:
  - data/feedback.jsonl         — signed disposition log (append-only)
  - data/golden_set.json        — analyst-confirmed TPs used as regression must-catch set
  - per-rule FP rate warnings   — shown by evaluate.py when rate exceeds 20%
  - tune.py weighting hints     — attack types with analyst FNs get up-weighted

Usage:
    from feedback import record_disposition, load_dispositions, fp_rate_by_rule

DO NOT MODIFY THIS FILE. The agent only modifies detect.py.
"""

import json
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.jsonl")
GOLDEN_SET_FILE = os.path.join(DATA_DIR, "golden_set.json")

# Analyst IDs that are authorised to record dispositions.
# Add real usernames / GitHub handles here before deployment.
# An empty set disables the allowlist check (development mode).
AUTHORIZED_ANALYSTS: frozenset = frozenset()

FP_ALERT_THRESHOLD = 0.20   # warn when any rule's analyst FP rate exceeds this


class Disposition(str, Enum):
    TRUE_POSITIVE = "tp"
    FALSE_POSITIVE = "fp"
    FALSE_NEGATIVE = "fn"
    BENIGN_EXPLAIN = "benign"


# ═══ Recording ═══════════════════════════════════════════════════════════════

def record_disposition(
    event_id: str,
    rule_id: str,
    disposition: Disposition,
    analyst: str,
    note: str = "",
    events_snapshot: Optional[Dict] = None,
) -> Dict:
    """
    Append a signed disposition record to data/feedback.jsonl.

    Parameters
    ----------
    event_id   : ID of the event being reviewed (e.g. "EVT-00042")
    rule_id    : Rule that triggered the alert (e.g. "RULE-001")
    disposition: Analyst verdict (Disposition enum)
    analyst    : Reviewer identifier (username / GitHub handle)
    note       : Free-text root-cause explanation (required for fp / benign)
    events_snapshot: Optional dict of relevant event fields for audit trail

    Returns the disposition record that was written.
    """
    if AUTHORIZED_ANALYSTS and analyst not in AUTHORIZED_ANALYSTS:
        raise PermissionError(
            f"Analyst '{analyst}' is not in the authorized analyst list. "
            "Add them to AUTHORIZED_ANALYSTS in feedback.py."
        )

    if str(disposition) in (Disposition.FALSE_POSITIVE, Disposition.BENIGN_EXPLAIN) and not note:
        raise ValueError("A root-cause note is required for fp / benign dispositions.")

    record = {
        "event_id":    event_id,
        "rule_id":     rule_id,
        "disposition": str(disposition.value if isinstance(disposition, Disposition) else disposition),
        "analyst":     analyst,
        "note":        note,
        "timestamp":   datetime.now(tz=timezone.utc).isoformat(),
    }
    if events_snapshot:
        # Store only a selection of fields to avoid PII / large objects
        record["event_preview"] = {
            k: events_snapshot.get(k)
            for k in ("sourcetype", "src_ip", "dest_ip", "user", "attack_type", "event_type")
            if events_snapshot.get(k) is not None
        }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")

    return record


# ═══ Loading ═════════════════════════════════════════════════════════════════

def load_dispositions(since: Optional[datetime] = None) -> List[Dict]:
    """
    Return all analyst dispositions, optionally filtered to those recorded
    after `since` (a timezone-aware datetime).
    """
    if not os.path.exists(FEEDBACK_FILE):
        return []

    records = []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since is not None:
                ts = datetime.fromisoformat(rec.get("timestamp", "1970-01-01T00:00:00+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < since:
                    continue
            records.append(rec)

    return records


# ═══ Analytics ═══════════════════════════════════════════════════════════════

def fp_rate_by_rule(dispositions: Optional[List[Dict]] = None) -> Dict[str, float]:
    """
    Return the analyst-confirmed false positive rate per rule_id.

    fp_rate = fp_count / (tp_count + fp_count)
    Rules with zero confirmed TP or FP are omitted.
    """
    if dispositions is None:
        dispositions = load_dispositions()

    counts: Dict[str, Dict[str, int]] = {}
    for rec in dispositions:
        rid = rec.get("rule_id", "unknown")
        d = rec.get("disposition", "")
        counts.setdefault(rid, {"tp": 0, "fp": 0, "fn": 0})
        if d in ("tp",):
            counts[rid]["tp"] += 1
        elif d in ("fp", "benign"):
            counts[rid]["fp"] += 1
        elif d == "fn":
            counts[rid]["fn"] += 1

    rates: Dict[str, float] = {}
    for rid, c in counts.items():
        total = c["tp"] + c["fp"]
        if total > 0:
            rates[rid] = c["fp"] / total

    return rates


def fn_attack_types(dispositions: Optional[List[Dict]] = None) -> Dict[str, int]:
    """
    Return a count of analyst-confirmed false negatives grouped by attack type.
    Useful for weighting tune.py to prioritise recall-improvement for missed classes.
    """
    if dispositions is None:
        dispositions = load_dispositions()

    counts: Dict[str, int] = {}
    for rec in dispositions:
        if rec.get("disposition") == "fn":
            at = (rec.get("event_preview") or {}).get("attack_type", "unknown")
            counts[at] = counts.get(at, 0) + 1
    return counts


def check_fp_rate_warnings(dispositions: Optional[List[Dict]] = None) -> List[str]:
    """
    Return warning strings for any rule whose analyst FP rate exceeds
    FP_ALERT_THRESHOLD (default 20%).  Used by evaluate.py verbose output.
    """
    warnings = []
    for rid, rate in fp_rate_by_rule(dispositions).items():
        if rate >= FP_ALERT_THRESHOLD:
            warnings.append(
                f"⚠️  {rid}: analyst FP rate = {rate:.0%} "
                f"(threshold {FP_ALERT_THRESHOLD:.0%}) — consider raising thresholds"
            )
    return warnings


# ═══ Golden Set ══════════════════════════════════════════════════════════════

def promote_golden_set(dispositions: Optional[List[Dict]] = None) -> int:
    """
    Merge analyst-confirmed TP events into data/golden_set.json.
    These events are used by benchmark.yml as a must-catch regression set:
    any future detect.py that misses a golden-set event fails CI.

    Returns the count of newly added event IDs.
    """
    if dispositions is None:
        dispositions = load_dispositions()

    confirmed_tp_ids = {
        rec["event_id"]
        for rec in dispositions
        if rec.get("disposition") == "tp" and rec.get("event_id")
    }

    existing: Dict = {}
    if os.path.exists(GOLDEN_SET_FILE):
        with open(GOLDEN_SET_FILE, "r", encoding="utf-8") as fh:
            try:
                existing = json.load(fh)
            except json.JSONDecodeError:
                existing = {}

    existing_ids: set = set(existing.get("event_ids", []))
    new_ids = confirmed_tp_ids - existing_ids

    if new_ids:
        existing["event_ids"] = sorted(existing_ids | new_ids)
        existing["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        existing["total"] = len(existing["event_ids"])
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(GOLDEN_SET_FILE, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2)

    return len(new_ids)


def load_golden_set() -> List[str]:
    """Return the list of must-catch event IDs from the golden set."""
    if not os.path.exists(GOLDEN_SET_FILE):
        return []
    with open(GOLDEN_SET_FILE, "r", encoding="utf-8") as fh:
        try:
            return json.load(fh).get("event_ids", [])
        except json.JSONDecodeError:
            return []


# ═══ Allowlist Suggestions ═══════════════════════════════════════════════════

def suggest_allowlist_entries(dispositions: Optional[List[Dict]] = None) -> List[Dict]:
    """
    For each analyst-confirmed FP, extract distinguishing features and suggest
    allowlist entries that could suppress the alert without missing real attacks.

    Returns a list of suggestion dicts ready to be reviewed and added to detect.py.
    """
    if dispositions is None:
        dispositions = load_dispositions()

    suggestions = []
    for rec in dispositions:
        if rec.get("disposition") not in ("fp", "benign"):
            continue

        preview = rec.get("event_preview") or {}
        suggestion: Dict = {
            "rule_id":      rec.get("rule_id"),
            "event_id":     rec.get("event_id"),
            "analyst_note": rec.get("note", ""),
            "features":     {},
        }

        src_ip = preview.get("src_ip")
        if src_ip:
            suggestion["features"]["src_ip"] = src_ip

        user = preview.get("user")
        if user:
            suggestion["features"]["user"] = user

        sourcetype = preview.get("sourcetype")
        if sourcetype:
            suggestion["features"]["sourcetype"] = sourcetype

        attack_type = preview.get("attack_type")
        if attack_type:
            suggestion["features"]["misclassified_attack_type"] = attack_type

        if suggestion["features"]:
            suggestions.append(suggestion)

    return suggestions
