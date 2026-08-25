<!--
ML-CRA roadmap v04.
Назначение версии: закрепить компактный режим работы над проектом после анализа ml-cra_v03.zip и bio_inspired_project_engineering_standard_v02.md.
Правило языка: русская документация сначала; англоязычные термины допускаются как имена файлов, метрик, библиотек, сущностей ML или устойчивые термины с русским пояснением.
-->

# ML-CRA — дорожная карта и регламент компактной работы

## 0. Статус документа

`roadmap.md` является главным управляющим документом ML-CRA. Он одновременно выполняет функции дорожной карты, реестра текущего состояния, политики создания артефактов и компактной проектной памяти.

Этот файл заменяет практику создания нового номерного отчета на каждом шаге. Старые номерные отчеты сохраняются как исторический аудиторский след в `docs/archive/reports/`, но не являются рабочей зоной проекта.

Новый отдельный регламент работы над ML-CRA не создается. Основание: в предыдущей версии `roadmap.md` уже был зафиксирован отказ от продолжения цепочки `REPORT_35`, `REPORT_36`, ... и переход к модели `roadmap.md` + документы этапов; создание нового регламента увеличило бы число документов вместо уменьшения.

Методологическое основание компактного режима: `bio_inspired_project_engineering_standard_v02.md` задает MAPE-K-контур — наблюдение, анализ, планирование, выполнение и общую базу знаний, а также требует, чтобы проектная память сохраняла основания решений, источники, проверки, ошибки и ограничения. Для ML-CRA это реализуется не россыпью новых Markdown-файлов, а усилением `roadmap.md`, активного документа этапа, конфигураций и машинно-читаемых результатов.

## 1. Назначение проекта

Название проекта: **ML Claim Reliability Auditor**, кратко **ML-CRA**, русское название — «Аудитор надежности утверждений в ML-экспериментах».

Смысл проекта: проверять не только то, какая модель получила лучшую метрику, а достаточно ли доказательств для утверждения, что одна модель надежно превосходит другую.

Главная гипотеза проекта: во многих ML-экспериментах вывод «эта модель лучше» оказывается хрупким, если проверить его не одним запуском, а серией контролируемых проверок.

Минимальная версия проекта ограничивается табличным обучением с учителем. Полная автоматизация машинного обучения, крупные глубокие проверочные наборы, производственный мониторинг и другие расширения не входят в ближайший рабочий объем.

## 2. Управляющие исследовательские вопросы

Проект не должен превращаться в соревнование моделей на одном наборе данных. Управляющие вопросы ML-CRA:

1. Устойчиво ли утверждение к зерну случайности?
2. Чувствительно ли утверждение к протоколу разбиения?
3. Возникает ли конфликт метрик?
4. Достаточен ли размер эффекта для содержательного вывода?
5. Соразмерна ли стоимость качества выигрышу модели?
6. Какую категорию надежности получает утверждение: сильно подтверждено, умеренно подтверждено, слабо подтверждено, хрупко, не подтверждено или опровергнуто?

## 3. Каноническая структура проекта

Рабочая структура после компактной реорганизации:

```text
ml-cra/
  roadmap.md
  bio_inspired_project_engineering_standard_v02.md
  configs/
    claims/
    model_spaces/
    project_readiness/
    runtime/
    stress_tests/
    verdict_policies/
  data_registry/
    *.csv
  docs/
    archive/
      reports/
      stages/
    dataset_selection/
      cards/
      experiment_protocols/
      identifier_protocols/
      model_protocols/
      preprocessing_protocols/
    stages/
      stage_01_project_scope.md
      stage_02_data_and_candidate_selection.md
      stage_03_diagnostic_experiments.md
      stage_04_primary_candidate_validation.md
      stage_05_claim_audit_protocol.md
      stage_06_packaging_and_publication.md
      stage_07_code_modularization.md
      stage_08_project_completion_and_release_readiness.md
  notebooks/
    *.ipynb
  src/
    mlcra/
```

Канонические рабочие зоны:

- `roadmap.md` — текущее состояние, правила работы, ближайший шаг, реестр значимых решений;
- `docs/stages/` — один документ на этап;
- `configs/` — машинно-читаемые настройки утверждений, пространств моделей, стресс-тестов и политик вердикта;
- `data_registry/` — машинно-читаемые реестры, схемы, результаты и журналы проверок;
- `notebooks/` и `src/` — исполняемый исследовательский и программный слой;
- `docs/archive/` — исторические материалы, не редактируемые как рабочие документы.

`docs/reports/` как рабочая папка больше не используется. Если в локальном проекте она еще существует, ее содержимое переносится в `docs/archive/reports/`.

## 4. Статусы файлов и объектов

Для предотвращения расползания проекта вводятся статусы.

Статусы файлов:

- `active` — рабочий файл, который может обновляться;
- `archive-only` — исторический файл, который не редактируется в обычной работе;
- `superseded` — файл заменен более новым каноническим файлом;
- `generated` — производный файл результата или проверки;
- `config` — входная конфигурация эксперимента, утверждения или политики.

Статусы исследовательских объектов:

- `accepted` — принят как рабочий объект с достаточным основанием;
- `review` — требует ручной проверки;
- `hold` — временно удерживается и не используется как основание окончательного вывода;
- `rejected` — отклонен с причиной;
- `requires_check` — решение требует дополнительной проверки;
- `archive-only` — сохранен только как историческое основание.

Правило: объект без evidence record — записи основания — не может получить статус `accepted`.

## 5. Политика создания новых файлов

Новый файл создается только если он нужен для воспроизводимости, машинной обработки, повторного использования, аудита или выполнения кода. Новый файл не создается, если достаточно обновить `roadmap.md` или документ текущего этапа.

Разрешенные новые файлы:

1. Документ этапа в `docs/stages/`, если начинается новый этап и такого документа еще нет.
2. CSV/JSON в `data_registry/`, если это машинно-читаемый реестр, схема, результат эксперимента или журнал проверки.
3. CSV/JSON/YAML в `configs/`, если это входная конфигурация утверждения, модели, стресс-теста или политики вердикта.
4. `.ipynb` или `.py`, если это исполняемый исследовательский или программный слой.
5. Архивная копия в `docs/archive/`, если файл выводится из активной работы.

Запрещенные файлы без отдельного решения John:

1. Новые номерные отчеты `REPORT_35`, `REPORT_36`, ...
2. Новый общий регламент, дублирующий `roadmap.md`.
3. Новый Markdown-документ только для фиксации промежуточного вывода, если этот вывод можно внести в `roadmap.md` или активный документ этапа.
4. Отдельный `decision_log.md`, `experiment_log.md`, `failure_modes.md`, `dataset_health.md`, `source_evidence_index.md`, если их содержание не требует самостоятельного машинного или публикационного использования.

Правило: шаблон из биоинспирированного стандарта не равен обязательному отдельному файлу. Если стандарт требует decision log, experiment log или failure modes, в ML-CRA это по умолчанию реализуется разделом в `roadmap.md` или документе этапа.

## 6. Компактный MAPE-K-цикл работы

Каждый значимый шаг ML-CRA проводится по циклу MAPE-K:

1. **Monitor / наблюдение** — что изменилось: данные, метрики, предупреждения, результаты, файлы, ошибки.
2. **Analyze / анализ** — что это значит: есть ли утечка, нестабильность, конфликт метрик, неполное основание, устаревший документ.
3. **Plan / планирование** — какое действие допустимо: обновить этап, выполнить тетрадь, изменить конфигурацию, перевести объект в review/hold/rejected.
4. **Execute / выполнение** — выполнить только разрешенное действие.
5. **Knowledge / база знаний** — зафиксировать результат в одном каноническом месте.

Практическое правило: один исследовательский шаг должен приводить к минимальному набору изменений:

```text
1 шаг работы -> 1 активный документ этапа + при необходимости 1 набор машинно-читаемых результатов + обновление roadmap.md только при изменении статуса проекта
```

Если после шага появляется больше трех новых файлов, нужно остановиться и проверить, не нарушена ли политика артефактов.

## 7. Цепочка трассируемости ML-CRA

Каждый результат должен быть встроен в цепочку:

```text
candidate registry -> protocol/config -> execution artifact -> review -> decision
```

Расшифровка:

- `candidate registry` — какой набор данных, модель или утверждение рассматривается;
- `protocol/config` — по какому протоколу или конфигурации идет проверка;
- `execution artifact` — какой файл результата создан;
- `review` — какие проверки качества, предупреждения и ограничения зафиксированы;
- `decision` — какой статус получает объект и с каким основанием.

Результат, не связанный с этой цепочкой, не используется как основание окончательного решения.

## 8. Evidence record — запись основания

Для каждого значимого решения указывается краткое основание и уровень обоснованности.

Уровни обоснованности:

1. `confirmed_by_literature` — подтверждено литературой;
2. `confirmed_by_official_documentation` — подтверждено официальной документацией;
3. `confirmed_experimentally` — подтверждено экспериментально;
4. `supported_by_engineering_practice` — поддерживается инженерной практикой;
5. `heuristic_assumption` — эвристическое предположение;
6. `requires_additional_check` — требует дополнительной проверки.

Минимальная запись основания:

```text
Решение: ...
Основание: ...
Уровень обоснованности: ...
Файлы/источники: ...
Ограничение: ...
```

Если достаточного основания нет, решение не считается окончательным.

## 9. Правила работы с CSV и конфигурациями

CSV в `data_registry/` не является заменой отчета. Он должен быть машинно-читаемым артефактом.

CSV разрешен, если выполняется хотя бы одно условие:

- файл нужен для повторного чтения тетрадью или скриптом;
- файл содержит таблицу результатов;
- файл содержит схему ожидаемого выхода;
- файл содержит журнал проверки, предупреждений или статусов;
- файл используется для аудита решения.

CSV не создается, если он содержит только текстовое рассуждение, которое можно внести в документ этапа.

Конфигурации в `configs/` должны создаваться до запуска соответствующей проверки. Результаты в `data_registry/` должны ссылаться на идентификатор конфигурации, протокола или утверждения.

## 10. Правила работы с документами этапов

В `docs/stages/` действует правило: один этап — один активный документ.

Если появляется второй документ по тому же этапу, нужно выполнить одно из двух действий:

1. объединить содержание в активный документ этапа;
2. перевести старый документ в `docs/archive/stages/` со статусом `superseded`.

Документ этапа должен содержать:

1. назначение этапа;
2. статус этапа;
3. активные входные файлы;
4. выполненные проверки;
5. результаты и ограничения;
6. решения и evidence record;
7. ближайший допустимый шаг;
8. задачи John.

После выполнения тетради активный документ этапа обновляется до перехода к следующему исследовательскому шагу.

## 11. Текущие этапы проекта

### Этап 1 — постановка задачи и границы проекта

Документ этапа: `docs/stages/stage_01_project_scope.md`.

Статус: базово завершен.

### Этап 2 — данные и кандидаты наборов данных

Документ этапа: `docs/stages/stage_02_data_and_candidate_selection.md`.

Статус: завершен для первого OpenML-контура; UCI-контур отложен.

### Этап 3 — диагностические эксперименты

Документ этапа: `docs/stages/stage_03_diagnostic_experiments.md`.

Статус: завершен для трех OpenML-кандидатов на уровне диагностических контуров.

### Этап 4 — основной кандидат MiniBooNE и исследовательская проверка

Документ этапа: `docs/stages/stage_04_primary_candidate_validation.md`.

Статус: завершен для цели выбора основного табличного кандидата и перехода к методологическому стресс-тестированию.

### Этап 5 — протокол аудита утверждений и стресс-тестирование

Документ этапа: `docs/stages/stage_05_claim_audit_protocol.md`.

Статус: завершен на уровне итогового вердикта по claim `miniboone_hgb_vs_logreg_average_precision_v01`.

Фактическое состояние: выполнены блоки `ST05_01_current_nested_readout`, `ST05_02_seed_stability_grid`, `ST05_03a_split_protocol_10x1`, `ST05_04_metric_conflict_audit`, `ST05_05_parameter_selection_stability`, `ST05_06_cost_quality_audit`, `ST05_07_non_nested_optimism_probe` и `ST05_08_final_claim_verdict_draft`.

Итоговый результат этапа: claim `miniboone_hgb_vs_logreg_average_precision_v01` получает категорию `strongly_supported` в зафиксированном экспериментальном контуре MiniBooNE с обязательным раскрытием высокой вычислительной стоимости. По всем завершенным заранее зафиксированным вариантам протокола средний прирост `average_precision` равен `0.091210`, минимальный прирост — `0.082056`, максимальный прирост — `0.101970`; `hist_gradient_boosting` выигрывает у `logistic_regression` в 80/80 внешних блоках. Среднее время обучения `hist_gradient_boosting` выше времени обучения `logistic_regression` в `55.195823` раза, а среднее полное время выше в `54.506784` раза. `ST05_07` не выявил выраженного оптимистического смещения невложенной оценки: по 15 reference-сравнениям средняя delta `non_nested - nested` составила `-0.000190`, минимальная delta — `-0.000725`, максимальная delta — `0.000178`.

Ограничение: вердикт не означает универсальное превосходство `hist_gradient_boosting` над `logistic_regression`; он относится только к MiniBooNE, зафиксированному claim, основной метрике `average_precision`, заданным протоколам и зафиксированной сетке параметров. Практическое применение результата должно учитывать высокую вычислительную стоимость HGB.

### Этап 6 — упаковка, воспроизводимость и публикационная подготовка

Документ этапа: `docs/stages/stage_06_packaging_and_publication.md`.

Статус: завершен после выполнения `ST06_06_publication_readiness_verdict`.

Фактическое состояние: после закрытия `ST05_08_final_claim_verdict_draft` выполнен этап упаковки, воспроизводимости и публикационной подготовки. Выполнены блоки `ST06_01_packaging_and_publication_scope`, `ST06_02_reproducibility_package_inventory`, `ST06_03_stage05_reproduction_instruction`, `ST06_04_public_claim_language_and_limitations`, `ST06_05_code_packaging_readiness_audit` и `ST06_06_publication_readiness_verdict`. Итоговый публикационный статус: `limited_publication_ready_as_documented_evidence_record`. Проект можно показывать как документированный исследовательский evidence package, но нельзя представлять как упакованный воспроизводимый программный продукт. Код, `.ipynb`, `data_registry/*.csv` и `configs/*.csv` на `ST06_06` не изменялись.

### Этап 7 — модульная упаковка вычислительного слоя

Документ этапа: `docs/stages/stage_07_code_modularization.md`.

Статус: закрыт John после принятия и закрытия ST07_36. Повторный closure
re-audit дал `PASS=7; FAIL=0; BLOCKED=0`; John присвоил
`STAGE_CLOSED_BY_JOHN: Stage_7`. Ограниченный научный claim Stage 5 не
расширялся.

Фактическое состояние: этап открыт после закрытия Stage 6. На `ST07_01` определены границы модульной переработки вычислительного слоя. На `ST07_02` выполнена инвентаризация фактической логики `notebooks/04_dataset_smoke_experiments.ipynb`. На `ST07_03` утверждены границы первой волны модульной переработки: `io.py`, `validation.py`, `metrics.py`, `verdicts.py`. На `ST07_04` первым перенесен `ST05_04_metric_conflict_audit`; проверка подтвердила совпадение с эталонным CSV 19 × 24. На `ST07_05` перенесен `ST05_05_parameter_selection_stability`; модульный и notebook-результаты совпали с эталонным CSV 22 × 23. На `ST07_06` перенесен `ST05_06_cost_quality_audit`: `build_cost_quality_audit(...)` присутствует в `src/mlcra/verdicts.py`, notebook использует модульный вызов, John подтвердил ожидаемый результат, а повторная регрессионная проверка baseline v13 подтвердила совпадение 18 × 40 и отсутствие регрессий ST07_04–ST07_05. На `ST07_07` логика `ST05_01_current_nested_readout` перенесена в `build_current_effect_readout(...)`; точная программная регрессия подтвердила совпадение результата 132 × 30, включая 120 парных и 12 сводных строк, с каноническим CSV. Новые модели не обучались; исследовательский протокол, конфигурации, научные CSV и смысл evidence record Stage 5 не изменялись.

На `ST07_08` повторяющаяся логика строгой проверки и разбора пространства HGB и формирования идентификатора набора параметров перенесена в `src/mlcra/model_spaces.py`; четыре notebook-потребителя используют единый модульный контракт. Проверки подтвердили пространство 6 × 10, 16 grid-комбинаций и совпадение 105 из 105 сохранённых идентификаторов. John принял и закрыл ST07_08.

На `ST07_09` до изменения вычислительной логики зафиксированы граница будущего `src/mlcra/nested_cv.py`, инварианты внешнего `RepeatedStratifiedKFold` 5 × 2 и внутреннего `StratifiedKFold` 3, правила seed, scoring и model roles, многоуровневый эталон шести сохранённых nested-артефактов, положительные и отрицательные проверки и условия отдельного минимального переноса. Verifier отделяет неизменные исторические доказательства ST07_08 от своей текущей версии и проверяет текущие статусы секционно. `nested_cv.py` не создавался, notebook не изменялся, модели не обучались.

John принял и закрыл `ST07_09`. На `ST07_10` общий контракт получения
вероятности положительного класса и вычисления шести бинарных метрик перенесён
из notebook в `src/mlcra/metrics.py`; notebook использует модульный импорт.
Историческое поле `pr_auc` явно закреплено как совместимый псевдоним
`average_precision_score`, а не трапецеидальная площадь, без изменения
сохранённых значений или схем. Модели не обучались, notebook не выполнялся,
научные артефакты не изменялись.

На `ST07_11` создан `src/mlcra/nested_cv.py` с четырьмя ограниченными
контрактами: отображением номера внешнего блока, построением детерминированных
outer/inner splitter и оцениванием уже обученной модели. Notebook использует
модульные вызовы, но обе функции fit/tuning остаются локальными. Проверка на
детерминированном синтетическом наборе подтвердила 10 из 10 внешних split,
seed `20260507`–`20260516`, точный 36-полевой контракт, равенство шести метрик
официальным функциям scikit-learn и 17 из 17 ожидаемых отказов. Полный
MiniBooNE nested CV не запускался; научные артефакты не изменялись.

На `ST07_12` две оставшиеся функции fit/tuning базового nested-CV контура
перенесены из notebook в `src/mlcra/nested_cv.py`. Управляющая ячейка явно
передаёт protocol/candidate ID, геометрию split, seed, feature policy и
параметры `GridSearchCV`. Независимая характеристическая проверка на малом
синтетическом наборе подтвердила равенство всех детерминированных полей
control- и tuned-результатов, точные схемы 36/13/9, изоляцию внутреннего
выбора от внешней test-цели и 19 из 19 ожидаемых отказов. Полный MiniBooNE
nested CV не запускался; зарегистрированные научные артефакты не изменялись.

На `ST07_13` полный модульный MiniBooNE nested CV выполнен в изолированном
каталоге за `588.160` секунды без сети и без перезаписи `data_registry/`.
HGB и dummy дали точные зарегистрированные метрики, выбранные параметры,
quality checks и environment совпали точно. Logistic regression при
фактических 12 потоках OpenBLAS устойчиво отличается от golden master во всех
10 внешних блоках: 70 metric-cell; максимальная абсолютная delta
`average_precision=0.0026056674`. Диагностика показала точное совпадение всех
семи logistic-метрик при BLAS=4 threads, но это условие не зарегистрировано в
protocol lock или environment и найдено после просмотра результата, поэтому
не может использоваться для ретроактивного `PASS`. Warning-артефакт также
имеет дополнительную строку `joblib/loky`. Итог ST07_13 — технический
`FAIL`; claim и verdict Stage 5 не пересматривались.

На `ST07_14` John принял ST07_13 и до нового научного запуска зафиксировал
проспективную политику `prospective_single_thread_exact_same_backend` при
сохранении v01 golden master. Новый `src/mlcra/numeric_runtime.py` проверяет
точную идентичность загруженных NumPy/SciPy OpenBLAS-компонентов, применяет
один BLAS-поток через `threadpoolctl` на fit/predict и fail-fast отклоняет
неполную либо иную среду. Контракт относится к будущему
`miniboone_nested_cv_v02`; legacy-вызовы v01 сохранены. Полный MiniBooNE run,
изменение golden master и нормализация warning в этом блоке не выполнялись.

На `ST07_15` до любого v02 training зарегистрирован отдельный protocol lock
из 41 строки и expected-output schema из 118 строк для семи будущих
артефактов. Контракт точно наследует dataset, признаки, target, split, seed,
модели, model space и scoring v01; единственное намеренное отличие — принятый
runtime-контракт ST07_14. До promotion предусмотрены два изолированных run,
классы сравнения A/B/C/D, запрет warning suppression и отдельное решение John.
Training, notebook и сеть не использовались; v01 и его golden не изменялись.
John принял и закрыл ST07_15.

На `ST07_16` создан standalone software-fixture harness без сети и без полного
MiniBooNE run. Два свежих процесса в разных временных каталогах сформировали
семь schema-compatible артефактов с формами 30/10/3/16/2/8/2. После CSV
roundtrip exact-классы A/B и warning multiset D совпали, timing-класс C прошёл
finite/nonnegative contract; 18/18 негативных случаев отклонены. Результаты
fixture не являются научным evidence и не записываются в canonical v02 paths.
John принял и закрыл ST07_16.

После принятия ST07_16 выявлена оставшаяся техническая зависимость: generic функции
готовы к реальным входам, но единственная standalone CLI создаёт только
synthetic fixture; долговечного offline-only OpenML cache adapter и реального
MiniBooNE v02 entry point нет. Поэтому до двойной scientific validation John
отдельно авторизовал ограниченный ST07_17. Реализованы exact трёхфайловый
OpenML cache manifest, временная writable-копия, fail-closed network guard и
preflight-only CLI. Два fresh processes точно совпали по детерминированным
полям: dataset 41150/130064 × 50, target 93565/36499, protocol/schema/model
space/runtime 41/118/6/16/2, network attempts 0 и fit calls 0. Научные
candidate outputs не создавались. John принял и закрыл ST07_17.

```text
ST07_06_status: accepted_by_john
ST07_07_status: accepted_by_john
ST07_08_status: accepted_by_john
TASK_CLOSED: ST07_08_hgb_model_space_extraction
NEXT_BLOCK_AUTHORIZED: ST07_09_nested_cv_contract_and_golden_master_design
ST07_09_status: accepted_by_john
TASK_CLOSED: ST07_09_nested_cv_contract_and_golden_master_design
NEXT_BLOCK_AUTHORIZED: ST07_10_binary_metric_contract_and_extraction
ST07_10_status: accepted_by_john
TASK_CLOSED: ST07_10_binary_metric_contract_and_extraction
NEXT_BLOCK_AUTHORIZED: ST07_11_nested_cv_split_and_evaluation_extraction
ST07_11_status: accepted_by_john
TASK_CLOSED: ST07_11_nested_cv_split_and_evaluation_extraction
NEXT_BLOCK_AUTHORIZED: ST07_12_nested_cv_fit_and_tuning_extraction
ST07_12_status: accepted_by_john
TASK_CLOSED: ST07_12_nested_cv_fit_and_tuning_extraction
NEXT_BLOCK_AUTHORIZED: ST07_13_nested_cv_full_golden_master_validation
ST07_13_status: accepted_by_john
TASK_CLOSED: ST07_13_nested_cv_full_golden_master_validation
NEXT_BLOCK_AUTHORIZED: ST07_14_numeric_backend_and_thread_reproducibility_contract
ST07_14_NUMERIC_POLICY: prospective_single_thread_exact_same_backend
ST07_14_GOLDEN_POLICY: preserve_existing_v01_golden
ST07_14_status: accepted_by_john
TASK_CLOSED: ST07_14_numeric_backend_and_thread_reproducibility_contract
NEXT_BLOCK_AUTHORIZED: ST07_15_nested_cv_v02_protocol_and_validation_contract
ST07_15_status: accepted_by_john
TASK_CLOSED: ST07_15_nested_cv_v02_protocol_and_validation_contract
NEXT_BLOCK_AUTHORIZED: ST07_16_nested_cv_v02_execution_harness_and_artifact_validation_extraction
ST07_16_status: accepted_by_john
TASK_CLOSED: ST07_16_nested_cv_v02_execution_harness_and_artifact_validation_extraction
NEXT_BLOCK_AUTHORIZED: ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract
ST07_17_status: accepted_by_john
TASK_CLOSED: ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract
NEXT_BLOCK_AUTHORIZED: ST07_18_nested_cv_v02_dual_run_reproducibility_validation
ST07_18_status: accepted_by_john
TASK_CLOSED: ST07_18_nested_cv_v02_dual_run_reproducibility_validation
NEXT_BLOCK_AUTHORIZED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract
ST07_19_status: accepted_by_john
TASK_CLOSED: ST07_19_nested_cv_v02_artifact_context_and_provenance_contract
NEXT_BLOCK_AUTHORIZED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation
ST07_20_status: accepted_by_john
TASK_CLOSED: ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation
NEXT_BLOCK_AUTHORIZED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract
ST07_21_status: accepted_by_john
TASK_CLOSED: ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract
ST07_21_full_miniboone_training_authorized: false
ST07_21_network_authorized: false
ST07_21_canonical_v02_outputs_authorized: false
ST07_21_promotion_authorized: false
NEXT_BLOCK_AUTHORIZED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration
ST07_22_status: accepted_by_john
TASK_CLOSED: ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration
ST07_22_full_miniboone_training_authorized: false
ST07_22_network_authorized: false
ST07_22_canonical_v02_outputs_authorized: true
ST07_22_promotion_authorized: true
NEXT_BLOCK_AUTHORIZED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design
ST07_23_status: accepted_by_john
TASK_CLOSED: ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design
ST07_23_training_authorized: false
ST07_23_network_authorized: false
ST07_23_source_changes_authorized: false
ST07_23_scientific_artifact_changes_authorized: false
remaining_stage07_planned_blocks: 8
NEXT_BLOCK_AUTHORIZED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation
ST07_24_status: accepted_by_john
TASK_CLOSED: ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation
ST07_24_training_authorized: false
ST07_24_network_authorized: false
ST07_24_source_changes_authorized: true
ST07_24_scientific_artifact_changes_authorized: false
NEXT_BLOCK_AUTHORIZED: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation
ST07_25_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation
TASK_CLOSED: ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation
ST07_25_full_miniboone_training_authorized: true
ST07_25_network_authorized: false
ST07_25_source_changes_authorized: false
ST07_25_scientific_artifact_changes_authorized: true
ST07_25_full_miniboone_training_performed: true
ST07_25_network_access_performed: false
ST07_25_historical_golden_overwrites: 0
remaining_stage07_nominal_blocks: 7
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 7
remaining_breakdown: ST05_02=0;ST05_03a=3;ST05_07=3;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation
ST07_26_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation
TASK_CLOSED: ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation
ST07_26_training_authorized: true
ST07_26_network_authorized: false
ST07_26_source_changes_authorized: false
ST07_26_scientific_artifact_changes_authorized: true
ST07_26_scientific_verdict: PASS_CAUSAL_SUPPORT
ST07_26_logistic_fit_count: 100
ST07_26_hgb_fit_count: 0
ST07_26_dummy_fit_count: 0
ST07_26_inner_tuning_count: 0
ST07_26_network_attempts: 0
ST07_26_historical_golden_overwrites: 0
NEXT_BLOCK_AUTHORIZED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design
ST07_27_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design
TASK_CLOSED: ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design
ST07_27_training_authorized: false
ST07_27_network_authorized: false
ST07_27_source_changes_authorized: false
ST07_27_scientific_artifact_changes_authorized: false
ST07_27_implementation_started: NO
remaining_stage07_nominal_blocks: 6
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 6
remaining_breakdown: ST05_02=0;ST05_03a=2;ST05_07=3;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation
ST07_28_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation
TASK_CLOSED: ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation
ST07_28_training_authorized: false
ST07_28_network_authorized: false
ST07_28_source_changes_authorized: true
ST07_28_scientific_artifact_changes_authorized: false
ST07_28_implementation_started: YES
ST07_28_full_miniboone_training_performed: false
ST07_28_network_access_performed: false
ST07_28_scientific_artifact_changes_performed: false
remaining_stage07_nominal_blocks: 5
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 5
remaining_breakdown: ST05_02=0;ST05_03a=1;ST05_07=3;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_29_stage05_split_10x1_full_miniboone_and_golden_diagnostic_validation
ST07_29_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_29_stage05_split_10x1_full_miniboone_and_golden_diagnostic_validation
TASK_CLOSED: ST07_29_stage05_split_10x1_full_miniboone_and_golden_diagnostic_validation
ST07_29_full_miniboone_training_authorized: true
ST07_29_network_authorized: false
ST07_29_source_changes_authorized: false
ST07_29_scientific_artifact_changes_authorized: true
ST07_29_implementation_started: YES
ST07_29_full_miniboone_training_performed: true
ST07_29_network_access_performed: false
ST07_29_historical_golden_overwrites: 0
ST07_29_scientific_verdict: PASS
remaining_stage07_nominal_blocks: 4
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 4
remaining_breakdown: ST05_02=0;ST05_03a=0;ST05_07=3;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_30_stage05_non_nested_optimism_probe_modularization_contract_and_golden_master_design
ST07_30_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_30_stage05_non_nested_optimism_probe_modularization_contract_and_golden_master_design
TASK_CLOSED: ST07_30_stage05_non_nested_optimism_probe_modularization_contract_and_golden_master_design
ST07_30_training_authorized: false
ST07_30_network_authorized: false
ST07_30_source_changes_authorized: false
ST07_30_scientific_artifact_changes_authorized: false
ST07_30_implementation_started: NO
remaining_stage07_nominal_blocks: 3
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 3
remaining_breakdown: ST05_02=0;ST05_03a=0;ST05_07=2;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_31_stage05_non_nested_optimism_probe_modular_extraction_and_fixture_validation
ST07_31_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_31_stage05_non_nested_optimism_probe_modular_extraction_and_fixture_validation
TASK_CLOSED: ST07_31_stage05_non_nested_optimism_probe_modular_extraction_and_fixture_validation
ST07_31_training_authorized: false
ST07_31_network_authorized: false
ST07_31_source_changes_authorized: true
ST07_31_scientific_artifact_changes_authorized: false
ST07_31_implementation_started: YES
ST07_31_full_miniboone_training_performed: false
ST07_31_network_access_performed: false
ST07_31_scientific_artifact_changes_performed: false
remaining_stage07_nominal_blocks: 2
corrective_blocks_currently_required: 0
remaining_stage07_planned_blocks: 2
remaining_breakdown: ST05_02=0;ST05_03a=0;ST05_07=1;stage07_closure=1
NEXT_BLOCK_AUTHORIZED: ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation
ST07_32_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation
TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation
ST07_32_full_miniboone_training_authorized: true
ST07_32_network_authorized: false
ST07_32_source_changes_authorized: false
ST07_32_scientific_artifact_changes_authorized: true
ST07_32_implementation_started: YES
ST07_32_full_miniboone_training_performed: true
ST07_32_network_access_performed: false
ST07_32_historical_golden_overwrites: 0
ST07_32_scientific_verdict: PASS
ST07_33_status: technical_fail_superseded_by_authorized_corrective_design
stage07_closure_audit_verdict: FAIL
stage07_unresolved_closure_criteria: 1
stage07_status: active_closure_blocked_by_ST07_CLOSE_06
NEXT_BLOCK_AUTHORIZED: ST07_34_verdict_policy_application_contract_and_golden_master_design
ST07_34_status: technical_pass_ready_for_john_acceptance
ST07_34_implementation_started: NO
ST07_34_source_changes_authorized: false
ST07_34_scientific_artifact_changes_authorized: false
ST07_34_training_authorized: false
ST07_34_network_authorized: false
proposed_next_block: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation
ST07_35_status: proposed_not_authorized
ST07_35_implementation_started: NO
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

John принял и закрыл ST07_32, затем поручил выполнить closure audit Stage 7.
ST07_33 проверил семь критериев результата через матрицу трассируемости,
неослабленный cumulative pilot, AST-инвентаризацию и защищённые SHA-256.
Результат: `PASS=6`, `FAIL=1`, `BLOCKED=0`. Критерий ST07-CLOSE-06 не выполнен:
модульные I/O и schema checks существуют, но `src/mlcra/verdicts.py` не имеет
исполняемого контракта, который читает `miniboone_verdict_policy_v01.csv`,
применяет её упорядоченные условия к evidence record и fail-closed проверяет
категорию. Ручная таблица ST05_08 остаётся документальным historical evidence,
а не модульной проверкой policy.

```text
ST07_32_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation
TASK_CLOSED: ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation
ST07_33_status: technical_fail_superseded_by_authorized_corrective_design
stage07_closure_audit_verdict: FAIL
stage07_closure_criteria: PASS=6;FAIL=1;BLOCKED=0
stage07_unresolved_closure_criteria: 1
stage07_status: active_closure_blocked_by_ST07_CLOSE_06
NEXT_BLOCK_AUTHORIZED: ST07_34_verdict_policy_application_contract_and_golden_master_design
ST07_34_status: technical_pass_ready_for_john_acceptance
ST07_34_implementation_started: NO
ST07_34_source_changes_authorized: false
ST07_34_scientific_artifact_changes_authorized: false
ST07_34_training_authorized: false
ST07_34_network_authorized: false
proposed_next_block: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation
ST07_35_status: proposed_not_authorized
ST07_35_implementation_started: NO
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

John принял и закрыл `ST07_10_binary_metric_contract_and_extraction`, затем
отдельно авторизовал `ST07_11_nested_cv_split_and_evaluation_extraction`.
ST07_11 и ST07_12 технически выполнены, приняты и закрыты. ST07_13 отдельно
авторизован, выполнен с техническим `FAIL`, принят и закрыт John. ST07_14 и
ST07_15, ST07_16 и ST07_17 технически выполнены, приняты и закрыты. ST07_18
отдельно авторизован, технически выполнен с `PASS`, принят и закрыт John: два
fresh-process offline run воспроизвели зарегистрированные классы A/B/D точно,
класс C прошёл finite/nonnegative, а promotion и Stage 5 claim/verdict не
изменялись. Последующий анализ выявил, что защищённые поля
`quality_checks.details_ru` (A) и `warnings.warning_ru` (D) наследуют текст
ST07_16 fixture и потому неверно описывают provenance реальных MiniBooNE
candidate-run. Немедленный promotion отклонён; ближайший блок должен сначала
исправить источник контекста и проверить контракт без полного обучения. На
ST07_19 введён обязательный перечислимый fixture/scientific-candidate context,
связанный с row policy до первого fit. Fixture-тексты сохранены точно, а
будущий реальный run будет маркирован как scientific-validation candidate,
noncanonical и not promoted. Полное обучение и promotion не выполнялись; John
принял и закрыл ST07_19. Содержательный маршрут Stage 7 сохранён, но после
наблюдаемых дефектов в него были обоснованно вставлены offline preflight
 ST07_17 и provenance-correction ST07_19. John отдельно авторизовал ST07_20;
два свежих offline full run в разных процессах технически подтвердили
исправленный provenance, A/B/D exact, C finite/nonnegative, 16/16 quality,
network 0/0 и отсутствие canonical outputs/promotion. John принял и закрыл
ST07_20. На отдельно авторизованном ST07_21 выбран целостный source bundle
`run_a` по зарегистрированному execution order и создан семистрочный manifest
с file hashes, shapes, canonical targets и точным сохранением class C timing.
Training, сеть, canonical writes и promotion не выполнялись; John принял и
закрыл ST07_21. Затем John отдельно авторизовал ST07_22. Зарегистрированный
`run_a` продвинут в семь canonical paths через same-filesystem staging,
exclusive lock, no-overwrite `os.link`, terminal journal и post-commit
hash/schema verification. Значения CSV не преобразовывались; обучение, сеть и
изменение Stage 5 claim/verdict не выполнялись. John принял и закрыл ST07_22.
AST-аудит затем подтвердил, что критическая логика ST05_02, ST05_03a и ST05_07
ещё остаётся в notebook; поэтому Stage 7 не закрыт, а первым предложен
software-only contract/golden-design для `ST05_02_seed_stability_grid`. John
авторизовал, принял и закрыл этот ST07_23 design-блок без extraction и fit.
Номинальный остаток был декомпозирован как 2 + 3 + 3 + 1 = 9 блоков; первым
выполнен и принят ST07_24 extraction с детерминированной fixture-проверкой без
полного MiniBooNE fit. После него остаётся 1 + 3 + 3 + 1 = 8 блоков. Первым
предложен ST07_25: один полный offline MiniBooNE run ST05_02 и заранее
определённое fail-closed golden diagnostic сравнение без tolerance, изменения
исторических CSV или причинной атрибуции возможного расхождения.
John авторизовал ST07_25, принял и закрыл его объективный технический `FAIL`.
Class B mismatch локализован в LR: 350/350 прогнозно-метрических ячеек на 50
outer-блоках, тогда как HGB/dummy, class A/C и primary signal прошли. Это
активировало ранее предусмотренный корректирующий блок; предложен ST07_26 с
LR-only BLAS=4-vs-12 проверкой до перехода к номинальному ST05_03a.

ST07_26 затем принят и закрыт John: same-machine intervention точно связал
переключение LR-результата с BLAS=4/12 в текущей среде, не восстанавливая
неизвестную historical provenance. John авторизовал, принял и закрыл ST07_27
design ST05_03a; затем авторизовал, принял и закрыл ST07_28 extraction с
двухзапусковой fixture-проверкой. После отдельной авторизации ST07_29 zero-fit
preflight подтвердил offline dataset 130064×50, exact backend identity и
BLAS=4/restoration. Единственный full run (30 HGB tuning blocks, 60 control
fit, сеть 0) дал candidate 90×43/48×22, полностью exact historical golden по
классам A/B после CSV-roundtrip; timing C валиден, protected 15/15 и bounded
signal прошли. Результат — same-machine diagnostic `PASS`, не historical
thread attribution, не cross-environment claim и не изменение Stage 5
verdict. John принял и закрыл ST07_29. Остаток Stage 7 равен 3 блокам ST05_07
и одному closure-блоку; первым предложен software-only ST07_30 для контракта
и golden-master-дизайна без fit, сети, source extraction или изменения claim.
John отдельно авторизовал ST07_30. Design-gate зафиксировал будущую границу
ST05_07 в `stress_tests.py`, не реализуя её: contract/reference assembly,
single-level runner и bundle validation разделены. Source inventory остаётся
1 cell/609 lines/3 functions; protocol — HGB-only, 3 seeds, 5×2, AP и locked
grid 16. Три reference inputs имеют формы 3×39/150×43/90×43; historical golden
15×39 имеет 15/15 keys и классы A/B/C=30/8/1. Независимый validator точно
пересчитал 9/9 reference means и 15/15 delta/status relations; 27/27 mutations
отклонены. Notebook/source/config/golden/claim/verdict сохранены, fit/network=0.
John принял и закрыл ST07_30. Номинально остаются extraction, отдельная full
diagnostic validation ST05_07 и closure Stage 7. Матрица MAPE-K дала 4.90/5
следующему software-only ST07_31 extraction + deterministic fixture против
3.45 объединения с full validation, 1.85 full rerun до extraction и 1.60
преждевременного closure. John отдельно авторизовал ST07_31. Модульный runner,
reference assembly и fail-closed validator реализованы; notebook cell 51
сокращена с 609 lines/3 functions до orchestration-only 105/0. Два настоящих
fixture-run дали `15×39`, exact A/B после CSV roundtrip, finite/nonnegative C и
38/38 отклонённых отрицательных мутаций. Protected 9/9 сохранены; полного
MiniBooNE fit, сети и изменения scientific artifacts не было. John принял и
закрыл ST07_31. Остались full diagnostic ST05_07 и closure audit. Матрица
MAPE-K выбрала отдельный ST07_32 с оценкой 4.55/5; он предложен, но не
авторизован и не начат.

### Этап 8 — проектная завершённость и готовность к релизу

Документ этапа:
`docs/stages/stage_08_project_completion_and_release_readiness.md`.

Статус: активен на уровне технически завершённого повторного аудита ST08_13,
ожидающего решения John; локальная продуктовая поверхность реализована, но
проектная завершённость и готовность к внешнему релизу имеют FAIL, публикация и
внешний релиз не авторизованы и не выполнялись.

ST08_01 сформировал criteria-first контракт из 24 требований по 8 независимым
измерениям: цель и границы, научные доказательства, программная верификация,
воспроизводимость и provenance, документация и применимость, упаковка и
распространение, правовые условия и цитирование, governance/security/release.
Все требования имеют design-статус `NOT_EVALUATED`; поэтому этот блок не
присваивает проекту ни completion verdict, ни release verdict. Агрегация
fail-closed отделяет проектную завершённость от готовности к внешнему релизу и
оставляет решения о переходе и релизе за John.

John принял и закрыл ST08_01 и авторизовал ST08_02. Baseline audit применил
контракт без remediation и получил требования `7 PASS / 7 FAIL / 10 BLOCKED /
0 SKIPPED`; dimensions `1 PASS / 4 FAIL / 3 BLOCKED`. D02 scientific evidence
имеет PASS, но `project_completion_verdict=FAIL`,
`external_release_readiness=FAIL`, `release_class=not_ready`. Зарегистрированы
9 открытых findings и 5 residual risks; обучение, изменение научных артефактов
и release actions равны нулю.

## 12. Реестр значимых решений

| ID | Решение | Основание | Уровень обоснованности | Статус |
|---|---|---|---|---|
| MLCRA-RD-001 | Не создавать новый регламент; усилить `roadmap.md` | В архиве уже есть `roadmap.md` с отказом от новых номерных отчетов; новый регламент увеличил бы число документов | supported_by_engineering_practice | accepted |
| MLCRA-RD-002 | Перенести старые `docs/reports/REPORT_*` в `docs/archive/reports/` | Старые отчеты нужны как аудиторский след, но не должны быть рабочей зоной | supported_by_engineering_practice | accepted |
| MLCRA-RD-003 | Ввести правило «один этап — один активный документ» | В архиве найдено два документа этапа 5, что привело к несинхронизации | confirmed_experimentally | accepted |
| MLCRA-RD-004 | Не создавать отдельные `decision_log.md`, `experiment_log.md`, `failure_modes.md` по умолчанию | Биоинспирированный стандарт требует проектную память, но не требует обязательно реализовывать каждый элемент отдельным файлом | supported_by_engineering_practice | accepted |
| MLCRA-RD-005 | Считать `ST05_02_seed_stability_grid` выполненным артефактом, требующим отражения в документе этапа 5 | В `data_registry/` присутствуют три файла результатов `ST05_02` | confirmed_experimentally | accepted |
| MLCRA-RD-006 | Считать `ST05_03a_split_protocol_10x1`, `ST05_04_metric_conflict_audit`, `ST05_05_parameter_selection_stability` и `ST05_06_cost_quality_audit` выполненными блоками этапа 5 | В `data_registry/` присутствуют результаты соответствующих блоков; активный документ этапа 5 обновлен; `ST05_06` сформировал `openml_miniboone_stage05_cost_quality_audit.csv` с 18 строками | confirmed_experimentally | accepted |
| MLCRA-RD-007 | Считать `ST05_07_non_nested_optimism_probe` выполненным после отдельного решения о запуске новых моделей | В `data_registry/` присутствует файл `openml_miniboone_stage05_non_nested_optimism_probe.csv`; audit-файл содержит 15 строк; выраженного оптимистического смещения невложенной оценки относительно вложенных внешних оценок не обнаружено | confirmed_experimentally | accepted |
| MLCRA-RD-008 | Следующим допустимым шагом считать `ST05_08_final_claim_verdict_draft` | После `ST05_01`–`ST05_07` накоплен полный набор evidence record по устойчивости качества, конфликту метрик, стабильности параметров, вычислительной стоимости и риску невложенного оптимизма; следующий шаг должен синтезировать вердикт без нового обучения моделей | supported_by_engineering_practice | accepted |
| MLCRA-RD-009 | Считать `ST05_08_final_claim_verdict_draft` выполненным и закрыть этап 5 на уровне итогового вердикта MiniBooNE | В `docs/stages/stage_05_claim_audit_protocol.md` зафиксирован итоговый вердикт по claim `miniboone_hgb_vs_logreg_average_precision_v01`: категория `strongly_supported` с обязательным раскрытием высокой вычислительной стоимости; новые модели не запускались | confirmed_experimentally | accepted |
| MLCRA-RD-010 | Начать этап 6 с `ST06_01_packaging_and_publication_scope` | После закрытия Stage 5 главный риск смещается с проверки claim на упаковку evidence record, воспроизводимость и корректное внешнее предъявление результата; стартовый блок этапа 6 не требует нового запуска моделей | supported_by_engineering_practice | accepted |
| MLCRA-RD-011 | Считать `ST06_02_reproducibility_package_inventory` выполненным и перейти к инструкции воспроизведения Stage 5 | В `docs/stages/stage_06_packaging_and_publication.md` зафиксирован минимальный пакет воспроизводимости Stage 5: управляющие документы, предрегистрационные входы, исследовательская тетрадь, базовые nested-результаты и результаты `ST05_01`–`ST05_07`; новые модели не запускались | confirmed_experimentally | accepted |
| MLCRA-RD-012 | Считать `ST06_03_stage05_reproduction_instruction` выполненным и перейти к формализации публичного языка claim | В `docs/stages/stage_06_packaging_and_publication.md` зафиксирована инструкция документального воспроизведения Stage 5 по цепочке `claim -> protocol/config -> execution artifact -> results -> review -> verdict`; новые модели не запускались | supported_by_engineering_practice | accepted |
| MLCRA-RD-013 | Считать `ST06_04_public_claim_language_and_limitations` выполненным и перейти к аудиту готовности к упаковке кода | В `docs/stages/stage_06_packaging_and_publication.md` зафиксированы краткая и расширенная допустимые формулировки MiniBooNE claim, обязательные ограничения, запрещенные интерпретации и правило раскрытия вычислительной стоимости; новые модели не запускались | supported_by_engineering_practice | accepted |
| MLCRA-RD-014 | Считать `ST06_05_code_packaging_readiness_audit` выполненным и перейти к итоговому вердикту публикационной готовности | В `docs/stages/stage_06_packaging_and_publication.md` зафиксировано, что Stage 5 воспроизводим как документированный evidence record, но не готов как стабильный программный API; модульный слой `src/mlcra/` пока представлен пустыми заготовками, а основной вычислительный слой находится в исследовательской тетради | confirmed_experimentally | accepted |
| MLCRA-RD-015 | Считать `ST06_06_publication_readiness_verdict` выполненным и закрыть этап 6 на уровне публикационного вердикта | В `docs/stages/stage_06_packaging_and_publication.md` зафиксирован статус `limited_publication_ready_as_documented_evidence_record`: ML-CRA можно показывать как документированный исследовательский evidence package, но не как упакованный воспроизводимый программный продукт | supported_by_engineering_practice | accepted |
| MLCRA-RD-016 | Открыть этап 7 и считать `ST07_01_code_modularization_scope` выполненным без изменения кода | Stage 6 показал, что проект готов к внешнему предъявлению только как документированный evidence record; для перехода к воспроизводимому программному продукту сначала нужно определить границы модульной упаковки вычислительного слоя, не меняя `.py` и `.ipynb` до инвентаризации notebook-логики | supported_by_engineering_practice | accepted |
| MLCRA-RD-017 | Считать `ST07_02_notebook_logic_inventory` выполненным без изменения кода | В `docs/stages/stage_07_code_modularization.md` зафиксирована карта фактической логики `notebooks/04_dataset_smoke_experiments.ipynb`: 51 ячейка, 11 markdown, 40 code; выделены блоки Stage 5, повторяемые утилиты и предварительный порядок модульной переработки | confirmed_experimentally | accepted |
| MLCRA-RD-018 | Считать `ST07_03_module_boundary_and_contract_design` выполненным без изменения кода и перенести следующий шаг в новый чат | В `docs/stages/stage_07_code_modularization.md` утверждены границы первой волны модульной переработки: `io.py`, `validation.py`, `metrics.py`, `verdicts.py`; первым переносимым блоком выбран `ST05_04_metric_conflict_audit`; следующий шаг потребует изменения `.py` и `.ipynb` | supported_by_engineering_practice | accepted |
| MLCRA-RD-019 | Считать `ST07_04_first_module_extraction` выполненным | Логика `ST05_04_metric_conflict_audit` перенесена из notebook в `src/mlcra/verdicts.py`; вспомогательные контракты вынесены в `io.py`, `validation.py` и `metrics.py`; проверка `ST07_04_CHECK: True` подтвердила совпадение с эталонным CSV на 19 строк | confirmed_experimentally | accepted |
| MLCRA-RD-020 | Следующим шагом считать выбор второго безобучающего audit-блока для переноса | После первого переноса модульный слой еще не покрывает всю безобучающую логику Stage 5; безопаснее продолжать первой волной без запуска моделей, выбирая между `ST05_05_parameter_selection_stability` и `ST05_06_cost_quality_audit` | supported_by_engineering_practice | accepted |
| MLCRA-RD-021 | Вторым переносимым безобучающим блоком выбрать `ST05_05_parameter_selection_stability` | Блок имеет меньший риск численного изменения, чем `ST05_06_cost_quality_audit`: не содержит отношений времени, делений и преобразования направлений нескольких метрик; сохраненный CSV позволяет выполнить точную регрессионную проверку | supported_by_engineering_practice | accepted |
| MLCRA-RD-022 | Считать `ST07_05_next_no_training_audit_extraction_scope` выполненным | `build_parameter_selection_stability_audit(...)` добавлена в `src/mlcra/verdicts.py`, notebook переведен на модульный вызов; проверки `ST07_05_MODULE_CHECK: True` и `ST07_05_NOTEBOOK_CHECK: True` подтвердили совпадение таблицы 22 × 23 с эталоном | confirmed_experimentally | accepted |
| MLCRA-RD-023 | Следующим шагом считать `ST07_06_cost_quality_audit_extraction` | После переноса `ST05_04` и `ST05_05` последним безобучающим audit-блоком первой волны остается `ST05_06_cost_quality_audit`; его более широкий численный контракт требует отдельного переноса и регрессионной проверки | supported_by_engineering_practice | accepted |
| MLCRA-RD-024 | Считать `ST07_06_cost_quality_audit_extraction` выполненным и принятым | John подтвердил совпадение результата с ожидаемым; функция `build_cost_quality_audit(...)` и notebook-вызов присутствуют в baseline v13; повторная проверка подтвердила таблицу 18 × 40 и сохранение результатов ST07_04–ST07_05 | confirmed_by_user_acceptance_and_regression_verification | accepted |
| MLCRA-RD-025 | Считать `ST07_07_current_effect_readout_extraction` технически выполненным и передать John на принятие | `build_current_effect_readout(...)` перенесла вычисление ST05_01 в `src/mlcra/verdicts.py`; точная регрессия после CSV-roundtrip подтвердила форму 132 × 30, 120 парных и 12 сводных строк и полное совпадение с каноническим CSV без нового обучения | confirmed_by_regression_verification | ready_for_john_acceptance |
| MLCRA-RD-026 | Принять и закрыть `ST07_07_current_effect_readout_extraction`; отдельно авторизовать `ST07_08_hgb_model_space_extraction` | Прямое решение John от 24 июля 2026 года: `ST07_07_status: accepted_by_john`, `TASK_CLOSED: ST07_07_current_effect_readout_extraction`, `NEXT_BLOCK_AUTHORIZED: ST07_08_hgb_model_space_extraction` | confirmed_by_user_decision | accepted |
| MLCRA-RD-027 | Принять и закрыть `ST07_08_hgb_model_space_extraction` | Новый `src/mlcra/model_spaces.py` формирует точные grid/fixed-словари из зарегистрированного CSV 6 × 10 и стабильные HGB ID; четыре notebook-потребителя переведены на модульный контракт; 105 из 105 сохранённых ID совпали с независимым расчётом; объективная проверка контрольной точки v18 завершилась PASS, после чего John принял результат | confirmed_by_user_decision_and_regression_verification | accepted |
| MLCRA-RD-028 | Авторизовать `ST07_09_nested_cv_contract_and_golden_master_design` до переноса CV-кода | После принятого model-space контракта ближайший высокий риск связан с переносом обучения, split, seed и scoring; John принял следующий блок и отдельно разрешил выполнение согласованного списка изменений | confirmed_by_user_decision | accepted |
| MLCRA-RD-029 | Принять и закрыть `ST07_09_nested_cv_contract_and_golden_master_design` | В Stage 7 зафиксированы граница будущего `nested_cv.py`, инварианты nested CV, многоуровневый golden master — эталон регрессии, матрица проверок и запрет автоматического переноса; John принял результат и присвоил закрытие задачи | confirmed_by_user_decision_and_local_contract_verification | accepted |
| MLCRA-RD-030 | Принять и закрыть `ST07_09`; авторизовать, технически выполнить, принять и закрыть `ST07_10_binary_metric_contract_and_extraction` | Прямые решения John; две общие функции бинарного оценивания перенесены в `src/mlcra/metrics.py`, notebook переведён на модульный импорт, характеристическая проверка сохраняет шесть метрик и историческую AP-семантику `pr_auc` без обучения и изменения научных артефактов; John принял и закрыл результат | confirmed_by_user_decision_and_regression_verification | accepted |
| MLCRA-RD-031 | Предложить `ST07_11_nested_cv_split_and_evaluation_extraction` как следующий блок, но не начинать его без отдельной авторизации | Принятые `model_spaces.py`, `metrics.py` и контракт ST07_09 закрывают зависимости для детерминированной геометрии split и оценки уже обученной модели; взвешенная матрица решений дала 4.85/5 против 3.25/5 для немедленного полного переноса обучения; выбор ограничивает научный и вычислительный риск | supported_by_local_dependency_analysis_official_documentation_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-032 | Авторизовать, технически выполнить, принять и закрыть `ST07_11_nested_cv_split_and_evaluation_extraction` | Прямые решения John; создан `nested_cv.py`, notebook переведён на четыре ограниченных модульных контракта, детерминированная характеристическая проверка подтвердила split 10/10, seed 20260507–20260516, схему 36 полей, шесть метрик и 17/17 негативных случаев без полного MiniBooNE-прогона и изменения научных артефактов; John принял и закрыл результат | confirmed_by_user_decision_and_software_verification | accepted |
| MLCRA-RD-033 | Предложить `ST07_12_nested_cv_fit_and_tuning_extraction`, но не начинать без отдельной авторизации | После ST07_11 в базовом nested-CV блоке notebook остаются ровно две локальные функции fit/tuning, 63 и 101 строка; их зависимости уже модульны. Взвешенная матрица дала 4.45/5 для совместного переноса с synthetic-fixture против 4.40/5 для только control-fit и 3.25/5 для объединения с полным MiniBooNE rerun. John отдельно авторизовал предложенную границу | confirmed_by_user_decision_and_prior_engineering_risk_assessment | accepted |
| MLCRA-RD-034 | Принять и закрыть `ST07_12_nested_cv_fit_and_tuning_extraction` | Прямое решение John; две функции перенесены в `nested_cv.py`, а независимая synthetic-fixture проверка подтвердила изоляцию outer test, схемы 36/13/9 и 19/19 негативных случаев без полного MiniBooNE-прогона и изменения научных артефактов | confirmed_by_user_decision_and_characterization_verification | accepted |
| MLCRA-RD-035 | Предложить `ST07_13_nested_cv_full_golden_master_validation`, но не начинать без отдельной авторизации | Все шесть контрактов базового nested CV модульны, зарегистрированная и текущая среды совпадают, dataset 41150 присутствует в локальном OpenML cache, а ST07_09 уже определил шесть golden-master артефактов и классы сравнения. Взвешенная матрица дала 4.60/5 для полного изолированного прогона против 4.20/5 для переноса summary/quality логики и 3.25/5 для немедленного ST05_02. Историческая стоимость составляет около 58 минут fit-времени, поэтому блок требует отдельной авторизации | supported_by_local_dependency_analysis_official_documentation_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-036 | Выполнить авторизованный `ST07_13_nested_cv_full_golden_master_validation` и зафиксировать технический `FAIL` без изменения эталонов | Полный run завершён; HGB, dummy, selected params, quality checks и environment воспроизведены, но ambient OpenBLAS=12 дал 70 logistic metric-cell расхождений, а warnings — дополнительную строку. Диагностика BLAS=4 точно воспроизвела logistic golden по всем 10 блокам, выявив незарегистрированный численный фактор; post-hoc условие не использовано для PASS | confirmed_experimentally_with_protocol_limitation | ready_for_john_acceptance |
| MLCRA-RD-037 | Принять и закрыть ST07_13; проспективно зарегистрировать точный backend и один BLAS-поток без изменения v01 golden | Прямое решение John; официальный контракт scikit-learn отделяет BLAS-параллелизм от `n_jobs` и указывает переменные среды или `threadpoolctl` как механизм управления. Локальная проверка подтвердила два OpenBLAS-контроллера, переход 12/12 → 1/1 → 12/12, точный повтор synthetic logistic и 9/9 ожидаемых отказов. Значение 4 из ST07_13 не ратифицировано post hoc | confirmed_by_user_decision_official_documentation_and_software_verification | ready_for_john_acceptance |
| MLCRA-RD-038 | Принять и закрыть ST07_14; до v02 training зарегистрировать полный protocol и validation contract | Прямое решение John; v02 protocol lock содержит 41 строку, schema — 118 строк и семь артефактов; научные инварианты v01 наследуются точно, runtime ST07_14 является единственной проспективной дельтой, а 15/15 негативных случаев отклоняются. NIST AI RMF требует документировать методы, метрики и инструменты TEVV для повторяемой оценки; John принял и закрыл ST07_15 | confirmed_by_user_decision_official_guidance_and_contract_verification | accepted |
| MLCRA-RD-039 | Предложить `ST07_16_nested_cv_v02_execution_harness_and_artifact_validation_extraction`, но не начинать без отдельной авторизации | ST07_15 уже фиксирует два изолированных run и сравнение A/B/C/D, однако notebook всё ещё содержит подготовку MiniBooNE, estimator factory, orchestration, summary, environment, quality и запись артефактов, а модульный слой не имеет standalone runner или dual-run comparator. Предварительная программная верификация harness до дорогой научной валидации отделяет дефект реализации от результата эксперимента; John отдельно авторизовал ST07_16 | confirmed_by_user_decision_and_prior_engineering_risk_assessment | accepted |
| MLCRA-RD-040 | Технически выполнить, принять и закрыть ST07_16 как software verification без полного MiniBooNE run | Два fresh-process fixture run сформировали 7/7 артефактов с формами 30/10/3/16/2/8/2; A/B/D совпали точно после CSV roundtrip, C finite/nonnegative, 18/18 негативных случаев отклонены, protected 15/15 неизменны, canonical v02 outputs отсутствуют; John принял и закрыл результат | confirmed_by_user_decision_and_software_verification | accepted |
| MLCRA-RD-041 | Предложить и после отдельного решения John авторизовать `ST07_17_nested_cv_v02_offline_miniboone_runner_and_preflight_contract` | ST07_16 проверил generic orchestration и synthetic fixture, однако durable CLI реального v02 run и fail-closed offline OpenML cache adapter отсутствовали; ST07_13 уже наблюдал три cache-runner diagnostic stop. Матрица решения дала 4.80/5 preflight-блоку против 2.80/5 немедленного dual run и 3.90/5 объединения runner с scientific validation; John отдельно присвоил NEXT_BLOCK_AUTHORIZED | confirmed_by_user_decision_and_prior_engineering_risk_assessment | accepted |
| MLCRA-RD-042 | Технически выполнить, принять и закрыть ST07_17 как offline-only preflight без fit | Два fresh processes прочитали точный трёхфайловый cache manifest, подтвердили MiniBooNE 41150/130064 × 50 и 93565/36499, protocol/schema/model space/runtime 41/118/6/16/2, network attempts 0, fit calls 0, все зарегистрированные отказы, protected manifest и отсутствие 7/7 canonical v02 outputs; John принял и закрыл результат | confirmed_by_user_decision_software_verification_and_contract_testing | accepted |
| MLCRA-RD-043 | Предложить `ST07_18_nested_cv_v02_dual_run_reproducibility_validation`, но не начинать без отдельной авторизации | После ST07_17 закрыты generic harness и offline real-data preflight; protocol lock уже требует два fresh-process full run, A/B/C/D comparison и отдельный promotion gate. Взвешенная матрица дала 4.55/5 отдельной validation против 3.25/5 объединения с promotion, 3.35/5 одного run и 2.95/5 возврата к extraction | supported_by_local_dependency_analysis_registered_protocol_official_documentation_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-044 | Выполнить, принять и закрыть `ST07_18_nested_cv_v02_dual_run_reproducibility_validation` без promotion | После исключённой implementation-attempt с ошибкой имени schema-поля оба run начаты заново. Итоговые процессы завершились 0/0, дали 7/7 artifacts и 16/16 quality PASS каждый; A=69, B=38 и D=9 совпали точно, C=2 finite/nonnegative, network=0/0, runtime=2 backend × 1 thread, protected=196/196, canonical outputs отсутствуют 7/7. Результат ограничен same-environment computational reproducibility и не меняет Stage 5 claim/verdict; John отдельно принял и закрыл блок | confirmed_by_user_decision_and_experiment_under_registered_protocol | accepted |
| MLCRA-RD-045 | Предложить `ST07_19_nested_cv_v02_artifact_context_and_provenance_contract`, но не начинать без отдельной авторизации | В реальных candidate CSV ST07_18 общие builders сохранили fixture-тексты ST07_16 в защищённых полях `quality_checks.details_ru` класса A и `warnings.warning_ru` класса D. Их promotion закрепил бы ложный provenance; protocol также не задаёт выбор run при различающихся timing C. Взвешенная матрица дала 4.90/5 отдельному software-only исправлению против 2.45 немедленному promotion, 2.75 notebook extraction и 3.35 объединённому исправлению/revalidation/promotion | supported_by_local_source_and_schema_analysis_w3c_provenance_fair_nist_configuration_change_control | proposed_not_authorized |
| MLCRA-RD-046 | Выполнить, принять и закрыть `ST07_19_nested_cv_v02_artifact_context_and_provenance_contract` без полного MiniBooNE run и promotion | `V02ArtifactContext` допускает ровно fixture и scientific candidate, fail-closed связывает контекст с row policy до fit и повторно при assembly. Два fixture process сохранили прежние строки точно, 8/8 новых context-negative и 18/18 harness-negative отклонены, два offline preflight дали 0 fit/0 network; protocol/schema/ST07_18 evidence неизменны, canonical outputs отсутствуют 7/7; John принял и закрыл блок | confirmed_by_user_decision_software_verification_official_python_w3c_provenance_and_nist_change_control | accepted |
| MLCRA-RD-047 | Предложить `ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation`, но не начинать без отдельной авторизации | Содержательный маршрут Stage 7 сохранён с корректирующими MAPE-K-вставками ST07_17 и ST07_19. После принятия ST07_19 остаётся доказать на двух свежих offline run, что scientific-candidate provenance корректен в полном контуре и A/B/D exact, C finite/nonnegative. Матрица дала 4.60/5 revalidation против 2.10 немедленного promotion старых CSV, 3.30 предварительного promotion-source решения и 2.35 возврата к extraction. NIST терминологически ограничивает результат same-environment repeatability, а не cross-environment reproducibility | supported_by_local_dependency_analysis_registered_protocol_nist_terminology_official_tev_v_guidance_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-048 | Авторизовать, технически выполнить, принять и закрыть `ST07_20_nested_cv_v02_provenance_corrected_dual_run_revalidation` без promotion | Прямое решение John; два fresh-process offline run завершились 0/0 и дали 7/7 schema-valid artifacts, 16/16 quality, A=69/B=38/D=9 exact, C=2 finite/nonnegative, scientific provenance 2×4/4, network 0/0, runtime 2 backend × 1 thread, protected contracts 8/8 и отсутствие 7/7 canonical outputs. Результат ограничен same-environment repeatability; Stage 5 claim/verdict и promotion не изменялись; John принял и закрыл блок | confirmed_by_user_decision_and_experiment_under_registered_protocol | accepted |
| MLCRA-RD-049 | Предложить `ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract`, но не начинать без отдельной авторизации | После принятия ST07_20 promotion gate научно пройден, но source run и class C timing provenance не зарегистрированы. Оба временных bundle доступны 14/14 и совпадают с evidence; отличается только outer_scores из-за допустимых timing C. Взвешенная матрица дала 5.00/5 отдельному атомарному source/timing contract против 3.00 немедленного promotion, 3.35 преждевременного staging обоих run, 3.35 notebook extraction и 2.75 cross-environment validation. W3C PROV, FAIR R1.2 и NIST CM-3 требуют трассируемого источника и документированного change control | supported_by_local_evidence_registered_protocol_w3c_prov_fair_nist_configuration_change_control_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-050 | Авторизовать, технически выполнить, принять и закрыть `ST07_21_nested_cv_v02_promotion_source_and_timing_provenance_contract` без promotion | Прямые решения John; protocol/schema/ST07_20 evidence сохранили точные SHA-256, оба временных bundle повторно прошли 14/14 hashes и schema. По заранее определённому execution order выбран весь `run_a` 7/7, manifest зарегистрировал bundle/file hashes, формы, canonical targets и exact class C timing provenance; 10/10 негативных мутаций отклонены. Training/network/copy/promotion равны нулю, canonical outputs отсутствуют 7/7, Stage 5 claim/verdict не менялись; John принял и закрыл блок | confirmed_by_user_decision_local_hash_and_schema_verification_w3c_prov_fair_and_nist_change_control | accepted |
| MLCRA-RD-051 | Предложить `ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration`, но не начинать без отдельной авторизации | После принятия ST07_21 source `run_a` зарегистрирован 7/7 и доступен, а canonical outputs отсутствуют 7/7. Матрица дала 4.80/5 транзакционному promotion против 3.65 durable staging, 2.70 повторного обучения, 2.45 cross-environment calibration и 3.30 notebook extraction. W3C PROV и NIST configuration management поддерживают трассируемость и change control; официальный `os.replace` гарантирует атомарность только отдельной успешной замены. Поэтому bundle-контракт должен быть `prepare -> validate -> lock -> commit -> verify_or_rollback` с durable journal и fail-closed partial-state detection, а не заявлением единой filesystem-atomic операции | supported_by_local_dependency_analysis_w3c_prov_nist_configuration_management_official_python_documentation_and_engineering_risk_assessment | proposed_not_authorized |
| MLCRA-RD-052 | Авторизовать, технически выполнить, принять и закрыть `ST07_22_nested_cv_v02_transactional_promotion_and_canonical_artifact_registration` | Прямые решения John. Preflight подтвердил source/schema/protected/canonical-absence 7/7/118/5/7 и 10/10 fail-closed negative tests. `os.replace` для targets заменён более строгим no-overwrite `os.link`, поскольку overwrite противоречил принятому инварианту. Transaction `st07_22_20260801T140111126958Z_07257bee4409` прошёл prepare/validate/lock/commit/verify, terminal journal=`committed`, canonical hashes и schema совпали 7/7, rollback errors=0, lock/staging удалены. Обучение=0, сеть=0, Stage 5 claim/verdict unchanged; John принял и закрыл блок | confirmed_by_user_decision_local_transaction_journal_hash_schema_verification_official_python_w3c_prov_and_nist_configuration_management | accepted |
| MLCRA-RD-053 | Принять и закрыть ST07_22; предложить `ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design`, но не начинать без отдельной авторизации | Прямое решение John закрывает ST07_22. AST-аудит выявил в notebook 52 ячейки, 4426 строк кода и 36 локальных функций; ST05_02 занимает ячейки 36–39, 687 строк и 5 функций. План stress tests задаёт ST05_02 как `must_have` раньше ST05_03a/07, три golden имеют точные формы 150×43/50×17/72×22 и SHA-256. Базовые nested/model-space/metric зависимости модульны, но специальный stress-test contract отсутствует. Матрица дала 5.00/5 contract/golden design без fit против 3.80 немедленного extraction+rereun и 1.60 закрытия Stage 7 | supported_by_user_decision_local_ast_hash_schema_analysis_registered_protocol_scikit_learn_documentation_and_peer_reviewed_methodology | proposed_not_authorized |

| MLCRA-RD-054 | Авторизовать, технически выполнить, принять и закрыть `ST07_23_stage05_seed_stability_modularization_contract_and_golden_master_design` без extraction и fit | Прямые решения John. Зарегистрированы cell IDs/hashes 4/4, 687 строк и 5 функций; протокол 5 seeds × 5 splits × 2 repeats, inner 3, locked HGB space 16, три model roles; schemas 43/17/22, формы 150×43/50×17/72×22, уникальные ключи, порядок, pairing и metric direction. Положительный contract PASS, 16/16 отрицательных мутаций отклонены. Notebook, `src/mlcra/`, golden CSV, claim/verdict сохранены; training/network/scientific validation равны нулю. Исторические golden зарегистрированы как immutable reference, а не доказательство rerun в незарегистрированной среде; John принял и закрыл блок | confirmed_by_user_decision_local_ast_hash_full_csv_contract_verification_scikit_learn_documentation_and_peer_reviewed_methodology | accepted |
| MLCRA-RD-055 | Принять и закрыть ST07_23; зафиксировать девять номинально оставшихся блоков и предложить `ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation` без реализации | Решение John закрывает ST07_23. Completion-gap audit подтверждает три notebook-only блока: ST05_02 4/687/5, ST05_03a 3/638/5, ST05_07 1/609/3. По шаблону design → extraction/fixture → отдельная validation и финальный closure остаток равен 2+3+3+1=9; это не верхняя граница при будущем наблюдаемом FAIL. Взвешенная матрица дала 4.90/5 ST05_02 extraction+fixture против 3.80 немедленного full rerun, 3.90 перехода к ST05_03a и 1.60 закрытия Stage 7. Protected notebook/modules/golden сохранены, training/network/implementation равны нулю | supported_by_user_decision_local_json_ast_hash_analysis_registered_protocol_scikit_learn_documentation_peer_reviewed_methodology_and_engineering_risk_assessment | proposed_not_authorized |

| MLCRA-RD-056 | Авторизовать, технически выполнить, принять и закрыть `ST07_24_stage05_seed_stability_modular_extraction_and_fixture_validation` без полного MiniBooNE rerun | Прямые решения John. ST05_02 перенесён из 687 notebook-строк и 5 локальных функций в `src/mlcra/stress_tests.py`; четыре ячейки стали thin orchestration 98/0, остальные 48/48 сохранены. Independent fixture дал 150×43/50×17/72×22, exact deterministic reference fields и analytical summary, CSV roundtrip PASS, timing finite/nonnegative, 20/20 отрицательных мутаций и synthetic real-fit separation HGB seed 20260507 от inner seed. Golden/config hashes сохранены 6/6; full MiniBooNE training/network/scientific artifact changes равны нулю; John принял и закрыл блок | confirmed_by_user_decision_local_hash_ast_fixture_roundtrip_negative_testing_official_scikit_learn_documentation_and_peer_reviewed_nested_selection_methodology | accepted |

| MLCRA-RD-057 | Принять и закрыть ST07_24; предложить `ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation`, но не начинать без отдельной авторизации | Прямое решение John закрывает ST07_24. Остаётся 8 номинальных блоков: 1+3+3+1; зарегистрированный порядок требует завершить ST05_02 до ST05_03a. Исторические golden 150×43/50×17/72×22 неизменны, но не имеют достаточного backend/thread provenance, поэтому они используются только как immutable exact diagnostic comparator без межсредового claim и без post-result tolerance. Матрица дала 4.50/5 отдельному full offline validation против 4.00 ещё одного preflight, 3.90 перехода к ST05_03a и 1.60 закрытия Stage 7. PASS будущего блока требует exact A/B, valid C и всех protocol gates; mismatch означает FAIL без причинной атрибуции и без изменения защищённых артефактов | supported_by_user_decision_local_dependency_hash_and_contract_analysis_bio_inspired_mape_k_official_scikit_learn_documentation_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-058 | Авторизовать и технически выполнить `ST07_25_stage05_seed_stability_full_miniboone_and_golden_diagnostic_validation`; сохранить объективный `FAIL` без подгонки | Один fresh-process offline run за 3087.451 s дал корректные формы 150×43/50×17/72×22, class A exact, class C valid, protected 9/9 и зарегистрированный primary signal 5/5 seed. Class B не exact: outer 350/1500 и summary 144/288; selected params 0/50. Все outer mismatch принадлежат logistic regression, HGB и dummy exact. Исторический backend/thread provenance неизвестен, поэтому причинность не приписана; tolerance, golden, claim/verdict не изменены | confirmed_by_user_authorization_local_full_run_independent_recomputation_hashes_official_scikit_learn_and_peer_reviewed_methodology | ready_for_john_acceptance_technical_fail |
| MLCRA-RD-059 | Принять и закрыть отрицательный ST07_25; предложить корректирующий `ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation`, но не начинать без авторизации | Принятие John подтверждает корректность fail-closed результата, но новый наблюдаемый class-B FAIL активирует ранее зарегистрированную политику corrective-block-on-observed-failure. ST07_13 показал BLAS=4 exact и BLAS=12 mismatch на 10 блоках; ST07_25 распространил mismatch BLAS=12 на 50 блоков, но причинный перенос 4→50 ещё не проверен. Матрица дала 4.70/5 LR-only 4-vs-12 diagnostic против 2.75 немедленного ST05_03a design, 3.35 полного HGB rerun и 2.20 отказа от диагностики. Предлагаемый блок не меняет golden, protocol, claim/verdict и не запускает HGB | supported_by_user_decision_local_st0713_st0725_evidence_bio_inspired_mape_k_official_scikit_learn_threadpoolctl_and_nist_terminology | proposed_not_authorized |
| MLCRA-RD-060 | Авторизовать и технически выполнить `ST07_26_stage05_seed_stability_logistic_blas_4_vs_12_causal_diagnostic_validation`; ограничить вывод текущей same-machine средой | Прямое решение John. Preflight дал 0 fit и подтвердил offline dataset/cache, protected 15/15, exact backend identities и применимость BLAS 4/12. Один fresh-process run выполнил 100 LR-fit, 0 HGB, 0 dummy, 0 inner tuning и 0 network attempts. После CSV-roundtrip BLAS=4 exact 350/350 к historical golden, BLAS=12 exact 350/350 к ST07_25 candidate, split mismatch 0/1000, timing valid, thread limits enforced/restored. Это причинно поддерживает число BLAS-потоков как фактор текущего same-machine LR mismatch, но не восстанавливает неизвестную историческую thread provenance, не меняет golden/protocol/claim/verdict и не даёт cross-environment claim | confirmed_by_user_authorization_local_controlled_intervention_exact_csv_roundtrip_hash_verification_official_scikit_learn_threadpoolctl_and_nist_terminology | ready_for_john_acceptance |
| MLCRA-RD-061 | Принять и закрыть ST07_26; предложить `ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design`, но не начинать без отдельной авторизации | Решение John закрывает корректирующую петлю ST05_02. Объективный остаток сохраняется 3+3+1=7. Следующий по locked stress-test order notebook-only блок ST05_03a занимает 3 ячейки/638 строк/5 функций и задаёт 3 seeds × 10x1 outer × 3 models, inner 3, HGB space 16; historical golden имеют формы 90×43/48×22 и точные SHA-256. ST07_26 не восстановил historical thread provenance, поэтому сначала нужен software-only contract/golden design без fit. Матрица дала 4.90/5 design против 4.30 немедленного extraction, 3.10 полного rerun, 3.10 перехода к ST05_07 и 1.60 закрытия Stage 7 | supported_by_user_decision_local_ast_hash_schema_and_dependency_analysis_bio_inspired_mape_k_official_scikit_learn_nist_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-062 | Авторизовать и технически выполнить `ST07_27_stage05_split_10x1_modularization_contract_and_golden_master_design` без extraction и fit | Прямое решение John. Зафиксированы 3 notebook cells/638 строк/5 функций; протокол 3 seeds × 10×1, inner 3 с inner seed=outer seed, три model roles и locked HGB space 16; golden 90×43/48×22 проверены по SHA/schema/key/order. Из outer CSV точно восстановлены pairing, direction, n_blocks и sign counts 48 summary rows. Float-агрегаты не объявлены точно восстанавливаемыми после раздельной CSV-сериализации: они защищены SHA и внутренними инвариантами, post-result tolerance не вводился. Положительный contract PASS, 21/21 независимых отрицательных мутаций отклонены, protected 10/10. Notebook, `src/mlcra/`, configs, golden, ST07_26 evidence и claim/verdict неизменны; fit/network/scientific validation равны нулю | confirmed_by_user_authorization_local_full_contract_hash_ast_schema_pairing_sign_count_and_invariant_verification_official_scikit_learn_nist_and_peer_reviewed_methodology | ready_for_john_acceptance |
| MLCRA-RD-063 | Принять и закрыть ST07_27; предложить `ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation`, но не начинать без отдельной авторизации | Прямое решение John закрывает design-блок ST05_03a. Notebook inventory остаётся 3 cells/638 lines/5 functions, а специализированного Split10x1 contract/runner/validator в `src/mlcra/` нет; registered protocol задаёт 3 seeds × 10×1, inner 3, три модели и HGB space 16, historical golden — 90×43/48×22. Остаток равен 2+3+1=6. Взвешенная матрица дала 4.90/5 extraction+deterministic fixture без полного MiniBooNE против 3.80 extraction+full rerun, 3.10 перехода к ST05_07, 2.40 rerun до extraction и 1.60 закрытия Stage 7. Предложение отдельно сохраняет legacy inner seed=outer seed и отделяет software verification от будущей scientific validation | supported_by_user_decision_local_json_ast_hash_dependency_and_registered_protocol_analysis_bio_inspired_mape_k_official_scikit_learn_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-064 | Авторизовать и технически выполнить `ST07_28_stage05_split_10x1_modular_extraction_and_fixture_validation` без полного MiniBooNE-run | Прямое решение John. ST05_03a перенесён из 3 notebook cells/638 lines/5 functions в typed contract/bundle/summary/validator/runner; ячейки стали thin orchestration 3/109/0, остальные 49/49 сохранены. Opt-in inner seed policy сохраняет default base+split и реализует historical outer-seed constant для ST05_03a. Два deterministic fixture-run дали 90×43/48×22, exact class A/B после CSV roundtrip, finite/nonnegative C и 20/20 отклонённых мутаций. Protected configs/golden 5/5 сохранены; full MiniBooNE training/network/scientific validation равны нулю | confirmed_by_user_authorization_local_ast_hash_two_run_fixture_roundtrip_negative_testing_official_scikit_learn_and_peer_reviewed_nested_selection_methodology | ready_for_john_acceptance |
| MLCRA-RD-065 | Принять и закрыть ST07_28; предложить `ST07_29_stage05_split_10x1_full_miniboone_and_golden_diagnostic_validation`, но не начинать без отдельной авторизации | Решение John закрывает software extraction ST05_03a; остаётся 1+3+1=5 блоков. Fixture 90×43/48×22, two-run exact A/B и 20/20 mutations не заменяют full-data validation. ST07_26 причинно поддержал BLAS thread count для same-machine LR mismatch, поэтому будущий diagnostic заранее фиксирует BLAS=4, сохраняя unknown historical provenance и immutable golden. Матрица дала 4.50/5 отдельному full offline diagnostic против 4.00 ещё одного preflight, 3.20 перехода к ST05_07, 3.10 смешения с prospective BLAS=1 и 1.60 закрытия Stage 7. PASS допускается только при exact A/B, valid C и всех gates; tolerance, golden, protocol, claim/verdict не меняются | supported_by_user_decision_local_hash_contract_dependency_and_st0726_evidence_bio_inspired_mape_k_official_scikit_learn_nist_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-066 | Авторизовать, принять и закрыть `ST07_29_stage05_split_10x1_full_miniboone_and_golden_diagnostic_validation` при заранее объявленном BLAS=4 | Прямые решения John. Zero-fit preflight подтвердил offline cache 3 файла, MiniBooNE 130064×50, target 93565/36499, exact backend identity к ST07_26, BLAS=4 и restoration. Единственный full run за 2038.06305 s выполнил 30 HGB tuning blocks и 60 control fit, network=0. Candidate 90×43/48×22 после CSV-roundtrip имеет class A/B mismatch 0/0, class C valid; protected 15/15 и bounded signal PASS: AP 30/30 positive, mean 0.090329031494, empirical q05 0.084244773270. Golden, source, protocol, claim и Stage 5 verdict не изменены; разрешён только same-machine diagnostic вывод, historical BLAS attribution и cross-environment claim запрещены | confirmed_by_user_authorization_and_acceptance_local_full_run_independent_exact_csv_and_hash_validation_official_scikit_learn_nist_and_peer_reviewed_methodology | accepted |
| MLCRA-RD-067 | Принять и закрыть ST07_29; предложить `ST07_30_stage05_non_nested_optimism_probe_modularization_contract_and_golden_master_design`, но не начинать без отдельной авторизации | Решение John закрывает ST05_03a. Остаток равен 3+1=4. Полный AST-аудит фиксирует единственный оставшийся notebook-only блок ST05_07: cell 51/id ec095766, 609 lines, 3 functions, source SHA-256 f363827d...; специализированной реализации в src нет. Registered protocol задаёт HGB-only single-level 5×2, 3 seeds, AP, grid 16 и пять nested references на seed; historical golden имеет 15×39, 15/15 keys и SHA-256 cdb9bbd.... Матрица дала 4.90/5 software-only design против 3.65 extraction, 1.85 немедленного full run и 1.60 closure. Будущий design обязан до extraction зафиксировать A/B/C, schema/order, reference/delta semantics и mutations; fit, сеть, source/golden/claim/verdict changes равны нулю | supported_by_user_decision_local_json_ast_hash_schema_dependency_and_registered_protocol_analysis_bio_inspired_mape_k_official_scikit_learn_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-068 | Авторизовать и технически выполнить `ST07_30_stage05_non_nested_optimism_probe_modularization_contract_and_golden_master_design` без extraction и fit | Прямое решение John. Design-gate фиксирует future boundary в stress_tests.py: contract/reference assembly/selector/classifier, отдельный GridSearchCV runner и bundle validator. Source 1/609/3, protocol 3 seeds/5×2/HGB/AP, model space 6×10/16, reference inputs 3×39/150×43/90×43 и golden 15×39/15 keys/class A-B-C 30-8-1 проверены. Все 9 reference means и 15 delta/status/parameter relations пересчитаны независимо, 27/27 mutation отклонены; protected 11/11 и scope 4/4. Training/network/source extraction/scientific validation равны нулю; historical evidence и Stage 5 verdict не переинтерпретированы | supported_by_user_authorization_local_json_ast_hash_relational_and_mutation_analysis_bio_inspired_mape_k_official_scikit_learn_and_peer_reviewed_methodology | ready_for_john_acceptance |
| MLCRA-RD-069 | Принять и закрыть ST07_30; предложить `ST07_31_stage05_non_nested_optimism_probe_modular_extraction_and_fixture_validation`, но не начинать без отдельной авторизации | Прямое решение John закрывает design-зависимость. Остаётся 2+1=3 блока. ST05_07 по-прежнему notebook-only: 1 cell/609 lines/3 functions; специализированной реализации в stress_tests.py нет. Матрица дала 4.90/5 extraction+deterministic fixture без full MiniBooNE против 3.45 смешения extraction/full validation, 1.85 full rerun до extraction и 1.60 closure. Будущий ST07_31 должен реализовать границы ST07_30, сделать notebook orchestration-only, подтвердить двумя fixture-run exact A/B, finite/nonnegative C, 15x39/3x5 order и 27/27 mutation rejections, сохранив configs/reference/golden/claim/verdict; full MiniBooNE training, network и scientific validation равны нулю | supported_by_user_decision_local_json_ast_hash_dependency_and_contract_analysis_bio_inspired_mape_k_official_scikit_learn_and_peer_reviewed_methodology | proposed_not_authorized |
| MLCRA-RD-070 | Авторизовать, технически выполнить, принять и закрыть `ST07_31_stage05_non_nested_optimism_probe_modular_extraction_and_fixture_validation` без полного MiniBooNE-run | Прямые решения John. ST05_07 перенесён из cell 51 с 609 lines/3 functions в immutable contract, reference assembly/selection, GridSearchCV runner и fail-closed bundle validator; notebook стал thin orchestration 1/105/0, остальные 51/51 ячейка сохранены. Два настоящих deterministic fixture-run дали 15×39 и references 9×7; class A/B exact после CSV roundtrip, class C finite/nonnegative, 38/38 исправных отрицательных мутаций отклонены. Protected configs/reference/golden/claim 9/9 сохранены; full MiniBooNE training, network и scientific artifact changes равны нулю. Это software verification, а не научная ревалидация historical ST05_07; John принял и закрыл блок | confirmed_by_user_authorization_and_acceptance_local_ast_hash_real_gridsearch_two_run_fixture_csv_roundtrip_mutation_and_protected_hash_verification_bio_inspired_mape_k_official_scikit_learn_and_peer_reviewed_methodology | accepted |
| MLCRA-RD-071 | Принять и закрыть ST07_31; предложить `ST07_32_stage05_non_nested_optimism_probe_full_miniboone_and_golden_diagnostic_validation`, но не начинать без отдельной авторизации | Решение John закрывает software extraction ST05_07. Fixture 15×39 и references 9×7 подтверждают программный контракт, но не full-data equivalence; остаются ровно full diagnostic и closure. Registered ST05_07 задаёт HGB-only GridSearchCV, 3 seeds, 5×2, average precision и locked grid 16; historical golden неизменен, 15×39, SHA-256 cdb9bbd.... Матрица MAPE-K дала 4.55/5 отдельному offline diagnostic против 3.75 ещё одного preflight, 2.30 немедленного closure и 1.90 изменения runtime-протокола. Будущий блок обязан до fit зафиксировать offline cache, backend и фактический OpenMP/BLAS state; historical OpenMP/BLAS provenance остаётся unknown_not_inferred. PASS допускается только при exact A/B после CSV-roundtrip, valid C и всех contract gates; mismatch означает FAIL без post-result tolerance, без причинной атрибуции и без изменения golden/protocol/claim/verdict | supported_by_user_decision_local_hash_contract_dependency_and_runtime_analysis_bio_inspired_mape_k_official_scikit_learn_parallelism_gridsearch_and_peer_reviewed_selection_bias_methodology | proposed_not_authorized |
| MLCRA-RD-072 | Принять и закрыть ST07_32; выполнить авторизованный closure audit Stage 7 без автоматического закрытия стадии | John принял ST07_32. Контрольная точка v44 имеет SHA-256 9a6e5968..., 256/256 уникальных entries и до аудита 0 workspace mismatch. Неослабленный cumulative pilot дал 49/49 PASS; closure проверяется отдельно по семи критериям §8 и fail-closed правилу | confirmed_by_user_decision_local_checkpoint_hash_cumulative_verification_and_requirements_traceability | accepted |
| MLCRA-RD-073 | Не закрывать Stage 7 после ST07_33 и предложить `ST07_34_verdict_policy_application_contract_and_golden_master_design` без реализации | Closure matrix дала PASS=6, FAIL=1, BLOCKED=0. I/O и schema validation модульны, но отсутствует исполняемый контракт применения policy CSV 6×16 к evidence record; четыре публичных builder в verdicts.py не выбирают и не проверяют итоговую категорию. Ручной ST05_08 не заменяет modular policy gate. Предложен отдельный design-first блок без изменения claim/verdict | confirmed_by_local_ast_api_policy_and_documentary_analysis_supported_by_nasa_review_practice_iso15288_and_bio_inspired_mape_k | proposed_not_authorized |
| MLCRA-RD-074 | Авторизовать и технически выполнить `ST07_34_verdict_policy_application_contract_and_golden_master_design` без source extraction и изменения научного состояния | Прямое решение John. Design разделяет typed evidence facts, versioned category clause evaluators, ranked policy application и bundle validator; эвристический NLP-разбор русской policy запрещён. Golden независимо пересчитывает 80/80 положительных primary blocks, mean 0.09121044365165432, q05 0.08625925727315661, 5/5 secondary metrics без конфликта и fit ratio 55.195823; ожидает rank 6 `strongly_supported` с четырьмя disclosures. Зафиксированы 10 boundary checks и 22 fail-closed mutations. Protected 12/12, scope 5/5, source/training/network/scientific changes 0. ST07-CLOSE-06 остаётся FAIL до будущей реализации и golden validation | supported_by_user_authorization_local_hash_pairwise_quantile_schema_and_contract_analysis_bio_inspired_mape_k_iso29148_nasa_verification_matrix_nist_software_vv | ready_for_john_acceptance |
| MLCRA-RD-075 | Принять и закрыть ST07_34; авторизовать и технически выполнить `ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation` | Прямые решения John. В verdicts.py реализованы три immutable typed schemas и четыре build/evaluate/apply/validate contracts. Golden из 9 protected sources, включая прямой ST05_01 readout, дал quality 13/13, primary 80/80, mean 0.09121044365165432, linear q05 0.08625925727315661, 5/5 secondary support, fit ratio 55.195823 и deterministic rank 6 strongly_supported с 4 disclosures. Policy row order не влияет на result; 10/10 boundaries и 22/22 fail-closed mutations проверены. Notebook, policy, claim, scientific CSV и historical verdict сохранены; training 0. Stage 7 не закрывается до отдельного post-ST07_35 closure re-audit | confirmed_by_user_authorization_local_typed_contract_hash_pairing_golden_boundary_mutation_and_regression_verification_bio_inspired_mape_k_iso29148_nasa_verification_matrix_nist_software_vv | ready_for_john_acceptance |
| MLCRA-RD-076 | Зарегистрировать принятие и закрытие ST07_36 и закрытие Stage 7; предложить, но не начинать `ST08_01_project_completion_and_release_readiness_contract_design` | Прямые решения John закрывают ST07_36 и Stage 7 после объективной матрицы 7/0/0. Source checkpoint v49 имеет SHA-256 5111e145... и 267/267 уникальных entries, рабочая копия до изменения совпала 267/267, protected 18/18. Stage 6 оставил ограниченный публикационный статус, а Stage 7 закрыл его модульную зависимость, но не является проектным release verdict. MCDA дала 5.00 design-first contract против 3.15 немедленного audit без критериев, 2.30 release, 2.20 нового experiment и 1.90 product expansion. Будущий контракт должен раздельно определить completion, software V&V, scientific validation, documentation, packaging и release readiness; Stage 8 не создан и не начат | supported_by_user_decision_local_checkpoint_hash_gap_and_mcda_analysis_iso15288_iso29148_nasa_npr7123_nist_ai_rmf_and_nist_sp500_234 | proposed_not_authorized |
| MLCRA-RD-077 | Принять и закрыть выбор после Stage 7; авторизовать и технически выполнить `ST08_01_project_completion_and_release_readiness_contract_design` без фактического аудита или релиза | Прямое решение John. Контракт фиксирует 24 трассируемых требования по 8 измерениям, 23 mandatory и 1 conditional, исходно 24/24 `NOT_EVALUATED`; задаёт независимые completion/release агрегаты, fail-closed статусы, структуру будущего audit artifact и 14 классов отрицательных мутаций. Source checkpoint v51 имеет SHA-256 2d3ba635... и до изменения совпал с рабочей копией 269/269; protected 18/18. Training, network, scientific artifact changes, audit results и external side effects равны нулю. ST08_02 только предложен | supported_by_user_authorization_local_checkpoint_hash_requirements_traceability_and_contract_verification_bio_inspired_mape_k_iso15288_iso29148_iso25010_iso25040_nasa_npr7123_nist_ai_rmf_nist_software_vv_ssdf_national_academies_pypa_github_and_cff | ready_for_john_acceptance |
| MLCRA-RD-078 | Принять и закрыть ST08_01; авторизовать и технически выполнить `ST08_02_project_completion_and_release_readiness_baseline_audit` без remediation или release | Прямое решение John. Source v52 SHA-256 56e51b... совпал с 273/273 workspace files. Матрица дала requirements PASS/FAIL/BLOCKED/SKIPPED=7/7/10/0 и dimensions=1/4/3. D02 scientific evidence PASS не компенсирует D01/D04/D05/D07 FAIL и D03/D06/D08 BLOCKED; project completion и external release readiness равны FAIL, release class not_ready. Девять findings охватывают current-path defects, owner scope, reproducibility, root entry, release class, license/citation, dataset-license conflict, security assurance и pending dispositions. Protected 18/18; training/scientific changes/release actions=0 | confirmed_by_user_authorization_local_checkpoint_hash_requirements_traceability_fail_closed_aggregation_mutation_testing_and_authoritative_iso_nist_nasa_pypa_github_cff_uci_sources | ready_for_john_acceptance_technical_fail |
| MLCRA-RD-079 | Принять и закрыть ST08_02; авторизовать и технически выполнить `ST08_03_project_scope_release_class_and_owner_decision_resolution`; предложить ограниченную ветку публичной продуктализации без её начала | Прямые решения John приняли D01–D09: полная цель Stage 1 сохраняется; bounded MiniBooNE claim не расширяется; universal CLI, public GitHub и reconstructible Python distribution обязательны; лицензия MIT; автор Иван Полищук, ORCID 0009-0005-6596-0605; raw/cache исключаются; порядок risk/dependency-first. Релизная лестница: public development после legal/docs/security minimum, `0.1.0` после clean installable CLI, `1.0.0` после classification+regression+dashboard+RU/EN docs; PyPI отложен. Из действующих agent rules удалён фиксированный source-change reporting template, но diff review и change reconciliation сохранены; исторические записи не переписаны. Protected 18/18; training/network/release actions 0. Следующим только предложен design-first `ST08_04_public_product_scope_and_release_train_contract_design` | confirmed_by_user_decisions_local_scope_hash_and_verification_nist_ai_rmf_pypa_github_mit_cff_orcid_uci_and_stage1_traceability | ready_for_john_acceptance |
| MLCRA-RD-080 | Принять и закрыть ST08_03; авторизовать и технически выполнить `ST08_04_public_product_scope_and_release_train_contract_design` без реализации или релиза | Прямое поручение John продолжить с ST08_04 после закрытия ST08_03. Контракт фиксирует 5 stakeholder scenarios, единый CLI `audit/verify/doctor`, локальный UTF-8 CSV и JSON Schema input, запрет недоверенного pickle/import/network, 6 exit codes, честную 0.1.0 binary-classification границу и 1.0.0 regression/dashboard/RU-EN границу, 3 fail-closed release gates, 12 readiness/utility metrics, 8 Stage 1 trace rows и 10 proposed-not-authorized блоков. v54 недоступен, поэтому зафиксирован независимый prechange manifest 277 files SHA-256 a3dee65d...; protected 18/18. Source/training/scientific/release actions 0. Следующим только предложен legal-lineage ST08_05 | supported_by_user_authorization_local_stage1_st0802_st0803_and_contract_verification_iso29148_iso9241_nist_ai_rmf_ssdf_pypa_python_json_schema_and_semver | ready_for_john_acceptance |
| MLCRA-RD-081 | Принять и закрыть ST08_04; авторизовать и технически выполнить `ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition`; перейти на Codex-only и риск-ориентированные checkpoints | Прямое решение John. Цепочка UCI 199 → OpenML 41150 → ML-CRA проверена; конфликт CC BY 4.0 UCI и CC0 OpenML не скрыт и консервативно управляется по CC BY 4.0. Все 157 текстовых MiniBooNE/41150-reference files распределены 17/121/2/1/16/0 по пяти dispositions без unmapped; raw/cache запрещены, два direct-sample assets и один stale metadata mutator исключены. ST08-FIND-07 разрешён на contract/inventory уровне, public development остаётся blocked до ST08_06. Browser handoff прекращён; ZIP для обратимого ST08_05 пропущен по risk criteria, v55 сохранён. Baseline PASS; cumulative pilot сохранил FAIL восьми historical gates из-за отсутствующих внешних ZIP v44/v45/v47-v49/v51-v53, при этом текущие structural/scientific regressions PASS и verifier не ослаблялся | supported_by_user_decision_official_uci_openml_cc_by_cc0_terms_nist_provenance_git_version_control_local_inventory_mutation_baseline_and_explicit_cumulative_pilot_disposition | ready_for_john_acceptance |
| MLCRA-RD-082 | Принять и закрыть ST08_05; авторизовать и технически выполнить `ST08_06_project_license_citation_and_public_repository_legal_artifacts` без публикации | Прямое решение John. Созданы точный SPDX/OSI MIT `LICENSE`, CFF 1.2.0 `CITATION.cff` с Иваном Полищуком и проверяемым ORCID, отдельное уведомление UCI/OpenML/CC BY 4.0 и fail-closed публичный манифест. Официальная CFF JSON Schema, SPDX MIT JSON, ORCID MOD 11-2, полный path inventory и отрицательные мутации проверяют артефакты. Два direct-sample файла, stale CC0 mutator, docs/archive, raw/cache patterns и четыре нулевых placeholder-файла исключены без удаления; неизвестный либо изменившийся состав блокирует публикацию. Публикация и release version не создавались; public-development gate остаётся BLOCKED до README, security assurance, репозитория и отдельного решения John. Новый ZIP пропущен по риск-ориентированному правилу | supported_by_user_authorization_osi_spdx_cff_schema_github_orcid_cc_by_local_fail_closed_inventory_baseline_and_regression_verification | ready_for_john_acceptance |
| MLCRA-RD-083 | Принять и закрыть ST08_06; авторизовать и технически выполнить `ST08_07_python_packaging_dependency_and_clean_environment_contract` без CLI или релиза | Прямое решение John. Стандартный `pyproject.toml` фиксирует PEP 440 development-version `0.1.0.dev0`, Python 3.12, MIT, автора, `LICENSE` и `DATASET_ATTRIBUTION.md`, exact core dependencies и exact namespace discovery десяти модулей без нулевых placeholders; OpenML отделён как непроверенный research extra. Hash-locked Windows/CPython 3.12 lock содержит 9 exact wheels и 9 SHA-256. Изолированный build создал sdist 24 entries и wheel-from-sdist 16 entries; новый venv offline установил dependencies и wheel, дал `pip check` PASS, isolated import 11/11 и точную metadata. Проверена только одна environment cell; CLI, cross-platform support, README, security, release и публикация остаются blocked, training/scientific changes равны нулю | supported_by_user_authorization_local_AST_metadata_hash_build_clean_install_inventory_and_mutation_evidence_official_PyPA_pip_setuptools_and_PEP440 | ready_for_john_acceptance |
| MLCRA-RD-084 | Зарегистрировать принятие и закрытие ST08_07; авторизовать, технически выполнить, затем зарегистрировать принятие и закрытие `ST08_08_universal_CLI_classification_vertical_slice` | Прямые решения John. Устанавливаемые `audit/verify/doctor` реализуют fail-closed ограниченный контур бинарной табличной классификации, exact bundle и verification без повторного fit. 11/11 фокусных тестов, чистая offline установка, synthetic fixture и программная характеристика на точном локальном MiniBooNE кеше прошли; 18/18 protected SHA-256 совпали. Научный протокол и вердикт не менялись; универсальная сравнительная претензия, публикация и release отсутствуют | supported_by_user_decisions_local_schema_CLI_clean_install_mutation_and_regression_evidence_official_Python_PyPA_JSON_Schema_scikit_learn_and_pickle_security_documentation | accepted_and_closed_by_John |
| MLCRA-RD-085 | Принять и закрыть ST08_08; авторизовать и технически выполнить `ST08_09_CI_security_and_release_candidate_assurance` без внешнего запуска, публикации или релиза | Прямое решение John и риск-ориентированный secure-development анализ. Least-privilege CI фиксирует actions полными commit SHA, Windows 2022 и последний доступный официальный Windows binary CPython 3.12.10; hosted run не выполнялся. 35-tool hash lock установлен offline; первый pip-audit обнаружил setuptools 82.0.1 advisory и привёл к контролируемому обновлению до 83.0.0, после чего runtime 15/15 и assurance 35/35 дали 0 известных уязвимостей. detect-secrets: 270 файлов, 23 точных детектора, 0 находок; мутации 12/12; sdist/wheel и clean install/CLI PASS; protected 18/18. Pattern scan и advisory audit имеют явные пределы, GitHub secret scanning и hosted CI остаются ненаблюдаемыми | supported_by_user_authorization_NIST_SSDF_GitHub_secure_Actions_and_runner_docs_PyPA_pip_audit_detect_secrets_Python_release_local_hash_mutation_archive_clean_install_and_regression_evidence | ready_for_john_acceptance |
| MLCRA-RD-086 | Принять и закрыть ST08_09; авторизовать и технически выполнить `ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation` без публикации, релиза или научного изменения | Прямое решение John и документационная проверка. Корневые README EN/RU имеют по 12 проверяемых разделов, 3 дословно одинаковых PowerShell-блока и 26 разрешившихся локальных ссылок; пять активных stage-документов согласованы с 23 существующими путями без изменения защищённого Stage 5. Чистая установка по 35+15 hash-locked зависимостям, doctor/audit/verify, sdist/wheel 28/20, 31/31 тест, 277-file secret scan и dependency audit прошли; protected 18/18. Необходимый regression repair заменил слабый общий порог CI guards на проверку каждого native command. Hosted CI и публикация не выполнялись, release_ready остаётся false, ST08_11 только предложен | supported_by_user_authorization_GitHub_README_PyPA_pyproject_Python_venv_pip_secure_local_install_Diataxis_local_link_path_clean_install_mutation_archive_security_and_regression_evidence | ready_for_john_acceptance |
| MLCRA-RD-087 | Принять и закрыть ST08_10; авторизовать и технически выполнить `ST08_11_tabular_regression_protocol_core_and_CLI_support` | Прямые решения John. Реализованы строгая схема табличной регрессии, фиксированные Ridge/HGBR, парный KFold, RMSE/MAE, единое ядро audit/verify, 41/41 исходных и 21/21 чисто установленных CLI-проверок; синтетический результат ограничен программной характеристикой. MiniBooNE protected 18/18 сохранены, реальная научная валидация оставлена отдельной зависимостью | supported_by_user_authorization_local_schema_paired_protocol_mutation_clean_install_and_regression_verification_official_scikit_learn_JSON_Schema_and_Varma_Simon | accepted_and_closed_by_John |
| MLCRA-RD-088 | Принять и закрыть ST08_11; авторизовать и технически выполнить `ST08_11A_registered_regression_dataset_claim_and_scientific_validation`; сохранить объективный `not_supported` | John выбрал UCI Wine Quality red до доступа к результату. Проспективно зафиксированы 5x5 KFold, пять зёрен, Ridge/HGBR, RMSE/MAE и порог 0.05. Все 25 разностей положительны, но средняя 0.04573015523955133 ниже порога, поэтому claim не поддержан без post-result снижения. Два запуска детерминированы, verify без fit, 45/45 focused, baseline и текущие pilot checks PASS; raw исключён, CC BY 4.0 и DOI зарегистрированы, protected 18/18 | supported_by_user_authorization_and_dataset_selection_official_UCI_CC_BY_peer_reviewed_Cortez_prospective_protocol_paired_recomputation_mutation_baseline_and_regression_verification | ready_for_john_acceptance_technical_pass_scientific_not_supported |
| MLCRA-RD-089 | Принять и закрыть ST08_11A; авторизовать, технически выполнить, принять и закрыть `ST08_12_dashboard_shared_core_and_CLI_golden_equivalence` без публикации | Прямые решения John. Новый dashboard вызывает verify_bundle, строит один deterministic JSON и exact RU/EN static HTML с SHA-256 manifest; повторная проверка требует golden equality без fit и сети. Негативный regression verdict сохраняется, HTML payload escaped, JavaScript/server отсутствуют. Source, mutation, bilingual, archive, clean package and protected checks зарегистрированы; научные значения не менялись. John присвоил ST08_12 `ACCEPTED_BY_JOHN` и `TASK_CLOSED`; имя ST08_13 указано без зарезервированной метки авторизации | supported_by_user_authorization_acceptance_and_closure_local_shared_core_golden_hash_mutation_and_regression_verification_official_Python_html_OWASP_W3C_WCAG_and_NIST_VV | accepted_and_closed_by_John |
| MLCRA-RD-090 | Авторизовать и технически выполнить `ST08_13_release_candidate_completion_security_and_readiness_reaudit` без remediation, публикации или релиза | Прямое решение John и повторное применение неизменной матрицы 24 требований. Baseline, 63 focused tests, локальные source/security/dependency/archive/clean-install проверки и 18/18 protected hashes прошли; cumulative pilot сохранил восемь historical FAIL, внешние ZIP checkpoints недоступны, hosted CI и GitHub secret scanning не наблюдались. Результат 19 PASS / 2 FAIL / 3 BLOCKED, dimensions 5/2/1, project completion FAIL, external release readiness FAIL. По конвенции ST08_02 технический FAIL описывает объект, тогда как процедура аудита имеет отдельный PASS; ST08_14 только предложен | supported_by_user_authorization_fail_closed_independent_aggregation_mutation_clean_install_current_advisory_and_official_NIST_SSDF_GitHub_PyPA_evidence | ready_for_john_acceptance_technical_fail_object_fail |
| MLCRA-RD-091 | Принять и закрыть ST08_13; авторизовать и технически выполнить перспективную миграцию REQ08/REQ12 на текущее хеш-связанное каноническое состояние без переписывания исторических FAIL | Прямое решение John. Требования v01 и пять исторических файлов ST08_13 защищены точными SHA-256; v02 сохраняет 22 строки дословно и изменяет только семь разрешённых полей REQ08/REQ12 при неизменном `NOT_EVALUATED`. Полный текущий project-file universe связан путём, SHA-256 и размером; два циклических выхода исключены явно. Валидация проверяет public inventory, protected 18/18, CI, exact scope и мутации. Исторические REQ08 `FAIL` и REQ12 `BLOCKED` сохранены; новый re-audit, внешние действия, выпуск и ZIP не выполнялись | supported_by_user_authorization_NIST_FIPS180_4_NIST_SSDF_NIST_SP800_53_configuration_control_local_hash_relation_manifest_and_mutation_verification | ready_for_john_acceptance |
| MLCRA-RD-092 | Принять и закрыть ST08_13A; выполнить авторизованный `ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence` без версии или релиза | Прямое решение John разрешает внешний блок. Локальная проверка выявила конфликт между полным policy inventory и разрешённым публикационным подмножеством; поэтому вводится отдельный SHA-256 manifest точного `git ls-files` дерева, а ST08_13A сохраняется как исторический снимок. Репозиторий, hosted CI, secret scanning, private vulnerability reporting, защита main и fresh-clone recovery требуют наблюдаемого внешнего evidence; до него статус остаётся pending | supported_by_user_authorization_local_fail_closed_inventory_analysis_official_GitHub_REST_Actions_secret_scanning_branch_protection_private_reporting_NIST_FIPS180_4_and_SSDF | implementation_in_progress |

## 13. Известные несинхронизации, закрытые этой версией

1. Старые отчеты находились в `docs/reports/`, хотя эта папка уже не должна быть рабочей зоной. Решение: перенести в `docs/archive/reports/`.
2. Этап 5 был представлен двумя активными документами. Решение: объединить содержание в `docs/stages/stage_05_claim_audit_protocol.md`; второй документ перевести в `docs/archive/stages/`.
3. `ST05_02_seed_stability_grid` присутствовал как результат в `data_registry/`, но активный документ этапа 5 сообщал, что новые стресс-запуски еще не выполнялись. Решение: обновить документ этапа 5.
4. Baseline v13 содержал реализованный `ST07_06`, но `roadmap.md` и Stage 7 продолжали называть его следующим шагом. Решение: зафиксировать приёмку John и повторную регрессионную проверку.
5. Инструкция Stage 6 называла три обязательных nested-артефакта несуществующими именами с дополнительным `_cv`. Решение: заменить их фактическими путями и сохранить `nested_cv` только в имени существующего protocol lock.

## 14. Ближайший допустимый шаг

John принял и закрыл ST08_01 и авторизовал ST08_02. Контракт применён к
baseline v52 без исправления объекта оценки. Отрицательный readiness verdict
зарегистрирован с девятью findings; внешний релиз не разрешён.

Историческое состояние выбора, необходимое для аудиторского следа Stage 7:

```text
NEXT_BLOCK_AUTHORIZED: ST07_34_verdict_policy_application_contract_and_golden_master_design
ACCEPTED_BY_JOHN: ST07_34_verdict_policy_application_contract_and_golden_master_design
TASK_CLOSED: ST07_34_verdict_policy_application_contract_and_golden_master_design
NEXT_BLOCK_AUTHORIZED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation
ST07_35_status: accepted_by_john
ACCEPTED_BY_JOHN: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation
TASK_CLOSED: ST07_35_verdict_policy_application_modular_extraction_and_golden_master_validation
ST07_35_formal_task_closure: closed_by_john
NEXT_BLOCK_AUTHORIZED: ST07_36_stage07_post_verdict_policy_closure_reaudit
stage07_closure_audit_after_ST07_35: COMPLETED_PASS
stage07_closure_reaudit_verdict: PASS
stage07_closure_criteria: PASS=7;FAIL=0;BLOCKED=0
ACCEPTED_BY_JOHN: ST07_36_stage07_post_verdict_policy_closure_reaudit
TASK_CLOSED: ST07_36_stage07_post_verdict_policy_closure_reaudit
STAGE_CLOSED_BY_JOHN: Stage_7
stage07_status: closed_by_john
stage07_closed: true
ST07_36_status: accepted_by_john
ST07_36_implementation_started: YES_COMPLETE
proposed_next_block: ST08_01_project_completion_and_release_readiness_contract_design
ST08_01_status: proposed_not_authorized
ST08_01_implementation_started: NO
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Текущее авторизованное состояние:

```text
ACCEPTED_BY_JOHN: STAGE07_closure_registration_and_next_stage_selection
TASK_CLOSED: STAGE07_closure_registration_and_next_stage_selection
NEXT_BLOCK_AUTHORIZED: ST08_01_project_completion_and_release_readiness_contract_design
stage08_status: active_contract_design
ST08_01_status: technical_pass_ready_for_john_acceptance
ST08_01_implementation_started: YES_COMPLETE
ST08_01_audit_execution_authorized: false
ST08_01_release_authorized: false
proposed_next_block: ST08_02_project_completion_and_release_readiness_baseline_audit
ST08_02_status: proposed_not_authorized
ST08_02_implementation_started: NO
TECHNICAL_STATUS: PASS
```

Текущий audit state:

```text
ACCEPTED_BY_JOHN: ST08_01_project_completion_and_release_readiness_contract_design
TASK_CLOSED: ST08_01_project_completion_and_release_readiness_contract_design
NEXT_BLOCK_AUTHORIZED: ST08_02_project_completion_and_release_readiness_baseline_audit
ST08_02_status: technical_fail_ready_for_john_acceptance
ST08_02_implementation_started: YES_COMPLETE
ST08_02_remediation_authorized: false
ST08_02_release_authorized: false
stage08_requirement_results: PASS=7;FAIL=7;BLOCKED=10;SKIPPED=0
stage08_dimension_results: PASS=1;FAIL=4;BLOCKED=3
project_completion_verdict: FAIL
external_release_readiness: FAIL
release_class: not_ready
proposed_next_block: ST08_03_project_scope_release_class_and_owner_decision_resolution
ST08_03_status: proposed_not_authorized
ST08_03_implementation_started: NO
TECHNICAL_STATUS: FAIL
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Ближайший допустимый шаг — сначала получить owner decisions — решения John,
которые определяют границы remediation: MVP outputs, supported interface,
release class, Python distribution и license/citation policy. ST08_03 не
авторизован и не начат.

## 15. Задачи John

1. Рассмотреть отрицательный, но технически корректный audit ST08_02. При
   принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
2. Если согласован owner-decision-first шаг, только John может присвоить:

```text
NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution
```

3. До такой авторизации не выбирать за John MVP/release/license/citation
   политику, не выполнять remediation и не осуществлять внешний релиз.

### ST08_03 — разрешённые решения владельца и следующая ветка

John принял и закрыл ST08_02, авторизовал ST08_03 и после человеко-понятной
расшифровки принял D01–D09. Зарегистрированы полная исходная цель Stage 1,
универсальный CLI, публичный GitHub, воспроизводимая Python-дистрибуция, MIT,
автор `Иван Полищук`, ORCID `https://orcid.org/0009-0005-6596-0605`, политика
данных и risk/dependency-first порядок.

```text
ACCEPTED_BY_JOHN: ST08_02_project_completion_and_release_readiness_baseline_audit
TASK_CLOSED: ST08_02_project_completion_and_release_readiness_baseline_audit
NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution
ST08_03_status: technical_pass_ready_for_john_acceptance
ST08_03_implementation_started: YES_COMPLETE
target_release_class: public_installable_python_distribution
target_repository: https://github.com/Vanargo/ML-CRA
project_license: MIT
creator: Иван Полищук
orcid: https://orcid.org/0009-0005-6596-0605
first_supported_release: 0.1.0_after_clean_installable_cli
version_1_0_0_gate: classification+regression+dashboard+bilingual_docs
external_release_authorized: false
proposed_next_block: ST08_04_public_product_scope_and_release_train_contract_design
ST08_04_status: proposed_not_authorized
ST08_04_implementation_started: NO
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Человеко-понятный смысл: ST08_03 не сделал проект готовым к публикации, но снял
все неопределённости, принадлежавшие владельцу, и установил измеримую границу
будущей продуктовой ветки. Научный результат не изменён. Следующий design-блок
ещё не разрешён; фактическая публикация, CLI, dashboard, LICENSE и package не
создавались.

По отдельному решению John из будущих agent rules удалён фиксированный шаблон
показа исходного и нового фрагмента. Объективная diff-проверка и сопоставление
плана с фактическим журналом изменений сохранены. Исторические записи Stage 4–7
не изменялись и не являются будущей нормой.

## 16. Задачи John

1. Принять либо вернуть технически завершённый ST08_03.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. В новом чате отдельно решить, авторизовать ли
   `ST08_04_public_product_scope_and_release_train_contract_design`.

## 17. ST08_04 — контракт публичного продукта и release train

John сообщил о закрытии ST08_03 и поручил продолжить с ST08_04. Design-контракт
зарегистрирован в
`configs/project_readiness/stage08_public_product_scope_and_release_train_contract_v01.json`.

```text
ACCEPTED_BY_JOHN: ST08_03_project_scope_release_class_and_owner_decision_resolution
TASK_CLOSED: ST08_03_project_scope_release_class_and_owner_decision_resolution
NEXT_BLOCK_AUTHORIZED: ST08_04_public_product_scope_and_release_train_contract_design
ST08_04_status: technical_pass_ready_for_john_acceptance
ST08_04_implementation_started: YES_COMPLETE_DESIGN_ONLY
stakeholder_scenarios: 5
CLI_commands: audit+verify+doctor
problem_support_0_1_0: binary_tabular_classification
problem_support_1_0_0: binary_tabular_classification+tabular_regression
release_gates: public_development+0.1.0+1.0.0
objective_metrics: 12
stage1_trace_rows: 8
protected_artifacts: 18/18
product_implementation_performed: false
external_release_authorized: false
proposed_next_block: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
ST08_05_status: proposed_not_authorized
ST08_05_implementation_started: NO
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Человеко-понятный смысл: впервые зафиксировано, что именно должен делать
устанавливаемый продукт, для кого, с какими входами, выходами, ошибками и
измеримыми release gates. `0.1.0` честно ограничен бинарной классификацией;
регрессия и dashboard обязательны к `1.0.0`, но пока не реализованы. Отрицательный
научный verdict является успешным выполнением, а недостаточность evidence —
отдельным отказом. Ни один релизный gate не получил PASS, CLI и package не
созданы. Следующий блок только предложен.

Недоступность заявленного `ml_cra_v54.zip` зафиксирована явно: вместо
непроверяемого совпадения использован prechange workspace-manifest 277 файлов,
SHA-256 `a3dee65d92cc155bb99c97ac732f258c58ac95b52ba10d38ace141597787a1e7`.
Новая контрольная точка должна стать проверяемым handoff — состоянием передачи.

## 18. Задачи John

1. Принять либо вернуть ST08_04.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только
   `ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition`.
4. Не считать десять строк release train пакетной авторизацией и не выполнять
   внешний релиз по одному design PASS.

## 19. ST08_05 — происхождение MiniBooNE и распоряжение релизными артефактами

John принял ST08_04, поручил двигаться далее и исключил браузерный ChatGPT из
разработки. В границе единственного предложенного следующего блока выполнен
только ST08_05:

```text
ACCEPTED_BY_JOHN: ST08_04_public_product_scope_and_release_train_contract_design
TASK_CLOSED: ST08_04_public_product_scope_and_release_train_contract_design
NEXT_BLOCK_AUTHORIZED: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
ST08_05_status: technical_pass_ready_for_john_acceptance
ST08_06_status: proposed_not_authorized
external_release_authorized: false
```

Официальные записи образуют цепочку UCI dataset 199 → OpenML mirror 41150 →
ML-CRA, но конфликтуют по лицензии: [UCI](https://archive.ics.uci.edu/dataset/199/miniboone+particle+identification)
указывает CC BY 4.0 и DOI `10.24432/C5QC87`, а
[OpenML API](https://www.openml.org/api/v1/json/data/41150) — CC0 и исходный UCI
URL. Полномочие OpenML uploader ослабить условия первичного источника не
установлено, поэтому для публикационного контроля принято консервативное
fail-closed правило CC BY 4.0 с creator/source/license/change attribution. Это
не юридическое заключение.

Полный inventory после ST08_05 содержит 157 файлов со ссылкой `MiniBooNE` или
`41150`: 17 implementation conditional, 121 derived/metadata conditional with
attribution, 2 direct-sample exclusions, 1 stale-CC0 mutator exclusion, 16
governance/history inclusions, 0 unmapped. Raw/cache не распространяются.
ST08-FIND-07 разрешён на contract/inventory уровне; public development остаётся
blocked до отдельно авторизованного ST08_06, который должен создать и проверить
MIT `LICENSE`, `CITATION.cff`, dataset attribution и public manifest.

Browser handoff прекращён. ZIP теперь создаётся по критериям риска, а не после
каждой задачи. Для обратимого ST08_05 без stage closure и external handoff он
имеет `SKIPPED`; точный `ml_cra_v55.zip` с SHA-256
`0b7b954eca46038ed63b9d8d2e0be450a6b131c477a626261d460b77a3a1d0b7`
сохраняет доизменительное состояние. Полный отказ от recovery не принят:
текущая рабочая копия не является Git repository, поэтому стратегические ZIP
остаются до отдельного решения и проверки version-control recovery.

Baseline после исправления cumulative allowlist прошёл. Cumulative pilot не
объявляется зелёным: восемь historical gates требуют отсутствующие внешние ZIP
v44, v45, v47, v48, v49, v51, v52 и v53. Все текущие структурные и научные
регрессии в том же прогоне прошли; защищённый verifier не изменялся.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_06_project_license_citation_and_public_repository_legal_artifacts
ST08_06_status: proposed_not_authorized
```

Эти значения означают, что ограниченный lineage/disposition-блок проверен и
готов к решению John, но не что проект юридически очищен или готов к публикации.

## 20. Задачи John

1. Принять либо вернуть ST08_05.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только ST08_06.

## 20. ST08_06 — лицензия, цитирование и юридические артефакты публичного репозитория

John принял и закрыл ST08_05 и поручил двигаться далее. По порядку, ранее
зафиксированному в
`configs/project_readiness/stage08_public_product_scope_and_release_train_contract_v01.json`,
это разрешило только ST08_06:

```text
ACCEPTED_BY_JOHN: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
TASK_CLOSED: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
NEXT_BLOCK_AUTHORIZED: ST08_06_project_license_citation_and_public_repository_legal_artifacts
ST08_06_status: technical_pass_ready_for_john_acceptance
ST08_07_status: proposed_not_authorized
external_publication_authorized: false
```

В корне созданы `LICENSE`, `CITATION.cff` и `DATASET_ATTRIBUTION.md`. Текст MIT
сверен с [OSI](https://opensource.org/license/mit) и официальной записью
[SPDX](https://spdx.org/licenses/MIT.html); MIT относится только к оригинальному
коду и документации ML-CRA и не перелицензирует MiniBooNE. `CITATION.cff`
проверен по официальной JSON Schema CFF 1.2.0 и содержит одобренные John имя,
ORCID и целевой URL репозитория без вымышленной версии или даты релиза.
[GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files)
определяет корневой `CITATION.cff` как машино- и человекочитаемый источник
цитирования, а [CFF schema guide](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md)
показывает, что `version` не обязателен. ORCID проверен по официальному
алгоритму MOD 11-2.

Публичный манифест
`configs/project_readiness/st08_06_public_repository_asset_manifest_v01.json`
использует приоритетные правила и default-deny: два direct-sample артефакта,
stale CC0 mutator, исторический `docs/archive/`, raw/cache patterns и четыре
нулевых placeholder-файла исключены. Три ранее не отмеченных пустых Python-файла
обнаружены полным инвентарём; их назначение не выводится, содержимое не
создаётся и файлы не удаляются. Состав кандидата связывается с точным числом
путей и SHA-256 списка путей, поэтому новый неизвестный путь блокирует
публикацию до повторного решения.

`DATASET_ATTRIBUTION.md` реализует creator/source/DOI/license/change и
no-endorsement условия ST08_05. Официальное изложение
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) требует надлежащего
указания авторства, ссылки на лицензию и отметки изменений без создания
впечатления об одобрении. Юридическое заключение не выполнялось.

Public-development gate остаётся `BLOCKED`: в ST08_06 не создавались README,
security policy/scan, GitHub-репозиторий или явная авторизация публикации.
Это означает, что юридические артефакты технически готовы, но проект всё ещё
нельзя публиковать. Доказательства находятся в
`data_registry/st08_06_project_license_citation_and_public_repository_legal_artifacts_evidence_v01.json`.

Baseline прошёл. Cumulative pilot сохранил восемь historical FAIL: все восемь
проверок требуют отсутствующие внешние ZIP v44, v45, v47, v48, v49, v51, v52 и
v53; ST08_03 дополнительно и ожидаемо фиксирует
`forbidden_outputs_absent=False`, поскольку ST08_06 теперь авторизованно создал
`LICENSE` и `CITATION.cff`. Все текущие syntax, CSV, notebook, required-path,
documentary, protected и Stage 7 computational regressions в том же прогоне
прошли. Verifier не ослаблялся, исторические архивы не фабриковались.

Новый ZIP имеет `SKIPPED`: стадия не закрывается, внешней передачи нет,
изменения текстовые и обратимые, а точные evidence/change scope/path manifest
создают проверяемое состояние. Это не отменяет отдельную будущую задачу по
version-control recovery.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_07_python_packaging_dependency_and_clean_environment_contract
ST08_07_status: proposed_not_authorized
```

Человекочитаемый смысл: ST08_06 прошёл ограниченные технические проверки и
готов к решению John. Это не приёмка, не разрешение публикации и не вывод о
полной юридической чистоте проекта.

## 21. Задачи John

1. Принять либо вернуть только ST08_06.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только предложенный ST08_07.
4. Не публиковать проект до прохождения оставшихся шлюзов и отдельной явной
   авторизации внешнего действия.
4. Не выполнять публикацию до отдельного release authorization и прохождения
   применимых шлюзов.

## 22. ST08_07 — Python packaging, dependency lock и clean environment

John принял и закрыл ST08_06 и поручил двигаться далее. По ранее принятому
release train это разрешило только ST08_07:

```text
ACCEPTED_BY_JOHN: ST08_06_project_license_citation_and_public_repository_legal_artifacts
TASK_CLOSED: ST08_06_project_license_citation_and_public_repository_legal_artifacts
NEXT_BLOCK_AUTHORIZED: ST08_07_python_packaging_dependency_and_clean_environment_contract
ST08_07_status: technical_pass_ready_for_john_acceptance
ST08_08_status: proposed_not_authorized
external_publication_authorized: false
```

Создан `pyproject.toml` с `setuptools==82.0.1`, development-version
`0.1.0.dev0`, Python `>=3.12,<3.13`, MIT, автором и точными core dependencies.
PEP 440 подтверждает, что `.dev0` предшествует final `0.1.0`; это metadata для
проверки сборки, а не релиз. `[project.scripts]` отсутствует, потому что CLI
принадлежит отдельно авторизуемому ST08_08.

Exact setuptools namespace discovery упаковал десять реализованных модулей и
исключил нулевой `mlcra.data_registry`. OpenML объявлен отдельным
`research-openml` extra и не выдан за поддержанное ядро. Hash-locked файл
`requirements/locks/st08_07-py312-windows-x86_64.txt` фиксирует девять exact
runtime wheels и SHA-256.

Официальный `build==1.5.0` в изоляции создал sdist, затем wheel из sdist. Новый
venv установил hash-locked зависимости offline и локальный wheel без сети;
`pip check`, 11/11 isolated imports, installed metadata и package inventory
прошли. Временные build/dist/venv/wheelhouse/egg-info удалены; публикация не
выполнялась. Проверена только одна ячейка CPython 3.12.0 / Windows x86_64;
Linux, macOS, другие Python и research extra не объявлены поддержанными.

ST08-FIND-03 и ST08-FIND-05 частично разрешены: стандартные metadata, exact
dependencies, sdist/wheel и clean import существуют, но поддерживаемой команды
нет до ST08_08. Public-development и 0.1.0 gates остаются BLOCKED также из-за
README, CI/security, неполной матрицы и отсутствия решения John о релизе.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_08_universal_CLI_classification_vertical_slice
ST08_08_status: proposed_not_authorized
```

Эти значения означают task-specific техническую готовность ST08_07 к решению
John, но не приёмку, научную ревалидацию, выпуск `0.1.0` или готовность к
публикации.

## 23. Задачи John

1. Принять либо вернуть только ST08_07.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только ST08_08.
4. Не публиковать `0.1.0.dev0` и не считать его релизом.

## 24. ST08_08 — универсальный CLI бинарной классификации

John присвоил ST08_07 `ACCEPTED_BY_JOHN` и `TASK_CLOSED`, после чего явно
авторизовал только `ST08_08_universal_CLI_classification_vertical_slice`.

Реализованы устанавливаемые команды `mlcra audit`, `mlcra verify` и
`mlcra doctor` для fail-closed (отказоустойчиво закрытого) ограниченного контура
бинарной табличной классификации. Спецификация валидируется поставляемой JSON Schema
Draft 2020-12; URL, произвольный код/модели, pickle, регрессия, несколько классов,
неполные нечисловые данные и перезапись вывода не поддерживаются. `audit` создаёт
ровно восемь JSON-артефактов с SHA-256 и атомарной публикацией, `verify` проверяет
их и пересчитывает вердикт без обучения, `doctor` проверяет окружение без сети и
обучения.

Фокусные тесты: 11/11 PASS, все коды `0/2/3/4/5/6`. Чистая установка wheel в
CPython 3.12.0 / Windows AMD64 с 15 hash-locked зависимостями прошла, console script
и `doctor=0` подтверждены. Синтетический пример дал 8/8 положительных блоков и
среднюю разницу average precision `0.5158023952204487` при пороге `0.05`.

MiniBooNE использован только как программная характеристика CLI: точный локальный
кеш, сеть 0, 130064x50, два блока, `audit=0`, `verify=0`, средняя разница
`0.09079498654089707`. Каноническая научная валидация не менялась; 18/18
защищённых SHA-256 совпали.

Baseline прошёл. Cumulative pilot сохранил восемь ранее известных исторических
FAIL старых ZIP/условия ST08_03; все текущие регрессии прошли. Новый ZIP пропущен:
нет закрытия стадии и внешней передачи, проект теперь ведётся John и Codex, а
изменения обратимы и зафиксированы контрактом, evidence и change scope.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_09_CI_security_and_release_candidate_assurance
ST08_09_status: proposed_not_authorized
```

Эти значения означают техническую готовность только ST08_08 к решению John, а не
приёмку, релиз, публикацию или разрешение начинать ST08_09.

## 25. Задачи John

1. Принять либо вернуть на доработку только ST08_08.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только предложенный ST08_09.

## 26. ST08_09 — CI, безопасность и проверка кандидата на выпуск

John принял и закрыл ST08_08; следующий точный блок ST08_09 реализован без
внешнего репозитория, публикации и релиза. Создан least-privilege (с минимальными
полномочиями) GitHub Actions workflow с неизменяемыми commit SHA, фиксированными
Windows 2022 / CPython 3.12.10 и явным распространением сбоев PowerShell.

35 точных assurance-зависимостей установлены offline по SHA-256. Первый pip-audit
обнаружил уязвимый `setuptools==82.0.1`; текущий backend обновлён до исправленного
`83.0.0`, после чего 15 runtime и 35 assurance зависимостей дали 0 известных
уязвимостей. detect-secrets проверил 270 файлов 23 точными детекторами без находок.
Мутации 12/12, архивы sdist/wheel, чистая установка, `pip check`, `doctor` и 11/11
CLI-тестов прошли; protected SHA-256 совпали 18/18.

Hosted CI не запускался, внешнее GitHub secret scanning не включено, README/RU/EN,
release-candidate повторный аудит, дополнительная матрица и решение John о релизе
остаются открыты. CPython 3.12.10 — последний официальный Windows binary ветки,
но он не содержит более поздние source-only security fixes; стратегия поддержки
интерпретатора остаётся релизным риском. Эти ограничения не скрываются и не
позволяют считать проект готовым к публикации.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
ST08_10_status: proposed_not_authorized
```

Значения означают техническую готовность только ST08_09 к решению John, но не
приёмку, выполненный hosted CI, публикацию, релиз или начало ST08_10.

## 27. Задачи John

1. Принять либо вернуть на доработку только ST08_09.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только предложенный ST08_10.
4. Не публиковать и не выпускать ML-CRA до отдельной авторизации и прохождения
   оставшихся шлюзов.

## 28. ST08_10 — двуязычный пользовательский путь и актуальные ссылки

John принял и закрыл ST08_09; разрешённый ST08_10 создал корневые `README.md` и
`README_RU.md` для одного ограниченного рабочего процесса бинарной табличной
классификации. Оба документа имеют по 12 обязательных разделов и три дословно
одинаковых PowerShell-блока. Проверено 26 локальных ссылок. `pyproject.toml`
использует английский README как полное описание пакета, а русский документ
остаётся равноправной точкой входа.

Текущие ссылки Stage 1–4 переведены со старых ZIP/`docs/generated`/
`docs/reports` на существующий `docs/archive`; Stage 4 отделяет текущий Stage 5
от архивного заменённого документа. Stage 6 указывает фактический модульный
слой вместо не созданного исторического `src/mlcra/stage05/`. Защищённые
научные файлы не менялись, SHA-256 совпали 18/18.

Чистая установка CPython 3.12.0 / Windows AMD64 по 35 инструментальным и 15
runtime hash-locked зависимостям прошла. `doctor` подтвердил окружение, но
сохранил `release_ready=false`; fixture `audit` создал ровно 8 файлов и
`supported`, а `verify` прошёл без повторного обучения. Sdist/wheel 28/20,
31/31 тест, поиск секретов по 277 файлам и актуальный аудит 15+35 зависимостей
прошли. CI-валидатор дополнительно усилен до отдельного `$LASTEXITCODE` после
каждой нативной команды многострочного шага.

Публичный манифест: 322 пути, 0 неразмеченных, SHA-256 списка
`50fe2d8425f786cfc86f7d21bcc93c074bfd766430d51e4ca088db3a98d22ea5`.
README-блокер снят, но hosted CI, внешнее secret scanning, повторный аудит
кандидата, публичный репозиторий и авторизация John остаются открыты. ZIP
пропущен по риск-ориентированному правилу: стадия не закрыта и внешней передачи
нет.

```text
ACCEPTED_BY_JOHN: ST08_09_CI_security_and_release_candidate_assurance
TASK_CLOSED: ST08_09_CI_security_and_release_candidate_assurance
NEXT_BLOCK_AUTHORIZED: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
proposed_next_block: ST08_11_tabular_regression_protocol_core_and_CLI_support
ST08_11_status: proposed_not_authorized
```

Значения означают, что ST08_09 принят, а только ST08_10 технически готов к
решению John. Они не означают приёмку ST08_10, релиз, публикацию, поддержку
регрессии или разрешение начинать ST08_11.

## 29. Задачи John

1. Принять либо вернуть на доработку только ST08_10.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только предложенный ST08_11.
4. Не публиковать и не выпускать ML-CRA до отдельной авторизации и прохождения
   оставшихся шлюзов.

## 30. ST08_11 — технический регрессионный вертикальный срез

John принял и закрыл ST08_10 и тем самым авторизовал только
`ST08_11_tabular_regression_protocol_core_and_CLI_support`. Созданы строгая
регрессионная JSON Schema, диспетчеризация общего прикладного ядра, числовой
вход, фиксированные Ridge/HGBR, парный KFold по заранее заданным зернам, RMSE/MAE,
регрессионный восьмифайловый пакет и повторная проверка без обучения.

Область поддержки ограничена `exchangeable_rows`: временные, групповые,
пространственные и повторные наблюдения требуют другого проспективного протокола.
Подбора моделей и гиперпараметров нет. Синтетический пример 41x1 дал 8/8
положительных блоков, среднюю разность RMSE `6.47927764243067` при пороге `1.0`
и ограниченный `supported`; это программная характеристика, а не научная
валидация реального предметного утверждения.

41/41 исходных теста, sdist/wheel 30/21, чистая установка 15 точных зависимостей,
21/21 установленный CLI-тест, два walkthrough (пошаговых пользовательских
сценария), baseline, 18/18 защищённых SHA-256 и поиск секретных шаблонов прошли.
Накопительный pilot имеет только восемь прежних исторических FAIL старых ZIP и
условия ST08_03; нового отказа ST08_11 нет. Публичный манифест — 329 путей,
0 неразмеченных. ZIP пропущен по риск-ориентированному правилу.

```text
ACCEPTED_BY_JOHN: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
TASK_CLOSED: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
NEXT_BLOCK_AUTHORIZED: ST08_11_tabular_regression_protocol_core_and_CLI_support
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
scientific_validation_real_regression_dataset: SKIPPED_NOT_AUTHORIZED
release_1_0_0_regression_gate: BLOCKED
```

Статус PASS означает готовность только технического результата ST08_11 к
решению John. Он не означает приёмку, научную валидацию реальной регрессионной
задачи, готовность 1.0.0, панель, публикацию или релиз.

## 31. Корректирующая зависимость перед ST08_12

```text
proposed_next_block: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
ST08_11A_status: proposed_not_authorized
ST08_12_status: deferred_until_regression_scientific_dependency_is_resolved
```

Контракт продукта требует отдельной научной и программной валидации регрессии
до шлюза 1.0.0. У существующих кандидатов регрессии временная структура и
неразрешённые поля лицензии/приёмки, поэтому применять к ним KFold обменных строк
молча нельзя. До панели предлагается отдельный блок выбора John и проспективной
регистрации реального датасета, утверждения, лицензии, структуры выборки,
разбиения, метрик и политики вердикта. Выполнение не начиналось.

## 32. Задачи John

1. Принять либо вернуть на доработку только ST08_11.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, разрешать ли только предложенный ST08_11A.
4. Не авторизовывать ST08_12, публикацию или релиз неявно через приёмку ST08_11.

## 33. ST08_11A — реальная регрессионная научная валидация

John принял и закрыл ST08_11, авторизовал ST08_11A и выбрал красный вариант UCI
Wine Quality. До загрузки данных зафиксированы 5×5 парных K-fold-блоков,
Ridge/HGBR, RMSE/MAE, пять зёрен, порог средней разности `0.05` и неизменяемая
политика вердикта. UCI DOI — `10.24432/C56S3T`, лицензия — CC BY 4.0; исходные
строки в проект не включены.

Все 25 разностей `RMSE_Ridge - RMSE_HGBR` положительны, но средняя разность
`0.04573015523955133` ниже порога. Объективный claim-вердикт —
`not_supported`; порог после результата не изменён. Два запуска совпали по
научно значимому содержимому, два `verify` прошли без обучения. Вывод ограничен
красным файлом, фиксированным протоколом и недоказанным допущением обменности;
универсальное или причинное превосходство не утверждается.

```text
ACCEPTED_BY_JOHN: ST08_11_tabular_regression_protocol_core_and_CLI_support
TASK_CLOSED: ST08_11_tabular_regression_protocol_core_and_CLI_support
NEXT_BLOCK_AUTHORIZED: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
DATASET_SELECTED_BY_JOHN: UCI_Wine_Quality_red_v01
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
scientific_claim_verdict: not_supported
```

`PASS` относится к корректности проспективной регистрации, выполнения и
проверки, а не к положительной поддержке claim. John должен принять либо вернуть
ST08_11A; публикация, релиз и следующий блок не авторизованы.

## 34. Предлагаемый следующий блок

```text
proposed_next_block: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
ST08_12_status: proposed_not_authorized
```

## 35. Задачи John

1. Принять либо вернуть ST08_11A.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только ST08_12.

## 36. ST08_12 — панель и golden equivalence

John принял и закрыл ST08_11A и авторизовал ST08_12. Реализована автономная
команда панели, которая сначала проверяет существующий bundle общим ядром, а
затем создаёт один точный JSON, RU/EN HTML и хеш-манифест. Повторная проверка
требует точного совпадения всех представлений; fit, сеть, JavaScript и сервер
отсутствуют. Проверки охватывают классификацию, отрицательный регрессионный
вердикт, запрет fit, HTML-экранирование, подмену и перезапись.

```text
ACCEPTED_BY_JOHN: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
TASK_CLOSED: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
NEXT_BLOCK_AUTHORIZED: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
ACCEPTED_BY_JOHN: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
TASK_CLOSED: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

PASS относится к программному и документальному совпадению панели с bundle и
не меняет научные вердикты. Публикация и релиз не разрешены.

## 37. Предлагаемый следующий блок

```text
proposed_next_block: ST08_13_release_candidate_completion_security_and_readiness_reaudit
ST08_13_status: proposed_not_authorized
```

## 38. Задачи John

1. ST08_12 принят и закрыт; дополнительных действий по нему не требуется.
2. Если требуется начать ST08_13, отдельно присвоить зарезервированную метку
   авторизации следующего блока с идентификатором
   `ST08_13_release_candidate_completion_security_and_readiness_reaudit`.
3. До такой метки сохранять ST08_13 в состоянии `proposed_not_authorized`.

## 39. ST08_13 — повторный release-candidate re-audit

John отдельно авторизовал ST08_13. Неизменная матрица 24 требований применена
без исправления объекта, научных изменений или внешних действий. Baseline,
63 профильных теста, локальные source/security проверки, dependency audit,
sdist/wheel, clean install, walkthrough и 18/18 protected hashes прошли. Полный
cumulative pilot сохранил восемь исторических FAIL; внешние ZIP checkpoints
недоступны, hosted CI и репозиторное secret scanning не наблюдались.

Результат требований: `19 PASS / 2 FAIL / 3 BLOCKED`; измерений:
`5 PASS / 2 FAIL / 1 BLOCKED`. Независимая агрегация дала
`project_completion_verdict=FAIL`, `external_release_readiness=FAIL` и
`release_class=not_ready`. Сама процедура аудита имеет отдельный PASS, но по
конвенции отрицательного readiness-аудита `TECHNICAL_STATUS` объекта равен FAIL.

```text
NEXT_BLOCK_AUTHORIZED: ST08_13_release_candidate_completion_security_and_readiness_reaudit
TECHNICAL_STATUS: FAIL
READINESS: READY_FOR_JOHN_ACCEPTANCE
PROJECT_COMPLETION_VERDICT: FAIL
EXTERNAL_RELEASE_READINESS: FAIL
```

## 40. Предлагаемый следующий блок

```text
proposed_next_block: ST08_14_public_repository_publication_and_external_release
ST08_14_status: proposed_not_authorized
```

## 41. Задачи John

1. Принять либо отклонить техническое выполнение ST08_13; при принятии отдельно
   присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
2. Отдельно распорядиться строгими REQ08/REQ12 и внешними release-шлюзами.
3. Не начинать ST08_14 без отдельной зарезервированной метки авторизации; при
   текущем `not_ready` агент его не рекомендует.

## 42. ST08_13A — перспективная миграция REQ08/REQ12

John принял и закрыл ST08_13 и выбрал отдельную перспективную миграцию
REQ08/REQ12 на текущее хеш-связанное каноническое состояние без переписывания
исторических FAIL. Точное решение достаточно для этой локальной измеримой
задачи; агент не записывает неиспользованную John зарезервированную метку
`NEXT_BLOCK_AUTHORIZED`.

```text
ACCEPTED_BY_JOHN: ST08_13_release_candidate_completion_security_and_readiness_reaudit
TASK_CLOSED: ST08_13_release_candidate_completion_security_and_readiness_reaudit
ST08_13A_task_id: ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration
ST08_13A_status: technical_pass_ready_for_john_acceptance
historical_ST08_13_REQ08: FAIL_PRESERVED
historical_ST08_13_REQ12: BLOCKED_PRESERVED
prospective_v02_REQ08: NOT_EVALUATED
prospective_v02_REQ12: NOT_EVALUATED
reaudit_v02_performed: false
external_actions_performed: 0
```

Новая матрица v02 имеет 24 требования. Двадцать две строки совпадают с v01;
только REQ08/REQ12 получают перспективные методы. REQ08 требует PASS актуальных
проверок и точного сохранения восьми зарегистрированных исторических FAIL без
новых отказов. REQ12 использует полный текущий SHA-256/size manifest вместо
обязательной доступности старых внешних ZIP, сохраняя сведения об их отсутствии
как историческое evidence. Пять файлов ST08_13 остаются побайтно неизменными.

SHA-256 применяется в границе [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final):
он обнаруживает изменение байтов, но не доказывает правильность или авторство.
Версионирование baseline и контроль дельты опираются на [NIST SP 800-53 Rev. 5
CM-2/CM-3](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), а provenance и
целостность release-релевантных файлов — на [NIST SP 800-218 SSDF
1.1](https://csrc.nist.gov/pubs/sp/800/218/final).

`TECHNICAL_STATUS: PASS` относится к миграции, manifest и мутационным
проверкам, а не к проектному completion. Последний фактический readiness verdict
остаётся ST08_13=`FAIL/not_ready`; v02 ещё не применена новым аудитом. ZIP имеет
`SKIPPED`, публикация и репозиторные действия не выполнялись.

## 43. Предлагаемый следующий блок

```text
proposed_next_block: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
ST08_13B_status: proposed_not_authorized
ST08_14_status: proposed_not_authorized
```

Следующий разумный блок должен отдельно получить внешние доказательства:
созданный репозиторий, наблюдаемый hosted CI и серверное secret scanning — без
релиза. Он является внешним действием и не начнётся без отдельной авторизации
John. После него потребуется отдельный re-audit по v02; ни ST08_13B, ни такой
аудит, ни ST08_14 текущей задачей не разрешены.

## 44. Задачи John

1. Принять либо вернуть только ST08_13A.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли ST08_13B; до этого не создавать внешний
   репозиторий и не отправлять проект.
4. Не считать перспективную миграцию новым проектным PASS до отдельного аудита
   v02.

## 45. ST08_13B — внешний bootstrap без релиза

John принял и закрыл ST08_13A и авторизовал точный внешний блок
`ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence`.
Разрешены публичный `Vanargo/ML-CRA`, отправка только include-путей, hosted CI,
server-side secret scanning, private vulnerability reporting, защита `main` и
проверка восстановления свежим clone. Тег, GitHub Release, PyPI и научные
изменения запрещены.

```text
ACCEPTED_BY_JOHN: ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration
TASK_CLOSED: ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration
NEXT_BLOCK_AUTHORIZED: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
ST08_13B_status: technical_pass_ready_for_john_acceptance
hosted_CI_observed: success_run_32832251575_commit_74ccb767f08def2ce4c6cf0441a2ba044db1e66a
external_release_authorized: false
```

Публикуемый Git tree проверяется отдельным path/hash/size manifest и допускает
только правила включения ST08-06-MANIFEST-06/07. Полный локальный inventory
остаётся отдельной политической проверкой и не требует публиковать 45 исключённых
путей. ST08_13A не переписывается и не запускается как вечный current-state gate:
его семь ключевых файлов защищены точными SHA-256, а текущий hosted gate имеет
версию ST08_13B.

Официальный GitHub REST API подтвердил публичный активный репозиторий,
успешный запуск `32832251575` для точного коммита `74ccb767...`, задание
`assurance=success`, включённую private vulnerability reporting и активный
ruleset `21408995` для ветви по умолчанию. Аутентифицированные снимки John
подтверждают Dependabot alerts, secret scanning и push protection. Ruleset не
имеет обхода, запрещает удаление и force push, требует pull request, линейную
историю, разрешение обсуждений, актуальную ветвь и проверку `assurance`.

Свежий клон удалённого репозитория совпал с коммитом и манифестом: 314 путей,
312 хешированных файлов, 0 расхождений, 18/18 защищённых Git blobs сохранены.
Тег, GitHub Release и пакет не публиковались. ST08_13B технически завершён и
ожидает принятия John; отдельный readiness-аудит по v02 не разрешён и не
выполнялся.

## 46. Задачи John

1. Принять либо вернуть ST08_13B.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Не считать публичный репозиторий релизом и отдельно решать вопрос будущего
   re-audit по v02.

## 47. ST08_13C — перспективный release-candidate re-audit v02

John принял и закрыл ST08_13B и авторизовал
`ST08_13C_prospective_release_candidate_v02_reaudit`. Все 24 требования v02
применяются к новому точному Git-кандидату без изменения v01, исторических
ST08_13/ST08_13A/ST08_13B, научных claim/protocol/verdict или числовых
артефактов.

```text
ACCEPTED_BY_JOHN: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
TASK_CLOSED: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
NEXT_BLOCK_AUTHORIZED: ST08_13C_prospective_release_candidate_v02_reaudit
PROJECT_COMPLETION_VERDICT: PASS_if_all_registered_candidate_observations_pass
EXTERNAL_RELEASE_READINESS: BLOCKED_until_John_release_authorization
external_release_authorized: false
```

Текущий манифест v02-кандидата версионируется отдельно от исторических
манифестов и связывает Git paths, SHA-256 и размеры. Cumulative pilot обязан
сохранить ровно восемь старых FAIL без новых отказов. Успешный hosted
`assurance` на точном кандидате обязателен: конфигурация workflow сама по себе
не доказывает выполнение.

После выполнения всех наблюдений допустим итог `24/24 PASS`, `8/8 dimensions
PASS`, `project_completion=PASS`. Внешняя готовность остаётся независимо
`BLOCKED` только шлюзом `John_release_authorization_not_granted`. Такое
разделение следует NIST AI RMF MANAGE 1.1: оценка достижения целей и решение о
продолжении deployment являются связанными, но различными решениями. Нового
обучения или научной репликации ST08_13C не выполняет.

## 48. Задачи John

1. Отправить локальную ветвь ST08_13C и открыть pull request без преждевременного
   слияния.
2. Передать успешный hosted run агенту для завершения evidence record.
3. После итогового отчёта принять либо вернуть ST08_13C.
4. Отдельно решать вопрос релиза; текущая авторизация его не включает.
