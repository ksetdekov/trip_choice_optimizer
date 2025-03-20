# trip_choice_optimizer

find best options of an list of commute options using Thompson Sampling algorithms for Mean-Variance Bandits (<https://arxiv.org/pdf/2002.00232.pdf>)

## TODO

- [x] Update bot.py to be able to create variants in an optimization.
- [x] Update bot.py to be able to create a new optimization.
- [x] bot can add a new option to an optimization using an inline keyboard.
- [x] bot cat sample options from a list of options.
- [x] handled an error with optimization being named too long - "Звать Мерлина, если он орет?”- это давало превышение 64 байт в callback_data
- [] сделать усечение длины названий до 280 байт
- [] на этапе удаления оптимизации также передавать id оптимизации в callback_data

```bash
docker build -t ksetdekov/trip_choice_optimizer:latest .
docker login
docker push ksetdekov/trip_choice_optimizer:latest
```