"""
SecOps Autoresearch — Shadow Evaluation
Runs candidate detection thresholds/rules alongside production without
surfacing alerts to analysts. Validates new configs against live/replay
traffic before enforcement.

Usage:
    from shadow import start_session, run_batch, evaluate_session, list_sessions
    python shadow.py --start --candidate '{"brute_force": {"RAPID_THRESHOLD": 4}}'
    python shadow.py --status
    python shadow.py --evaluate SESSION_ID
    python shadow.py --promote SESSION_ID

DO NOT MODIFY THIS FILE. The agent only modifies detect.py.
"""

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SHADOW_SESSIONS_DIR = os.path.join(DATA_DIR, "shadow_sessions")
SHADOW_LOG_FILE = os.path.join(DATA_DIR, "shadow_log.jsonl")
SHADOW_EVALUATIONS_FILE = os.path.join(DATA_DIR, "shadow_evaluations.jsonl")

STATUS_ACTIVE   = "active"
STATUS_EXPIRED  = "expired"
STATUS_PROMOTED = "promoted"
STATUS_REJECTED = "rejected"


# ═══ Session Management ══════════════════════════════════════════════════════

def _session_path(session_id: str) -> str:
    return os.path.join(SHADOW_SESSIONS_DIR, f"{session_id}.json")


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def start_session(
    candidate_thresholds: Dict[str, Dict],
    session_id: Optional[str] = None,
    soak_hours: int = 24,
    description: str = "",
) -> str:
    """
    Persist a shadow session config and return session_id.

    Parameters
    ----------
    candidate_thresholds : override dict compatible with detect.RULE_THRESHOLDS
    session_id           : custom ID (auto-generated from timestamp if omitted)
    soak_hours           : minimum hours before session can be auto-promoted
    description          : human-readable description of what is being tested
    """
    import detect  # local import to avoid circular issues at module level

    if session_id is None:
        session_id = datetime.now(tz=timezone.utc).strftime("shadow-%Y%m%d-%H%M%S")

    os.makedirs(SHADOW_SESSIONS_DIR, exist_ok=True)

    session = {
        "session_id":       session_id,
        "status":           STATUS_ACTIVE,
        "description":      description or f"Shadow test of {list(candidate_thresholds.keys())}",
        "candidate_thresholds": candidate_thresholds,
        "production_thresholds": copy.deepcopy(detect.RULE_THRESHOLDS),
        "soak_hours":       soak_hours,
        "started_at":       _now(),
        "expires_at":       (
            datetime.now(tz=timezone.utc) + timedelta(hours=soak_hours)
        ).isoformat(),
        "batch_count":      0,
        "total_events":     0,
    }

    with open(_session_path(session_id), "w", encoding="utf-8") as fh:
        json.dump(session, fh, indent=2)

    print(f"  ✅ Shadow session started: {session_id}")
    print(f"     Soak period: {soak_hours}h, expires at {session['expires_at']}")
    return session_id


def _load_session(session_id: str) -> Dict:
    path = _session_path(session_id)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Session '{session_id}' not found at {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _save_session(session: Dict) -> None:
    with open(_session_path(session["session_id"]), "w", encoding="utf-8") as fh:
        json.dump(session, fh, indent=2)


def list_sessions() -> List[Dict]:
    """Return all shadow sessions with status and soak progress."""
    if not os.path.exists(SHADOW_SESSIONS_DIR):
        return []

    sessions = []
    for fname in sorted(os.listdir(SHADOW_SESSIONS_DIR)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(SHADOW_SESSIONS_DIR, fname), encoding="utf-8") as fh:
            try:
                sessions.append(json.load(fh))
            except json.JSONDecodeError:
                continue

    return sessions


# ═══ Batch Evaluation ════════════════════════════════════════════════════════

def run_batch(events: List[Dict], session_id: str) -> Dict[str, Any]:
    """
    Run both production and candidate rulesets on `events`.
    Write delta to shadow_log.jsonl.

    Returns
    -------
    {
      "production_ids": [...],
      "candidate_ids":  [...],
      "candidate_only": [...],   # potential FP candidates (candidate fires, prod doesn't)
      "production_only": [...],  # regressions (prod fires, candidate doesn't)
      "agreement_rate":  float,  # % of events both agree on
    }
    """
    import detect

    session = _load_session(session_id)
    if session["status"] != STATUS_ACTIVE:
        raise RuntimeError(f"Session '{session_id}' is not active (status={session['status']})")

    # Run production
    prod_results = detect.run_detection(events)

    # Run candidate (patch thresholds temporarily)
    saved = copy.deepcopy(detect.RULE_THRESHOLDS)
    for rule_id, params in session["candidate_thresholds"].items():
        if rule_id in detect.RULE_THRESHOLDS:
            detect.RULE_THRESHOLDS[rule_id].update(params)
    try:
        cand_results = detect.run_detection(events)
    finally:
        detect.RULE_THRESHOLDS.clear()
        detect.RULE_THRESHOLDS.update(saved)

    prod_ids  = set(prod_results["detected_event_ids"])
    cand_ids  = set(cand_results["detected_event_ids"])
    total = max(len(prod_ids), len(cand_ids), 1)

    delta = {
        "session_id":      session_id,
        "timestamp":       _now(),
        "event_count":     len(events),
        "production_count": len(prod_ids),
        "candidate_count":  len(cand_ids),
        "candidate_only":  sorted(cand_ids - prod_ids),
        "production_only": sorted(prod_ids - cand_ids),
        "agreement_rate":  round(len(prod_ids & cand_ids) / total, 4),
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SHADOW_LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(delta) + "\n")

    # Update session counters
    session["batch_count"] += 1
    session["total_events"] += len(events)
    _save_session(session)

    return {
        "production_ids":  sorted(prod_ids),
        "candidate_ids":   sorted(cand_ids),
        "candidate_only":  delta["candidate_only"],
        "production_only": delta["production_only"],
        "agreement_rate":  delta["agreement_rate"],
    }


# ═══ Soak Period Evaluation ══════════════════════════════════════════════════

def evaluate_session(session_id: str, labeled_events: Optional[List[Dict]] = None) -> Dict:
    """
    Compute aggregate metrics for all batches in a session.

    If labeled_events is provided, compute full precision/recall/F1/FPR for
    both production and candidate over all logged events in this session.
    Otherwise, reports agreement rates and differential counts only.
    """
    session = _load_session(session_id)

    # Load all deltas for this session from the log
    deltas = []
    if os.path.exists(SHADOW_LOG_FILE):
        with open(SHADOW_LOG_FILE, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("session_id") == session_id:
                        deltas.append(rec)
                except json.JSONDecodeError:
                    continue

    if not deltas:
        return {"session_id": session_id, "status": "no_batches", "deltas": 0}

    total_events     = sum(d["event_count"] for d in deltas)
    cand_only_total  = sum(len(d["candidate_only"]) for d in deltas)
    prod_only_total  = sum(len(d["production_only"]) for d in deltas)
    avg_agreement    = sum(d["agreement_rate"] for d in deltas) / len(deltas)
    avg_cand         = sum(d["candidate_count"] for d in deltas) / len(deltas)
    avg_prod         = sum(d["production_count"] for d in deltas) / len(deltas)

    result: Dict[str, Any] = {
        "session_id":         session_id,
        "description":        session["description"],
        "status":             session["status"],
        "batches":            len(deltas),
        "total_events":       total_events,
        "avg_agreement_rate": round(avg_agreement, 4),
        "candidate_only_total":  cand_only_total,
        "production_only_total": prod_only_total,
        "avg_candidate_detections": round(avg_cand, 2),
        "avg_production_detections": round(avg_prod, 2),
        "fp_candidate_rate_approx": round(
            cand_only_total / max(total_events, 1), 4
        ),
        "fn_candidate_rate_approx": round(
            prod_only_total / max(total_events, 1), 4
        ),
        "recommendation": (
            "promote"
            if cand_only_total <= prod_only_total * 1.1 and prod_only_total <= cand_only_total
            else "reject"
        ),
    }

    if labeled_events:
        from evaluate import compute_metrics

        all_cand_ids = [eid for d in deltas for eid in d.get("candidate_only", [])]
        all_prod_ids = [eid for d in deltas for eid in d.get("production_only", [])]
        # Approximation — only reliable if labeled_events is the same set used in batches
        prod_m = compute_metrics(all_prod_ids, labeled_events)
        cand_m = compute_metrics(all_cand_ids, labeled_events)
        result["production_metrics"] = prod_m
        result["candidate_metrics"]  = cand_m

    # Log evaluation result
    with open(SHADOW_EVALUATIONS_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"evaluated_at": _now(), **result}) + "\n")

    return result


# ═══ Promotion ═══════════════════════════════════════════════════════════════

def promote_candidate(session_id: str) -> bool:
    """
    If candidate is recommended, patch RULE_THRESHOLDS in detect.py
    and mark the session as promoted. Returns True if promoted.

    This writes detect.py directly.  Review the diff before accepting.
    """
    import detect

    session = _load_session(session_id)
    evaluation = evaluate_session(session_id)

    if evaluation.get("recommendation") != "promote":
        print(f"  ❌ Session '{session_id}' is not recommended for promotion.")
        print(f"     candidate_only={evaluation['candidate_only_total']}  "
              f"production_only={evaluation['production_only_total']}")
        return False

    print("  Applying candidate thresholds to detect.RULE_THRESHOLDS...")
    for rule_id, params in session["candidate_thresholds"].items():
        if rule_id in detect.RULE_THRESHOLDS:
            detect.RULE_THRESHOLDS[rule_id].update(params)
            print(f"    {rule_id}: {params}")

    session["status"] = STATUS_PROMOTED
    session["promoted_at"] = _now()
    _save_session(session)

    print("  ✅ Candidate promoted in-memory. Update RULE_THRESHOLDS in detect.py to persist.")
    return True


# ═══ CLI ═════════════════════════════════════════════════════════════════════

def _cli() -> None:
    parser = argparse.ArgumentParser(description="SecOps Shadow Evaluation CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--start",    action="store_true", help="Start a new shadow session")
    group.add_argument("--status",   action="store_true", help="List all shadow sessions")
    group.add_argument("--evaluate", metavar="SESSION_ID",  help="Evaluate a session")
    group.add_argument("--promote",  metavar="SESSION_ID",  help="Promote a session candidate")

    parser.add_argument("--candidate",    default="{}", help='JSON dict of threshold overrides')
    parser.add_argument("--soak-hours",   type=int, default=24)
    parser.add_argument("--description",  default="")

    args = parser.parse_args()

    if args.start:
        try:
            overrides = json.loads(args.candidate)
        except json.JSONDecodeError as exc:
            print(f"❌ Invalid JSON for --candidate: {exc}")
            sys.exit(1)
        start_session(overrides, soak_hours=args.soak_hours, description=args.description)

    elif args.status:
        sessions = list_sessions()
        if not sessions:
            print("No shadow sessions found.")
            return
        print(f"\n{'ID':30s} {'Status':10s} {'Batches':8s} {'Events':10s} {'Description'}")
        print("─" * 80)
        for s in sessions:
            print(f"{s['session_id']:30s} {s['status']:10s} "
                  f"{s['batch_count']:8d} {s['total_events']:10d} {s['description'][:30]}")

    elif args.evaluate:
        result = evaluate_session(args.evaluate)
        print(json.dumps(result, indent=2))

    elif args.promote:
        promoted = promote_candidate(args.promote)
        sys.exit(0 if promoted else 1)


if __name__ == "__main__":
    _cli()
