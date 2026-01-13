import shlex

from primitive_db.constants import (
    CMD_CREATE_TABLE,
    CMD_DROP_TABLE,
    CMD_EXIT,
    CMD_HELP,
    CMD_LIST_TABLES,
    KW_DELETE,
    KW_FROM,
    KW_INSERT,
    KW_INTO,
    KW_SELECT,
    KW_SET,
    KW_UPDATE,
    KW_VALUES,
    KW_WHERE,
)
from primitive_db.exceptions import ParseError


def parse_command(line):
    """
    Parse input line into command dict.
    Returns dict with at least {"kind": "..."}.
    """
    text = (line or "").strip()
    if not text:
        return {"kind": "empty"}

    head = _first_word(text).lower()

    if head in (CMD_HELP, CMD_EXIT, CMD_CREATE_TABLE, CMD_LIST_TABLES, CMD_DROP_TABLE):
        return _parse_simple(text)

    if head == KW_INSERT:
        return _parse_insert(text)

    if head == KW_SELECT:
        return _parse_select(text)

    if head == KW_UPDATE:
        return _parse_update(text)

    if head == KW_DELETE:
        return _parse_delete(text)

    return {"kind": "unknown", "name": head, "raw": text}


def _parse_simple(text):
    parts = shlex.split(text)
    cmd = parts[0].lower()

    if cmd == CMD_HELP:
        return {"kind": "help"}

    if cmd == CMD_EXIT:
        return {"kind": "exit"}

    if cmd == CMD_LIST_TABLES:
        return {"kind": "list_tables"}

    if cmd == CMD_DROP_TABLE:
        if len(parts) != 2:
            raise ParseError(f"Ожидается: {CMD_DROP_TABLE} <table_name>")
        return {"kind": "drop_table", "table": parts[1]}

    if cmd == CMD_CREATE_TABLE:
        if len(parts) < 3:
            raise ParseError(f"Ожидается: {CMD_CREATE_TABLE} <table> <col:type> ...")
        table = parts[1]
        cols = parts[2:]
        return {"kind": "create_table", "table": table, "columns": cols}

    return {"kind": "unknown", "name": cmd, "raw": text}


def _parse_insert(text):
    lower = text.lower()
    if not lower.startswith(f"{KW_INSERT} "):
        raise ParseError("Некорректная команда insert")

    words = shlex.split(text)
    if len(words) < 5:
        raise ParseError("Ожидается: insert into <table> values (<...>)")

    if words[1].lower() != KW_INTO:
        raise ParseError("Ожидается: insert into <table> values (<...>)")

    table = words[2]

    idx_values = _index_of_word(words, KW_VALUES)
    if idx_values is None:
        raise ParseError("Ожидается ключевое слово values")

    values_part = text[text.lower().find(KW_VALUES) + len(KW_VALUES) :].strip()
    inner = _extract_parentheses(values_part)
    values = [_parse_literal(v) for v in _split_csv_like(inner)]

    return {"kind": "insert", "table": table, "values_raw": values}


def _parse_select(text):
    lower = text.lower()
    if not lower.startswith(f"{KW_SELECT} "):
        raise ParseError("Некорректная команда select")

    words = shlex.split(text)
    if len(words) < 3:
        raise ParseError("Ожидается: select from <table> [where <col> = <value>]")

    if words[1].lower() != KW_FROM:
        raise ParseError("Ожидается: select from <table> ...")

    table = words[2]

    where_pos = _index_of_word(words, KW_WHERE)
    if where_pos is None:
        return {"kind": "select", "table": table, "where": None}

    where_str = text[text.lower().find(KW_WHERE) + len(KW_WHERE) :].strip()
    where = _parse_condition(where_str)
    return {"kind": "select", "table": table, "where": where}


def _parse_update(text):
    words = shlex.split(text)
    if len(words) < 6:
        raise ParseError("Ожидается: update <table> set <col>=<val> where <col>=<val>")

    if words[0].lower() != KW_UPDATE:
        raise ParseError("Некорректная команда update")

    table = words[1]

    set_pos = _index_of_word(words, KW_SET)
    where_pos = _index_of_word(words, KW_WHERE)
    if set_pos is None or where_pos is None or where_pos <= set_pos:
        raise ParseError("Ожидается: update <table> set ... where ...")

    lower_text = text.lower()
    set_str = text[
        lower_text.find(KW_SET) + len(KW_SET) : lower_text.find(KW_WHERE)
    ].strip()
    where_str = text[lower_text.find(KW_WHERE) + len(KW_WHERE) :].strip()

    set_clause = _parse_assignments(set_str)
    where_clause = _parse_condition(where_str)

    return {"kind": "update", "table": table, "set": set_clause, "where": where_clause}


def _parse_delete(text):
    words = shlex.split(text)
    if len(words) < 5:
        raise ParseError("Ожидается: delete from <table> where <col> = <value>")

    if words[0].lower() != KW_DELETE or words[1].lower() != KW_FROM:
        raise ParseError("Ожидается: delete from <table> where ...")

    table = words[2]

    lower_text = text.lower()
    if KW_WHERE not in lower_text:
        raise ParseError("Ожидается: delete from <table> where ...")

    where_str = text[lower_text.find(KW_WHERE) + len(KW_WHERE) :].strip()
    where_clause = _parse_condition(where_str)

    return {"kind": "delete", "table": table, "where": where_clause}


def _first_word(text):
    parts = text.strip().split(maxsplit=1)
    return parts[0] if parts else ""


def _index_of_word(words, word):
    w = word.lower()
    for i, token in enumerate(words):
        if token.lower() == w:
            return i
    return None


def _extract_parentheses(text):
    s = text.strip()
    if not s.startswith("(") or not s.endswith(")"):
        raise ParseError("Ожидаются скобки: values (<...>)")
    return s[1:-1]


def _split_csv_like(s):
    items = []
    buf = []
    quote = None
    escape = False

    for ch in s:
        if escape:
            buf.append(ch)
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if quote:
            if ch == quote:
                quote = None
                buf.append(ch)
            else:
                buf.append(ch)
            continue

        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue

        if ch == ",":
            item = "".join(buf).strip()
            items.append(item)
            buf = []
            continue

        buf.append(ch)

    last = "".join(buf).strip()
    if last or s.strip() == "":
        items.append(last)

    cleaned = []
    for it in items:
        if it == "":
            raise ParseError("Пустое значение в списке values")
        cleaned.append(it)
    return cleaned


def _parse_condition(s):
    col, raw = _split_by_equals(s)
    col = col.strip()
    if not col:
        raise ParseError("Пустое имя столбца в where")
    value = _parse_literal(raw.strip())
    return {col: value}


def _parse_assignments(s):
    parts = _split_csv_like(s)
    result = {}
    for p in parts:
        col, raw = _split_by_equals(p)
        col = col.strip()
        if not col:
            raise ParseError("Пустое имя столбца в set")
        result[col] = _parse_literal(raw.strip())
    return result


def _split_by_equals(s):
    quote = None
    escape = False
    for i, ch in enumerate(s):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            continue
        if ch == "=":
            left = s[:i]
            right = s[i + 1 :]
            return left, right
    raise ParseError('Ожидается знак "="')


def _parse_literal(token):
    t = token.strip()
    if t == "":
        raise ParseError("Пустое значение")

    low = t.lower()
    if low == "true":
        return True
    if low == "false":
        return False

    if _looks_like_int(t):
        try:
            return int(t)
        except ValueError as e:
            raise ParseError(f"Некорректное int значение: {t}") from e

    if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
        return t[1:-1].replace('\\"', '"').replace("\\'", "'")

    return t


def _looks_like_int(s):
    if s.startswith(("+", "-")):
        return s[1:].isdigit() and len(s) > 1
    return s.isdigit()
