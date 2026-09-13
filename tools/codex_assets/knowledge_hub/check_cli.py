import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
from .common import KnowledgeHubError, display_path, file_sha256, load_markdown, user_path_prefixes
from .model import FRONTMATTER_MIRROR_FIELDS, validate_item
from .output_contract import status_contract
from .security import scan_secret_text
from .source_coverage import select_source_coverage_closeout
from .check_validation_pre import run_pre_after, run_pre_before
from .check_validation_registry import run_registry_head, run_registry_rest
from .check_validation_governance import run_governance
from .check_validation_post import run_body_coverage, run_index_security
root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]
parser = argparse.ArgumentParser(description='Validate Knowledge Hub registry and safety boundaries.')
parser.add_argument('--dry-run', action='store_true')
output_mode = parser.add_mutually_exclusive_group()
output_mode.add_argument('--json', action='store_true')
output_mode.add_argument('--summary-json', action='store_true')
parser.add_argument('--sources-only', action='store_true')
parser.add_argument('--explain', default='', metavar='ITEM_ID')
parser.add_argument('--diagnostics', action='store_true')
parser.add_argument('--as-of', default='', metavar='YYYY-MM-DD', help='Use a fixed date for review_after checks.')
args = parser.parse_args(argv)
errors = []
warnings = []
explain = None
READABILITY_GATE_START = dt.date(2026, 6, 21)

def resolve_today():
    if args.as_of:
        raw_value = args.as_of
        source = 'arg:--as-of'
    else:
        raw_value = os.environ.get('KNOWLEDGE_TODAY', '')
        source = 'env:KNOWLEDGE_TODAY' if raw_value else 'system-date'
    if raw_value:
        try:
            return (dt.date.fromisoformat(raw_value), source)
        except Exception:
            parser.error(f'invalid date for {source}: {raw_value}')
    return (dt.date.today(), source)
today, today_source = resolve_today()
TEXT_FILE_SUFFIXES = {'.md', '.json', '.jsonl', '.sh', '.txt'}

def iter_text_files(scan_roots, suffixes=TEXT_FILE_SUFFIXES):
    seen_paths = set()
    for base in scan_roots:
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else base.rglob('*')
        for path in candidates:
            if path in seen_paths:
                continue
            seen_paths.add(path)
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            yield path

def frontmatter_scalar(path, field):
    try:
        lines = path.read_text(errors='ignore').splitlines()
    except Exception:
        return ''
    if not lines or lines[0].strip() != '---':
        return ''
    pattern = re.compile(f'^{re.escape(field)}:\\s*(.*?)\\s*$')
    for line in lines[1:]:
        if line.strip() == '---':
            break
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip('"\'')
    return ''

def normalize_frontmatter_value(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): normalize_frontmatter_value(row) for key, row in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_frontmatter_value(row) for row in value]
    return value
if args.sources_only and args.explain:
    warnings.append(f'knowledge-check: --explain is ignored with --sources-only: {args.explain}')
ALLOWED_ITEM_KINDS = {'standard', 'runbook', 'architecture', 'decision', 'project-current', 'project-archive', 'validation', 'audit', 'patent', 'debug-record', 'external-source-note', 'owner-decision-worksheet', 'patent-disclosure', 'codex-session', 'codex-workflow', 'personal-note', 'artifact-ref', 'authorization', 'automation-run'}
ALLOWED_ITEM_STATUSES = {'draft', 'active', 'reviewing', 'archived', 'superseded', 'rejected', 'personal'}
ALLOWED_ITEM_SCOPES = {'team-general', 'project-specific', 'codex-memory-curation-governance'}
ALLOWED_ITEM_VISIBILITIES = {'team-internal', 'personal-local'}
ALLOWED_ITEM_PROMOTIONS = {'none'}
OWNER_GATE_BLOCKING_REVIEW_STATUSES = {'pending-owner-review', 'needs-owner-resolution', 'owner-intake-ready', 'source-identity-match', 'embedded-knowledge-owner-review-required', 'blocked-pending-owner-review', 'blocked-pending-owner-status-decision', 'blocked-personal-local', 'blocked-pending-archive-metadata'}
ALLOWED_DOMAIN_ROOTS = {'root', 'governance', 'projects', 'notes', 'embedded', 'patents', 'codex'}
ALLOWED_SOURCE_ROLES = {'hub-canonical-source', 'hub-native-source', 'hub-runtime-input'}
ALLOWED_SOURCE_AUTHORITIES = {'knowledge-hub-canonical', 'knowledge-hub-ledger', 'runtime-input-provenance'}
ALLOWED_SOURCE_STATUSES = {'registered', 'retired'}
ALLOWED_SOURCE_WRITE_POLICIES = {'knowledge-hub-only', 'hub-native-registry', 'runtime-read-only-input'}
ALLOWED_SOURCE_FINAL_DISPOSITIONS = {'hub-canonical', 'hub-native-source', 'runtime-input-reference-only'}
ALLOWED_SOURCE_CONTROL_OBJECT_TYPES = {'markdown', 'session', 'history', 'tool', 'source-code', 'config', 'artifact', 'binary', 'log', 'archive', 'manifest', 'automation-run', 'unknown'}
ALLOWED_SOURCE_CONTROL_DISPOSITIONS = {'copy-body', 'summary-only', 'artifact-ref', 'reference-only', 'archive-only', 'hash-only-provenance', 'exclude'}
ALLOWED_SOURCE_CONTROL_STATUSES = {'pending', 'covered', 'blocked', 'excluded'}
SOURCE_CONTROL_REQUIRED_FILES = ['README.md', 'inventory.jsonl', 'coverage.md', 'source-policy.md']
SOURCE_CONTROL_REQUIRED_ROW_FIELDS = ['id', 'source_id', 'source_path', 'object_type', 'hub_disposition', 'target_path', 'status', 'reason_zh', 'risk_zh', 'checked_at']
SOURCE_CONTROL_RAW_OBJECT_TYPES = {'session', 'history', 'source-code', 'binary', 'log'}
LOCAL_PATH_PREFIXES = ('artifacts/', 'docs/', 'domains/', 'inbox/', 'notes/', 'projects/', 'sources/', 'registry/', 'indexes/', 'governance/', 'tools/', 'templates/')
SHA256_RE = re.compile('[0-9a-f]{64}')
REVIEW_CONTENT_BOUND_DECISIONS = {'accept-as-review-record', 'archive-only', 'reject'}
OWNER_DECISION_DRAFT_FIELDS = {'owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'source_sha256', 'source_size', 'evidence_refs', 'status_reason'}
ALLOWED_PROJECT_REGISTRY_STATUSES = {'registered', 'retired'}
ALLOWED_REPOSITORY_LIFECYCLES = {'first-party', 'external-reference', 'workspace-only', 'retired'}
ALLOWED_COMPONENT_STATUSES = {'registered', 'workspace-only', 'external-reference', 'retired'}
ALLOWED_REMOTE_KINDS = {'internal-git', 'github', 'gitee', 'external-git', 'local-only'}
ALLOWED_LOGICAL_WORKSPACE_PREFIXES = ('workspace://', '~/knowledge-hub', '~/codex', '~/.codex')
FORBIDDEN_REGISTRY_PATH_TOKENS = ('/home/', '/vsdata/', '~/work/', '~/embedded', '~/bin/', '/work/', '/bin/')

def contains_forbidden_registry_path(value):
    text = str(value or '')
    return any((token in text for token in FORBIDDEN_REGISTRY_PATH_TOKENS))

def is_allowed_workspace_ref(value):
    text = str(value or '')
    return text.startswith(ALLOWED_LOGICAL_WORKSPACE_PREFIXES)

def registry_relpath_ok(value):
    text = str(value or '')
    if not text:
        return False
    return not pathlib.Path(text).is_absolute() and (not text.startswith(('./', '../', '~')))

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f'{path}: invalid json: {exc}')
        return {}

def load_jsonl(path):
    rows = []
    if not path.exists():
        warnings.append(f'{path}: missing')
        return rows
    for lineno, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f'{path}:{lineno}: invalid jsonl: {exc}')
    return rows

def is_owner_decision_draft_path(path):
    name = path.name
    if name.endswith('.local.jsonl'):
        return False
    if 'owner-decision-worksheets' in name or 'owner-intake-package' in name:
        return False
    return ('owner-decision' in name or 'owner-decisions' in name) and path.suffix == '.jsonl'

def audit_owner_decision_draft_leaks(registered_paths):
    manifest_dir = root / 'artifacts' / 'manifests'
    if not manifest_dir.exists():
        return
    candidate_paths = sorted({*manifest_dir.glob('*owner-decision*.jsonl'), *manifest_dir.glob('*owner-decisions*.jsonl')})
    for path in candidate_paths:
        if not is_owner_decision_draft_path(path):
            continue
        relative = str(path.relative_to(root))
        rows = load_jsonl(path)
        has_owner_fields = any((isinstance(row, dict) and any((str(row.get(field, '')).strip() for field in OWNER_DECISION_DRAFT_FIELDS)) for row in rows))
        if has_owner_fields and relative not in registered_paths:
            warnings.append(f'owner-decision-draft:{relative} non-local owner decision JSONL with owner fields is not registered; use *.local.jsonl for drafts or register an explicit reviewed landing artifact')

def build_diagnostics(error_items, warning_items):
    rules = [('registry-parse', 'registry JSON/JSONL 解析失败', '先修复对应 registry 文件的 JSON 或 JSONL 语法，再重跑 knowledge-check。', lambda msg: 'invalid json' in msg or 'invalid jsonl' in msg), ('source-registry', 'source registry 字段或枚举异常', '检查 registry/sources.json 中对应 source 的 id、role、authority、status 和 write_policy。', lambda msg: msg.startswith('sources:')), ('source-index', 'source index 漏登或残留', '同步 indexes/by-source.md 的 Knowledge Sources 表，确保和 registry/sources.json 一致。', lambda msg: msg.startswith('index:indexes/by-source.md')), ('source-coverage', 'source coverage 终态矩阵异常', '更新最新 artifacts/manifests/knowledge-hub-source-coverage-closeout-*.jsonl，确保每个 registered source 都有终态分类、决策和风险说明。', lambda msg: msg.startswith('source-coverage:')), ('source-control', 'source 主控目录异常', '检查 sources/<source_id>/README.md、inventory.jsonl、coverage.md、source-policy.md，确保每个 registered source 都有 Hub 内控制面，raw/session/source-code 不能 copy-body 进入正文层。', lambda msg: msg.startswith('source-control:')), ('owner-target', 'owner 决策目标缺失', '检查 owner decision landing JSONL 的 target_decision，并确认已映射到硬切换后的 projects/ 目标文件；reference-only/report-only 项不要求本地正文目标。', lambda msg: msg.startswith('owner-target:')), ('owner-decision-draft', 'owner decision 草稿命名异常', '将未签收 owner decision 草稿改为 *.local.jsonl，或在真实 owner 签收后登记为 reviewed landing artifact；Codex 不代签、不关闭 gate。', lambda msg: msg.startswith('owner-decision-draft:')), ('automation-boundary', '自动化 report-only / no-memory 边界异常', '检查 registry/maintenance-runs.jsonl 中 enabled、mode、writes_memory、writes_team_active_index 和 no_memory_write_gate 字段；自动化默认只能 read-only/report-only/plan-only/local-commit。', lambda msg: msg.startswith('maintenance-runs:')), ('boundary-health', 'PCR02 boundary manifest 内部证据异常', '检查 PCR02 Level 2 boundary manifest、registry item、by-source 和 by-project 索引；该检查只看 Knowledge Hub 内部证据，不读取源项目正文。', lambda msg: msg.startswith('boundary-health:')), ('owner-gated-active', 'owner-gated 源路径被提升为 active', '检查 owner decision worksheets 和 item owner gate 字段；未完成 owner 决策、目标决策和复核证据前，不要登记为 active。', lambda msg: msg.startswith(('owner-gated:', 'owner-gate:'))), ('owner-project-topic-registry', 'owner/project/topic registry 异常', '检查 registry/owners.json、registry/projects.json 或 registry/topics.json 的登记项和枚举。', lambda msg: msg.startswith(('owners:', 'projects:', 'project-groups:', 'repositories:', 'components:', 'project-routes:', 'workspaces:', 'topics:'))), ('owner-routing', 'owner decision 角色路由异常', '检查 registry/owner-routing.json，确保每个 open owner worksheet 角色都有只读分派路由，routing_owner 和 candidate_registry_owners 已登记，且不得把 routing_owner 当作 owner decision。', lambda msg: msg.startswith('owner-routing:')), ('template-schema', '模板字段缺失', '检查 templates/*.md，补齐 registry/schema.md 要求的字段，保持人工新增入口可用。', lambda msg: msg.startswith('template:')), ('manifest-jsonl-profile', 'manifest JSONL 轻量契约异常', '检查 2026-06-21 及之后的 Knowledge Hub governance manifest JSONL，补齐 id、status、中文说明、证据和边界字段；历史 manifest 不做反向强制改写。', lambda msg: msg.startswith('manifest-profile:')), ('manual-entry', '人工新增入口过期', '同步 tools/knowledge-new.sh 和 templates/README.md 中当前 registry/index/source-policy 门禁提示。', lambda msg: msg.startswith('manual-entry:')), ('item-source-ref', 'item source 或 artifact 引用异常', '检查 registry/items.jsonl 中 source_id、source_manifest、source_sha256 或 artifact-ref 元数据。', lambda msg: msg.startswith('items:') and any((token in msg for token in ['source_id', 'source_manifest', 'source_sha256', 'artifact-ref', 'artifact ', 'artifact sha256', 'artifact size']))), ('validation-ref', 'validation_refs 异常', '检查 registry/items.jsonl 中 validation_refs 是否为非空字符串列表；本地路径必须存在，命令型引用不会被执行。', lambda msg: msg.startswith('items:') and 'validation_ref' in msg), ('item-boundary', 'item 字段、枚举或边界异常', '检查 registry/items.jsonl 中对应 item 的必填字段、枚举、domain/path/scope/visibility 边界。', lambda msg: msg.startswith('items:')), ('frontmatter-status', '正文 frontmatter 与 registry 状态不一致', '以 registry/items.jsonl 为生命周期权威；不得自动提升 active。由 owner 确认后，将正文 status 调整为 registry 状态，或按授权更新 registry。', lambda msg: msg.startswith('frontmatter-status:')), ('body-coverage', '长期正文缺少精确登记或冻结集合覆盖', '检查 registry/body-coverage.json 的路径清单 hash；新增 L2 正文应精确登记，历史 corpus 只能通过显式集合覆盖，不能用宽泛前缀静默吞掉新文件。', lambda msg: msg.startswith('body-coverage:')), ('artifact-vault', '附件 vault 完整性异常', '核对 patent artifact manifest 与 artifacts/vault 的 path、size、sha256；缺失附件必须明确标成 external-reference-only，不能宣称本地存在。', lambda msg: msg.startswith('artifact-vault:')), ('core-index', '核心索引覆盖异常', '同步 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md，确保每个 registry item 恰好有规范引用。', lambda msg: msg.startswith(('index:indexes/by-owner.md', 'index:indexes/by-review-date.md', 'index:indexes/by-status.md'))), ('decision-index', '决策索引覆盖异常', '同步 registry/decisions.jsonl 与 indexes/by-decision.md，只要求 registry decision 在决策索引中恰好出现一次，不把 owner worksheet 或 source-policy decision 当作 registry decision。', lambda msg: msg.startswith('index:indexes/by-decision.md')), ('index-local-ref', '索引中的本地路径引用失效', '检查 indexes/*.md 中反引号包裹的本地路径或 glob，修正为存在的 Knowledge Hub 相对路径。', lambda msg: msg.startswith('index:') and 'missing local' in msg), ('active-safety', 'active 安全边界异常', '检查 active bucket、personal-local、AI 生成内容人工复核字段，未满足门禁前不要提升为 active。', lambda msg: 'active bucket references' in msg or 'personal-local' in msg or 'ai-generated active' in msg), ('secret-pattern', '疑似 secret 模式命中', '立即检查对应文本，移除 token、private key、password、cookie 等运行时 secret；保留脱敏引用。', lambda msg: msg.startswith('secret-pattern:')), ('user-path-boundary', '用户绝对路径边界异常', '把长期文本中的用户机器绝对路径改为 ~/ 形式；工具内部可解析真实路径，但对外输出必须脱敏。', lambda msg: msg.startswith('user-path-boundary:')), ('path-routing', '全局路径路由漂移', '按 governance/path-routing.md 收敛旧归档路径；Hub 内不得重新出现会影响回答或新增落盘的旧路径 runtime 入口。', lambda msg: msg.startswith('path-routing:')), ('explain', 'explain 目标不存在', '确认 --explain 参数使用的是 registry/items.jsonl 中真实存在的 item id。', lambda msg: msg.startswith('explain:'))]
    buckets = {}
    for message in error_items:
        category = None
        for category_id, title_zh, action_zh, matcher in rules:
            if matcher(message):
                category = (category_id, title_zh, action_zh)
                break
        if category is None:
            category = ('other', '未分类错误', '查看原始 ERROR 行，必要时补充 diagnostics 分类规则。')
        category_id, title_zh, action_zh = category
        bucket = buckets.setdefault(category_id, {'id': category_id, 'title_zh': title_zh, 'severity': 'error', 'count': 0, 'action_zh': action_zh, 'examples': []})
        bucket['count'] += 1
        if len(bucket['examples']) < 5:
            bucket['examples'].append(message)
    warning_examples = list(warning_items[:5])
    return {'summary_zh': f'发现 {len(error_items)} 个错误，{len(warning_items)} 个警告，归类为 {len(buckets)} 类。', 'categories': sorted(buckets.values(), key=lambda item: (-item['count'], item['id'])), 'warnings': {'count': len(warning_items), 'examples': warning_examples, 'action_zh': 'warning 不阻断检查，但应按 review_after、参数边界或外部 source 可用性安排人工复核。'}}
validation_ctx = dict(globals())
validation_ctx.update({'argparse': argparse, 'dt': dt, 'json': json, 'os': os, 'pathlib': pathlib, 're': re, 'subprocess': subprocess, 'sys': sys, 'KnowledgeHubError': KnowledgeHubError, 'display_path': display_path, 'file_sha256': file_sha256, 'load_markdown': load_markdown, 'user_path_prefixes': user_path_prefixes, 'FRONTMATTER_MIRROR_FIELDS': FRONTMATTER_MIRROR_FIELDS, 'validate_item': validate_item, 'status_contract': status_contract, 'scan_secret_text': scan_secret_text, 'select_source_coverage_closeout': select_source_coverage_closeout})
run_pre_before(validation_ctx)

def local_inventory_target_exists(target_text):
    if not target_text:
        return True
    if pathlib.Path(target_text).is_absolute() or target_text.startswith(('./', '../')):
        return False
    target_path = root / target_text
    if target_text.startswith(LOCAL_PATH_PREFIXES):
        return target_path.exists()
    return True
validation_ctx['local_inventory_target_exists'] = local_inventory_target_exists
run_pre_after(validation_ctx)
source_ids = validation_ctx['source_ids']
current_source_ids = validation_ctx['current_source_ids']
source_check_health = validation_ctx['source_check_health']
source_control_health = validation_ctx['source_control_health']
owner_target_health = validation_ctx['owner_target_health']
automation_safety_health = validation_ctx['automation_safety_health']
authorization_health = validation_ctx['authorization_health']
source_coverage_selection = validation_ctx['source_coverage_selection']
source_coverage_health = validation_ctx['source_coverage_health']
route_registry_health = validation_ctx['route_registry_health']
frontmatter_status_health = validation_ctx['frontmatter_status_health']
body_coverage_health = validation_ctx['body_coverage_health']
artifact_vault_health = validation_ctx['artifact_vault_health']
authorization_rows = validation_ctx['authorization_rows']
authorization_ids = validation_ctx['authorization_ids']
if not args.sources_only:
    run_registry_head(validation_ctx)

    def owner_gate_value_filled(value):
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return bool(value)
        return True

    def owner_gate_row_resolved(row):
        row_state = ' '.join((str(row.get(field, '')) for field in ['worksheet_status', 'row_status', 'status', 'default_state'])).lower()
        if not any((token in row_state for token in ('resolved', 'owner-approved', 'approved', 'closed'))):
            return False
        required_fields = list(row.get('required_owner_fields', []))
        for field in ['owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'review_after', 'source_status', 'evidence_refs', 'status_reason']:
            if field not in required_fields:
                required_fields.append(field)
        return all((owner_gate_value_filled(row.get(field)) for field in required_fields))
    validation_ctx['owner_gate_value_filled'] = owner_gate_value_filled
    validation_ctx['owner_gate_row_resolved'] = owner_gate_row_resolved
    run_registry_rest(validation_ctx)
    run_governance(validation_ctx)
    source_coverage_selection = validation_ctx['source_coverage_selection']
    owner_gated_source_paths = validation_ctx['owner_gated_source_paths']
    owner_gate_roles = validation_ctx['owner_gate_roles']
    owner_ids = validation_ctx['owner_ids']
    owner_route_keys = validation_ctx['owner_route_keys']
    project_ids = validation_ctx['project_ids']
    project_group_ids = validation_ctx['project_group_ids']
    repository_ids = validation_ctx['repository_ids']
    remote_keys = validation_ctx['remote_keys']
    component_ids = validation_ctx['component_ids']
    route_keys = validation_ctx['route_keys']
    topic_ids = validation_ctx['topic_ids']
    local_path_prefixes = validation_ctx['local_path_prefixes']
    ids = set()
    item_ids_by_path = {}
    items = load_jsonl(root / 'registry' / 'items.jsonl')
    registered_item_paths = {str(item.get('path', '')).strip() for item in items if isinstance(item, dict) and str(item.get('path', '')).strip()}
    for item in items:
        if not isinstance(item, dict):
            continue
        validation_refs = item.get('validation_refs', [])
        if not isinstance(validation_refs, list):
            continue
        for validation_ref in validation_refs:
            ref_text = str(validation_ref).strip()
            if ref_text and (not ref_text.startswith('rtk ')) and (not ref_text.startswith('command:')):
                registered_item_paths.add(ref_text)
    audit_owner_decision_draft_leaks(registered_item_paths)
    for item in items:
        item_id = item.get('id')
        if not item_id:
            errors.append('items: missing id')
            continue
        if item_id in ids:
            errors.append(f'items:{item_id} duplicate id')
        ids.add(item_id)
        for model_error in validate_item(item):
            errors.append(f'items:{item_id} model: {model_error}')
        item_path = str(item.get('path', '')).strip()
        if item_path:
            previous_id = item_ids_by_path.get(item_path)
            if previous_id:
                errors.append(f'items:{item_id} duplicate path {item_path}; canonical item is {previous_id}')
            else:
                item_ids_by_path[item_path] = item_id
        for field in ['title', 'kind', 'domain', 'path', 'scope', 'visibility', 'status', 'owner', 'source', 'review_after', 'created_at', 'updated_at', 'promotion', 'tags']:
            if field not in item or item.get(field) in ('', None, []):
                errors.append(f'items:{item_id} missing {field}')
        tags = item.get('tags')
        if tags is not None:
            if not isinstance(tags, list):
                errors.append(f'items:{item_id} tags must be list')
            else:
                for tag in tags:
                    if not isinstance(tag, str) or not tag.strip():
                        errors.append(f'items:{item_id} invalid tag: {tag}')
        if item.get('promotion') and item.get('promotion') not in ALLOWED_ITEM_PROMOTIONS:
            errors.append(f"items:{item_id} invalid promotion: {item.get('promotion')}")
        item_dates = {}
        for field in ['created_at', 'updated_at', 'review_after']:
            value = str(item.get(field, ''))
            if not value:
                continue
            try:
                item_dates[field] = dt.date.fromisoformat(value)
            except Exception:
                errors.append(f'items:{item_id} invalid {field}: {value}')
        if item_dates.get('created_at') and item_dates.get('updated_at'):
            if item_dates['updated_at'] < item_dates['created_at']:
                errors.append(f"items:{item_id} updated_at before created_at: {item.get('updated_at')} < {item.get('created_at')}")
        if item_dates.get('created_at') and item_dates['created_at'] >= READABILITY_GATE_START:
            if item.get('domain') == 'governance' and item.get('kind') == 'audit':
                for field in ['summary_zh', 'primary_language', 'source_language', 'translation_status', 'terminology_status']:
                    if not str(item.get(field, '')).strip():
                        errors.append(f'items:{item_id} missing {field} for post-2026-06-21 governance audit readability gate')
        if item.get('owner') and item.get('owner') not in owner_ids:
            errors.append(f"items:{item_id} owner not registered: {item.get('owner')}")
        validation_refs = item.get('validation_refs')
        if item.get('status') in {'active', 'reviewing'}:
            if validation_refs in (None, []):
                errors.append(f'items:{item_id} active/reviewing missing validation_refs')
        if validation_refs is not None:
            if not isinstance(validation_refs, list):
                errors.append(f'items:{item_id} validation_refs must be list')
            else:
                for validation_ref in validation_refs:
                    if not isinstance(validation_ref, str) or not validation_ref.strip():
                        errors.append(f'items:{item_id} invalid validation_ref: {validation_ref}')
                        continue
                    if ' ' in validation_ref:
                        continue
                    if pathlib.Path(validation_ref).is_absolute() or validation_ref.startswith(('./', '../')):
                        errors.append(f'items:{item_id} validation_ref must be repo-relative or command: {validation_ref}')
                        continue
                    if validation_ref.startswith(local_path_prefixes) or validation_ref in {'README.md', 'AGENTS.md'}:
                        if not (root / validation_ref).exists():
                            errors.append(f'items:{item_id} validation_ref missing local path: {validation_ref}')
                    elif '/' in validation_ref or pathlib.Path(validation_ref).suffix:
                        errors.append(f'items:{item_id} unsupported validation_ref format: {validation_ref}')
        source = item.get('source')
        if source and (not isinstance(source, dict)):
            errors.append(f'items:{item_id} source must be object')
            source = {}
        if isinstance(source, dict):
            item_source_id = source.get('source_id')
            if item_source_id and item_source_id not in source_ids:
                errors.append(f'items:{item_id} source_id not registered: {item_source_id}')
            source_manifest = source.get('source_manifest')
            if source_manifest:
                manifest_path = pathlib.Path(str(source_manifest))
                if manifest_path.is_absolute():
                    errors.append(f'items:{item_id} source_manifest must be relative: {source_manifest}')
                elif not (root / manifest_path).exists():
                    errors.append(f'items:{item_id} source_manifest missing: {source_manifest}')
            source_sha256 = source.get('source_sha256')
            if source_sha256 and (not SHA256_RE.fullmatch(str(source_sha256))):
                errors.append(f'items:{item_id} invalid source_sha256: {source_sha256}')
            item_source_path = source.get('source_path')
            if item.get('status') == 'active' and item_source_id and item_source_path:
                owner_gate_path = owner_gated_source_paths.get((item_source_id, item_source_path))
                if owner_gate_path:
                    errors.append(f'owner-gated:{item_id} active item references unresolved owner-gated source {item_source_id}:{item_source_path} ({owner_gate_path})')
        if item.get('kind') and item.get('kind') not in ALLOWED_ITEM_KINDS:
            errors.append(f"items:{item_id} invalid kind: {item.get('kind')}")
        if item.get('status') and item.get('status') not in ALLOWED_ITEM_STATUSES:
            errors.append(f"items:{item_id} invalid status: {item.get('status')}")
        if item.get('scope') and item.get('scope') not in ALLOWED_ITEM_SCOPES:
            errors.append(f"items:{item_id} invalid scope: {item.get('scope')}")
        if item.get('visibility') and item.get('visibility') not in ALLOWED_ITEM_VISIBILITIES:
            errors.append(f"items:{item_id} invalid visibility: {item.get('visibility')}")
        domain = str(item.get('domain', ''))
        domain_root = domain.split('/', 1)[0] if domain else ''
        if domain and domain_root not in ALLOWED_DOMAIN_ROOTS:
            errors.append(f'items:{item_id} invalid domain root: {domain}')
        if item.get('scope') == 'project-specific' and (not domain.startswith('projects/')):
            errors.append(f'items:{item_id} project-specific scope outside projects domain: {domain}')
        if domain.startswith('projects/'):
            project_id = domain.split('/', 1)[1]
            if project_id not in project_ids:
                errors.append(f'items:{item_id} project not registered: {project_id}')
        if item.get('scope') == 'codex-memory-curation-governance' and domain != 'codex':
            errors.append(f'items:{item_id} codex memory scope outside codex domain: {domain}')
        rel_path = pathlib.Path(str(item.get('path', '')))
        if rel_path.is_absolute():
            errors.append(f'items:{item_id} path must be relative: {rel_path}')
        elif not (root / rel_path).exists():
            errors.append(f'items:{item_id} path missing: {rel_path}')
        elif rel_path.suffix.lower() == '.md':
            frontmatter_status_health['checked_item_count'] += 1
            try:
                frontmatter_metadata, _frontmatter_body = load_markdown(root / rel_path)
            except KnowledgeHubError as exc:
                errors.append(f'frontmatter-status:{item_id} invalid YAML: {exc}')
                frontmatter_metadata = {}
            for field in FRONTMATTER_MIRROR_FIELDS:
                if field not in frontmatter_metadata:
                    continue
                registry_value = normalize_frontmatter_value(item.get(field))
                frontmatter_value = normalize_frontmatter_value(frontmatter_metadata.get(field))
                if registry_value == frontmatter_value:
                    continue
                frontmatter_status_health['mismatch_count'] += 1
                frontmatter_status_health['rows'].append({'item_id': item_id, 'path': rel_path.as_posix(), 'field': field, 'registry_value': registry_value, 'frontmatter_value': frontmatter_value, 'status': 'mismatch'})
                errors.append(f'frontmatter-status:{item_id} field={field} registry={registry_value!r} frontmatter={frontmatter_value!r}: {rel_path.as_posix()}')
            declared_status = frontmatter_scalar(root / rel_path, 'status')
            if declared_status:
                frontmatter_status_health['declared_status_count'] += 1
                row = {'item_id': item_id, 'path': rel_path.as_posix(), 'registry_status': str(item.get('status', '')), 'frontmatter_status': declared_status, 'status': 'pass'}
                if declared_status not in ALLOWED_ITEM_STATUSES:
                    row['status'] = 'invalid-frontmatter-status'
                    frontmatter_status_health['invalid_status_count'] += 1
                    errors.append(f'frontmatter-status:{item_id} invalid status {declared_status}: {rel_path.as_posix()}')
                elif declared_status != str(item.get('status', '')):
                    row['status'] = 'mismatch'
                    frontmatter_status_health['mismatch_count'] += 1
                    errors.append(f"frontmatter-status:{item_id} registry={item.get('status', '')} frontmatter={declared_status}: {rel_path.as_posix()}")
                frontmatter_status_health['rows'].append(row)
            for field, counter in (('owner', 'owner_mismatch_count'), ('review_after', 'review_after_mismatch_count')):
                declared_value = frontmatter_scalar(root / rel_path, field)
                registry_value = str(item.get(field, ''))
                if declared_value and declared_value != registry_value:
                    frontmatter_status_health[counter] += 1
                    frontmatter_status_health['rows'].append({'item_id': item_id, 'path': rel_path.as_posix(), 'field': field, 'registry_value': registry_value, 'frontmatter_value': declared_value, 'status': 'mismatch'})
                    errors.append(f'frontmatter-status:{item_id} field={field} registry={registry_value} frontmatter={declared_value}: {rel_path.as_posix()}')
        human_review_content_sha256 = str(item.get('human_review_content_sha256', ''))
        if human_review_content_sha256:
            if not SHA256_RE.fullmatch(human_review_content_sha256):
                errors.append(f'items:{item_id} invalid human_review_content_sha256: {human_review_content_sha256}')
            elif str(item.get('human_review_decision', '')) in REVIEW_CONTENT_BOUND_DECISIONS and (not rel_path.is_absolute()) and (root / rel_path).is_file():
                current_content_sha256 = file_sha256(root / rel_path)
                if current_content_sha256 != human_review_content_sha256:
                    errors.append(f'items:{item_id} human review content drift: reviewed={human_review_content_sha256} current={current_content_sha256}')
        path_text = str(item.get('path', ''))
        if domain == 'root' and path_text not in {'README.md', 'AGENTS.md'}:
            errors.append(f'items:{item_id} root domain path outside root docs: {path_text}')
        if domain == 'governance' and (not path_text.startswith(('governance/', 'registry/', 'indexes/', 'tools/', 'templates/', 'docs/goals/', 'artifacts/manifests/'))):
            errors.append(f'items:{item_id} governance domain path outside governance control plane: {path_text}')
        if domain.startswith('projects/'):
            project_id = domain.split('/', 1)[1]
            if not path_text.startswith((f'projects/{project_id}/', 'artifacts/manifests/')):
                errors.append(f'items:{item_id} project domain path mismatch: domain={domain} path={path_text}')
        if domain == 'notes' and (not path_text.startswith(('notes/', 'artifacts/manifests/'))):
            errors.append(f'items:{item_id} notes domain path outside notes/control artifacts: {path_text}')
        if domain == 'codex' and (not path_text.startswith(('domains/codex/', 'artifacts/manifests/'))):
            errors.append(f'items:{item_id} codex domain path outside codex control plane: {path_text}')
        if domain == 'embedded' and (not path_text.startswith(('domains/embedded/', 'artifacts/manifests/'))):
            errors.append(f'items:{item_id} embedded domain path outside embedded/control artifacts: {path_text}')
        if domain == 'patents' and (not path_text.startswith(('domains/patents/', 'artifacts/manifests/'))):
            errors.append(f'items:{item_id} patents domain path outside patents/control artifacts: {path_text}')
        if domain == 'personal':
            errors.append(f'items:{item_id} noncanonical personal domain; use domain=notes path=notes/personal/**')
        status = item.get('status')
        if status in {'active', 'reviewing'}:
            if not item.get('owner'):
                errors.append(f'items:{item_id} active/reviewing missing owner')
            review_date = item_dates.get('review_after')
            if review_date:
                if review_date < today:
                    warnings.append(f"items:{item_id} review_after is stale: {item.get('review_after')}")
        if status == 'active':
            owner_gate_verified = item.get('owner_gate_verified')
            if owner_gate_verified is False or str(owner_gate_verified).strip().lower() == 'false':
                errors.append(f'owner-gate:{item_id} active item has owner_gate_verified=false')
            review_status = str(item.get('review_status', '')).strip()
            if review_status in OWNER_GATE_BLOCKING_REVIEW_STATUSES:
                errors.append(f'owner-gate:{item_id} active item has blocking review_status: {review_status}')
        if status == 'superseded' and (not item.get('superseded_by')):
            errors.append(f'items:{item_id} superseded missing superseded_by')
        if item.get('kind') == 'artifact-ref':
            for field in ['uri', 'size', 'sha256']:
                if not item.get(field):
                    errors.append(f'items:{item_id} artifact-ref missing {field}')
            if item.get('sha256') and (not SHA256_RE.fullmatch(str(item.get('sha256')))):
                errors.append(f"items:{item_id} invalid artifact sha256: {item.get('sha256')}")
            if item.get('size') and (not isinstance(item.get('size'), int) or item.get('size') <= 0):
                errors.append(f"items:{item_id} invalid artifact size: {item.get('size')}")
        if item.get('scope') == 'project-specific' and str(item.get('path', '')).startswith('domains/embedded/standards/'):
            errors.append(f'items:{item_id} project-specific under embedded standards')
        if item.get('visibility') == 'personal-local' and item.get('status') == 'active':
            errors.append(f'items:{item_id} personal-local item must not be active')
        if item.get('generated_by_ai') is True and item.get('status') == 'active':
            missing_review = [field for field in ['human_reviewed_by', 'human_reviewed_at', 'review_basis'] if not item.get(field)]
            if missing_review:
                errors.append(f"items:{item_id} ai-generated active item missing human review fields: {','.join(missing_review)}")
        if item.get('generated_by_ai') is True and str(item.get('created_at', '')) >= '2026-06-21':
            missing_provenance = [field for field in ['ai_role', 'ai_model_or_tool', 'ai_generated_at'] if not item.get(field)]
            if missing_provenance:
                errors.append(f"items:{item_id} ai-generated item missing provenance fields: {','.join(missing_provenance)}")
    frontmatter_status_health['status'] = 'pass' if not frontmatter_status_health['mismatch_count'] and (not frontmatter_status_health['invalid_status_count']) and (not frontmatter_status_health['owner_mismatch_count']) and (not frontmatter_status_health['review_after_mismatch_count']) else 'fail'
    validation_ctx.update({'ids': ids, 'item_ids_by_path': item_ids_by_path, 'items': items, 'registered_item_paths': registered_item_paths})
    run_body_coverage(validation_ctx)
    artifact_manifest_path = root / artifact_vault_health['manifest']
    artifact_vault_root = root / artifact_vault_health['vault_root']
    artifact_errors = []
    artifact_expected_paths = set()
    if not artifact_manifest_path.exists():
        artifact_errors.append('artifact manifest is missing')
    elif not artifact_vault_root.is_dir():
        artifact_errors.append('artifact vault root is missing')
    else:
        artifact_rows = load_jsonl(artifact_manifest_path)
        artifact_vault_health['row_count'] = len(artifact_rows)
        if len(artifact_rows) != artifact_vault_health['expected_row_count']:
            artifact_errors.append(f"artifact identity row count mismatch: expected {artifact_vault_health['expected_row_count']}, actual {len(artifact_rows)}")
        seen_artifact_ids = set()
        for row in artifact_rows:
            artifact_id = str(row.get('id', '')).strip()
            source_path = str(row.get('source_path', '')).strip()
            presence = str(row.get('vault_presence', 'required')).strip() or 'required'
            expected_size = row.get('size')
            expected_hash = str(row.get('sha256', ''))
            identity_invalid = False
            if not artifact_id:
                artifact_errors.append('artifact row has missing id')
                identity_invalid = True
                artifact_id = '<unknown>'
            elif artifact_id in seen_artifact_ids:
                artifact_vault_health['duplicate_id_count'] += 1
                artifact_errors.append(f'duplicate artifact id: {artifact_id}')
                identity_invalid = True
            seen_artifact_ids.add(artifact_id)
            source_parts = pathlib.PurePosixPath(source_path).parts
            if not source_path or pathlib.Path(source_path).is_absolute() or source_path.startswith(('../', './', '~/')) or ('\\' in source_path) or (pathlib.PurePosixPath(source_path).as_posix() != source_path) or ('..' in source_parts):
                artifact_errors.append(f'{artifact_id} invalid source_path: {source_path}')
                artifact_vault_health['invalid_identity_count'] += 1
                continue
            if source_path in artifact_expected_paths:
                artifact_vault_health['duplicate_path_count'] += 1
                artifact_errors.append(f'duplicate artifact source_path: {source_path}')
                identity_invalid = True
            artifact_expected_paths.add(source_path)
            if not isinstance(expected_size, int) or expected_size <= 0:
                artifact_errors.append(f'{artifact_id} invalid size: {expected_size}')
                identity_invalid = True
            if len(expected_hash) != 64 or any((ch not in '0123456789abcdef' for ch in expected_hash)):
                artifact_errors.append(f'{artifact_id} invalid sha256: {expected_hash}')
                identity_invalid = True
            if identity_invalid:
                artifact_vault_health['invalid_identity_count'] += 1
            target = artifact_vault_root / source_path
            if presence == 'external-reference-only':
                artifact_vault_health['external_reference_only_count'] += 1
                if target.exists():
                    artifact_errors.append(f'{artifact_id} is marked external-reference-only but exists in vault')
                continue
            if presence != 'required':
                artifact_errors.append(f'{artifact_id} invalid vault_presence: {presence}')
                continue
            if target.is_symlink():
                artifact_vault_health['symlink_count'] += 1
                artifact_errors.append(f'{artifact_id} vault file must not be a symlink: {source_path}')
                continue
            if not target.is_file():
                artifact_vault_health['missing_required_count'] += 1
                artifact_errors.append(f'{artifact_id} required vault file is missing: {source_path}')
                continue
            artifact_vault_health['required_present_count'] += 1
            actual_size = target.stat().st_size
            if not isinstance(expected_size, int) or actual_size != expected_size:
                artifact_vault_health['size_mismatch_count'] += 1
                artifact_errors.append(f'{artifact_id} size mismatch: expected {expected_size}, actual {actual_size}')
            actual_hash = file_sha256(target)
            if expected_hash != actual_hash:
                artifact_vault_health['hash_mismatch_count'] += 1
                artifact_errors.append(f'{artifact_id} sha256 mismatch: expected {expected_hash}, actual {actual_hash}')
        vault_entries = list(artifact_vault_root.rglob('*'))
        unexpected_symlinks = [path.relative_to(artifact_vault_root).as_posix() for path in vault_entries if path.is_symlink()]
        artifact_vault_health['symlink_count'] = len(unexpected_symlinks)
        artifact_errors.extend((f'vault symlink is forbidden: {path}' for path in unexpected_symlinks[:20]))
        actual_paths = {path.relative_to(artifact_vault_root).as_posix() for path in vault_entries if path.is_file() and (not path.is_symlink())}
        extra_paths = sorted(actual_paths - artifact_expected_paths)
        artifact_vault_health['extra_file_count'] = len(extra_paths)
        artifact_errors.extend((f'unregistered vault file: {path}' for path in extra_paths[:20]))
    artifact_vault_health['errors'] = artifact_errors
    artifact_vault_health['status'] = 'pass' if not artifact_errors else 'fail'
    errors.extend((f'artifact-vault:{message}' for message in artifact_errors))

    def expand_range_ids(text, path):
        expanded = set()
        for prefix_start, number_start, prefix_end, number_end in re.findall('`([^`]+?)(\\d+)`\\.\\.`([^`]+?)(\\d+)`', text):
            if prefix_start != prefix_end:
                warnings.append(f'index:{path.relative_to(root)} unsupported range prefix: {prefix_start}..{prefix_end}')
                continue
            width = max(len(number_start), len(number_end))
            for number in range(int(number_start), int(number_end) + 1):
                expanded.add(f'{prefix_start}{number:0{width}d}')
        return expanded

    def indexed_ids(path):
        if not path.exists():
            errors.append(f'index missing: {path.relative_to(root)}')
            return set()
        text = path.read_text()
        found = set(re.findall('`([^`]+)`', text))
        found.update(expand_range_ids(text, path))
        return found

    def canonical_status_ids(path):
        if not path.exists():
            errors.append(f'index missing: {path.relative_to(root)}')
            return set()
        found = set()
        for line in path.read_text().splitlines():
            if not (line.startswith('- active:') or line.startswith('- reviewing:') or line.startswith('- archived:')):
                continue
            found.update(re.findall('`([^`]+)`', line))
            found.update(expand_range_ids(line, path))
        return found

    def status_bucket_ids(path, bucket):
        if not path.exists():
            errors.append(f'index missing: {path.relative_to(root)}')
            return set()
        found = set()
        prefix = f'- {bucket}:'
        for line in path.read_text().splitlines():
            if not line.startswith(prefix):
                continue
            found.update(re.findall('`([^`]+)`', line))
            found.update(expand_range_ids(line, path))
        return found

    def item_ref_counts(path, canonical_status_only=False):
        if not path.exists():
            errors.append(f'index missing: {path.relative_to(root)}')
            return {}
        counts = {}
        lines = path.read_text().splitlines()
        range_pattern = re.compile('`([^`]+?)(\\d+)`\\.\\.`([^`]+?)(\\d+)`')
        for line in lines:
            if canonical_status_only and (not (line.startswith('- active:') or line.startswith('- reviewing:') or line.startswith('- archived:'))):
                continue
            explicit_line = range_pattern.sub('', line)
            for ref in re.findall('`([^`]+)`', explicit_line):
                if ref in ids:
                    counts[ref] = counts.get(ref, 0) + 1
            for ref in expand_range_ids(line, path):
                if ref in ids:
                    counts[ref] = counts.get(ref, 0) + 1
        return counts
    validation_ctx.update({'expand_range_ids': expand_range_ids, 'indexed_ids': indexed_ids, 'canonical_status_ids': canonical_status_ids, 'status_bucket_ids': status_bucket_ids, 'item_ref_counts': item_ref_counts})
    run_index_security(validation_ctx)
    if 'explain' in validation_ctx:
        explain = validation_ctx['explain']
    scan_roots = validation_ctx['scan_roots']
PATH_ROUTING_TERMS = [('~/embedded/knowledge', '~/embedded/knowledge'), ('~/embedded/knowledge', str(pathlib.Path.home() / 'embedded' / 'knowledge')), ('EMBEDDED_KNOWLEDGE_HOME', 'EMBEDDED_KNOWLEDGE_HOME'), ('~/embedded/engineering_archive', '~/embedded/engineering_archive'), ('~/embedded/engineering_archive', str(pathlib.Path.home() / 'embedded' / 'engineering_archive')), ('~/codex/docs/archive', '~/codex/docs/archive'), ('~/codex/docs/archive', str(pathlib.Path.home() / 'codex' / 'docs' / 'archive'))]
PATH_ROUTING_CANONICAL_ROUTES = {}

def classify_path_routing_hit(rel_path, line_text):
    normalized = rel_path.replace('\\', '/')
    text = line_text.lower()
    if normalized in {'README.md', 'governance/path-routing.md', 'governance/source-boundaries.md', 'governance/source-lifecycle-policy.md', 'registry/schema.md', 'tools/knowledge-path-audit.sh', 'tools/knowledge-check.sh'}:
        return 'canonical-policy'
    if normalized.startswith('domains/codex/archive/codex-archive/'):
        return 'provenance'
    if normalized.startswith('sources/') or normalized in {'registry/sources.json', 'registry/retired-sources.jsonl'}:
        return 'provenance'
    if normalized.startswith('artifacts/manifests/') or normalized.startswith('registry/authorizations') or normalized.startswith('registry/automation-runs'):
        return 'provenance'
    if '旧' in line_text or 'retired' in text or 'provenance' in text or ('不再作为' in line_text):
        return 'canonical-policy'
    return 'runtime-route-candidate'
path_routing_health = {'status': 'pass', 'mode': 'hub-local-hard-gate', 'terms': sorted({display for display, _term in PATH_ROUTING_TERMS}), 'canonical_routes': PATH_ROUTING_CANONICAL_ROUTES, 'match_count': 0, 'canonical_policy_count': 0, 'provenance_count': 0, 'runtime_route_candidate_count': 0, 'runtime_route_candidates': [], 'notes_zh': '旧路径和环境变量没有兼容路由；只允许出现在 detector config 或不可执行 provenance 中，runtime-route-candidate 会阻断 knowledge-check。'}
if not args.sources_only:
    for path in iter_text_files(scan_roots):
        rel_path = str(path.relative_to(root))
        try:
            lines = path.read_text(errors='ignore').splitlines()
        except Exception as exc:
            warnings.append(f'path-routing:{display_path(path)} unreadable: {exc}')
            continue
        for lineno, line in enumerate(lines, start=1):
            if not any((term in line for _display, term in PATH_ROUTING_TERMS)):
                continue
            classification = classify_path_routing_hit(rel_path, line)
            path_routing_health['match_count'] += 1
            if classification == 'canonical-policy':
                path_routing_health['canonical_policy_count'] += 1
            elif classification == 'provenance':
                path_routing_health['provenance_count'] += 1
            else:
                row = {'path': rel_path, 'line': lineno, 'text': line.strip()[:200]}
                path_routing_health['runtime_route_candidate_count'] += 1
                path_routing_health['runtime_route_candidates'].append(row)
                errors.append(f'path-routing:{rel_path}:{lineno}')
    if path_routing_health['runtime_route_candidate_count']:
        path_routing_health['status'] = 'fail'
result = {'status': 'pass' if not errors else 'needs-fix', 'root': display_path(root), 'today': today.isoformat(), 'as_of_source': today_source, 'source_coverage_selection': source_coverage_selection, 'source_coverage_health': source_coverage_health, 'source_check_health': source_check_health, 'source_control_health': source_control_health, 'owner_target_health': owner_target_health, 'authorization_health': authorization_health, 'automation_safety_health': automation_safety_health, 'route_registry_health': route_registry_health, 'path_routing_health': path_routing_health, 'frontmatter_status_health': frontmatter_status_health, 'body_coverage_health': body_coverage_health, 'artifact_vault_health': artifact_vault_health, 'errors': errors, 'warnings': warnings, 'dry_run': bool(args.dry_run)}
result['status_contract'] = status_contract(result['status'])
if explain is not None:
    result['explain'] = explain
if args.diagnostics:
    result['diagnostics'] = build_diagnostics(errors, warnings)
if args.json or args.summary_json:
    projection = result
    if args.summary_json:
        diagnostics = result.get('diagnostics', {})
        projection = {'schema_version': 1, 'projection': 'knowledge-check-summary-v1', 'status': result['status'], 'status_contract': result['status_contract'], 'root': result['root'], 'today': result['today'], 'dry_run': result['dry_run'], 'error_count': len(errors), 'warning_count': len(warnings), 'error_sample': errors[:20], 'warning_sample': warnings[:10], 'diagnostic_categories': [{'id': row.get('id', ''), 'count': row.get('count', 0), 'action_zh': row.get('action_zh', '')} for row in diagnostics.get('categories', [])[:20]], 'health': {'source_coverage': source_coverage_health.get('status', ''), 'source_control': source_control_health.get('status', ''), 'owner_target': owner_target_health.get('status', ''), 'authorization': authorization_health.get('status', ''), 'automation_safety': automation_safety_health.get('status', ''), 'route_registry': route_registry_health.get('status', ''), 'path_routing': path_routing_health.get('status', ''), 'frontmatter': frontmatter_status_health.get('status', ''), 'body_coverage': body_coverage_health.get('status', ''), 'artifact_vault': artifact_vault_health.get('status', '')}}
    print(json.dumps(projection, ensure_ascii=False, indent=2))
else:
    print(f"status: {result['status']}")
    print(f'errors: {len(errors)}')
    print(f'warnings: {len(warnings)}')
    for item in errors[:40]:
        print(f'ERROR {item}')
    for item in warnings[:40]:
        print(f'WARN {item}')
    if explain is not None:
        print('explain:')
        print(f"  id: {explain['id']}")
        print(f"  found: {str(explain['found']).lower()}")
        if explain['registry']:
            registry = explain['registry']
            print(f"  title: {registry.get('title', '')}")
            print(f"  status: {registry.get('status', '')}")
            print(f"  owner: {registry.get('owner', '')}")
            print(f"  path: {registry.get('path', '')}")
            print(f"  path_exists: {str(registry.get('path_exists', False)).lower()}")
        for rel_index, detail in explain['indexes'].items():
            bucket = f", bucket={detail['bucket']}" if 'bucket' in detail else ''
            print(f"  index {rel_index}: {detail['status']} ({detail['reference_count']}x{bucket})")
        for hint in explain['maintenance_hints']:
            print(f'  hint: {hint}')
    if args.diagnostics:
        diagnostics = result['diagnostics']
        print('diagnostics:')
        print(f"  summary: {diagnostics['summary_zh']}")
        for category in diagnostics['categories']:
            print(f"  category {category['id']}: {category['title_zh']} ({category['count']}x)")
            print(f"    action: {category['action_zh']}")
            for example in category['examples']:
                print(f'    example: {example}')
        if diagnostics['warnings']['count']:
            print(f"  warnings: {diagnostics['warnings']['count']}x")
            print(f"    action: {diagnostics['warnings']['action_zh']}")
            for example in diagnostics['warnings']['examples']:
                print(f'    example: {example}')
sys.exit(0 if not errors else 1)
