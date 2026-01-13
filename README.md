# Primitive DB (учебный проект)

Консольное приложение, имитирующее примитивную базу данных:
- Таблицы и CRUD-операции
- Хранение метаданных в `db_meta.json`
- Хранение данных таблиц в `data/<table>.json`
- Декораторы: обработка ошибок, подтверждение опасных действий, замер времени
- Кэширование одинаковых запросов `select` (замыкание)

## Требования
- Python 3.11+
- Poetry

## Установка
```bash
make install
```

## Запуск
```bash
make run
```

После установки и запуска доступна команда:
```bash
poetry run database
```

## Команды

### Общие
- `help` — справка
- `exit` — выход

### Таблицы
- `create_table <table_name> <col:type> <col:type> ...`
  - Автоматически добавляется `ID:int` первым столбцом
- `list_tables`
- `drop_table <table_name>` (спросит подтверждение y/n)

Поддерживаемые типы: `int`, `str`, `bool`

### CRUD
- `insert into <table_name> values (<v1>, <v2>, ...)`
  - `ID` не вводится, генерируется автоматически: 1,2,3...
- `select from <table_name>`
- `select from <table_name> where <col> = <value>`
- `update <table_name> set <col>=<value> where <col>=<value>`
- `delete from <table_name> where <col> = <value>` (спросит подтверждение y/n)

### Формат значений
- Строки: `"..."` или `'...'` (кавычки рекомендуются, особенно если есть пробелы/запятые)
- bool: `true/false` (регистр не важен)
- int: целое число (например `28`, `-10`)

## Кэш select
Повторный `select` с тем же `table + where` возвращает кэшированный результат.
Кэш инвалидируется после `insert/update/delete/drop_table` для соответствующей таблицы.

## Демо-сценарий (asciinema)
Сценарий команд для записи — см. `DEMO_SCRIPT.md`.
