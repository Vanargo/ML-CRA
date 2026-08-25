# Протокол первой безопасной тетради минимального диагностического эксперимента OpenML

Целевая будущая тетрадь:

```text
notebooks/04_dataset_smoke_experiments.ipynb
```

Назначение: выполнить первый минимальный диагностический запуск OpenML-кандидатов после утверждения протоколов признаков, моделей, разбиений и метрик.

## Граница безопасности

Это не финальный эксперимент и не выбор победителя. Будущая тетрадь должна только проверить, что первый контур технически собирается без нарушения протоколов проекта.

## Кандидаты

1. `openml_electricity_151`;
2. `openml_miniboone_41150`;
3. `openml_click_prediction_small_41434`.

## Первый обязательный режим

Используется одно стратифицированное случайное разбиение для каждого кандидата.

Временное разбиение `electricity` не включается в обязательный первый запуск; сначала нужно проверить восстановление порядка по `date`, `day`, `period`.

## Признаки

`openml_electricity_151`:

```text
nswprice; nswdemand; vicprice; vicdemand; transfer
```

`openml_miniboone_41150`:

```text
ParticleID_0 ... ParticleID_49
```

`openml_click_prediction_small_41434`:

```text
impression; depth; position
```

Идентификаторы `Click_prediction_small` исключаются.

## Модели

1. `DummyClassifier` — модель-заглушка;
2. `LogisticRegression` — регуляризованная логистическая регрессия;
3. `HistGradientBoostingClassifier` — гистограммный градиентный бустинг.

`RandomForestClassifier` не входит в обязательный первый запуск.

CatBoost и LightGBM не используются.

## Метрики

1. ROC-AUC — площадь под ROC-кривой;
2. PR-AUC — площадь под кривой точность-полнота;
3. F1 — гармоническое среднее точности и полноты;
4. balanced accuracy — сбалансированная точность;
5. log loss — логарифмическая потеря;
6. Brier score — оценка качества вероятностного прогноза.

## Ожидаемые выходные файлы будущей тетради

```text
data_registry/openml_first_diagnostic_scores.csv
data_registry/openml_first_diagnostic_warnings.csv
data_registry/openml_first_diagnostic_environment.csv
```

## Запреты

Будущая тетрадь не должна менять статусы кандидатов, выполнять подбор гиперпараметров, использовать идентификаторы как признаки, выполнять целевое кодирование или объявлять победителя.
