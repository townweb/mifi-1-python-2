APP_TITLE = "***База данных***"

PROMPT_TEXT = ">>>Введите команду: "

CMD_HELP = "help"
CMD_EXIT = "exit"

CMD_CREATE_TABLE = "create_table"
CMD_LIST_TABLES = "list_tables"
CMD_DROP_TABLE = "drop_table"

KW_INSERT = "insert"
KW_SELECT = "select"
KW_UPDATE = "update"
KW_DELETE = "delete"

KW_INTO = "into"
KW_FROM = "from"
KW_VALUES = "values"
KW_WHERE = "where"
KW_SET = "set"

STORAGE_DIR = "data"
META_FILE = "db_meta.json"
TABLE_FILE_EXT = ".json"

ID_COL_NAME = "ID"
ID_COL_TYPE = "int"

VALID_TYPES = ("int", "str", "bool")

MSG_UNKNOWN_FUNCTION = "Функции {name} нет. Попробуйте снова."
MSG_INVALID_VALUE = "Некорректное значение: {value}. Попробуйте снова."

MSG_TABLE_CREATED = 'Таблица "{table}" успешно создана со столбцами: {cols}'
MSG_TABLE_EXISTS = 'Ошибка: Таблица "{table}" уже существует.'
MSG_TABLE_NOT_EXISTS = 'Ошибка: Таблица "{table}" не существует.'
MSG_NO_TABLES = "Таблиц нет."

MSG_ROW_INSERTED = 'Запись с ID={id} успешно добавлена в таблицу "{table}".'
MSG_UPDATED = 'Обновлено записей: {count} в таблице "{table}".'
MSG_DELETED = 'Удалено записей: {count} из таблицы "{table}".'

MSG_OPERATION_CANCELED = "Операция отменена."
MSG_CONFIRM_TEMPLATE = 'Вы уверены, что хотите выполнить "{action}"? [y/n]: '

MSG_TIME_TEMPLATE = "Функция {name} выполнилась за {seconds:.3f} секунд"

MSG_CACHE_HIT = "Кэш: использован сохранённый результат."
MSG_CACHE_MISS = "Кэш: вычисление результата."

HELP_TEXT = """
***Процесс работы с таблицей и данными***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> ...
<command> list_tables
<command> drop_table <имя_таблицы>

<command> insert into <имя_таблицы> values (<v1>, <v2>, ...)
<command> select from <имя_таблицы>
<command> select from <имя_таблицы> where <столбец> = <значение>
<command> update <имя_таблицы> set <столбец>=<значение> where <столбец>=<значение>
<command> delete from <имя_таблицы> where <столбец> = <значение>

Общие команды:
<command> exit
<command> help
""".strip()
