#!/usr/bin/env bash
set -uo pipefail

cache=.cache/knowledge-hub/mcp-conformance
mkdir -p "$cache/scenarios"
source_revision="$(git rev-parse --verify HEAD)"
if [[ ! "$source_revision" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'invalid checked-out revision: %s\n' "$source_revision" >&2
  exit 1
fi
export KNOWLEDGE_HUB_SOURCE_REVISION="$source_revision"
mapfile -t scenarios < <(
  rtk python3 - <<'PY'
import json
from pathlib import Path
policy = json.loads(Path('registry/mcp-conformance-policy.json').read_text(encoding='utf-8'))
for scenario in policy['hosted_official_scenarios']:
    print(scenario)
PY
)
: > "$cache/scenario-exits.tsv"

for scenario in "${scenarios[@]}"; do
  npx --yes @modelcontextprotocol/conformance@0.2.0-alpha.10 \
    server --url http://127.0.0.1:3000/mcp \
    --scenario "$scenario" --spec-version 2026-07-28 --verbose \
    2>&1 | tee "$cache/scenarios/$scenario.log"
  rc=${PIPESTATUS[0]}
  printf '%s\t%s\n' "$scenario" "$rc" >> "$cache/scenario-exits.tsv"
done

rtk python3 - <<'PY'
import hashlib
import json
import os
import re
import sys
from pathlib import Path

root = Path('.cache/knowledge-hub/mcp-conformance')
policy = json.loads(Path('registry/mcp-conformance-policy.json').read_text(encoding='utf-8'))
exits = {}
path = root / 'scenario-exits.tsv'
if path.exists():
    for line in path.read_text(encoding='utf-8').splitlines():
        name, value = line.split('\t', 1)
        exits[name] = int(value)

resource_smoke_path = root / 'product-resource-read.json'
resource_smoke = False
if resource_smoke_path.exists():
    try:
        payload = json.loads(resource_smoke_path.read_text(encoding='utf-8'))
        result = payload.get('result', {})
        contents = result.get('contents', []) if isinstance(result, dict) else []
        resource_smoke = (
            result.get('resultType') == 'complete'
            and result.get('ttlMs') == 0
            and result.get('cacheScope') == 'private'
            and bool(contents)
            and contents[0].get('uri') == 'knowledge://health'
        )
    except (OSError, ValueError, TypeError, AttributeError):
        resource_smoke = False

rows = []
profile_contract_passed = resource_smoke
all_raw_scenarios_passed = True
for scenario in policy['hosted_official_scenarios']:
    log_path = root / 'scenarios' / (scenario + '.log')
    log_text = log_path.read_text(encoding='utf-8', errors='replace') if log_path.exists() else ''
    summary_match = re.search(r'Passed:\s*(\d+)/(\d+),\s*(\d+) failed,\s*(\d+) warnings', log_text)
    summary = None
    if summary_match:
        summary = {
            'passed': int(summary_match.group(1)),
            'total': int(summary_match.group(2)),
            'failed': int(summary_match.group(3)),
            'warnings': int(summary_match.group(4)),
        }
    observed_failures = re.findall(r'^  - ([A-Za-z0-9_-]+):', log_text, flags=re.MULTILINE)
    allowed = list(policy['profile_applicability'][scenario]['allowed_non_applicable_failures'])
    rc = exits.get(scenario, 255)
    raw_passed = rc == 0 and summary is not None and summary['failed'] == 0
    all_raw_scenarios_passed = all_raw_scenarios_passed and raw_passed
    exact_applicability = (
        summary is not None
        and summary['failed'] == len(observed_failures)
        and sorted(observed_failures) == sorted(allowed)
        and ((not allowed and rc == 0) or (allowed and rc != 0))
    )
    profile_contract_passed = profile_contract_passed and exact_applicability
    untestable_messages = re.findall(r'Error:\s*(Not testable:[^\n\r]+)', log_text)
    rows.append({
        'scenario': scenario,
        'upstream_exit_code': rc,
        'runner_summary': summary,
        'observed_failure_names': observed_failures,
        'allowed_non_applicable_failures': allowed,
        'applicable_failure_count': len([name for name in observed_failures if name not in allowed]),
        'untestable_message_count': len(untestable_messages),
        'raw_upstream_passed': raw_passed,
        'profile_applicability_passed': exact_applicability,
        'log_sha256': hashlib.sha256(log_path.read_bytes()).hexdigest() if log_path.exists() else '',
    })

receipt = {
    'schema_version': 'knowledge-hub.mcp-conformance-evidence.v2',
    'repository': os.environ.get('GITHUB_REPOSITORY', ''),
    'source_revision': os.environ.get('KNOWLEDGE_HUB_SOURCE_REVISION', ''),
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
    'hosted_official_scenarios': policy['hosted_official_scenarios'],
    'product_resource_read_smoke_passed': resource_smoke,
    'scenarios': rows,
    'all_raw_upstream_scenarios_passed': all_raw_scenarios_passed,
    'profile_contract_passed': profile_contract_passed,
}
canonical = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
receipt['result_sha256'] = hashlib.sha256(canonical).hexdigest()
(root / 'evidence.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('KNOWLEDGE_HUB_MCP_RECEIPT=' + json.dumps(receipt, ensure_ascii=False, sort_keys=True))
sys.exit(0 if profile_contract_passed else 1)
PY
