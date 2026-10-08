"""Order eligible intent layers; this cannot admit filtered or unscored rows."""

import re
from .search_core import _domain_matches


def order_query_intent(candidates, plan, query):
    if not plan.enabled:
        return candidates
    normative = [row for row in candidates if 'active-general-policy' in row.get('why_selected', [])]
    if plan.shared_policy_context and plan.shared_terms and plan.project_terms:
        shared = [row for row in normative if 'shared-policy-comparison' in row.get('why_selected', [])]
        project = [row for row in candidates if any(_domain_matches(row.get('domain', ''), domain)
                                                  for domain in plan.project_domains)]
        if re.search('步骤|实操|采样|采集|操作流程|\b(?:steps|procedure|instructions)\b', query, re.I):
            guides = [row for row in project if row.get('kind') == 'runbook']
            project = guides or project
        chosen = shared[:1] + project[:1]
        for row in chosen:
            row['why_selected'].append('comparison-layer-coverage')
        return chosen + [row for row in candidates if row not in chosen]
    if plan.governance and normative:
        normative.sort(key=lambda row:row.get('kind') != 'standard')
        for row in normative:
            row['why_selected'].append('normative-query-authority')
        return normative + [row for row in candidates if row not in normative]
    return candidates
