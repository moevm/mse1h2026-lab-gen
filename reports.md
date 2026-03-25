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
python main.py lab1 --student Басыров --mode=init
```
- сгенерировать вариант ЛР2:
```bash
python main.py lab2 --student Басыров --mode=init
```
- сгенерировать вариант ЛР3:
```bash
python main.py lab3 --student Басыров --mode=init
```
- проверить решение ЛР1 на рабочем примере:
```bash
python main.py lab1 --student Басыров --mode=check --solution=./examples/lab1_solution_good.c
```

## Итерация №2
Материалы:
 - [specification.md](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/specification.md) - спецификация требований
 - [lab1_concept.md](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/lab1_concept.md) - концепция задачи для 1 лабораторной работы
 - [lab2_concept.md](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/lab2_concept.md) - концепция задачи для 2 лабораторной работы
 - [lab3_concept.md](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/lab3_concept.md) - концепция задачи для 3 лабораторной работы
 - [iteration_2.pdf](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/iteration_2.pdf) - презентация проекта
 - [screencast.mp4](https://github.com/moevm/mse1h2026-lab-gen/blob/reports/docs/screencast.mp4) - скринкаст

