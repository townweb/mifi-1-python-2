from primitive_db.constants import (
    ID_COL_NAME,
    ID_COL_TYPE,
    MSG_CACHE_HIT,
    MSG_CACHE_MISS,
    MSG_DELETED,
    MSG_NO_TABLES,
    MSG_ROW_INSERTED,
    MSG_TABLE_CREATED,
    MSG_TABLE_EXISTS,
    MSG_TABLE_NOT_EXISTS,
    MSG_UPDATED,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.exceptions import NotFoundError, ValidationError
from primitive_db.utils import (
    delete_table_file,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


@handle_db_errors
def list_tables():
    """Вывести список таблиц."""
    metadata = load_metadata()
    tables = sorted(metadata.keys())
    if not tables:
        print(MSG_NO_TABLES)
        return None
    for table in tables:
        print(f"- {table}")
    return None


@handle_db_errors
def create_table(table_name, columns):
    """Создать таблицу с указанными столбцами."""
    metadata = load_metadata()

    if table_name in metadata:
        raise ValidationError(MSG_TABLE_EXISTS.format(table=table_name))

    parsed_cols = _parse_columns(columns)
    full_cols = [{"name": ID_COL_NAME, "type": ID_COL_TYPE}] + parsed_cols

    metadata[table_name] = {
        "columns": full_cols,
        "last_id": 0,
    }
    save_metadata(metadata)

    cols_str = ", ".join([f'{c["name"]}:{c["type"]}' for c in full_cols])
    print(MSG_TABLE_CREATED.format(table=table_name, cols=cols_str))
    return None


@confirm_action("удаление таблицы")
@handle_db_errors
def drop_table(table_name, cacher):
    """Удалить таблицу и связанный файл данных."""
    metadata = load_metadata()

    if table_name not in metadata:
        raise NotFoundError(MSG_TABLE_NOT_EXISTS.format(table=table_name))

    metadata.pop(table_name, None)
    save_metadata(metadata)

    delete_table_file(table_name)
    cacher.invalidate(table_name)

    print(f'Таблица "{table_name}" успешно удалена.')
    return None


@log_time
@handle_db_errors
def insert_row(table_name, values_raw, cacher):
    """Добавить строку в таблицу."""
    metadata = load_metadata()
    schema = _get_schema(metadata, table_name)

    cols = schema["columns"]
    expected = len(cols) - 1
    if len(values_raw) != expected:
        raise ValidationError(
            f"Ожидается значений: {expected}, получено: {len(values_raw)}"
        )

    values = [_coerce_value(v, cols[i + 1]["type"]) for i, v in enumerate(values_raw)]

    rows = load_table_data(table_name)
    new_id = int(schema["last_id"]) + 1
    schema["last_id"] = new_id

    row = {ID_COL_NAME: new_id}
    for i, col in enumerate(cols[1:]):
        row[col["name"]] = values[i]

    rows.append(row)
    save_table_data(table_name, rows)

    metadata[table_name] = schema
    save_metadata(metadata)

    cacher.invalidate(table_name)
    print(MSG_ROW_INSERTED.format(id=new_id, table=table_name))
    return None


@log_time
@handle_db_errors
def select_rows(table_name, where, cacher):
    """Выбрать строки таблицы по условию (или все)."""
    metadata = load_metadata()
    schema = _get_schema(metadata, table_name)

    key = _select_cache_key(table_name, where)
    rows = cacher(key, lambda: _select_impl(table_name, where))
    if cacher.was_hit:
        print(MSG_CACHE_HIT)
    else:
        print(MSG_CACHE_MISS)

    _print_rows(schema["columns"], rows)
    return None


@log_time
@handle_db_errors
def update_rows(table_name, set_clause, where_clause, cacher):
    """Обновить строки таблицы по условию."""
    metadata = load_metadata()
    schema = _get_schema(metadata, table_name)
    cols = schema["columns"]

    _ensure_columns_exist(cols, set_clause)
    _ensure_columns_exist(cols, where_clause)

    typed_set = _coerce_clause(cols, set_clause)
    typed_where = _coerce_clause(cols, where_clause)

    rows = load_table_data(table_name)
    count = 0
    for row in rows:
        if _row_matches(row, typed_where):
            for key, value in typed_set.items():
                row[key] = value
            count += 1

    save_table_data(table_name, rows)
    cacher.invalidate(table_name)

    print(MSG_UPDATED.format(count=count, table=table_name))
    return None


@confirm_action("удаление записей")
@log_time
@handle_db_errors
def delete_rows(table_name, where_clause, cacher):
    """Удалить строки по условию."""
    metadata = load_metadata()
    schema = _get_schema(metadata, table_name)
    cols = schema["columns"]

    _ensure_columns_exist(cols, where_clause)
    typed_where = _coerce_clause(cols, where_clause)

    rows = load_table_data(table_name)
    kept = []
    deleted = 0
    for row in rows:
        if _row_matches(row, typed_where):
            deleted += 1
        else:
            kept.append(row)

    save_table_data(table_name, kept)
    cacher.invalidate(table_name)

    print(MSG_DELETED.format(count=deleted, table=table_name))
    return None


def _parse_columns(columns):
    parsed = []
    for spec in columns:
        if ":" not in spec:
            raise ValidationError(f"Некорректное описание столбца: {spec}")
        name, typ = spec.split(":", 1)
        name = name.strip()
        typ = typ.strip()
        if not name:
            raise ValidationError(f"Пустое имя столбца: {spec}")
        if typ not in VALID_TYPES:
            raise ValidationError(
                f"Некорректный тип: {typ}. Допустимо: {', '.join(VALID_TYPES)}"
            )
        if name == ID_COL_NAME:
            raise ValidationError('Столбец "ID" добавляется автоматически.')
        parsed.append({"name": name, "type": typ})
    return parsed


def _get_schema(metadata, table_name):
    if table_name not in metadata:
        raise NotFoundError(MSG_TABLE_NOT_EXISTS.format(table=table_name))
    return metadata[table_name]


def _type_of_column(columns, col_name):
    for col in columns:
        if col["name"] == col_name:
            return col["type"]
    raise NotFoundError(f'Столбец "{col_name}" не найден.')


def _ensure_columns_exist(columns, clause):
    for key in clause.keys():
        _type_of_column(columns, key)


def _coerce_clause(columns, clause):
    result = {}
    for key, value in clause.items():
        col_type = _type_of_column(columns, key)
        result[key] = _coerce_value(value, col_type)
    return result


def _coerce_value(value, expected_type):
    if expected_type == "int":
        if isinstance(value, bool):
            raise ValidationError("bool нельзя использовать как int")
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError as exc:
                raise ValidationError(f"Ожидался int, получено: {value}") from exc
        raise ValidationError(f"Ожидался int, получено: {value}")

    if expected_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            low = value.lower()
            if low == "true":
                return True
            if low == "false":
                return False
        raise ValidationError(f"Ожидался bool(true/false), получено: {value}")

    if expected_type == "str":
        if isinstance(value, str):
            return value
        return str(value)

    raise ValidationError(f"Неизвестный тип в схеме: {expected_type}")


def _select_cache_key(table_name, where):
    if not where:
        return (table_name, None, None)
    col = next(iter(where.keys()))
    val = where[col]
    return (table_name, col, _cache_value_key(val))


def _cache_value_key(val):
    if isinstance(val, bool):
        return ("bool", "true" if val else "false")
    if isinstance(val, int):
        return ("int", str(val))
    return ("str", str(val))


def _select_impl(table_name, where):
    rows = load_table_data(table_name)
    if not where:
        return rows
    return [row for row in rows if _row_matches(row, where)]


def _row_matches(row, where):
    for key, value in where.items():
        if key not in row:
            return False
        if row[key] != value:
            return False
    return True


def _print_rows(columns, rows):
    try:
        from prettytable import PrettyTable
    except ImportError as exc:
        raise ValidationError("PrettyTable не установлен") from exc

    field_names = [col["name"] for col in columns]
    table = PrettyTable()
    table.field_names = field_names

    for row in rows:
        table.add_row([_to_display(row.get(name)) for name in field_names])

    print(table)


def _to_display(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return value
