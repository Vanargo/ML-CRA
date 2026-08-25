# Протокол обновления рабочих статусов OpenML-кандидатов после REPORT_31

## 1. Назначение

Этот документ описывает, как переносить обновление `dataset_candidate_registry.csv`, подготовленное в `REPORT_31`.

## 2. Файлы

Основной файл для замены:

```text
data_registry/dataset_candidate_registry.csv
```

Сопутствующие файлы аудита:

```text
data_registry/dataset_candidate_registry_report31_change_audit.csv
data_registry/openml_report31_candidate_status_update.csv
data_registry/openml_candidate_status_definitions.csv
data_registry/openml_report31_evidence_index.csv
```

## 3. Правила переноса

1. Сначала сохранить исходный текущий `data_registry/dataset_candidate_registry.csv` в резервную копию вне git-изменений или отдельным именем.
2. Затем заменить `data_registry/dataset_candidate_registry.csv` файлом из пакета `REPORT_31`.
3. После замены проверить, что количество строк осталось прежним: 10 строк данных плюс строка заголовка.
4. Проверить, что изменены только три кандидата: `openml_miniboone_41150`, `openml_electricity_151`, `openml_click_prediction_small_41434`.
5. Не менять тетради и программный код на этом шаге.

## 4. Граница решения

Обновление статусов не означает финальный выбор набора данных. Оно только задает рабочие роли кандидатов для следующего этапа.
