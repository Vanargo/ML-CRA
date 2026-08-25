<!--
ML-CRA stage document update v01.
Документ обновлен после фактического запуска вложенной проверки MiniBooNE v01.
Новые номерные отчеты не создаются: решение фиксируется в документе этапа.
-->

# Этап 4 — основной кандидат MiniBooNE и исследовательская проверка

## 1. Назначение документа

Это главный документ этапа 4. Он фиксирует состояние MiniBooNE после минимального исследовательского контура и после вложенной проверки v01. Новые `REPORT_*` для этого шага не создаются.

Основание формата: `roadmap.md`, страница: не применяется, раздел `6. Правила дальнейшей работы`, строки 126–130. Дословный фрагмент: «Новый номерной отчет не создается по умолчанию. Результат шага вносится в `roadmap.md` и/или документ текущего этапа».

## 2. Статус этапа

Статус: завершен для цели выбора основного табличного кандидата и перехода к методологическому стресс-тестированию.

Смысл статуса ограничен: MiniBooNE принимается как проверенный основной кандидат для следующего этапа ML-CRA, но это не означает, что публикационное утверждение уже доказано.

Основание ограничения: `data_registry/openml_candidate_status_definitions.csv`, страница: не применяется, строка 2. Дословный фрагмент: «нельзя трактовать как финально выбранный датасет диссертации или статьи без дальнейшей проверки метаданных, лицензии и протокола воспроизводимости».

## 3. Исходное основание выбора MiniBooNE

MiniBooNE получил рабочий статус `primary_tabular_candidate` после второго диагностического контура.

Основание: `data_registry/dataset_candidate_registry.csv`, страница: не применяется, строка 3. Дословный фрагмент: «openml_miniboone_41150,OpenML,41150,MiniBooNE,...,primary_tabular_candidate,"REPORT_31: promoted to primary stable tabular OpenML candidate after repeated stratified diagnostic contour».

Минимальный исследовательский контур MiniBooNE был выполнен до вложенной проверки: файл результатов содержал 30 строк, то есть 10 внешних блоков × 3 модели; критических предупреждений не было; подбор параметров не выполнялся.

Основание: `docs/archive/reports/REPORT_34_openml_miniboone_research_results_review.md`, страница: не применяется, раздел `2. Контроль полноты`, строки 14–28. Дословный фрагмент: «`openml_miniboone_research_scores.csv`: 30 строк, то есть 10 внешних блоков × 3 модели ... Все строки результатов имеют `hyperparameter_tuning_used=no` ... Критических предупреждений выполнения не найдено».

## 4. Вложенная проверка v01 — протокол

Вложенная проверка выполнена по протоколу `miniboone_nested_cv_v01` для кандидата `openml_miniboone_41150`.

Основание результата: `openml_miniboone_nested_outer_scores.csv`, страница: не применяется, строка 2. Дословный фрагмент: «miniboone_nested_cv_v01,openml_miniboone_41150,41150,MiniBooNE,signal,False,True,True,1,1,1,5,2,3,hist_gradient_boosting».

Внешний контур имел 5 блоков и 2 повтора; внутренний контур для `hist_gradient_boosting` имел 3 блока.

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строка 3. Дословный фрагмент: «hist_gradient_boosting,tuned_candidate,10,5,2,3,20260507,nested_research_draft».

Контрольные модели `dummy_prior` и `logistic_regression` запускались как контрольные модели без внутреннего подбора параметров.

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строки 2–4. Дословные фрагменты: «dummy_prior,control,10,5,2,,20260507,nested_research_draft»; «logistic_regression,control,10,5,2,,20260507,nested_research_draft».

## 5. Контроль полноты вложенной проверки

Все проверки полноты завершились со статусом `pass`.

Основание результата: `openml_miniboone_nested_quality_checks.csv`, страница: не применяется, строки 2–14. Дословные фрагменты: «input_model_space_exists,pass»; «outer_scores_row_count,pass»; «selected_params_row_count,pass»; «summary_row_count,pass»; «feature_count_locked,pass»; «hist_gradient_boosting_selected_params_within_locked_grid,pass»; «environment_required_columns,pass».

Ожидаемое число строк внешних оценок подтверждено: 30 строк.

Основание результата: `openml_miniboone_nested_quality_checks.csv`, страница: не применяется, строка 4. Дословный фрагмент: «outer_scores_row_count,pass,Ожидалось 30 строк внешних оценок».

Ожидаемое число строк выбранных параметров подтверждено: 10 строк.

Основание результата: `openml_miniboone_nested_quality_checks.csv`, страница: не применяется, строка 5. Дословный фрагмент: «selected_params_row_count,pass,Ожидалось 10 строк выбранных параметров».

Замок признаков подтвержден: во всех строках `feature_count=50`.

Основание результата: `openml_miniboone_nested_quality_checks.csv`, страница: не применяется, строка 7. Дословный фрагмент: «feature_count_locked,pass,Во всех строках должно быть feature_count=50».

Предупреждений уровня ошибки или критической проблемы в файле предупреждений нет; файл содержит информационную строку о границах протокола.

Основание результата: `openml_miniboone_nested_warnings.csv`, страница: не применяется, строка 2. Дословный фрагмент: «info,openml_miniboone_41150,miniboone_nested_cv_v01,all,all,all,all,protocol_boundary,Вложенная проверка использует внешний RepeatedStratifiedKFold 5×2; выбор параметров hist_gradient_boosting выполняется только во внутреннем StratifiedKFold».

Среда выполнения зафиксирована отдельным файлом.

Основание результата: `openml_miniboone_nested_environment.csv`, страница: не применяется, строки 2–7. Дословные фрагменты: «python,"3.12.0 ... [MSC v.1935 64 bit (AMD64)]",miniboone_nested_cv_v01»; «sklearn,1.8.0,miniboone_nested_cv_v01»; «pandas,3.0.2,miniboone_nested_cv_v01»; «numpy,2.4.4,miniboone_nested_cv_v01».

## 6. Результаты вложенной проверки

Сводка по основному критерию и ключевым отчетным метрикам:

| Модель | Роль | Внешних блоков | `average_precision_mean` | `average_precision_std` | `roc_auc_mean` | `f1_mean` |
|---|---:|---:|---:|---:|---:|---:|
| `hist_gradient_boosting` | `tuned_candidate` | 10 | 0.959310 | 0.002259 | 0.985045 | 0.902052 |
| `logistic_regression` | `control` | 10 | 0.867408 | 0.002849 | 0.939278 | 0.776990 |
| `dummy_prior` | `control` | 10 | 0.280623 | 0.000011 | 0.500000 | 0.000000 |

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строки 2–4. Дословные фрагменты: «dummy_prior,control,10,5,2,,20260507,nested_research_draft»; «hist_gradient_boosting,tuned_candidate,10,5,2,3,20260507,nested_research_draft»; «logistic_regression,control,10,5,2,,20260507,nested_research_draft».

Численные значения по `hist_gradient_boosting`: `roc_auc_mean=0.985044505024930`, `average_precision_mean=0.9593097386614368`, `f1_mean=0.9020517907645060`.

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строка 3. Дословный фрагмент: «0.98504450502493,0.0006631888473009962,0.9839710361780579,0.986156528792159,0.9593097386614368,0.0022594383363297305».

Численные значения по `logistic_regression`: `roc_auc_mean=0.9392779788132692`, `average_precision_mean=0.8674083259975133`, `f1_mean=0.7769900143084667`.

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строка 4. Дословный фрагмент: «0.9392779788132692,0.0012838057641707586,0.9367205458954988,0.9413248647171036,0.8674083259975133,0.0028487053106193796».

Численные значения по `dummy_prior`: `roc_auc_mean=0.5`, `average_precision_mean=0.2806233852401565`, `f1_mean=0.0`.

Основание результата: `openml_miniboone_nested_summary.csv`, страница: не применяется, строка 2. Дословный фрагмент: «0.5,0.0,0.5,0.5,0.2806233852401565,1.1062141837436812e-05».

## 7. Выбранные параметры `hist_gradient_boosting`

Во всех 10 внешних блоках совпали `learning_rate=0.1`, `max_iter=150`, `max_leaf_nodes=63`. Параметр `l2_regularization` не совпал во всех блоках: значение `0.0` выбрано в 7 блоках, значение `0.01` выбрано в 3 блоках.

Основание результата: `openml_miniboone_nested_selected_params.csv`, страница: не применяется, строки 2–11. Дословные фрагменты: строки 2–4 и 6–8, 10 содержат «""l2_regularization"": 0.0, ""learning_rate"": 0.1, ""max_iter"": 150, ""max_leaf_nodes"": 63»; строки 5, 9, 11 содержат «""l2_regularization"": 0.01, ""learning_rate"": 0.1, ""max_iter"": 150, ""max_leaf_nodes"": 63».

Число внутренних кандидатов параметров в каждом внешнем блоке равно 16.

Основание результата: `openml_miniboone_nested_selected_params.csv`, страница: не применяется, строки 2–11. Дословный фрагмент: каждая строка выбранных параметров заканчивается фрагментом «3,2026050X,16,nested_research_draft», где `16` — число внутренних кандидатов параметров.

## 8. Решение по этапу 4

Решение 4.1. MiniBooNE принимается как проверенный основной табличный кандидат для следующего этапа ML-CRA.

Основания решения: исходный статус `primary_tabular_candidate` уже был зафиксирован в реестре; вложенная проверка v01 завершилась полным набором `pass`-проверок; `hist_gradient_boosting` сохранил преимущество над `logistic_regression` и `dummy_prior` по основному критерию `average_precision`.

Решение 4.2. Статус MiniBooNE не повышается до финального публикационного статуса в этом документе.

Основания ограничения: статус `primary_tabular_candidate` не равен финальному выбору набора данных; текущий результат относится к одному набору данных и одному основному семейству модели; следующий исследовательский шаг должен проверить не только уровень метрик, но и устойчивость методологического утверждения.

Решение 4.3. Актуальный следующий документ этапа: `docs/stages/stage_05_claim_audit_protocol.md`. Исторический второй документ перенесён в `docs/archive/stages/stage_05_methodological_stress_testing_superseded.md`.

Смысл перехода: этап 5 должен проверять не утверждение «модель хорошая», а устойчивость исследовательского вывода при изменении зерен случайности, протоколов разбиения, метрик, стоимости обучения и политики вердикта.

Основание направления в исходной постановке проекта: `docs/stages/stage_05_claim_audit_protocol.md`, страница: не применяется, раздел `3. Основание этапа`, строки 19–21. Дословный фрагмент: «The central object is not a model, not a dataset, and not a metric. The central object is: Experimental claim»; «RQ1. Random seed stability ... RQ2. Split protocol sensitivity ... RQ3. Metric conflict ... RQ4. Effect size ... RQ5. Cost of quality ... RQ6. Claim verdict».

## 9. Закрывающие критерии этапа 4

| Критерий | Статус | Основание |
|---|---:|---|
| Вложенный протокол зафиксирован до запуска | выполнено | `configs/model_spaces/miniboone_hist_gradient_boosting_nested_space.csv`; `data_registry/openml_miniboone_nested_cv_protocol_lock.csv` |
| Пространство параметров зафиксировано до запуска | выполнено | `openml_miniboone_nested_quality_checks.csv`, строка 2: «input_model_space_exists,pass» |
| Кодовое изменение оформлено через «Как было → Как стало» | выполнено | рабочий чат, кодовые ячейки 24–30 добавлялись в этом формате |
| Результаты вложенной проверки сохранены | выполнено | шесть файлов `openml_miniboone_nested_*.csv` загружены пользователем |
| Отдельная проверка подтвердила полноту | выполнено | `openml_miniboone_nested_quality_checks.csv`, строки 2–14: все проверки `pass` |
| Вопрос о повышении статуса MiniBooNE рассмотрен | выполнено частично | принято решение не повышать до финального публикационного статуса на этом этапе |

## 10. Задачи John

1. Сохранить этот документ как `docs/stages/stage_04_primary_candidate_validation.md`, заменив предыдущую версию.
2. Сохранить загруженные результаты вложенной проверки в `data_registry/`, если они еще не сохранены в проекте.
3. Не менять `dataset_candidate_registry.csv` до отдельного решения о статусах кандидатов.
4. Для продолжения использовать актуальный документ `docs/stages/stage_05_claim_audit_protocol.md`; архивный заменённый документ не является текущей инструкцией.
