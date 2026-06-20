# Генератор лабораторных работ

Проект генерирует персонализированные варианты лабораторных работ по программированию и проверочные тесты для них.

Сейчас реализованы 6 из 6 лабораторных работ:

- `lab1` - набор подзадач на обработку массива;
- `lab2` - многофайловый C-проект с pipeline из step/core функций;
- `lab3` - обработка текста и предложений;
- `lab4` - обзор стандартной библиотеки C и работа со строками;
- `lab5` - работа с регулярными выражениями;
- `lab6` - работа с динамическим списком.


## Требуемое окружение

Для запуска через Docker нужно установить:

- `git`;
- Docker 24 или новее.

Для локального запуска без Docker нужно установить:

- Python 3.12;
- `pip`;
- `gcc` и `make` для проверок C-решений.

Все команды ниже выполняются из корня репозитория `mse1h2026-lab-gen`.

## Запуск через Docker

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

Проверить корректность запуска:

```bash
python main.py lab1 --seed smoke-seed --mode=init
python main.py lab6 --seed smoke-seed --mode=dry-run
```

Ожидаемый результат: команды завершаются без `Traceback`, выводят текст задания или JSON с полем `assignment`.

## Локальный запуск

```bash
git clone https://github.com/moevm/mse1h2026-lab-gen.git
cd mse1h2026-lab-gen
python -m pip install -e ".[test]"
labgen --help
```

Старый запуск через `python main.py ...` также поддерживается.

## Добавление в кафедральный Docker-образ

Проект можно установить как Python-зависимость из GitHub без установки `git` в образ:

```dockerfile
RUN pip install https://github.com/moevm/mse1h2026-lab-gen/archive/refs/heads/main.zip
```

Если в образе уже есть `git`, можно использовать `git+https`:

```dockerfile
RUN pip install git+https://github.com/moevm/mse1h2026-lab-gen.git@main
```

После установки в образе будет доступна команда `labgen`:

```bash
labgen lab1 --seed Басыров --mode=init
labgen lab4 --seed Басыров --mode=check --solution=solution.c
```

## Примеры команд

Показать параметры конкретной лабораторной:

```bash
python main.py lab1 -h
labgen lab6 -h
```

Сгенерировать вариант:

```bash
python main.py lab1 --seed Басыров --mode=init
python main.py lab2 --seed Басыров --mode=init
python main.py lab3 --seed Басыров --mode=init
python main.py lab4 --seed Басыров --mode=init
python main.py lab5 --seed Басыров --mode=init
python main.py lab6 --seed Басыров --mode=init
```

Вывести задание вместе со сгенерированными тестами:

```bash
python main.py lab4 --seed Басыров --mode=dry-run
python main.py lab6 --seed Басыров --mode=dry-run
```

Проверить решение:

```bash
python main.py lab1 --seed Басыров --mode=check --solution=./examples/lab1_solution_good.c
python main.py lab5 --seed test123 --mode=check --solution=./examples/lab5_solution_good.c
python main.py lab6 --seed test_student --mode=check --solution=./examples/lab6_solution_good.c
```

Для ЛР1 поддержана опция случайного выбора основания системы счисления для чисел на входе и выходе (от 10 до 234):

```bash
python main.py lab1 --seed Басыров --mode=init --random-base --base-min 10 --base-max 234
```

Для ЛР2 поддержана проверка текстового blob-файла:

```bash
python -m prog_labgen.lab2.lab2_cli --blob-file ./examples/lab2_solution_good.txt --seed example-lab2 --mode=check
```

## Тесты

В проекте есть несколько уровней автоматизированных проверок:

- `pytest` - smoke-тесты CLI и unit-тесты отдельных лабораторных;
- `scripts/run_example_checks.py` - интеграционная проверка good/bad эталонных решений для ЛР1-ЛР6;
- `scripts/stress_generate_variants.py` - массовая проверка генерации вариантов на наборе seed-ов;
- GitHub Actions - запуск тестов, интеграционных проверок, stress-проверки и Docker-сценариев на `push` и `pull_request`.

Локальный запуск:

```bash
python -m pip install -e ".[test]"
python -m pytest
python scripts/run_example_checks.py
python scripts/stress_generate_variants.py --count 25
```

Запуск внутри Docker-контейнера:

```bash
python -m pytest
python scripts/run_example_checks.py
python scripts/stress_generate_variants.py --runner labgen --count 25
```

Запуск одной командой через Docker без ручного входа в контейнер:

```bash
docker run --rm mse-lab-gen -lc "python -m pytest && python scripts/run_example_checks.py && python scripts/stress_generate_variants.py --runner labgen --count 25"
```

### Stress-проверка генерации

Stress-проверка нужна, чтобы будущие изменения не выдавали студентам сломанные варианты. Скрипт запускает `init` и `dry-run` для каждой лабораторной на фиксированных seed-ах из `scripts/seed_to_check.txt` и на синтетических seed-ах вида `ci-seed-0000`.

Проверяется:

- команда завершилась с кодом `0`;
- вывод не пустой;
- в выводе нет `Traceback`;
- в выводе нет `None`, `TODO`, `<undefined>`;
- повторный запуск с тем же seed дает тот же результат;
- на наборе seed-ов для каждой лабораторной появляется больше одного варианта;
- если `dry-run` выводит JSON, он валиден и содержит `assignment`;
- если в JSON есть `tests`, каждый тест содержит входные данные и `expected_stdout`.

Пример запуска:

```bash
python scripts/stress_generate_variants.py --labs lab1 lab2 lab3 lab4 lab5 lab6 --count 100
```

При ошибке скрипт печатает команду для воспроизведения:

```text
FAILED
lab=lab3
seed=ci-1842
mode=dry-run

Reproduce:
python main.py lab3 --seed ci-1842 --mode=dry-run
```

### GitHub Actions

В `.github/workflows/tests.yml` настроен быстрый CI для `push` и `pull_request`.

Он проверяет:

- установку проекта как пакета через `pip install -e ".[test]"`;
- запуск установленной команды `labgen` из директории вне репозитория;
- обратную совместимость `python main.py ...`;
- `help` для ЛР1-ЛР6 через `labgen` и `python main.py`;
- `pytest`;
- good/bad эталонные решения для ЛР1-ЛР6;
- малый seed stress;
- сборку Docker-образа;
- запуск `labgen`, `python main.py`, `pytest`, good/bad checks и stress внутри Docker.

В `.github/workflows/stress.yml` настроен тяжелый ручной stress-прогон:

```bash
python scripts/stress_generate_variants.py --runner labgen --count 1000
```

Он нужен для поиска редких падений генератора на большом количестве seed-ов и не блокирует каждый pull request.

## Документация

Материалы по итерациям и концепции лабораторных находятся в ветке `reports`:

- `docs/specification.md` - спецификация требований;
- `docs/lab1_concept.md` - концепция ЛР1;
- `docs/lab2_concept.md` - концепция ЛР2;
- `docs/lab3_concept.md` - концепция ЛР3;
- `docs/lab4_concept.md` - концепция ЛР4;
- `docs/lab5_concept.md` - концепция ЛР5;
- `docs/lab6_concept.md` - концепция ЛР6;
- `docs/iteration_*.pdf` - презентации по итерациям;
- `reports.md` - ссылки на материалы по итерациям.
