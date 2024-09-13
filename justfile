#!/usr/bin/env just --justfile
set dotenv-load

DB_URL := "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_SERVER:$POSTGRES_PORT/$POSTGRES_DB"

# Подготовка проекта
prepare:
  poetry install
  poetry self add poetry-plugin-dotenv
  cp .env.template .env
  echo "Пожалуйста установите значения для переменных окружения в файле .env"

# Подключение к бд
psql:
  psql {{ DB_URL }}

# Выполнить sql скрипт
db_exec filename:
  psql {{ DB_URL }} -a -f {{filename}}

# Удаление базы данных
db_drop:
  psql {{ DB_URL }} -a -f posgresql-scripts/drop.sql

# Создание базы данных
db_init:
  psql {{ DB_URL }} -a -f posgresql-scripts/init.sql

# Очистка базы данных
db_reset: db_drop db_init

# Запуск сервера
run:
  poetry run uvicorn main:app --reload

lint mode="fix":
  #!/bin/bash
  if [ "{{ mode }}" == "fix" ]; then
    poetry run isort .
    poetry run black .
    poetry run flake8
  elif [ "{{ mode }}" == "check" ]; then
    poetry run flake8
    poetry run black --diff --check .
    poetry run isort --diff --check .
  else
    echo "Invalid argument '{{ mode }}'"
  fi
