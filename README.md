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

Обычный запуск из репозитория через `python main.py ...` также поддерживается.

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

В проекте есть несколько уровней проверок:

- `pytest` - функциональные smoke-тесты CLI и unit-тесты отдельных лабораторных;
- `scripts/run_example_checks.py` - интеграционная проверка good/bad эталонных решений для ЛР1-ЛР4.
- `scripts/stress_generate_variants.py` - массовая проверка генерации вариантов на наборе seed-ов.

Запуск внутри Docker-контейнера:

```bash
python -m pytest
python scripts/run_example_checks.py
python scripts/stress_generate_variants.py --count 25
```

Запуск одной командой через Docker без ручного входа в контейнер:

```bash
docker run --rm mse-lab-gen -lc "python -m pytest && python scripts/run_example_checks.py && python scripts/stress_generate_variants.py --count 25"
```

### Stress-проверка генерации

Stress-проверка нужна, чтобы будущие изменения не выдавали студентам сломанные варианты. Скрипт запускает `init` и `dry-run` для каждой лабораторной на фиксированных seed-ах из `scripts/seed_to_check.txt` и на синтетических seed-ах вида `ci-seed-0000`.

Проверяется:

- команда завершилась с кодом `0`;
- вывод не пустой;
- в выводе нет `Traceback`;
- в выводе нет `None`, `TODO`, `<undefined>`;
- повторный запуск с тем же seed дает тот же результат.
- на наборе seed-ов для каждой лабораторной появляется больше одного варианта.
- если `dry-run` выводит JSON, он должен быть валидным и содержать `assignment`;
- если в JSON есть `tests`, каждый тест должен содержать входные данные и `expected_stdout`.

Пример запуска:

```bash
python scripts/stress_generate_variants.py --labs lab1 lab2 lab3 lab4 --count 100
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
- `help` для всех лабораторных через `labgen` и `python main.py`;
- `pytest`;
- good/bad эталонные решения;
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
- `docs/iteration_*.pdf` - презентации по итерациям.
