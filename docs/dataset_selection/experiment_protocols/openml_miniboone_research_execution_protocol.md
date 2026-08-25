# Протокол выполнения `REPORT_33`: MiniBooNE minimal research

## Что запускается

Запускаются только новые ячейки 18–24 в `notebooks/04_dataset_smoke_experiments.ipynb` после уже существующих ячеек `REPORT_27` и `REPORT_29`.

## Что запрещено

1. Не менять `dataset_candidate_registry.csv`.
2. Не менять список признаков MiniBooNE.
3. Не подбирать гиперпараметры.
4. Не удалять `dummy_prior`.
5. Не заменять `RepeatedStratifiedKFold` другим разбиением без отдельного отчета.
6. Не интерпретировать результат как финальное качество ML-CRA.

## Что должно получиться

- `data_registry/openml_miniboone_research_scores.csv`
- `data_registry/openml_miniboone_research_summary.csv`
- `data_registry/openml_miniboone_research_warnings.csv`
- `data_registry/openml_miniboone_research_environment.csv`

## Что прислать после запуска

Нужно прислать все четыре файла. Если выполнение остановится, нужно прислать номер ячейки и полный текст ошибки.
