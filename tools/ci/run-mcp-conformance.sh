#!/usr/bin/env bash
set -uo pipefail

cache=.cache/knowledge-hub/mcp-conformance
mkdir -p "$cache/scenarios"
mapfile -t scenarios < <(
  rtk python3 - <<'PY'
import json
from pathlib import Path
policy = json.loads(Path('registry/mcp-conformance-policy.json').read_text(encoding='utf-8'))
for scenario in policy['required_official_scenarios']:
    print(scenario)
PY
)
: > "$cache/scenario-exits.tsv"
overall=0

for scenario in "${scenarios[@]}"; do
  before="$(find results -type f -name checks.json 2>/dev/null | wc -l || true)"
  set +e
  npx --yes @modelcontextprotocol/conformance@0.2.0-alpha.10 \
    server --url http://127.0.0.1:3000/mcp \
    --scenario "$scenario" --spec-version 2026-07-28 --verbose \
    2>&1 | tee "$cache/scenarios/$scenario.log"
  rc=${PIPESTATUS[0]}
  set -e
  printf '%s\t%s\n' "$scenario" "$rc" >> "$cache/scenario-exits.tsv"
  latest="$(find results -type f -name checks.json -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)"
  after="$(find results -type f -name checks.json 2>/dev/null | wc -l || true)"
  if [[ -n "$latest" && "$after" -gt "$before" ]]; then
    cp "$latest" "$cache/scenarios/$scenario.checks.json"
  else
    overall=1
  fi
  if [[ "$rc" -ne 0 ]]; then
    overall=1
  fi
done

rtk python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path('.cache/knowledge-hub/mcp-conformance')
policy = json.loads(Path('registry/mcp-conformance-policy.json').read_text(encoding='utf-8'))
exits = {}
path = root / 'scenario-exits.tsv'
if path.exists():
    for line in path.read_text(encoding='utf-8').splitlines():
        name, value = line.split('\t', 1)
        exits[name] = int(value)

rows = []
all_success = True
for scenario in policy['required_official_scenarios']:
    checks_path = root / 'scenarios' / (scenario + '.checks.json')
    checks = []
    if checks_path.exists():
        checks = json.loads(checks_path.read_text(encoding='utf-8'))
    failures = [row for row in checks if str(row.get('status', '')).upper() == 'FAILURE']
    untestable = [row for row in failures if bool((row.get('details') or {}).get('untestable'))]
    substantive = [row for row in failures if row not in untestable]
    digest = hashlib.sha256(checks_path.read_bytes()).hexdigest() if checks_path.exists() else ''
    rc = exits.get(scenario, 255)
    passed = rc == 0 and bool(checks) and not failures
    all_success = all_success and passed
    rows.append({
        'scenario': scenario,
        'exit_code': rc,
        'check_count': len(checks),
        'failure_count': len(failures),
        'untestable_failure_count': len(untestable),
        'substantive_failure_count': len(substantive),
        'failure_ids': [str(row.get('id', '')) for row in failures],
        'checks_sha256': digest,
        'passed': passed,
    })

receipt = {
    'schema_version': 'knowledge-hub.mcp-conformance-evidence.v1',
    'repository': os.environ.get('GITHUB_REPOSITORY', ''),
    'source_revision': os.environ.get('GITHUB_SHA', ''),
    'github_run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
    'github_run_attempt': int(os.environ.get('GITHUB_RUN_ATTEMPT', '0')),
    'protocol_version': policy['protocol_version'],
    'native_profile': policy['native_profile'],
    'claim_scope': policy['claim_scope'],
    'runner': {
        'package': policy['runner']['package'],
        'version': (root / 'runner-version.txt').read_text(encoding='utf-8').strip() if (root / 'runner-version.txt').exists() else '',
        'integrity': (root / 'runner-integrity.txt').read_text(encoding='utf-8').strip() if (root / 'runner-integrity.txt').exists() else '',
    },
    'expected_failure_baseline_used': False,
    'required_scenarios': policy['required_official_scenarios'],
    'scenarios': rows,
    'all_required_scenarios_passed': all_success,
}
canonical = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
receipt['result_sha256'] = hashlib.sha256(canonical).hexdigest()
(root / 'evidence.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
PY

exit "$overall"
