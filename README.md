# Генератор лабораторных работ

Проект генерирует персонализированные варианты лабораторных работ по программированию.

Сейчас поддержаны ЛР1-ЛР4:

- `lab1` - набор подзадач на обработку массива;
- `lab2` - многофайловый C-проект с pipeline из step/core функций;
- `lab3` - обработка текста и предложений;
- `lab4` - обзор стандартной библиотеки C и работа со строками.

## Запуск через Docker

Нужно установить:

- `git`;
- `Docker`.

Скопируйте и выполните команды:

```bash
git clone https://github.com/moevm/mse1h2026-lab-gen.git
cd mse1h2026-lab-gen
docker build -t mse-lab-gen .
docker run --rm -it mse-lab-gen
```

Посмотреть доступные команды внутри контейнера:

```bash
python main.py -h
```

## Примеры команд

Показать параметры конкретной лабораторной:

```bash
python main.py lab1 -h
```

Сгенерировать вариант:

```bash
python main.py lab1 --seed Басыров --mode=init
python main.py lab2 --seed Басыров --mode=init
python main.py lab3 --seed Басыров --mode=init
python main.py lab4 --seed Басыров --mode=init
```

Вывести задание вместе со сгенерированными тестами:

```bash
python main.py lab4 --seed Басыров --mode=dry-run
```

Проверить решение:

```bash
python main.py lab1 --seed Басыров --mode=check --solution=./examples/lab1_solution_good.c
```

## Тесты

В проекте есть два уровня проверок:

- `pytest` - функциональные smoke-тесты CLI и unit-тесты отдельных лабораторных;
- `scripts/run_example_checks.py` - интеграционная проверка good/bad эталонных решений для ЛР1-ЛР4.

Запуск внутри Docker-контейнера:

```bash
python -m pytest
python scripts/run_example_checks.py
```

Запуск одной командой через Docker без ручного входа в контейнер:

```bash
docker run --rm mse-lab-gen -lc "python -m pytest && python scripts/run_example_checks.py"
```

Эти же проверки запускаются в GitHub Actions при `push` и `pull_request`.


## Документация

Материалы по итерациям и концепции лабораторных находятся в ветке `reports`:

- `docs/specification.md` - спецификация требований;
- `docs/lab1_concept.md` - концепция ЛР1;
- `docs/lab2_concept.md` - концепция ЛР2;
- `docs/lab3_concept.md` - концепция ЛР3;
- `docs/lab4_concept.md` - концепция ЛР4;
- `docs/iteration_*.pdf` - презентации по итерациям.
