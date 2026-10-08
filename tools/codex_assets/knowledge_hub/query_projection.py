"""Explicit shared/project comparison clauses; no relevance-driven term removal."""

import re
from typing import Sequence, Tuple


def shared_policy_context(query: str, shared_terms, project_terms) -> bool:
    if shared_terms and project_terms:
        return True
    return bool(re.search(
        r'(?:团队|通用|跨项目).*?(?:规范|标准|规则|方法论|指南|写法|流程|指导|记录)|'
        r'共享(?:规范|标准|方法|指南|规则|流程)|'
        r'\b(?:team|general|common|cross-project)\b.*\b(?:standard|policy|runbook|guide|guidance|procedure|rules)\b|'
        r'\bshared\s+(?:standard|policy|runbook|guide|guidance|procedure|rules)\b', query, re.I))


def comparison_terms(query: str, terms: Sequence[str], project_anchors: Sequence[str]) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    if not project_anchors:
        return (), ()
    clauses = re.split(r'[和与，,、;；]|\b(?:and|or|versus|vs|against)\b', query.lower())
    shared, project = [], []
    for clause in clauses:
        if any(re.search(r'(?<![a-z0-9])' + re.escape(anchor) + r'(?![a-z0-9])', clause)
               for anchor in project_anchors):
            project.append(re.split(r'是不是|是一份|是同一|是一种|需要分别|分别', clause, maxsplit=1)[0])
        elif re.search(r'团队|通用|跨项目|共享(?:规范|标准|方法|指南|规则|流程)|(?:规范|规则|标准)\s*$', clause):
            shared.append(clause)
    if not shared or not project:
        return (), ()
    shared_text, project_text = '\n'.join(shared), '\n'.join(project)
    return (tuple(term for term in terms if term in shared_text),
            tuple(term for term in terms if term in project_text))
