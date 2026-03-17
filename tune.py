"""
SecOps Autoresearch — Threshold Tuner
Sweeps configurable thresholds in detect.py (via RULE_THRESHOLDS) to find
optimal values that maximise F1 while minimising false positive rate.

Usage:
    python tune.py                            # Grid-search all rules
    python tune.py --rule brute_force         # Tune one rule only
    python tune.py --quick                    # Coarse grid, ~10x faster
    python tune.py --output results/tune.json # Custom output path

How it works:
    tune.py patches detect.RULE_THRESHOLDS (a mutable module-level dict)
    between runs, so no file rewriting is needed. Each candidate combination
    is evaluated against the full labeled dataset and the overall + per-rule
    F1 scores are recorded.

DO NOT MODIFY THIS FILE. The agent only modifies detect.py.
"""

import argparse
import copy
import itertools
import json
import os
import sys
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import detect
from evaluate import compute_metrics, compute_per_rule_metrics

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
UNLABELED_FILE = os.path.join(DATA_DIR, "events_unlabeled.json")

# ═══ Search Spaces ═══════════════════════════════════════════════════════════
# Reduce range sizes for --quick mode; full grid otherwise.

SEARCH_SPACE: Dict[str, Dict[str, List[Any]]] = {
    "brute_force": {
        "RAPID_THRESHOLD":        [4, 5, 6, 7, 8, 10, 12],
        "RAPID_WINDOW_MINUTES":   [5, 8, 10, 15, 20],
        "SLOW_THRESHOLD":         [2, 3, 4, 5],
        "SLOW_MIN_SPAN_MINUTES":  [15, 20, 30, 45, 60],
    },
    "dns_exfiltration": {
        "MIN_QUERIES_PER_DOMAIN": [3, 4, 5, 6, 8],
        "MIN_LABEL_LENGTH":       [10, 12, 15, 20, 25],
        "MIN_ENTROPY":            [2.5, 3.0, 3.5, 4.0],
        "MIN_UNIQUE_LABEL_RATIO": [0.6, 0.7, 0.8, 0.9],
    },
    "c2_beaconing": {
        "MIN_CONNECTIONS": [3, 5, 8, 10, 15],
        "MAX_BYTES_OUT":   [300, 400, 500, 600, 800, 1000],
        "MAX_BYTES_IN":    [150, 200, 250, 300, 400],
    },
    "lateral_movement": {
        "UNIQUE_DEST_THRESHOLD":    [3, 4, 5, 6],
        "WINDOW_MINUTES":           [10, 15, 20, 30],
        "MAX_AVERAGE_GAP_SECONDS":  [120, 180, 240, 360, 480],
        "MAX_TRANSFER_BYTES":       [50_000, 75_000, 100_000, 200_000],
    },
}

# Coarser grid for --quick mode (every other value)
QUICK_SEARCH_SPACE: Dict[str, Dict[str, List[Any]]] = {
    rule_id: {param: vals[::2] for param, vals in params.items()}
    for rule_id, params in SEARCH_SPACE.items()
}

# Maps rule_id → RULE-NNN for per-rule metric lookup
RULE_ID_MAP: Dict[str, str] = {
    "brute_force":       "RULE-001",
    "dns_exfiltration":  "RULE-002",
    "c2_beaconing":      "RULE-003",
    "lateral_movement":  "RULE-004",
}


# ═══ Data Loading ════════════════════════════════════════════════════════════

def load_events() -> Tuple[List[Dict], List[Dict]]:
    if not os.path.exists(EVENTS_FILE):
        print("❌ No data found. Run `python prepare.py` first.")
        sys.exit(1)
    with open(EVENTS_FILE) as f:
        labeled = json.load(f)
    with open(UNLABELED_FILE) as f:
        unlabeled = json.load(f)
    return labeled, unlabeled


# ═══ Evaluation ══════════════════════════════════════════════════════════════

def evaluate_with_thresholds(
    labeled: List[Dict],
    unlabeled: List[Dict],
    override: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Patch detect.RULE_THRESHOLDS, run detection, restore, return metrics.
    Thread-unsafe (module-level state mutation) — run sweep single-threaded.
    """
    saved = copy.deepcopy(detect.RULE_THRESHOLDS)
    for rule_id, params in override.items():
        detect.RULE_THRESHOLDS[rule_id].update(params)

    try:
        results = detect.run_detection(unlabeled)
        overall = compute_metrics(results["detected_event_ids"], labeled)
        per_rule = compute_per_rule_metrics(results["rule_results"], labeled)
        return overall, per_rule
    finally:
        detect.RULE_THRESHOLDS.clear()
        detect.RULE_THRESHOLDS.update(saved)


# ═══ Sweep ═══════════════════════════════════════════════════════════════════

def sweep_one_rule(
    rule_id: str,
    labeled: List[Dict],
    unlabeled: List[Dict],
    space: Dict[str, Dict[str, List[Any]]],
) -> Dict[str, Any]:
    """
    Grid-search all threshold combinations for a single rule, fixing all
    other rules at their defaults. Returns the best-found configuration.
    """
    param_names = list(space[rule_id].keys())
    param_values = [space[rule_id][k] for k in param_names]
    total = 1
    for v in param_values:
        total *= len(v)

    rule_num = RULE_ID_MAP.get(rule_id, "RULE-???")
    print(f"\n  Sweeping {rule_id} ({total} combinations)...")

    best: Dict[str, Any] = {"f1": -1.0, "overall_f1": -1.0, "params": {}, "rule_metrics": {}, "overall_metrics": {}}

    for combo in itertools.product(*param_values):
        params = dict(zip(param_names, combo))
        overall, per_rule = evaluate_with_thresholds(labeled, unlabeled, {rule_id: params})

        # Optimise for the per-rule F1 of the target rule; break ties with overall F1
        rule_m = per_rule.get(rule_num, overall)
        f1 = rule_m.get("f1_score", 0.0)
        overall_f1 = overall["f1_score"]

        if f1 > best["f1"] or (f1 == best["f1"] and overall_f1 > best["overall_f1"]):
            best = {
                "f1":            f1,
                "overall_f1":    overall_f1,
                "params":        params,
                "rule_metrics":  rule_m,
                "overall_metrics": overall,
            }

    return best


def sweep_all_rules(
    labeled: List[Dict],
    unlabeled: List[Dict],
    space: Dict[str, Dict[str, List[Any]]],
    rules: List[str],
) -> Dict[str, Any]:
    """Sweep each rule independently and return the combined best recommendations."""
    baseline_overall, baseline_per_rule = evaluate_with_thresholds(labeled, unlabeled, {})
    print(f"\n  Baseline overall F1: {baseline_overall['f1_score']:.6f}")

    results: Dict[str, Any] = {
        "baseline": {
            "overall": baseline_overall,
            "per_rule": baseline_per_rule,
        },
        "best_per_rule": {},
    }

    for rule_id in rules:
        best = sweep_one_rule(rule_id, labeled, unlabeled, space)
        results["best_per_rule"][rule_id] = best

        improved = best["f1"] > baseline_per_rule.get(RULE_ID_MAP.get(rule_id, ""), {}).get("f1_score", 0.0)
        marker = " ✓ improved" if improved else ""
        print(f"  Best {rule_id}: F1={best['f1']:.4f} (overall={best['overall_f1']:.4f}){marker}")
        for k, v in best["params"].items():
            current = detect.RULE_THRESHOLDS[rule_id][k]
            delta = " ← change recommended" if v != current else ""
            print(f"    {k:35s} = {str(v):>10}{delta}")

    return results


# ═══ Main ════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SecOps threshold tuner — grid-search RULE_THRESHOLDS"
    )
    parser.add_argument(
        "--rule",
        choices=list(SEARCH_SPACE.keys()),
        default=None,
        help="Tune a single rule (default: all rules)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a coarser grid (~10x faster, less thorough)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(DATA_DIR, "tune_results.json"),
        help="Path to write JSON results (default: data/tune_results.json)",
    )
    args = parser.parse_args()

    labeled, unlabeled = load_events()
    space = QUICK_SEARCH_SPACE if args.quick else SEARCH_SPACE
    rules_to_tune = [args.rule] if args.rule else list(SEARCH_SPACE.keys())
    mode = "quick" if args.quick else "full"

    print(f"\n{'═' * 60}")
    print(f"  SecOps Autoresearch — Threshold Tuner ({mode} grid)")
    print(f"  Rules: {', '.join(rules_to_tune)}")
    print(f"{'═' * 60}")

    results = sweep_all_rules(labeled, unlabeled, space, rules_to_tune)

    os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'═' * 60}")
    print(f"  Results saved to {args.output}")
    print(f"  To apply: copy recommended params into RULE_THRESHOLDS in detect.py")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()
