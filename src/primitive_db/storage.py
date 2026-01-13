import json
import os

from primitive_db.constants import META_FILE, STORAGE_DIR, TABLE_FILE_EXT
from primitive_db.exceptions import StorageError


def ensure_storage_dir():
    """Ensure storage directory exists."""
    os.makedirs(STORAGE_DIR, exist_ok=True)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as e:
        raise StorageError(f"Ошибка чтения JSON: {path}: {e}") from e


def _write_json_atomic(path, data):
    try:
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as e:
        raise StorageError(f"Ошибка записи JSON: {path}: {e}") from e


def load_metadata():
    """Load metadata from META_FILE. If missing, return empty dict."""
    return _read_json(META_FILE, {})


def save_metadata(metadata):
    """Save metadata to META_FILE atomically."""
    _write_json_atomic(META_FILE, metadata)


def _table_path(table_name):
    ensure_storage_dir()
    filename = f"{table_name}{TABLE_FILE_EXT}"
    return os.path.join(STORAGE_DIR, filename)


def load_table_data(table_name):
    """Load table data list from data/<table>.json. If missing, return empty list."""
    path = _table_path(table_name)
    return _read_json(path, [])


def save_table_data(table_name, rows):
    """Save table data list to data/<table>.json atomically."""
    path = _table_path(table_name)
    _write_json_atomic(path, rows)


def delete_table_file(table_name):
    """Delete table data file if exists."""
    path = _table_path(table_name)
    try:
        os.remove(path)
    except FileNotFoundError:
        return
    except OSError as e:
        raise StorageError(f"Ошибка удаления файла таблицы: {path}: {e}") from e
