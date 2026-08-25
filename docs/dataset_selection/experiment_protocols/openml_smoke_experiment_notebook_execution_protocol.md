# Протокол выполнения тетради `04_dataset_smoke_experiments.ipynb`

## Назначение

Тетрадь выполняет первый минимальный диагностический запуск трех OpenML-кандидатов.

## Граница результата

Результаты имеют статус `diagnostic_draft`. Они не выбирают победителя, не подтверждают финальное утверждение и не меняют статусы наборов данных.

## Входные файлы

```text
data_registry/dataset_candidate_registry.csv
data_registry/openml_feature_preprocessing_plan.csv
data_registry/openml_model_protocol_plan.csv
data_registry/openml_split_protocol_plan.csv
data_registry/openml_metric_plan.csv
data_registry/openml_first_diagnostic_notebook_plan.csv
```

## Выходные файлы

```text
data_registry/openml_first_diagnostic_scores.csv
data_registry/openml_first_diagnostic_warnings.csv
data_registry/openml_first_diagnostic_environment.csv
```

## Обязательные ограничения

1. Не менять `dataset_candidate_registry.csv`.
2. Не менять карточки наборов данных.
3. Не использовать идентификаторы `Click_prediction_small`.
4. Не использовать `date`, `day`, `period` как признаки `electricity`.
5. Не добавлять подбор гиперпараметров.
6. Не объявлять победителя.

## Следующий шаг после выполнения

После успешного запуска нужно провести `REPORT_28_openml_first_diagnostic_results_review.md` по созданным CSV-файлам.
