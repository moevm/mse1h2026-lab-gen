## Установка и запуск

Для запуска проекта нужно:

- собрать Docker-образ:
```bash
docker build -t my-app .
```
- запустить контейнер:
```bash
docker run --rm -it my-app
```
- внутри контейнера посмотреть доступные команды:
```bash
python main.py -h
```

Примеры использования:

- показать параметры ЛР1:
```bash
python main.py lab1 -h
```
- сгенерировать вариант ЛР1:
```bash
python main.py lab1 --seed Басыров --mode=init
```
- сгенерировать вариант ЛР2:
```bash
python main.py lab2 --seed Басыров --mode=init
```
- сгенерировать вариант ЛР3:
```bash
python main.py lab3 --seed Басыров --mode=init
```
- проверить решение ЛР1:
```bash
python main.py lab1 --seed Басыров --mode=check --solution=./examples/lab1_solution_good.c
```

## Проверка работоспособности
Проверка работоспособности выполняется следующими командами:

```bash
python main.py -h
python main.py lab1 --seed Басыров --mode=init
python main.py lab1 --seed Басыров --mode=check --solution=./examples/lab1_solution_good.c
python main.py lab2 --seed Басыров --mode=init
python main.py lab3 --seed Басыров --mode=init
```

Ожидаемый результат:

- help показывает доступные лабораторные работы;
- команда `init` печатает вариант для выбранного студента;
- команда `check` на `lab1_solution_good.c` завершает проверку успешно.

## Дополнительная информация
Все материалы находятся в ветке reports в папке docs:
 - specification.md - спецификация требований(представлена также в README)
 - lab1_concept.md - концепция задачи для 1 лабораторной работы
 - lab2_concept.md - концепция задачи для 2 лабораторной работы
 - lab3_concept.md - концепция задачи для 3 лабораторной работы
 - iteration_1.pdf - презентация проекта по первой итерации
 - iteration_2.pdf - презентация проекта по второй итерации
 - screencast.mp4 - скринкаст
