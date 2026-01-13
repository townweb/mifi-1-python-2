import prompt

from primitive_db.constants import (
    APP_TITLE,
    HELP_TEXT,
    MSG_INVALID_VALUE,
    MSG_UNKNOWN_FUNCTION,
    PROMPT_TEXT,
)
from primitive_db.core import (
    create_table,
    delete_rows,
    drop_table,
    insert_row,
    list_tables,
    select_rows,
    update_rows,
)
from primitive_db.decorators import create_cacher
from primitive_db.exceptions import ParseError
from primitive_db.parser import parse_command


def run():
    """Основной цикл приложения."""
    print(APP_TITLE)
    print()
    print(HELP_TEXT)
    print()

    cacher = create_cacher()

    while True:
        try:
            line = prompt.string(PROMPT_TEXT)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break
        try:
            cmd = parse_command(line)
        except ParseError as exc:
            print(MSG_INVALID_VALUE.format(value=str(exc)))
            continue

        kind = cmd.get("kind")

        if kind == "empty":
            continue

        if kind == "help":
            print()
            print(HELP_TEXT)
            print()
            continue

        if kind == "exit":
            break

        if kind == "unknown":
            name = cmd.get("name") or "?"
            print(MSG_UNKNOWN_FUNCTION.format(name=name))
            continue

        _dispatch(cmd, cacher)


def _dispatch(cmd, cacher):
    kind = cmd["kind"]

    if kind == "list_tables":
        list_tables()
        return

    if kind == "create_table":
        create_table(cmd["table"], cmd["columns"])
        return

    if kind == "drop_table":
        drop_table(cmd["table"], cacher)
        return

    if kind == "insert":
        insert_row(cmd["table"], cmd["values_raw"], cacher)
        return

    if kind == "select":
        select_rows(cmd["table"], cmd["where"], cacher)
        return

    if kind == "update":
        update_rows(cmd["table"], cmd["set"], cmd["where"], cacher)
        return

    if kind == "delete":
        delete_rows(cmd["table"], cmd["where"], cacher)
        return

    print(MSG_UNKNOWN_FUNCTION.format(name=kind))
