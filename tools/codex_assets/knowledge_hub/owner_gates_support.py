import hashlib
import json
import os
import pathlib

root = pathlib.Path(".")
errors = []
source_roots = {}
owner_route_map = {}

def configure_owner_gates_support(root_value, errors_value, *, source_roots_value=None, owner_route_map_value=None):
    global root, errors, source_roots, owner_route_map
    root = root_value
    errors = errors_value
    if source_roots_value is not None:
        source_roots = source_roots_value
    if owner_route_map_value is not None:
        owner_route_map = owner_route_map_value

def load_jsonl(path):
    rows = []
    if not path.exists():
        errors.append(f'missing {path.relative_to(root)}')
        return rows
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        errors.append(f'cannot read {path.relative_to(root)}: {exc}')
        return rows
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:
            errors.append(f'{path.relative_to(root)}:{line_no}: invalid jsonl: {exc}')
    return rows

def load_json(path):
    if not path.exists():
        errors.append(f'missing {path.relative_to(root)}')
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f'cannot load {path.relative_to(root)}: {exc}')
        return {}

def path_from_arg(value):
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path

def _is_filled(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True

def source_path_values(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []

def source_path_matches(value, expected):
    return str(expected) in source_path_values(value)

def is_resolved(row):
    state_text = ' '.join((str(row.get(field, '')) for field in ['worksheet_status', 'row_status', 'status', 'default_state'])).lower()
    has_resolution_state = any((token in state_text for token in ['resolved', 'owner-approved', 'approved', 'closed']))
    if not has_resolution_state:
        return False
    required_fields = list(row.get('required_owner_fields', []))
    for field in ['owner_decision', 'target_decision', 'reviewed_by', 'reviewed_at', 'review_after', 'source_status', 'evidence_refs', 'status_reason']:
        if field not in required_fields:
            required_fields.append(field)
    return all((_is_filled(row.get(field)) for field in required_fields))

def default_field_value(field, row):
    if field == 'review_after':
        return row.get('review_after', '')
    if field.endswith('_refs') or field in {'evidence_refs', 'open_items'}:
        return []
    if field in {'automation_enabled', 'writes_memory', 'writes_team_active_index', 'no_memory_write_gate', 'not_active_source', 'contains_memory_candidates'}:
        return None
    return ''

def compute_source_identity(row):
    source_id = str(row.get('source_id', ''))
    source_path = str(row.get('source_path', ''))
    expected_sha256 = str(row.get('source_sha256_expected', ''))
    expected_size = row.get('source_size_expected', '')
    source_root = source_roots.get(source_id, '')
    identity = {'source_identity_read_mode': 'read-bytes-for-hash', 'source_body_read_for_hash': True, 'source_body_copied': False, 'source_project_written': False, 'source_root': source_root, 'source_path': source_path, 'source_file_exists': False, 'expected_sha256': expected_sha256, 'expected_size': expected_size, 'observed_sha256': '', 'observed_size': '', 'identity_status': 'unavailable', 'notes_zh': '只读源文件身份提示；为计算 hash 会读取 source 文件字节，但不复制正文、不写源项目、不代表 owner 已签收，不自动填充 source_sha256/source_size，不关闭门禁。'}
    if not source_root or not source_path:
        return identity
    base = pathlib.Path(source_root).expanduser().resolve()
    candidate = (base / source_path).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        identity['identity_status'] = 'path-outside-source-root'
        return identity
    if not candidate.is_file():
        identity['identity_status'] = 'missing'
        return identity
    try:
        data = candidate.read_bytes()
    except Exception:
        identity['identity_status'] = 'read-error'
        return identity
    observed_sha256 = hashlib.sha256(data).hexdigest()
    observed_size = len(data)
    identity['source_file_exists'] = True
    identity['observed_sha256'] = observed_sha256
    identity['observed_size'] = observed_size
    size_matches = str(expected_size) == str(observed_size) if expected_size != '' else False
    sha_matches = bool(expected_sha256) and expected_sha256 == observed_sha256
    if sha_matches and size_matches:
        identity['identity_status'] = 'match'
    elif expected_sha256 or expected_size != '':
        identity['identity_status'] = 'mismatch'
    else:
        identity['identity_status'] = 'observed-no-expected'
    return identity

def _row_ref(row):
    return {'worksheet_id': row['id'], 'source_id': row['source_id'], 'source_path': row['source_path'], 'owner': row['owner'], 'review_after': row['review_after']}

def _display_path(path):
    text = str(path)
    for prefix in user_path_prefixes():
        if text == prefix:
            return '~'
        if text.startswith(prefix + '/'):
            return '~' + text[len(prefix):]
    try:
        return str(path.relative_to(root))
    except ValueError:
        return text

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get('USER', '')
    if user_name:
        prefixes.append('/' + 'vsdata' + '/' + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != '/']

def _read_jsonl_local(path):
    local_errors = []
    rows_local = []
    if not path.exists():
        return ([], [f'missing {_display_path(path)}'])
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        return ([], [f'cannot read {_display_path(path)}: {exc}'])
    for line_no, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rows_local.append(json.loads(line))
        except Exception as exc:
            local_errors.append(f'{_display_path(path)}:{line_no}: invalid jsonl: {exc}')
    return (rows_local, local_errors)

def shlex_quote(value):
    text = str(value)
    if not text:
        return "''"
    safe_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@%+=:,./-'
    if all((char in safe_chars for char in text)):
        return text
    return "'" + text.replace("'", '\'"\'"\'') + "'"

def is_filled(value):
    return _is_filled(value)

def owner_route_for(source_id, owner_role):
    route = owner_route_map.get((source_id, owner_role), {})
    if route:
        return route
    return {'decision_owner_role': owner_role, 'source_id': source_id, 'routing_status': 'unmapped', 'routing_owner': '', 'candidate_registry_owners': [], 'required_real_owner_zh': '缺少 owner-routing.json 路由；需要人工补充分派责任人后再签收。', 'escalation_zh': '保持 owner gate open，不得代签。', 'must_not': ['不得把 unmapped owner role 当作已签收'], 'notes_zh': '只读缺省路由；不生成 owner decision，不关闭 gate。', 'no_owner_decision_generated': True}

def source_execution_root(source_id):
    source_root = str(source_roots.get(source_id, '') or '')
    if not source_root:
        return ''
    path = pathlib.Path(source_root).expanduser()
    if source_id == 'pcr02-project-docs' and path.name == 'docs':
        return _display_path(path.parent)
    return _display_path(path)

def effective_verification_commands(row, source_id):
    commands = list(row.get('verification_commands', []))
    execution_root = source_execution_root(source_id)
    required_fields = set(row.get('required_owner_fields', []))
    if execution_root and ('commit_branch_dirty_state_evidence' in required_fields or 'final_branch_commit_or_tag_refs' in required_fields):
        git_status_command = f'rtk git -C {execution_root} status --short --branch'
        git_head_command = f'rtk git -C {execution_root} rev-parse HEAD'
        if git_status_command not in commands:
            commands.append(git_status_command)
        if git_head_command not in commands:
            commands.append(git_head_command)
    return commands
