"""Closed conversational grammar; topic nouns and named entities are not aliases."""

import re
from dataclasses import dataclass

CHINESE_ENTITY_HEADS = ('项目', '设备', '产品', '板卡', '仓库')
ENTITY_DESCRIPTOR = r'(?:芯片|主板|硬件|电子|嵌入式)'
ENTITY_NAME = re.compile(r'[a-z0-9_][a-z0-9_./:+-]{0,255}', re.I)
ENTITY_HEAD = '(?:' + '|'.join(CHINESE_ENTITY_HEADS) + ')'
CN_HEAD = re.compile(r'\s*(?:的\s*)?(?:' + ENTITY_DESCRIPTOR + r')?' + ENTITY_HEAD + r'\s*(?:的\s*)?')
EN_ENTITY_HEAD = re.compile(r'(?:project|product|device|board|repository|repo|entity)(?:\s*:\s*|\s+)', re.I)


@dataclass(frozen=True)
class SubjectLexeme:
    name: str
    start: int
    end: int
    explicit: bool
    descriptor: str = ''


def _entity_value(query, start, aliases):
    for alias in aliases:
        if query[start:start + len(alias)].lower() == alias:
            end = start + len(alias)
            if end == len(query) or not re.match(r'[a-z0-9_./:+-]', query[end], re.I) or query[end:] == '.':
                return alias, end
    match = ENTITY_NAME.match(query, start)
    if not match:
        return '', start
    name = match.group().rstrip('.').lower()
    return name, start + len(name)


def subject_at(query, start, aliases=()):
    """The same bounded lexeme is consumed by positive and negative scopes."""
    while start < len(query) and query[start].isspace():
        start += 1
    prefix = EN_ENTITY_HEAD.match(query, start) or CN_HEAD.match(query, start)
    value_start = prefix.end() if prefix else start
    name, end = _entity_value(query, value_start, aliases)
    if not name:
        return None
    suffix = CN_HEAD.match(query, end)
    # A spaced head immediately followed by a new Latin value belongs to that
    # next value, e.g. "ORBIT17 项目CRAFT99", rather than the preceding alias.
    if suffix and end < len(query) and query[end].isspace() and ENTITY_NAME.match(query, suffix.end()):
        suffix = None
    descriptor = ''
    if suffix:
        descriptor = suffix.group().strip()
        if descriptor.startswith('的'):
            descriptor = descriptor[1:].strip()
        end = suffix.end()
    return SubjectLexeme(name, start, end, bool(prefix or suffix), descriptor)


def explicit_subjects(query, aliases=()):
    result, position = [], 0
    while position < len(query):
        if position and re.match(r'[a-z0-9_./:+-]', query[position - 1], re.I):
            position += 1
            continue
        value = subject_at(query, position, aliases)
        if value and value.explicit:
            result.append(value)
            position = value.end
        else:
            position += 1
    return tuple(result)

QUANTIFIER = re.compile(r'(?:第)?(?:[一二三四五六七八九十百]+|\d+)(?:大)?(?:个|段|份|种|项|条|篇|枚)(?=[\u4e00-\u9fff]|$)|整(?:段|篇|份)')
PREDICATE = re.compile(r'要把|只有|除了|(?:(?:还|仍|尚)?(?:不|未)能|还能|可以|^能)(?=[\u4e00-\u9fff])|'
                       r'必须|应当|应该|以后|之前|过(?=的|了|$)|整理成|写成|直接|是(?=一份|同一份)|'
                       r'(?:该)?(?:查|接)(?:哪个|哪些|什么)|多久|(?:能|可以)?(?:直接)?宣告|'
                       r'找到(?=[一二三四五六七八九十\d])|能把|(?:前|后)(?:应|须|需)|立即|随时|'
                       r'是(?:同一|一)(?:种|份|类|个)|哪个是|就当|所有|任何|各个|每个')
NORMATIVE = re.compile(r'必须|应当|应该|(?:能|可以|允许).*?(?:写|记录|宣告|作为|当作)|'
                       r'(?:哪些|什么).*?字段|(?:怎么|怎样|如何).*?写|'
                       r'(?:能|可以).*?(?:复制|作为|引用|使用)|\b(?:must|shall|allowed|permitted)\b', re.I)


def strip_grammar(value: str) -> str:
    # This is not domain synonym expansion; polarity is recorded from the
    # original query separately. 无线/非易失性 and named noun contents stay intact.
    return QUANTIFIER.sub(' ', PREDICATE.sub(' ', value))


def normative_question(query: str) -> bool:
    return bool(NORMATIVE.search(query))


def chinese_named_constraints(query, unknown, project_anchors):
    heads = CHINESE_ENTITY_HEADS
    head_pattern = '(?:' + '|'.join(heads) + ')'
    descriptors = chinese_entity_descriptors(query)
    names = [term for term in unknown if term not in descriptors
             if (any(term.endswith(head) and len(term) > len(head) for head in heads)
                 or re.search(re.escape(term) + head_pattern, query))]
    # Read names from the original sentence, before grammar/topic association.
    # Only explicit head/name adjacency is supported; DF never enters this rule.
    names.extend(value.name for value in explicit_subjects(query))
    return tuple(dict.fromkeys(term for term in names if term not in project_anchors))


def chinese_entity_descriptors(query):
    return tuple(dict.fromkeys(value.descriptor for value in explicit_subjects(query) if value.descriptor))
