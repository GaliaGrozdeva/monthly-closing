# Месечно приключване

Библиотека за счетоводни процедури. Python 3.13, Django 6.1.2 и SQLite.

## Стартиране на Windows

Първоначална подготовка: `setup.bat`. Стартиране: `start.bat`.
Адрес: <http://127.0.0.1:8000/>. Спиране: Ctrl+C в терминала.

## Проверки

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test
```

Работните данни са в `db.sqlite3` и не се включват в Git.
Настройките са за локална работа.
