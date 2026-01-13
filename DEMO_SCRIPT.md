# DEMO (asciinema) — последовательность команд

## 1) Установка и запуск
```bash
make install
make run
```

## 2) Работа в приложении (вводите по очереди)
```text
help
create_table users name:str age:int is_active:bool
list_tables

insert into users values ("Sergei", 28, true)
insert into users values ("Anna, Jr.", 28, false)

select from users
select from users where age = 28
select from users where age = 28

update users set is_active=true where name = "Anna, Jr."
select from users where name = "Anna, Jr."

delete from users where name = "Sergei"
y
select from users

drop_table users
y
list_tables
exit
```

## Ожидаемые демонстрации
- подтверждения y/n для `delete` и `drop_table`
- повторный `select` по одинаковому where должен сработать из кэша (будет сообщение)
- замеры времени для select/insert/update/delete
