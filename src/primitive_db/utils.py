import json
import os

from primitive_db.constants import META_FILE, STORAGE_DIR, TABLE_FILE_EXT
from primitive_db.exceptions import StorageError


def ensure_storage_dir():
    """Создать директорию хранения при необходимости."""
    os.makedirs(STORAGE_DIR, exist_ok=True)


def _read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as exc:
        raise StorageError(f"Ошибка чтения JSON: {path}: {exc}") from exc


def _write_json_atomic(path, data):
    try:
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        raise StorageError(f"Ошибка записи JSON: {path}: {exc}") from exc


def load_metadata():
    """Загрузить метаданные из META_FILE, вернуть {} если файла нет."""
    return _read_json(META_FILE, {})


def save_metadata(metadata):
    """Сохранить метаданные атомарно."""
    _write_json_atomic(META_FILE, metadata)


def _table_path(table_name):
    ensure_storage_dir()
    filename = f"{table_name}{TABLE_FILE_EXT}"
    return os.path.join(STORAGE_DIR, filename)


def load_table_data(table_name):
    """Загрузить список строк таблицы, вернуть [] если файла нет."""
    path = _table_path(table_name)
    return _read_json(path, [])


def save_table_data(table_name, rows):
    """Сохранить список строк таблицы атомарно."""
    path = _table_path(table_name)
    _write_json_atomic(path, rows)


def delete_table_file(table_name):
    """Удалить файл таблицы, если он существует."""
    path = _table_path(table_name)
    try:
        os.remove(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise StorageError(f"Ошибка удаления файла таблицы: {path}: {exc}") from exc
