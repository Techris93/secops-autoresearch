# Contributing to SecOpsAI

Thanks for your interest in contributing! SecOpsAI is an open-source project and welcomes contributions of all kinds — bug fixes, new detection rules, improved mitigations, docs, and tests.

## Getting Started

```bash
git clone https://github.com/Techris93/secopsai.git
cd secopsai
bash setup.sh
source .venv/bin/activate

# Run the test suite
python -m unittest discover -s tests -v

# Run the benchmark
python evaluate.py
```

## How to Contribute

### 1. Adding or improving a detection rule

Detection rules live in `detect.py` under `DETECTION_RULES` (for metadata) and `run_detection()` (for logic). Each rule must have:

- A stable `id` (e.g. `RULE-110`)
- A `name` and `mitre` technique ID
- Corresponding logic in `run_detection()` that returns a set of `event_id` strings
- At least one test case in `tests/test_regression.py` or a new test file

After adding a rule, run:

```bash
python evaluate.py --verbose
```

and confirm the F1 score doesn't regress on the synthetic benchmark.

### 2. Adding mitigation steps for a rule

Mitigation steps live in `MITIGATION_BY_RULE` in `openclaw_plugin.py`. Each entry is keyed by rule ID and contains a list of 3–5 actionable strings:

```python
"RULE-110": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ...",
],
```

Keep each step short, actionable, and specific to the threat pattern the rule detects.

### 3. Improving docs

Docs live in `docs/`. The most important files for new users are:

- `docs/getting-started.md`
- `docs/OpenClaw-Integration.md`
- `docs/BEGINNER-LIVE-GUIDE.md`
- `docs/rules-registry.md`

### 4. Reporting a bug

Open an issue at https://github.com/Techris93/secopsai/issues with:

- What you ran
- What you expected
- What happened (output or stack trace)
- Python version (`python --version`) and OS

### 5. Security issues

Please do **not** open a public issue for security vulnerabilities. Instead, reach out privately via the GitHub security advisory feature.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a short description of _what_ and _why_
- Run `python -m unittest discover -s tests -v` before opening a PR
- Run `python evaluate.py` and include the F1 output if you changed `detect.py`

## Code Style

- Python 3.10+, standard library only (no third-party dependencies in core)
- All file I/O must use `encoding="utf-8"`
- No unused imports; no bare `except`
- Follow the existing patterns in the file you're editing
