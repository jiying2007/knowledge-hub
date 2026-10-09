"""Literal heading/version focus and normative document form, never admission."""

import re
from .query_concepts import TOKEN, CJK, EN_SCAFFOLD, QUESTION_ACTIONS, ANCHOR_CONTEXT


def focus_bonus(query, plan, title):
    if not plan or not plan.enabled:
        return 0, []
    title, lowered = title.lower(), query.lower()
    focus = ''
    for match in TOKEN.finditer(query):
        term = match.group().lower()
        if (CJK.fullmatch(term) or term in plan.project_anchors or term in EN_SCAFFOLD
                or term in QUESTION_ACTIONS or term in ANCHOR_CONTEXT or re.fullmatch(r'v\d+', term)
                or not re.match('[a-z]', term) or term not in plan.terms):
            continue
        if (re.match(r'\s*[,、]\s*[A-Za-z]', query[match.end():])
                or re.search(r'[A-Za-z0-9_]+\s*[,、]\s*$', query[:match.start()])):
            continue
        focus = term
        break
    for alias in plan.project_anchors:
        title = re.sub(r'^' + re.escape(alias) + r'\s*', '', title)
    score, reasons = 0, []
    if focus and re.match(r'^' + re.escape(focus) + r'(?![a-z0-9])', title):
        score += 120
        reasons.append('literal-heading-focus')
    versions = re.findall(r'\bv\d+(?:\.\d+)*\b', lowered)
    if versions and any(re.search(r'\b' + re.escape(version) + r'\b', title) for version in versions):
        score += 120
        reasons.append('literal-heading-version')
    normative = bool(re.search('默认|规范|策略|允许|运行中|\b(?:default|policy|permitted)\b', lowered))
    if plan.shared_terms and plan.project_terms:
        normative = any(re.search('默认|规范|策略|允许|运行中|\b(?:default|policy|permitted)\b', term) for term in plan.terms)
    if (normative
            and re.search('当前.*决策|规范|策略|契约|\b(?:policy|contract)\b', title)
            and not re.search('实验|验证|\b(?:experiment|validation)\b', title)):
        score += 240
        reasons.append('normative-document-form')
    return score, reasons


def focus_order(row):
    reasons = row.get('why_selected', ())
    return ('literal-heading-focus' not in reasons, 'literal-heading-version' not in reasons,
            'normative-document-form' not in reasons, -int(row['score']), row['path'], row['item_id'])
