"""Bind an isolated view to verified source routing without copying credentials."""

from __future__ import annotations

import json
import urllib.parse
import datetime as dt

from .common import KnowledgeHubError, repository_rows, run_rtk, read_utf8_bounded, file_sha256
from .context import find_git_config, remote_urls_from_config
from .store import RepositoryTransaction
from .security import scan_secret_text
from .workspace_discovery import _source_entries
from .schemas import validate_instance


def bind_snapshot_route(source, snapshot, head):
    config, _ = find_git_config(str(source))
    remotes = remote_urls_from_config(config)
    registered = {row.get('remote_key'):row for row in repository_rows(source)}
    remote = next((row for row in remotes if row['remote'] == 'origin' and row['remote_key'] in registered), None)
    if remote is None:
        return {'status':'not-registered', 'source_remote_key':''}
    url = remote['url']
    parsed = urllib.parse.urlsplit(url)
    if (scan_secret_text(url) or parsed.password or parsed.query or parsed.fragment
            or parsed.scheme in ('http', 'https') and parsed.username):
        raise KnowledgeHubError('snapshot routing rejects credential-bearing remote configuration')
    row = registered[remote['remote_key']]
    ignored = run_rtk(snapshot, ['git', 'check-ignore', '-q', 'local/workspaces.json'], accepted_exit_codes=(0, 1))
    if ignored['exit_code'] != 0:
        raise KnowledgeHubError('snapshot routing view must use ignored host configuration')
    run_rtk(snapshot, ['git', 'remote', 'set-url', 'origin', url])
    path = snapshot / 'local/workspaces.json'
    baseline = {'local/workspaces.json':file_sha256(path)} if path.exists() else {}
    raw = read_utf8_bounded(path, 256 * 1024, 'snapshot workspace configuration') if path.exists() else '{}'
    document = json.loads(raw)
    if not isinstance(document, dict) or not isinstance(document.get('workspaces', []), list):
        raise KnowledgeHubError('snapshot workspace configuration is invalid')
    workspaces = document.get('workspaces', [])
    if len(workspaces) >= 5000:
        raise KnowledgeHubError('snapshot workspace configuration exceeds budget')
    evidence = _source_entries(snapshot)
    if evidence['git_head'] != head:
        raise KnowledgeHubError('snapshot routing HEAD does not match captured identity')
    binding = {'path':str(snapshot), 'workspace_ref':row['workspace_ref'], 'repo_id':row['repo_id'],
               'project_id':row['project_id'], 'remote_key':remote['remote_key'], 'source_evidence':evidence,
               'present':True, 'read_only_discovery':True, 'alternate_count':0, 'alternate_paths':[],
               'snapshot_view_only':True}
    document['workspaces'] = [binding] + workspaces
    for key, value in {'schema_version':1, 'generated_at':dt.date.today().isoformat(),
                       'discovery_mode':'read-only-local-git-remote-match', 'tracked':False,
                       'unmatched_registered_remote_keys':sorted(key for key in registered if key and key != remote['remote_key'])}.items():
        document.setdefault(key, value)
    if (snapshot / 'schemas/catalog.json').is_file() and validate_instance(snapshot, 'local-workspaces-v1', document)['status'] != 'pass':
        raise KnowledgeHubError('snapshot host view violates the existing workspace schema')
    transaction = RepositoryTransaction(snapshot, 'snapshot-host-view-binding', expected_inputs=baseline)
    transaction.add_text('local/workspaces.json', json.dumps(document, ensure_ascii=False, sort_keys=True) + '\n')
    transaction.apply()
    return {'status':'bound', 'source_remote_key':remote['remote_key'], 'repo_id':row['repo_id'],
            'workspace_ref':row['workspace_ref'], 'effective_workspace_sha256':file_sha256(path),
            'view_binding_only':True, 'owner_approval_granted':False}
