<!--
ML-CRA documentation compaction package v01.
Документ сформирован после REPORT_34 как переход от серии мелких REPORT-файлов к малому числу главных документов.
Термины на английском используются только если они являются названием проекта, метрикой, именем файла, именем библиотеки или цитатой из уже существующих материалов; по возможности дан русский перевод.
-->

# Этап 2 — данные и кандидаты наборов данных

## 1. Назначение документа

Этот документ является главным рабочим документом по выбору и аудиту наборов данных. Он заменяет необходимость каждый раз проходить `REPORT_06`–`REPORT_20`, карточки наборов данных и разрозненные CSV, когда нужно понять, какие данные допустимы и почему.

## 2. Статус этапа

Статус: первый OpenML-контур завершен; UCI-контур приостановлен из-за проблем доступа; текущая активная линия перешла к MiniBooNE.

## 3. Почему этап важен

Выбор данных является исследовательским этапом, а не технической уборкой. В исходной стратегии прямо зафиксировано: слабый выбор набора данных разрушит проект, даже если код будет хорошим. Текущая архивная копия источника: `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`, страница: не применяется, раздел `1. Why dataset strategy is critical`, строки 16–31. Дословный фрагмент: «A weak dataset selection will destroy the project even if the code is good ... Therefore, dataset sourcing is a core research phase, not a preliminary housekeeping task».

## 4. Принципы допуска набора данных

Набор должен быть достаточно открытым для публичного проекта и воспроизводимой загрузки; недопустимы неясное происхождение, неизвестная перепубликация, приватный доступ и лицензия, блокирующая воспроизводимость. Текущая архивная копия источника: `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`, страница: не применяется, раздел `2. Dataset sourcing principles`, строки 35–52. Дословный фрагмент: «A dataset must be open enough for a public GitHub project and must support reproducible acquisition ... Unacceptable: unclear origin; reuploaded dataset with unknown provenance; dataset requiring private access».

Метаданные обязательны: тип задачи, целевая переменная, описание признаков, размеры, пропуски, структура числовых и категориальных признаков, лицензия или источник, требования предобработки, возможная групповая или временная структура и известные риски утечки. Текущая архивная копия источника: `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`, страница: не применяется, раздел `Principle 4 — Metadata matters`, строки 79–92. Дословный фрагмент: «The dataset must include enough metadata to support a reliable audit: task type; target variable; feature descriptions; number of rows and features; missingness; categorical/numerical feature structure; license/source/citation; known preprocessing requirements; possible group or time structure; known leakage risks if documented».

Для ML-CRA желательно иметь не только случайные табличные наборы, но и хотя бы часть наборов со структурой, влияющей на разбиение: временной порядок, группы, сущности или повторные наблюдения. Текущая архивная копия источника: `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`, страница: не применяется, раздел `Principle 5 — Prefer datasets with split-relevant structure`, строки 94–105. Дословный фрагмент: «Because Split Sensitivity Audit is central to ML-CRA, the dataset pool should include at least some datasets with: timestamp; temporal ordering; group identifier; entity identifier; repeated-subject structure; naturally grouped observations».

## 5. Источники данных

OpenML является первым систематическим источником поиска, потому что предоставляет программный доступ, метаданные, задачи и проверочные наборы; одновременно OpenML не является автоматическим источником утверждения кандидата. Текущая архивная копия источника: `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`, страница: не применяется, раздел `3.1 OpenML`, строки 125–144. Дословный фрагмент: «OpenML is the primary candidate source because it provides programmatic access, metadata, tasks, and benchmark suites ... OpenML should be the first systematic search source, but not an automatic approval source».

## 6. Реестр кандидатов

Кандидатов нельзя выбирать только потому, что на них удобно получить красивый результат. Каждый серьезный кандидат должен пройти проверку источника, лицензии, размера, признаков, целевой переменной и рисков утечки. Текущая архивная копия источника: `docs/archive/reports/REPORT_07_dataset_candidate_registry_protocol.md`, страница: не применяется, раздел `1. Главный принцип`, строки 18–31. Дословный фрагмент: «Нельзя выбирать наборы данных только потому, что на них удобно получить красивый результат. Каждый серьезный кандидат должен пройти через: проверку источника; проверку лицензии; проверку размера; проверку признаков; проверку целевой переменной; проверку рисков утечки».

Историческая схема статусов включала `candidate`, `shortlisted`, `accepted`, `conditional`, `rejected`. Текущая архивная копия источника: `docs/archive/reports/REPORT_07_dataset_candidate_registry_protocol.md`, страница: не применяется, раздел `3.1 Обязательные поля / 4. Статусы кандидатов`, строки 117–156. Дословный фрагмент: «status | candidate, shortlisted, accepted, conditional, rejected ... candidate ... shortlisted ... accepted ... conditional ... rejected». После диагностических контуров для трех OpenML-кандидатов введены рабочие роли: `primary_tabular_candidate`, `temporal_sensitivity_candidate`, `leakage_risk_diagnostic_hold`. Текущая архивная копия источника: `docs/archive/reports/REPORT_31_openml_candidate_status_update.md`, страница: не применяется, раздел `6. Итоговое решение`, строки 107–115. Дословный фрагмент: «Принять рабочее обновление реестра: openml_miniboone_41150 — primary_tabular_candidate; openml_electricity_151 — temporal_sensitivity_candidate; openml_click_prediction_small_41434 — leakage_risk_diagnostic_hold».

## 7. Текущие роли кандидатов

1. `openml_miniboone_41150` — основной табличный кандидат.
2. `openml_electricity_151` — кандидат для проверки временной чувствительности и дрейфа.
3. `openml_click_prediction_small_41434` — удержанный диагностический пример риска идентификаторных признаков.

Эти роли не являются финальным публикационным выбором: в `REPORT_31` прямо зафиксировано, что решения основаны на диагностических контурах, а MiniBooNE еще не прошел финальную проверку метаданных и лицензии. Текущая архивная копия источника: `docs/archive/reports/REPORT_31_openml_candidate_status_update.md`, страница: не применяется, раздел `5. Самокритика решения`, строки 97–105. Дословный фрагмент: «MiniBooNE проверен на устойчивость к зернам случайности, но пока не проверен на внешние сдвиги распределения и не прошел финальную проверку метаданных и лицензии ... все три решения основаны на диагностических контурах, а не на финальном исследовательском протоколе».

## 8. Артефакты этапа

Основные исторические артефакты:

- `data_registry/dataset_candidate_registry.csv`;
- `docs/dataset_selection/cards/*.md`;
- `docs/archive/reports/REPORT_06_dataset_sourcing_strategy.md`;
- `docs/archive/reports/REPORT_07_dataset_candidate_registry_protocol.md`;
- `docs/archive/reports/` — архивные `REPORT_08`–`REPORT_20`;
- `data_registry/openml_*` и `data_registry/uci_*`, если они используются кодом или аудитом.

Новая политика: не создавать новые карточки и реестры без необходимости. Если статус или роль кандидата меняется, сначала обновляется этот документ, затем только один машинно-читаемый реестр.

## 9. Критерий готовности этапа

Этап считается готовым для перехода к экспериментам, если:

1. источник данных воспроизводим;
2. целевая переменная известна;
3. признаки перечислены;
4. риск утечки отдельно проверен;
5. протокол допустимого разбиения зафиксирован;
6. роль кандидата понятна.

## 10. Задачи John

1. Не удалять исторические карточки и отчеты по данным.
2. В дальнейшем не запрашивать создание новой карточки набора данных, если достаточно обновить этот документ.
3. Если появится новый набор данных, сначала добавить его в раздел «Кандидаты на вход», а отдельные CSV создавать только после решения о проверке.
