"""
SecOps Autoresearch — Detection Explainability  [SCAFFOLD — Item 8]
Generates human-readable reason codes and matched-feature summaries for
every detection so analysts understand WHY an alert fired.

MOTIVATION:
  "Alert fatigue" is exacerbated when analysts cannot quickly judge whether
  an alert is credible. A one-line reason code (e.g. "T1110: 12 failures in
  8 min from 203.0.113.5 — user admin") lets a Tier-1 analyst confirm or
  dismiss in seconds instead of pivoting to SIEM manually.

DESIGN:
  Each detection function is expected to return optional metadata alongside
  matching event IDs. explain.py assembles that metadata into:

    {
      "event_id":   "EVT-00042",
      "rule_id":    "RULE-001",
      "rule_name":  "Brute Force",
      "mitre":      "T1110",
      "reason":     "12 failures in 7.3 min from 203.0.113.5 targeting user admin",
      "features":   {
        "failure_count":         12,
        "window_minutes":        7.3,
        "src_ip":                "203.0.113.5",
        "target_user":           "admin",
        "subsequent_success":    true,
        "confidence":            0.94
      },
      "mitre_url":  "https://attack.mitre.org/techniques/T1110/",
      "timestamp":  "2026-03-17T14:22:00Z"
    }

TODO — implement the following:

  def explain_brute_force(events: List[Dict], detected_ids: Set[str]) -> List[Dict]:
      \"\"\"
      For each detected group, extract:
        - failure_count, window_minutes, src_ip, target_user
        - whether a subsequent success occurred (credential compromise indicator)
      \"\"\"
      ...

  def explain_dns_exfiltration(events: List[Dict], detected_ids: Set[str]) -> List[Dict]:
      \"\"\"
      For each flagged (src_ip, domain) pair, extract:
        - query_count, average_label_length, max_entropy,
          unique_label_ratio, has_txt_queries
      \"\"\"
      ...

  def explain_c2_beaconing(events: List[Dict], detected_ids: Set[str]) -> List[Dict]:
      \"\"\"
      For each flagged (src, dest) pair, extract:
        - connection_count, interval_cv (periodicity score),
          max_bytes_out, max_bytes_in, dest_port
      \"\"\"
      ...

  def explain_lateral_movement(events: List[Dict], detected_ids: Set[str]) -> List[Dict]:
      \"\"\"
      For each flagged source IP, extract:
        - unique_dest_count, window_minutes, average_gap_seconds,
          max_transfer_bytes, dest_ips list
      \"\"\"
      ...

  def explain_all(
      events: List[Dict],
      rule_results: Dict[str, List[str]],
      detection_rules: List[Dict],
  ) -> List[Dict]:
      \"\"\"
      Dispatch to per-rule explainers and return a flat list of
      explanation records, one per detected event_id.
      \"\"\"
      ...

  def format_markdown(explanations: List[Dict]) -> str:
      \"\"\"Render explanations as a Markdown table for PR comments / reports.\"\"\"
      ...

  def write_explanations(
      explanations: List[Dict],
      path: str = \"data/explanations.json\",
  ) -> None:
      \"\"\"Persist latest explanation set to disk.\"\"\"
      ...

INTEGRATION POINTS:
  - evaluate.py --verbose should call explain_all() and include reason codes
    in the per-rule breakdown output.
  - findings.py create_finding() should embed an explanation summary.
  - benchmark.yml should upload data/explanations.json as a build artifact.
  - The MkDocs docs site can render the latest explanations.json as a live
    alert sample on the Example Attack Scenarios page.

RULE COVERAGE (explainers needed for each DETECTION_RULES entry):
  RULE-001 Brute Force            → explain_brute_force()
  RULE-002 DNS Exfiltration       → explain_dns_exfiltration()
  RULE-003 C2 Beaconing           → explain_c2_beaconing()
  RULE-004 Lateral Movement       → explain_lateral_movement()
  RULE-005 PowerShell Abuse       → explain_powershell_abuse()     [TODO]
  RULE-006 Privilege Escalation   → explain_privilege_escalation() [TODO]
  RULE-007 Fileless LOLBins       → explain_fileless_lolbins()     [TODO]
  RULE-101..110 OpenClaw rules    → explain_openclaw()             [TODO]
"""

EXPLANATIONS_FILE = "data/explanations.json"

MITRE_BASE_URL = "https://attack.mitre.org/techniques/"


def mitre_url(technique_id: str) -> str:
    """Return the ATT&CK URL for a technique ID (e.g. 'T1110' → URL)."""
    tid = technique_id.replace(".", "/")
    return f"{MITRE_BASE_URL}{tid}/"


def _not_implemented(*_args, **_kwargs):
    raise NotImplementedError(
        "explain.py is a scaffold. See TODO comments for the implementation plan."
    )


explain_brute_force = _not_implemented
explain_dns_exfiltration = _not_implemented
explain_c2_beaconing = _not_implemented
explain_lateral_movement = _not_implemented
explain_all = _not_implemented
format_markdown = _not_implemented
write_explanations = _not_implemented
