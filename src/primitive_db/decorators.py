import time

import prompt

from primitive_db.constants import (
    MSG_CONFIRM_TEMPLATE,
    MSG_OPERATION_CANCELED,
    MSG_TIME_TEMPLATE,
)
from primitive_db.exceptions import DBError


def handle_db_errors(func):
    """Centralized error handling for DB operations."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DBError as e:
            print(f"Ошибка: {e}")
            return None
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база данных не инициализирована.")
            return None
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
            return None
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
            return None
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return None

    wrapper.__name__ = getattr(func, "__name__", "wrapper")
    wrapper.__doc__ = getattr(func, "__doc__", None)
    return wrapper


def confirm_action(action_name):
    """Decorator factory: asks y/n confirmation before dangerous action."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            answer = prompt.string(MSG_CONFIRM_TEMPLATE.format(action=action_name)).strip()
            if answer.lower() != "y":
                print(MSG_OPERATION_CANCELED)
                return None
            return func(*args, **kwargs)

        wrapper.__name__ = getattr(func, "__name__", "wrapper")
        wrapper.__doc__ = getattr(func, "__doc__", None)
        return wrapper

    return decorator


def log_time(func):
    """Logs execution time of a function."""

    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()
        print(MSG_TIME_TEMPLATE.format(name=func.__name__, seconds=end - start))
        return result

    wrapper.__name__ = getattr(func, "__name__", "wrapper")
    wrapper.__doc__ = getattr(func, "__doc__", None)
    return wrapper


def create_cacher():
    """
    Closure cache for select results.

    Returns function cache_result(key, value_func) with:
    - cache_result.was_hit: bool of last call
    - cache_result.invalidate(table_name): invalidate all keys for table
    """

    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            cache_result.was_hit = True
            return _clone_rows(cache[key])
        cache_result.was_hit = False
        value = value_func()
        cache[key] = _clone_rows(value)
        return _clone_rows(value)

    def invalidate(table_name):
        to_delete = [
            k for k in cache if isinstance(k, tuple) and k and k[0] == table_name
        ]
        for k in to_delete:
            cache.pop(k, None)

    cache_result.was_hit = False
    cache_result.invalidate = invalidate
    return cache_result


def _clone_rows(rows):
    return [dict(r) for r in rows]
