# Этап 8 — проектная завершённость и готовность к релизу

## 1. Назначение этапа

Stage 8 предназначен для проверки того, соответствует ли текущее состояние
ML-CRA его ограниченной цели и к какому классу внешнего предъявления или
релиза оно объективно готово. Этап не расширяет научный claim Stage 5 и не
считает закрытие Stage 7 автоматическим доказательством готовности всего
проекта.

Главное методологическое правило: project completion — проектная
завершённость, scientific validity — научная состоятельность, software
verification — программная верификация, reproducibility — воспроизводимость,
packaging — упаковка и external release readiness — готовность к внешнему
релизу являются разными измерениями и не подменяют друг друга.

## 2. Исходный статус и полномочия при открытии этапа

При открытии Stage 8 John принял выбор следующего блока и отдельно авторизовал
ST08_01; актуальное состояние последующих блоков фиксируется ниже по хронологии:

```text
ACCEPTED_BY_JOHN: STAGE07_closure_registration_and_next_stage_selection
TASK_CLOSED: STAGE07_closure_registration_and_next_stage_selection
NEXT_BLOCK_AUTHORIZED: ST08_01_project_completion_and_release_readiness_contract_design
stage08_status: active_contract_design
ST08_01_status: technical_pass_ready_for_john_acceptance
ST08_01_implementation_started: YES_COMPLETE
ST08_01_audit_execution_authorized: false
ST08_01_release_authorized: false
```

Этот документ и связанная матрица являются design-результатом — проектом
контракта. Они не содержат фактического project-wide verdict.

## 3. Исходная точка

Source checkpoint: `C:/Users/Vanargo/Downloads/ml-cra_v51.zip`.

```text
size_bytes: 1130649
sha256: 2d3ba63540a4284f1652e9aca57a5ad7fa731d64118be9171c69757a3c706260
entries: 271
files: 269
unique_entries: 271
workspace_missing_extra_mismatch_before_task: 0/0/0
baseline: PASS
```

Stage 7 закрыт John после closure matrix `PASS=7; FAIL=0; BLOCKED=0`.
Научный claim, protocol, policy, verdict, notebook и 18 защищённых артефактов
не меняются в ST08_01.

## 4. Контекст и открытая проектная зависимость

Stage 6 установил статус
`limited_publication_ready_as_documented_evidence_record`: результат можно
показывать как документированный исследовательский пакет доказательств, но не
как готовый воспроизводимый программный продукт. Stage 7 устранил
зарегистрированный разрыв модульного вычислительного слоя, однако Stage 7 имел
локальные инженерные критерии и не повторял project-wide release evaluation.

Поэтому Stage 8 начинается с criteria-first design: сначала фиксируются
требования, методы, источники, семантика результатов и правила агрегации, и
только затем отдельная авторизованная задача применяет их к проекту.

## 5. Профессиональная и источниковая основа

1. ISO/IEC/IEEE 15288:2023 задаёт общую систему процессов жизненного цикла и
   управляемых переходов с участием заинтересованных сторон.
2. ISO/IEC/IEEE 29148:2018 требует формализованных, проверяемых и
   трассируемых requirements — требований и связанных information items.
3. ISO/IEC 25010:2023 предоставляет модель качества продукта для задания
   целей тестирования, критериев качества и приёмки.
4. ISO/IEC 25040:2024 предоставляет рамку оценки качества ICT-продукта и
   запрещает выдавать общий framework за конкретный метод тестирования.
5. NASA NPR 7123.1D §5.2.3 и Appendix G связывает завершение review с
   disposition замечаний, success criteria, отслеживанием действий и решением
   полномочного лица.
6. NIST AI RMF 1.0 разделяет GOVERN, MAP, MEASURE, MANAGE; MANAGE 1.1 требует
   определить, достигает ли система заявленной цели и следует ли продолжать
   development/deployment.
7. NIST SP 500-234 и NIST IR 8397 поддерживают V&V, traceability,
   автоматизированные, структурные, black-box и historical checks.
8. NIST SP 800-218 SSDF поддерживает release integrity, архивирование
   релизных файлов и provenance — происхождение компонентов.
9. National Academies связывает вычислительную воспроизводимость с
   обнаружением ошибок и целостностью научных результатов.
10. Python Packaging User Guide определяет `pyproject.toml`, build-system,
    project metadata и dependency declarations как стандартный packaging
    interface; GitHub Docs фиксирует, что отсутствие лицензии не даёт
    разрешения на использование/распространение; Citation File Format задаёт
    машиночитаемые сведения о цитировании research software.
11. `bio_inspired_project_engineering_standard_v02.md` применяется через
    MAPE-K, гомеостатические инварианты, evidence record, fail-closed validation
    и явные ручные границы решений.

Внешние источники поддерживают методы и критерии, но не доказывают локальный
результат ML-CRA. Локальный PASS может быть получен только будущим исполняемым
аудитом.

## 6. MAPE-K контур Stage 8

- Monitor — инвентаризация текущих целей, результатов Stage 1–7, интерфейсов,
  документации, зависимостей, лицензий, citation, security и архивов.
- Analyze — раздельная оценка 24 требований, противоречий, отсутствующих
  доказательств, residual risks и release blockers.
- Plan — формирование минимальных corrective blocks только после фактического
  audit; отсутствие файла не превращается автоматически в разрешение его
  создать.
- Execute — отдельные John-authorized изменения, проверки и повторный audit.
- Knowledge — требования, evidence, dispositions, hashes, decisions и
  checkpoints в canonical registry.

## 7. Нормативная матрица требований

Канонический машиночитаемый контракт:

```text
configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v01.csv
```

Матрица содержит ровно 24 уникальных требования в 8 измерениях:

| Dimension | Требований | Предмет |
|---|---:|---|
| D01 | 3 | миссия и scope — границы |
| D02 | 3 | научные evidence и язык claim |
| D03 | 3 | software verification и supported interfaces |
| D04 | 3 | reproducibility и provenance |
| D05 | 3 | документация и usability |
| D06 | 3 | packaging и distribution |
| D07 | 3 | license, dataset rights и citation |
| D08 | 3 | governance, security и release decision |

Обязательные поля каждой строки: `requirement_id`, `dimension_id`,
`dimension_name`, проверяемое требование, authoritative basis, локальные пути
evidence, verification method, правила `PASS`, `FAIL`, `BLOCKED`, роль в
агрегации и design status.

Все `design_status` в ST08_01 равны `NOT_EVALUATED`. Иное значение означало бы
несанкционированное выполнение научной/инженерной оценки.

## 8. Семантика результатов и правила агрегации

Допустимые статусы фактического требования в будущем аудите:

- `PASS` — требование проверено указанным методом и правило PASS выполнено;
- `FAIL` — наблюдаемое состояние нарушает fail rule;
- `BLOCKED` — вывод невозможен из-за отсутствующего prerequisite или решения
  John;
- `SKIPPED` — только для явно неприменимого conditional requirement с
  зарегистрированным основанием;
- `NOT_EVALUATED` — design-only состояние до запуска аудита.

Fail-closed правила:

1. Dimension получает `PASS`, только если все mandatory requirements имеют
   `PASS`, а conditional — `PASS` либо обоснованный `SKIPPED`.
2. Любой `FAIL` делает dimension `FAIL`.
3. При отсутствии `FAIL`, но наличии `BLOCKED` или `NOT_EVALUATED`, dimension
   получает `BLOCKED`.
4. `project_completion_verdict=PASS` требует PASS D01–D05 и D08; D06–D07
   оцениваются отдельно и могут блокировать конкретный release class.
5. `external_release_readiness=PASS` требует PASS всех D01–D08 и ноль
   неурегулированных release-blocking residual risks.
6. Научный PASS D02 не компенсирует FAIL другого dimension.
7. Только John может принять итоговый verdict, выбрать release class и
   разрешить внешнюю публикацию или релиз.

## 9. Golden design будущего audit artifact

Будущий audit evidence должен иметь:

```text
schema_version: stage08_project_completion_and_release_readiness_audit_v01
requirements_total: 24
dimensions_total: 8
allowed_requirement_statuses: PASS|FAIL|BLOCKED|SKIPPED
dimension_results: 8
project_completion_verdict: PASS|FAIL|BLOCKED
external_release_readiness: PASS|FAIL|BLOCKED
release_class: internal_research_snapshot|documented_evidence_package|source_release|python_distribution|not_ready
open_findings: explicit list
residual_risks: explicit list
john_decision_required: true
```

Положительный golden-design проверяет точную форму и независимый пересчёт
агрегатов. Отрицательные мутации обязаны отклонять как минимум: duplicate ID,
unknown dimension/status, missing rule/source/path/method, преждевременный
`PASS`, `SKIPPED` mandatory requirement, неправильный aggregate, release PASS
при неположительном dimension, silent finding, protected hash mismatch и
автоматически приписанное решение John.

## 10. Защищённые артефакты и запрещённые действия

В ST08_01 защищены notebook, десять модулей `src/mlcra`, claim, verdict policy,
Stage 5 protocol и четыре ключевых scientific CSV — всего 18 SHA-256.

Не разрешены:

- фактическая оценка 24 требований;
- создание audit evidence с `PASS/FAIL/BLOCKED`;
- исправление выявляемых будущим audit пробелов;
- обучение, сеть и изменение datasets/claims/protocols/policies/verdicts;
- создание README, LICENSE, CITATION, pyproject, requirements, distribution;
- внешний release, публикация, deployment, CLI/dashboard expansion;
- автоматическое принятие ST08_01 или авторизация следующего блока.

## 11. Технические критерии завершения ST08_01

ST08_01 технически выполнен, если:

1. существует этот нормативный документ Stage 8;
2. CSV имеет 24 уникальные строки, D01–D08 по 3, полную схему и только
   `NOT_EVALUATED`;
3. семантика и aggregation rules однозначны и fail-closed;
4. JSON evidence сохраняет source v51, authoritative support, golden design,
   18 protected hashes, planned/actual changes и limits;
5. focused gate независимо проверяет структуру, hashes и отсутствие audit
   execution;
6. baseline и cumulative pilot проходят;
7. roadmap синхронизирован;
8. scientific artifacts, training, network и external side effects равны 0.

## 12. Предлагаемый следующий блок

После принятия ST08_01 логически следует только применение контракта без
ремедиации:

```text
proposed_next_block: ST08_02_project_completion_and_release_readiness_baseline_audit
ST08_02_status: proposed_not_authorized
ST08_02_implementation_started: NO
```

Измеримый результат ST08_02: оценить все 24 требования, независимо пересчитать
8 dimension verdicts, project completion и release readiness; зарегистрировать
каждый `PASS/FAIL/BLOCKED/SKIPPED`, findings и residual risks; не исправлять
пробелы и не выполнять release.

## 13. Задачи John

1. Принять либо вернуть design-контракт ST08_01.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED` для ST08_01.
3. Только если baseline audit согласован, отдельно присвоить
   `NEXT_BLOCK_AUTHORIZED: ST08_02_project_completion_and_release_readiness_baseline_audit`.
4. Не разрешать release или corrective implementation на основании одного
   design-блока.

## 14. ST08_02 — baseline audit проектной завершённости и готовности к релизу

### 14.1. Полномочие, профиль и граница

John принял и закрыл ST08_01 и отдельно авторизовал применение контракта:

```text
ACCEPTED_BY_JOHN: ST08_01_project_completion_and_release_readiness_contract_design
TASK_CLOSED: ST08_01_project_completion_and_release_readiness_contract_design
NEXT_BLOCK_AUTHORIZED: ST08_02_project_completion_and_release_readiness_baseline_audit
ST08_02_status: technical_fail_ready_for_john_acceptance
ST08_02_implementation_started: YES_COMPLETE
ST08_02_remediation_authorized: false
ST08_02_release_authorized: false
```

Профиль задачи — `SCIENTIFIC_VALIDATION`: аудит проверяет evidence —
доказательства, требования и проектные verdict — вердикты. Он не исправляет
объект оценки, не выполняет обучение и не создаёт release artifact — релизный
артефакт. Source checkpoint — `ml-cra_v52.zip`, SHA-256
`56e51b556ef40612c5d1b1ff7930d91ff12034d5553a0ee7ac1b407310ed80b3`,
размер `1149362`, 275/273/275 entries/files/unique. До изменений checkpoint и
рабочая копия совпали 273/273 без missing/extra/mismatch.

### 14.2. Метод и профессиональное основание

Применён requirements traceability matrix — матрица трассируемости требований:
каждая строка ST08-REQ-01–24 сопоставлена с наблюдаемым evidence, методом,
статусом, finding — замечанием и disposition — решением/состоянием. Агрегаты
пересчитаны независимо по fail-closed правилам §8.

Это соответствует MAPE-K из
`bio_inspired_project_engineering_standard_v02.md`: ST08_02 выполняет Monitor
и Analyze и сохраняет Knowledge, а Plan/Execute корректирующих изменений
требует отдельного решения John. ISO/IEC/IEEE 15288:2023 поддерживает
управляемые жизненные переходы; NIST AI RMF MANAGE 1.1 требует определить,
достигается ли заявленная цель и следует ли продолжать development/deployment;
NASA NPR 7123.1D связывает завершение review с success criteria, disposition
замечаний и решением полномочного лица. Внешние источники поддерживают метод,
но локальные статусы получены только из project files и наблюдаемых команд.

### 14.3. Наблюдаемые результаты требований

Канонический evidence:
`data_registry/stage08_project_completion_and_release_readiness_audit_evidence_v01.json`.

```text
stage08_requirement_results: PASS=7;FAIL=7;BLOCKED=10;SKIPPED=0
stage08_dimension_results: PASS=1;FAIL=4;BLOCKED=3
project_completion_verdict: FAIL
external_release_readiness: FAIL
release_class: not_ready
open_findings: 9
residual_risks: 5
```

| Dimension | Requirement statuses | Verdict | Краткое основание |
|---|---|---|---|
| D01 mission/scope | 1 PASS, 1 FAIL, 1 BLOCKED | FAIL | цель ограничена корректно, но stage traceability содержит битые current paths, а ожидаемые outputs не классифицированы John |
| D02 scientific evidence | 3 PASS | PASS | claim→protocol/config→evidence→verdict целостен; scientific invariants и bounded public language прошли |
| D03 software verification | 2 PASS, 1 BLOCKED | BLOCKED | модульный слой и cumulative verification прошли, но supported external interface не определён |
| D04 reproducibility/provenance | 1 PASS, 2 FAIL | FAIL | archive/provenance целостны, но нет reconstructible dependency spec и clean-copy command |
| D05 documentation/usability | 3 FAIL | FAIL | нет root README, complete instructions и path-valid current documentation |
| D06 packaging/distribution | 3 BLOCKED | BLOCKED | release class и применимость Python distribution не выбраны John |
| D07 legal/citation | 1 FAIL, 2 BLOCKED | FAIL | license/citation требуют John; dataset license metadata конфликтует |
| D08 governance/security/release | 3 BLOCKED | BLOCKED | findings видимы, но dispositions и release security assurance не завершены |

Положительный D02 означает только, что ограниченная научная цепочка MiniBooNE
сохраняется в зарегистрированном контуре. Он не доказывает project completion
или release readiness и не компенсирует другой dimension.

### 14.4. Девять открытых findings

1. `ST08-FIND-01`: девять уникальных current documentation references не
   разрешаются; затронуты ST08-REQ-02 и ST08-REQ-15.
2. `ST08-FIND-02`: CLI, dashboard, bilingual docs, public repository и
   supported external interface не имеют актуальной John-approved
   классификации.
3. `ST08-FIND-03`: отсутствуют dependency specification и проверяемая
   clean-copy installation/reproduction instruction.
4. `ST08-FIND-04`: отсутствует root entry document.
5. `ST08-FIND-05`: release class и Python-distribution applicability не
   определены.
6. `ST08-FIND-06`: нет John-approved license/non-open policy и citation
   identity.
7. `ST08-FIND-07`: локальные записи называют MiniBooNE `CC0`, тогда как
   актуальная официальная страница UCI указывает `CC BY 4.0` и DOI
   `10.24432/C5QC87`; redistribution заблокирован до reconciliation — сверки.
8. `ST08-FIND-08`: secret-pattern scan дал 0 findings и `pip check` PASS, но
   dependency inventory/security policy отсутствуют, а `pip-audit` недоступен.
9. `ST08-FIND-09`: все non-PASS видимы, но решения владельца и принятие
   результата остаются за John.

### 14.5. Проверки, ограничения и результат

Исполняемый gate проверяет exact 24 IDs, полную семиполевую result schema,
связь каждого non-PASS с одним из девяти findings, owner/consequence/
disposition, независимую агрегацию 8 dimensions, 18 protected hashes, source
v52, exact change scope и 14/14 отрицательных мутаций ST08_01.

Новые модели не обучались; scientific artifacts, claim, protocol, policy,
verdict и release state не изменялись. ST08_02 технически корректен именно как
отрицательный baseline verdict: подгонка критериев или исправление gaps внутри
аудита было бы методологической ошибкой.

```text
TECHNICAL_STATUS: FAIL
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

`FAIL` относится к readiness объекта аудита, а не к корректности процедуры:
verifier gate обязан получить PASS, подтверждая, что отрицательный verdict
вычислен и зарегистрирован правильно.

## 15. Предлагаемый следующий блок

Ближайшее действие должно сначала разрешить решения владельца, от которых
зависят границы любого последующего remediation:

```text
proposed_next_block: ST08_03_project_scope_release_class_and_owner_decision_resolution
ST08_03_status: proposed_not_authorized
ST08_03_implementation_started: NO
```

ST08_03 не должен создавать README, package, license или release. Его
измеримый результат — зарегистрировать решения John по текущей MVP-границе,
supported interface, release class, Python distribution, license/non-open
policy, citation identity и приоритету девяти findings; затем определить
минимальные корректирующие блоки без смешения независимых рисков.

## 16. Задачи John

1. Принять либо вернуть объективный отрицательный audit ST08_02.
2. Не интерпретировать D02 PASS как готовность проекта или релиза.
3. При согласии с owner-decision-first продолжением отдельно авторизовать
   `ST08_03_project_scope_release_class_and_owner_decision_resolution`.
4. Не выполнять внешний release и не выбирать лицензию автоматически.

## 17. ST08_03 — разрешение решений владельца

John принял и закрыл `ST08_02`, затем отдельно авторизовал
`ST08_03_project_scope_release_class_and_owner_decision_resolution`. После
человеко-понятной расшифровки D01–D09 John принял все продуктовые, научные,
интерфейсные, воспроизводимые и приоритетные положения, выбрал MIT License,
указал публичное имя `Иван Полищук` и подтвердил поэтапную релизную политику.

```text
ACCEPTED_BY_JOHN: ST08_02_project_completion_and_release_readiness_baseline_audit
TASK_CLOSED: ST08_02_project_completion_and_release_readiness_baseline_audit
NEXT_BLOCK_AUTHORIZED: ST08_03_project_scope_release_class_and_owner_decision_resolution
ST08_03_implementation_started: YES_COMPLETE
```

Человеко-понятный смысл: отрицательный baseline-аудит ST08_02 принят как
корректное описание незавершённого проекта. ST08_03 разрешён и технически
выполнен, но его принятие и закрытие ещё принадлежат John. Этот блок не исправлял
выявленные продуктовые пробелы и не выполнял публикацию.

## 18. Зарегистрированные решения D01–D09

| Решение | Принятое содержание | Практическое последствие |
|---|---|---|
| D01 | Сохранить исходную полную цель Stage 1 | Для `1.0.0` обязательны технический отчёт, воспроизводимый контур, CLI, панель, RU/EN-документация, публичный GitHub, классификация и регрессия |
| D02 | Сохранить ограниченный научный язык | MiniBooNE-доказательство не превращается в универсальное утверждение и не заменяет продуктовую проверку |
| D03 | Поддерживаемый внешний интерфейс — универсальный CLI | Следующий design-блок должен определить ограниченные входы, выходы, ошибки и пользовательские сценарии CLI |
| D04 | Цель — публичный GitHub-продукт | Частная передача ZIP научному руководителю или проверяющему исключена как несуществующий сценарий |
| D05 | Требуется воспроизводимая Python-дистрибуция | Чистая установка, зависимости, сборка и запуск становятся релизными шлюзами |
| D06 | MIT License | Файл лицензии будет создан отдельным разрешённым блоком; сторонние условия не переопределяются |
| D07 | Автор `Иван Полищук`; ORCID `https://orcid.org/0009-0005-6596-0605`; GitHub `Vanargo` | Будущий `CITATION.cff` и публичные метаданные имеют однозначную идентичность |
| D08 | Не включать raw/cache; согласовать производные доказательства | Конфликт OpenML/UCI должен быть устранён до публикации |
| D09 | Риск- и dependency-first порядок | Сначала граница продукта и права, затем упаковка/интерфейсы, документация/безопасность, повторный аудит и публикация |

Stage 1 прямо сохраняет табличную классификацию и регрессию в MVP и перечисляет
CLI, dashboard, двуязычную документацию и публичный GitHub среди ожидаемых
результатов. NIST AI RMF Core поддерживает сначала определение контекста,
пользователей, требований и границ, а затем измерение и приоритизированное
управление рисками. PyPA задаёт официальный контракт Python project metadata;
GitHub Docs требует явной лицензии для разрешения открытого повторного
использования; CFF задаёт машиночитаемое цитирование; UCI остаётся внешним
источником условий MiniBooNE.

Машиночитаемая запись решений:
`data_registry/st08_03_project_scope_release_class_owner_decision_evidence_v01.json`.

## 19. Целевая релизная политика

```text
TARGET_RELEASE_CLASS: public_installable_python_distribution
TARGET_REPOSITORY: https://github.com/Vanargo/ML-CRA
PROJECT_LICENSE: MIT
CREATOR: Иван Полищук
ORCID: https://orcid.org/0009-0005-6596-0605
FIRST_SUPPORTED_RELEASE: 0.1.0
VERSION_1_0_0_REQUIRES: classification+regression+dashboard+bilingual_docs
PYPI_PUBLICATION: deferred_owner_decision
EXTERNAL_RELEASE_AUTHORIZED_IN_ST08_03: false
```

Человеко-понятный смысл: проект должен стать открытым устанавливаемым Python-
продуктом. Публичный development repository допускается только после минимальных
правовых, документальных и безопасностных проверок; `0.1.0` требует работающий
устанавливаемый CLI; `1.0.0` требует всю принятую границу Stage 1. ST08_03 не
создавал GitHub-репозиторий, LICENSE, `CITATION.cff`, package или релиз.

## 20. Граница следующей ветки развития

Ветка `stage08_public_productization_release_train_v01` переводит ограниченный
исследовательский evidence package — пакет доказательств — в публичный,
устанавливаемый и проверяемый продукт без расширения зарегистрированного
научного claim — утверждения.

В границу входят:

1. сценарии внешнего пользователя и контракт универсального CLI;
2. табличная классификация и регрессия;
3. Python packaging, clean install и воспроизводимые зависимости;
4. MIT, `CITATION.cff`, происхождение и условия MiniBooNE;
5. единое проверенное ядро для CLI и будущей панели;
6. русская и английская документация;
7. CI, безопасность, release candidate audit и отдельная публикация.

Не входят универсальное превосходство моделей, full AutoML, крупные deep
learning benchmarks, hosted production service и изменение принятого
MiniBooNE claim/protocol/policy/verdict.

Первый блок ветки:

```text
proposed_next_block: ST08_04_public_product_scope_and_release_train_contract_design
ST08_04_status: proposed_not_authorized
ST08_04_implementation_started: NO
```

Человеко-понятный смысл: следующий блок должен только зафиксировать требования,
пользовательские сценарии, CLI-контракт, объективные метрики готовности и
релизные шлюзы. Он пока не разрешён и не должен реализовывать CLI, dashboard,
LICENSE, GitHub-публикацию или научное обучение.

## 21. Изменение правил коммуникации и отчётности

По прямому решению John машиночитаемые статусы теперь всегда сопровождаются
простым русским объяснением смысла, основания, последствия и требуемого действия.
Одновременно из действующих `AGENTS.md` и `ml-cra-stage-gate/SKILL.md` удалено
требование фиксированного шаблона показа исходного и нового фрагмента кода.

Это не отменяет обязательные actual diff review — проверку фактической разницы,
planned/actual change reconciliation — сверку плана с журналом изменений,
регрессионные проверки и трассируемое evidence. Старые упоминания прежнего
шаблона в Stage 4–7 сохранены только как исторические доказательства закрытых
задач и не управляют будущей работой.

## 22. Проверки и ограничения ST08_03

ST08_03 изменяет только восемь зарегистрированных путей. Научные notebook,
модули `src/mlcra/`, claim, protocol, policy, golden master и научные CSV
защищены прежними 18 SHA-256. Training, dataset network access и external
release actions равны нулю. README, LICENSE, `CITATION.cff`, `pyproject.toml`,
distribution artifacts и GitHub repository не создавались.

Первый полный pilot дал единственный `FAIL` нового ST08_03-gate: проверочный код
ошибочно требовал одинаковый регистр служебных меток в Stage 8 и roadmap, где
заранее использовались соответственно `PROJECT_LICENSE` и `project_license`.
Проверка исправлена на раздельную валидацию двух представлений без изменения
решений или порогов. Повторный pilot должен завершаться `PASS`; исходная попытка
сохранена в evidence record и не скрыта.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Человеко-понятный смысл: все решения владельца однозначно зарегистрированы,
граница следующей ветки определена, а научное состояние не изменено. Результат
готов к рассмотрению John, но ST08_03 ещё не принят и не закрыт; ST08_04 ещё не
авторизован.

## 23. Задачи John

1. Принять либо вернуть ST08_03.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Для продолжения в новом чате отдельно решить, авторизовать ли
   `ST08_04_public_product_scope_and_release_train_contract_design`.

## 24. ST08_04 — контракт публичного продукта и релизной последовательности

### 24.1. Полномочие, профиль и измеримый результат

В текущем чате `ML-CRA/Продолжение работы с ST08_04` John сообщил, что работа
остановилась после закрытия ST08_03 и формирования `ml_cra_v54.zip`, и прямо
поручил продолжить с ST08_04. Это регистрирует принятие и закрытие предыдущего
блока и авторизацию design-задачи:

```text
ACCEPTED_BY_JOHN: ST08_03_project_scope_release_class_and_owner_decision_resolution
TASK_CLOSED: ST08_03_project_scope_release_class_and_owner_decision_resolution
NEXT_BLOCK_AUTHORIZED: ST08_04_public_product_scope_and_release_train_contract_design
ST08_04_status: technical_pass_ready_for_john_acceptance
ST08_04_implementation_started: YES_COMPLETE_DESIGN_ONLY
ST08_04_product_implementation_authorized: false
ST08_04_external_release_authorized: false
ST08_04_new_training_authorized: false
```

Человеко-понятный смысл: решения владельца ST08_03 приняты, а ST08_04 разрешён
и технически завершён как проектирование. Реальный CLI, Python package,
dashboard, README, LICENSE, CITATION, GitHub-публикация и обучение не создавались.
John должен рассмотреть именно контракт, а не готовый продукт.

Профиль — `CHANGE`: изменяется каноническое проектное состояние и добавляется
машинно-читаемый контракт, но не программное или научное поведение. Измеримый
результат — однозначно определить шесть выходов, ранее требовавшихся ST08_03:
сценарии заинтересованных сторон, CLI-входы/выходы/отказы, границу классификации
и регрессии, три релизных шлюза, трассировку Stage 1 и объективные метрики.

### 24.2. Исходное состояние и ограничение контрольной точки

`ml_cra_v54.zip` не найден в проверенных `Desktop`, `Documents`, `Downloads` и
корне проекта, поэтому его размер, состав и SHA-256 не объявляются
подтверждёнными. Вместо выдуманного соответствия до изменений зафиксирован
независимый workspace-manifest — манифест рабочей копии:

```text
expected_source_checkpoint: ml_cra_v54.zip
source_checkpoint_available: false
prechange_workspace_files_excluding_venv_git_cache: 277
prechange_workspace_manifest_sha256: a3dee65d92cc155bb99c97ac732f258c58ac95b52ba10d38ace141597787a1e7
baseline_before_change: PASS
protected_artifacts_before_change: 18/18
```

Человеко-понятный смысл: рабочая копия пригодна для ограниченного design-блока и
все научные эталоны совпадают, но нельзя утверждать её побайтовое равенство
недоступному v54. Новый checkpoint должен стать следующей проверяемой точкой.

### 24.3. Канонический контракт и требования

Канонический машиночитаемый результат:

```text
configs/project_readiness/stage08_public_product_scope_and_release_train_contract_v01.json
```

Контракт содержит ровно:

- 5 сценариев `ST08-SCN-01`–`05`: внешний исследователь, независимый reviewer —
  проверяющий, release maintainer — сопровождающий релиза, пользователь
  регрессии и читатель dashboard;
- 3 команды одного устанавливаемого интерфейса: `audit`, `verify`, `doctor`;
- 6 кодов завершения с разделением успешного отрицательного научного вердикта,
  ошибки ввода, недостаточности evidence, runtime и нарушения целостности;
- 3 fail-closed релизных шлюза: public development, `0.1.0`, `1.0.0`;
- 12 объективных метрик, 8 строк трассировки выходов Stage 1 и 10 только
  предложенных будущих блоков.

Каждый сценарий имеет пользователя, цель, контекст, команду, входы, наблюдаемый
результат, non-goal — исключённую цель — и правило приёмки. Это реализует
requirements information items из
[ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html), а определение
пользователей, назначения, контекста и измерений следует MAP/MEASURE/MANAGE
[NIST AI RMF 1.0](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/).

### 24.4. Граница универсального CLI

`Universal CLI` означает единый поддерживаемый командный интерфейс продукта, а
не универсальность научного claim или поддержку произвольного ML-кода.

```text
mlcra audit --spec claim.json --data data.csv --output-dir run
mlcra verify --bundle run
mlcra doctor --format json
```

Будущая дистрибуция обязана объявить команду через `[project.scripts]`:
[PyPA `pyproject.toml`](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
связывает эту таблицу с `console_scripts`, а
[entry-points specification](https://packaging.python.org/en/latest/specifications/entry-points/)
определяет устанавливаемую оболочку команды и возврат process exit code — кода
завершения процесса.

Вход данных ограничен локальным UTF-8 CSV с заголовком, уникальными именами
полей и явно указанной целью. Claim specification — спецификация утверждения —
является JSON по версионированной схеме
[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12).
Недоверенные `pickle`, `joblib`, `cloudpickle`, произвольные Python import path,
URL и сеть запрещены по умолчанию. Основание — официальная
[Python `pickle` documentation](https://docs.python.org/3/library/pickle.html),
которая предупреждает, что unpickle недоверенных данных может выполнить
произвольный код.

Exit code `0` означает корректно завершённый аудит и включает положительный,
отрицательный или fragile — хрупкий — вердикт. Код `4` означает, что evidence
недостаточно для допустимого вердикта. Такое разделение не позволяет смешать
научный результат с исправностью программы. Код `2` сохранён для CLI usage
errors согласно официальному поведению
[Python `argparse`](https://docs.python.org/3/library/argparse.html).

### 24.5. Граница классификации и регрессии

Для `0.1.0` поддерживается только ограниченный вертикальный контур бинарной
табличной классификации. Регрессия и multiclass должны fail-closed отклоняться;
это честнее, чем объявлять поддержку, которой текущая реализация и evidence не
подтверждают. Для `1.0.0` обязательны бинарная классификация и табличная
регрессия; multiclass остаётся за отдельным решением.

Пользователь может выбирать только версионированные allowlisted — разрешённые
контрактом — идентификаторы моделей, preprocessing и метрик. Возможность
передать исполняемый объект не входит в поддерживаемую границу. Регрессия требует
будущих отдельно зарегистрированных dataset, claim, protocol, metrics, verdict
policy, software verification и scientific validation; существующий MiniBooNE
claim не переинтерпретируется как доказательство регрессионной поддержки.

### 24.6. Релизные шлюзы и SemVer

Public development допускается только после правового, документального,
безопасностного минимума и отдельной авторизации John. `0.1.0` требует
стандартные metadata, sdist/wheel, полный clean-install matrix, команды
`audit/verify/doctor`, отрицательные тесты, RU/EN quickstart, ноль неразрешённых
критических/высоких security findings и повторный readiness audit. `1.0.0`
дополнительно требует регрессию, dashboard на том же application core,
полную двуязычную документацию, стабильный public API и PASS Stage 8.

[PyPA packaging flow](https://packaging.python.org/en/latest/flow/) разделяет
source tree, metadata, sdist/wheel, публикацию и установку; поэтому успешная
сборка wheel не означает публикацию. [Semantic Versioning 2.0.0](https://semver.org/)
определяет `0.y.z` как initial development с нестабильным API, а `1.0.0` — как
границу объявленного public API. [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
обосновывает включение security practices в жизненный цикл до релиза.

### 24.7. Объективные метрики и предел вывода о полезности

Release gate требует `1.0` для P0 scenario pass rate, requirements trace,
clean-environment pass, negative mutation rejection, diagnostic completeness,
artifact provenance и documentation walkthrough; hidden network/manual code
edits, release blockers и dashboard/CLI mismatch должны быть `0`.

Эти пороги проверяют контрактную полноту, а не гарантируют общественную пользу.
[ISO 9241-11:2018](https://www.iso.org/standard/63500.html) рассматривает
usability как результат использования определёнными пользователями для
определённых целей в определённом контексте и не задаёт универсальный метод или
порог. Поэтому `ST08-MET-12` требует записывать completion time, ошибки и
feedback внешних walkthrough, но не выдумывает непроверенный численный порог.
Фактическая польза сообществу остаётся неизвестной до наблюдаемого использования.

### 24.8. Risk/dependency-first релизная последовательность

Контракт трассирует восемь выходов Stage 1 к будущим блокам и трём шлюзам.
Порядок: сначала MiniBooNE lineage/terms, затем MIT/CITATION, packaging и clean
environment, classification CLI, CI/security, документация, regression,
dashboard, повторный audit и только отдельное внешнее действие.

Все `ST08_05`–`ST08_14` имеют статус `proposed_not_authorized`. Они являются
архитектурной картой зависимостей, а не разрешением выполнить десять задач.
Первым предлагается только устранение правовой неопределённости MiniBooNE,
поскольку публикация кода и производных evidence до reconciliation создала бы
необратимый риск неправильных условий распространения.

### 24.9. Защищённое состояние, проверки и ограничения

Notebook, десять модулей, claim, verdict policy, Stage 5 protocol и четыре
ключевых scientific CSV сохранены по прежним 18 SHA-256. Source implementation,
training, dataset network access, scientific artifact changes и release actions
равны нулю. ST08_04 не подтверждает CLI usability, classification product
validity, regression validity или readiness любого релизного шлюза: все это
требует будущего наблюдаемого выполнения.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Человеко-понятный смысл: design-контракт внутренне согласован, ограничивает
поддержку наблюдаемыми доказательствами и готов к рассмотрению. `PASS` не
означает готовность продукта или релиза; `READY_FOR_JOHN_ACCEPTANCE` означает,
что John может принять или вернуть только ST08_04. Автоматический переход к
ST08_05 запрещён.

## 25. Предлагаемый следующий блок

```text
proposed_next_block: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
ST08_05_status: proposed_not_authorized
ST08_05_implementation_started: NO
```

Человеко-понятный смысл: ближайшая зависимость — сверить происхождение,
лицензию, атрибуцию и допустимость распространения каждого MiniBooNE-derived
artifact. Это предложение не разрешает менять registry, создавать LICENSE или
публиковать репозиторий.

## 26. Задачи John

1. Принять либо вернуть design-контракт ST08_04.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только первый блок
   `ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition`.
4. Не считать перечень ST08_05–ST08_14 пакетной авторизацией и не разрешать
   внешний релиз на основании design PASS.

## 27. ST08_05 — происхождение MiniBooNE, лицензионный конфликт и релизные артефакты

### 27.1. Полномочие и граница

John прямо принял ST08_04, поручил двигаться далее и установил Codex-only модель
работы без браузерного ChatGPT. В контексте единственного следующего блока,
предложенного ST08_04, это разрешает только ST08_05:

```text
ACCEPTED_BY_JOHN: ST08_04_public_product_scope_and_release_train_contract_design
TASK_CLOSED: ST08_04_public_product_scope_and_release_train_contract_design
NEXT_BLOCK_AUTHORIZED: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
ST08_05_status: technical_pass_ready_for_john_acceptance
ST08_05_implementation_started: YES_COMPLETE
ST08_06_status: proposed_not_authorized
external_release_authorized: false
```

Человеко-понятный смысл: ST08_04 принят и закрыт; выполнено только исследование
происхождения, условий и состава MiniBooNE-derived артефактов. `LICENSE`,
`CITATION.cff`, публичный manifest и репозиторий не создавались, а ST08_06 не
начат.

### 27.2. Проверенная цепочка и конфликт официальных метаданных

Зафиксирована цепочка UCI dataset 199 → OpenML mirror 41150 → локальное
получение → зарегистрированные протоколы и агрегированные результаты ML-CRA.
[OpenML API](https://www.openml.org/api/v1/json/data/41150) называет Byron Roe,
target `signal`, UCI original URL и лицензию `CC0`. Текущая официальная
[страница UCI](https://archive.ics.uci.edu/dataset/199/miniboone+particle+identification)
называет Byron Roe, DOI `10.24432/C5QC87` и `CC BY 4.0`.

Конфликт не разрешён молчаливым выбором удобного значения. Поскольку UCI —
указанный OpenML первичный источник, а полномочие загрузившего запись OpenML
лица применить CC0 не доказано, публичный контур консервативно управляется по
CC BY 4.0. Это fail-closed управление риском, а не юридическое заключение.
[CC0 legal code](https://creativecommons.org/publicdomain/zero/1.0/legalcode)
ограничивает waiver объёмом прав заявителя, а
[CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en)
требует предоставленные creator/source/license/change сведения. Поэтому
обязательная атрибуция включает Byron Roe, название, UCI, DOI, CC BY 4.0,
исходную ссылку, OpenML mirror 41150, выполненные преобразования и отсутствие
сырых данных в поставке; платформенная ссылка OpenML сохраняется согласно
[OpenML Terms and Citation](https://beta.openml.org/terms).

### 27.3. Полный инвентарь и решения о включении

Машиночитаемый контракт:
`configs/project_readiness/st08_05_miniboone_lineage_license_attribution_and_release_asset_disposition_v01.json`.
Приоритетные правила классифицируют каждый текущий текстовый файл с `MiniBooNE`
или `41150` ровно один раз. После добавления ST08_05 подтверждено 157 файлов:

```text
CONDITIONAL_IMPLEMENTATION: 17
CONDITIONAL_WITH_ATTRIBUTION: 121
EXCLUDE_DIRECT_SAMPLE: 2
EXCLUDE_STALE_METADATA_MUTATOR: 1
INCLUDE_GOVERNANCE_HISTORY: 16
UNMAPPED: 0
```

Из публичного кандидата исключены `data_registry/openml_feature_preview.csv` и
`notebooks/02_openml_candidate_data_preview.ipynb` с прямыми выборочными
значениями, а также поддерживаемый путь через
`notebooks/01_dataset_candidate_search_openml.ipynb`, который сохраняет
непримирённое значение CC0. Raw data и cache запрещены решением John. Код,
протоколы и агрегированное evidence условно допустимы только после отдельного
создания и проверки MIT project license, citation и dataset-attribution notice;
MIT не перелицензирует исходный dataset.

`notebooks/02_dataset_candidate_search_pmlb.ipynb` остаётся нулевым
placeholder-файлом. Его назначение не выводится из отсутствующего содержимого и
не изменяется ST08_05.

### 27.4. Codex-only работа и риск-ориентированные контрольные точки

По прямому решению John браузерный ChatGPT исключён из текущего workflow. ZIP
больше не создаётся автоматически для передачи между агентами. Для обычного
обратимого блока используются evidence, точный change log, проверки и manifest;
ZIP остаётся для завершения стадии, прямого запроса John, высокорискового или
труднообратимого изменения без эквивалентного восстановления либо переносимого
принятого состояния.

Это не означает отказ от восстановления: текущая рабочая копия не является Git
repository, поэтому стратегические архивы сохраняют роль до отдельного создания
и проверки version-control recovery. Для ST08_05 новый ZIP имеет `SKIPPED`:
стадия не закрывается, внешний handoff отсутствует, изменения обратимы и точный
доизменительный `ml_cra_v55.zip` доступен. Проверка v55 показала 280/280 файлов и
SHA-256 `0b7b954eca46038ed63b9d8d2e0be450a6b131c477a626261d460b77a3a1d0b7`.
Официальное [описание Git](https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control.html)
связывает version control с записью изменений и возвратом к прежнему состоянию,
а [NIST provenance](https://csrc.nist.gov/glossary/term/provenance) — с
трассируемой историей происхождения и изменений. Поэтому отсутствие браузерной
передачи устраняет автоматический ZIP, но не требование проверяемого recovery.

### 27.5. Проверки, предел вывода и статус

Доказательная запись:
`data_registry/st08_05_miniboone_lineage_license_attribution_and_release_asset_disposition_evidence_v01.json`.
Первая проверка обнаружила ошибку предварительного подсчёта: общий
`pilot_change_scope_v01.csv` после регистрации ST08_05 сам стал дополнительным
MiniBooNE-reference governance-файлом. Ожидание 156/15 исправлено на наблюдаемое
157/16; граница файлов не изменилась и `UNMAPPED` остался 0.

Проверки охватывают JSON/CSV contracts, полный инвентарь ссылок, отрицательные
мутации, защищённые SHA-256, отсутствие raw/cache и запрещённых release outputs.
Baseline прошёл. Cumulative pilot завершился `FAIL` только в восьми исторических
gate-проверках, требующих отсутствующие во внешних путях ZIP v44, v45, v47, v48,
v49, v51, v52 и v53. Текущие syntax, CSV, notebook, documentary, protected и
вычислительные регрессии до этих gate-проверок прошли; verifier не ослаблялся и
архивы не фабриковались. Это явная disposition недоступной внешней предпосылки,
а не заявление о полном зелёном cumulative pilot.

ST08-FIND-07 разрешён на уровне контракта и инвентаря, но public-development gate
остаётся заблокированным до отдельно авторизованного ST08_06.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Человеко-понятный смысл: происхождение и консервативное правило распространения
трассируются, каждый релевантный артефакт получил disposition, а запрещённого
релиза или научного изменения не было. Task-specific `PASS` присвоен при явной
disposition внешних исторических ZIP, поскольку точное сравнение с v55 доказало
только 11 разрешённых изменений и 18/18 protected; он не означает зелёный
cumulative pilot, юридическое заключение или разрешение публикации. John может
принять или вернуть только ST08_05.

## 28. Предлагаемый следующий блок

```text
proposed_next_block: ST08_06_project_license_citation_and_public_repository_legal_artifacts
ST08_06_status: proposed_not_authorized
ST08_06_implementation_started: NO
```

Следующий блок должен материализовать MIT `LICENSE`, `CITATION.cff`, dataset
attribution и публичный manifest, затем проверить их согласованность. Это
предложение не разрешает его выполнение или внешний релиз.

## 29. Задачи John

1. Принять либо вернуть ST08_05.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только ST08_06.
4. Не считать технический PASS юридическим заключением или разрешением
   публикации.

## 30. ST08_06 — лицензия, цитирование и юридические артефакты публичного репозитория

### 30.1. Полномочие, профиль и граница

John присвоил ST08_05 `ACCEPTED_BY_JOHN` и `TASK_CLOSED`, затем поручил
двигаться далее. Единственный следующий блок в принятом порядке ST08_04 —
`ST08_06_project_license_citation_and_public_repository_legal_artifacts`.
Профиль — `CHANGE`; публикация, README, packaging, security assurance, обучение
и изменение научного claim/protocol/evidence/verdict не разрешены.

```text
ACCEPTED_BY_JOHN: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
TASK_CLOSED: ST08_05_miniboone_lineage_license_attribution_and_release_asset_disposition
NEXT_BLOCK_AUTHORIZED: ST08_06_project_license_citation_and_public_repository_legal_artifacts
ST08_06_status: technical_pass_ready_for_john_acceptance
ST08_06_implementation_started: YES_COMPLETE
ST08_07_status: proposed_not_authorized
external_publication_authorized: false
```

Человекочитаемый смысл: John закрыл предыдущую задачу и разрешил материализовать
только юридико-метадатный минимум ST08_06. Никакого внешнего репозитория или
релиза агент не создавал.

### 30.2. Лицензия проекта и граница прав

Корневой `LICENSE` содержит MIT text с `Copyright (c) 2026 Иван Полищук`.
[OSI](https://opensource.org/license/mit) публикует одобренный текст MIT, а
[SPDX](https://spdx.org/licenses/MIT.html) фиксирует short identifier `MIT` и
машиносопоставимый текст. Локальная проверка заменила только допустимые поля
года и правообладателя в официальном SPDX-шаблоне и потребовала точного
совпадения остального текста.

MIT охватывает оригинальный код и документацию ML-CRA, но не меняет права на
MiniBooNE или другие материалы третьих лиц. Эта граница прямо закреплена в
`DATASET_ATTRIBUTION.md` и публичном манифесте. По рекомендации
[GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
лицензия находится в корне, однако это не является юридической консультацией.

### 30.3. Цитирование и проверка идентичности

`CITATION.cff` описывает программное обеспечение `ML Claim Reliability
Auditor`, автора Ивана Полищука, ORCID
`https://orcid.org/0009-0005-6596-0605`, MIT и целевой `repository-code`.
Версия и дата релиза намеренно отсутствуют: ни релиз, ни его версия не
авторизованы. Согласно официальному
[CFF schema guide 1.2.0](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md),
обязательны `authors`, `cff-version`, `message`, `title`, а `version` —
необязательное поле. Корневое расположение соответствует
[GitHub CITATION documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files).

Файл разобран как YAML и проверен официальной JSON Schema CFF 1.2.0 через
`PyYAML` и `jsonschema`. ORCID прошёл проверку контрольного знака MOD 11-2 по
[официальному описанию ORCID](https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier).

### 30.4. Атрибуция и fail-closed публичный манифест

`DATASET_ATTRIBUTION.md` переносит без ослабления сведения из раздела
`required_attribution` контракта
`configs/project_readiness/st08_05_miniboone_lineage_license_attribution_and_release_asset_disposition_v01.json`:
Byron Roe, название, UCI, DOI, CC BY 4.0, OpenML 41150, описание преобразований,
отсутствие raw data и запрет подразумеваемого одобрения. Официальное
[изложение CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) требует
credit, license link и change marking; controlling text остаётся
[legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en).

Машинный манифест
`configs/project_readiness/st08_06_public_repository_asset_manifest_v01.json`
реализует приоритетную классификацию с default `BLOCK_UNMAPPED`. До общих правил
он исключает direct samples, stale CC0 mutator, нулевые placeholders,
`docs/archive/` и raw/cache patterns. Полный инвентарь дополнительно обнаружил
нулевые `src/mlcra/data_registry/schema.py`, `scoring.py`, `validation.py`;
вместе с ранее известным пустым PMLB notebook они исключены без изменения и без
вывода о назначении. Точный count и SHA-256 отсортированного списка путей
делают появление неизвестного пути отрицательной мутацией, блокирующей
публикацию.

### 30.5. Проверки, ограничения и статус

Focused checks включают JSON parsing, CFF official-schema validation, SPDX MIT
text equality, ORCID checksum, полноту attribution, full path inventory,
приоритетную manifest classification, raw/cache absence, negative mutations,
18/18 protected SHA-256 и exact scope reconciliation. Baseline выполняется
неослабленной командой `python scripts/agent_verify.py --mode baseline`.
Cumulative pilot выполняется локальным venv, но его восемь исторических gate
checks сохраняют отдельный `FAIL`, если внешние ZIP v44, v45, v47, v48, v49,
v51, v52 и v53 по-прежнему отсутствуют; этот внешний prerequisite не
исправляется ослаблением verifier или фабрикацией архивов. Историческая
проверка ST08_03 дополнительно фиксирует `forbidden_outputs_absent=False`:
это ожидаемое следствие авторизованного создания `LICENSE` и `CITATION.cff` в
ST08_06, а не нарушение текущей области. Все предшествующие текущие syntax,
CSV, notebook, required-path, documentary, protected и Stage 7 computational
regressions в том же прогоне имеют `PASS`.

ST08_06 удовлетворяет только legal-artifacts prerequisite. Public-development
gate остаётся `BLOCKED` из-за отсутствующих README, security policy/scan,
публичного репозитория и отдельного явного решения John о публикации. ZIP имеет
`SKIPPED` по риск-ориентированному правилу: стадия не закрывается, external
handoff отсутствует, изменения обратимы и связаны exact evidence/scope/path
manifest.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Это означает task-specific техническую готовность к решению John, но не
публикационную готовность, приёмку John или юридическое заключение.

## 31. Предлагаемый следующий блок

```text
proposed_next_block: ST08_07_python_packaging_dependency_and_clean_environment_contract
ST08_07_status: proposed_not_authorized
ST08_07_implementation_started: NO
```

Следующий блок по принятому release train должен определить и проверить
восстанавливаемые Python distribution metadata и environment matrix. Это
предложение не разрешает начинать ST08_07 или создавать релиз.

## 32. Задачи John

1. Принять либо вернуть только ST08_06.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только ST08_07.
4. Не выполнять публикацию до прохождения оставшихся шлюзов и отдельной
   авторизации внешнего действия.

## 33. ST08_07 — Python-упаковка, зависимости и чистое окружение

### 33.1. Полномочие, профиль и граница

John присвоил ST08_06 `ACCEPTED_BY_JOHN` и `TASK_CLOSED`, затем поручил
двигаться далее. По принятому release train это разрешило только
`ST08_07_python_packaging_dependency_and_clean_environment_contract` с профилем
`CHANGE`. Реализация CLI относится к ST08_08; публикация, релиз, обучение и
изменение научного claim/protocol/evidence/verdict не разрешены.

```text
ACCEPTED_BY_JOHN: ST08_06_project_license_citation_and_public_repository_legal_artifacts
TASK_CLOSED: ST08_06_project_license_citation_and_public_repository_legal_artifacts
NEXT_BLOCK_AUTHORIZED: ST08_07_python_packaging_dependency_and_clean_environment_contract
ST08_07_status: technical_pass_ready_for_john_acceptance
ST08_07_implementation_started: YES_COMPLETE
declared_environment_cells: 1
validated_environment_cells: 1
ST08_08_status: proposed_not_authorized
external_publication_authorized: false
```

Человекочитаемый смысл: создан и проверен минимальный стандартный контур
сборки и установки только для одного честно объявленного окружения. Проект ещё
не имеет поддерживаемой команды `mlcra`, не является релизом и не готов к
публикации.

### 33.2. Стандартные метаданные и граница версии

Корневой `pyproject.toml` использует `setuptools.build_meta` и статические
project metadata: distribution name `ml-cra`, автора Ивана Полищука, SPDX
expression `MIT`, `LICENSE`, `DATASET_ATTRIBUTION.md`,
`requires-python = ">=3.12,<3.13"` и точные
runtime dependencies. Официальная
[PyPA specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
разделяет `[build-system]`, `[project]` и tool-specific configuration, требует
`name` и version — статическую либо dynamic — и задаёт поля dependencies,
optional-dependencies, Requires-Python и license-files.

Значение `0.1.0.dev0` не объявляется релизом `0.1.0`. По
[PEP 440](https://peps.python.org/pep-0440/) development release `.devN`
упорядочивается перед соответствующим final release. Независимая проверка через
`packaging 26.3` подтвердила нормализацию, development flag и
`0.1.0.dev0 < 0.1.0`. Поле `[project.scripts]` отсутствует намеренно: создание
console entry point до ST08_08 подменило бы следующую задачу пустой либо
непроверенной командой.

В `src/mlcra/` нет `__init__.py`; поэтому exact discovery использует
`[tool.setuptools.packages.find]`, `where = ["src"]`, `include = ["mlcra"]`
и implicit namespaces. Официальная
[setuptools documentation](https://setuptools.pypa.io/en/stable/userguide/package_discovery.html)
подтверждает, что `find` в `pyproject.toml` учитывает implicit namespace по
умолчанию. Точная граница включает десять реализованных модулей и исключает
нулевые `mlcra.data_registry` placeholders.

### 33.3. Зависимости и проверенная матрица

AST/import inventory и зарегистрированное окружение дали четыре прямые
зависимости поддерживаемого ядра: `numpy==2.4.4`, `pandas==3.0.2`,
`scikit-learn==1.8.0`, `threadpoolctl==3.6.0`. Транзитивный clean profile также
фиксирует `joblib`, `scipy`, `python-dateutil`, `six` и Windows `tzdata`.
Ленивый `openml` нужен только research offline-cache adapter и объявлен extra
`research-openml`; он не включён в проверенную core matrix.

`requirements/locks/st08_07-py312-windows-x86_64.txt` содержит девять точных
версий, девять SHA-256 и требует binary-only/hash-checking mode. Это следует
официальному руководству
[pip Repeatable Installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/):
pinning фиксирует версии, hashes фиксируют получаемые артефакты, а wheelhouse
допускает offline install. Lock платформенно ограничен CPython 3.12 Windows
x86_64; переносимость wheelhouse не утверждается.

Единственная объявленная и проверенная ячейка — CPython 3.12, фактически
3.12.0, Windows Server 2019 AMD64, core dependencies. Linux, macOS, PyPy, другие
архитектуры и Python minors имеют `NOT_DECLARED_NOT_TESTED`. Это не слабость
формулировки, а fail-closed запрет выдавать отсутствие CI и интерпретаторов за
совместимость.

### 33.4. Сборка и clean-install evidence

Временный `build==1.5.0` создал в изоляции sdist, затем wheel из этого sdist с
точно объявленным `setuptools==82.0.1`. Такая последовательность соответствует
[PyPA packaging flow](https://packaging.python.org/en/latest/flow/), который
различает source tree, metadata, sdist, wheel, installation и publication.

Наблюдаемые артефакты проверки:

```text
sdist: ml_cra-0.1.0.dev0.tar.gz
sdist_sha256: 747552cf1636ebbe2dd0d8faf075c968ff8ebfa09575909b35309cbd692211e7
sdist_entries: 24
wheel: ml_cra-0.1.0.dev0-py3-none-any.whl
wheel_sha256: a099262560517cecf2699a553c5beb44bd73f0bf0e153e82587a146be37cd2aa
wheel_entries: 16
distributed_modules: 10
```

В новый venv зависимости установлены из временного wheelhouse с `--no-index`
и обязательными hashes, затем wheel установлен с `--no-index --no-deps`.
`pip check` прошёл; isolated mode импортировал namespace `mlcra` и все десять
модулей из clean `site-packages`. Installed metadata точно сообщает имя,
development-version, Python boundary, MIT и зависимости. `mlcra.exe` и
`mlcra.data_registry` отсутствуют ожидаемо. Временные venv, wheelhouse, dist и
egg-info после проверки удалены и не являются release artifacts.

Сборщик выдал предупреждение об отсутствии стандартного корневого README.
Оно зарегистрировано, но не исправлено преждевременно: действующий release train
отводит реальный RU/EN user entry документ ST08_10 после появления интерфейса.
В `pyproject.toml` используется ограниченное inline development description,
которое не обещает CLI или релиз.

### 33.5. Верификация, ограничения и статус

Положительный metadata/dependency/environment contract прошёл; 13/13
отрицательных мутаций отклонены. Они включали удаление build-system, подмену
dev-version финальной, расширение Python, ослабление pins/hashes, перенос OpenML
в core, преждевременный script, расширение discovery, включение placeholders,
удаление license/author или обязательной dataset attribution. Защищённые научные артефакты проверяются точными
SHA-256; новые модели не запускались.

ST08-FIND-03 и ST08-FIND-05 только `PARTIALLY_RESOLVED`: metadata, sdist, wheel,
hash-locked dependencies и один clean import существуют, но воспроизведение
поддерживаемой команды невозможно до ST08_08. Public-development и `0.1.0`
gates остаются `BLOCKED`; research extra, cross-platform matrix, README,
security/CI и owner release decision не закрыты.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Это означает, что ограниченная задача упаковочного контракта выполнена и готова
к решению John. Статусы не означают приёмку, совместимость вне одной матричной
ячейки, научную ревалидацию, выпуск `0.1.0` или разрешение публикации.

## 34. Предлагаемый следующий блок

```text
proposed_next_block: ST08_08_universal_CLI_classification_vertical_slice
ST08_08_status: proposed_not_authorized
ST08_08_implementation_started: NO
```

По принятому release train следующий блок должен реализовать `audit`, `verify`
и `doctor` для ограниченного binary-classification vertical slice и fail-closed
unsupported cases. Предложение не разрешает начинать ST08_08.

## 35. Задачи John

1. Принять либо вернуть только ST08_07.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только ST08_08.
4. Не считать `0.1.0.dev0` релизом и не публиковать проект до прохождения
   оставшихся шлюзов и отдельной авторизации внешнего действия.

## 36. ST08_08 — универсальный CLI для ограниченной бинарной классификации

### 36.1. Полномочие и граница

John принял и закрыл ST08_07, затем явно авторизовал только
`ST08_08_universal_CLI_classification_vertical_slice`:

```text
ACCEPTED_BY_JOHN: ST08_07_python_packaging_dependency_and_clean_environment_contract
TASK_CLOSED: ST08_07_python_packaging_dependency_and_clean_environment_contract
NEXT_BLOCK_AUTHORIZED: ST08_08_universal_CLI_classification_vertical_slice
ST08_08_status: technical_pass_ready_for_john_acceptance
ST08_09_status: proposed_not_authorized
release_or_publication_authorized: false
scientific_claim_protocol_evidence_or_verdict_change_authorized: false
```

Реализован один узкий вертикальный срез: локальный UTF-8 CSV с полными конечными
числовыми признаками, ровно два класса и явная положительная метка. Регрессия,
многоклассовая классификация, URL, произвольный импорт моделей, исполняемая
десериализация и перезапись существующего каталога отклоняются до обучения.

### 36.2. Команды и воспроизводимый комплект доказательств

Установленный wheel создаёт `mlcra.exe` и три команды:

```text
mlcra audit --spec claim.json --data data.csv --output-dir run
mlcra verify --bundle run
mlcra doctor --format json
```

`audit` проверяет JSON по поставляемой Draft 2020-12 JSON Schema, выполняет заранее
разрешённое сравнение `HistGradientBoostingClassifier` и конвейера
`StandardScaler -> LogisticRegression` по `StratifiedKFold`, затем публикует ровно
восемь JSON-файлов через полный временный каталог и атомарное переименование в той
же файловой системе. `verify` сверяет состав и SHA-256, проверяет межфайловые связи
и заново вычисляет вердикт без обучения. `doctor` не использует сеть и не обучает
модели; он проверяет единственную заявленную ячейку CPython 3.12 / Windows AMD64 и
показывает незакрытые релизные шлюзы.

Официальная документация Python
[`argparse`](https://docs.python.org/3/library/argparse.html) задаёт подкоманды и
код 2 для ошибок разбора; спецификация
[PyPA entry points](https://packaging.python.org/en/latest/specifications/entry-points/)
связывает `[project.scripts]` с устанавливаемой командой. Документация
[`jsonschema`](https://python-jsonschema.readthedocs.io/en/stable/validate/)
поддерживает `Draft202012Validator`, а
[`StratifiedKFold`](https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.StratifiedKFold.html)
сохраняет доли классов и воспроизводим при фиксированном integer `random_state`.
Опасные pickle-входы не поддерживаются: официальная
[документация Python](https://docs.python.org/3.12/library/pickle.html)
предупреждает, что распаковка недоверенных данных способна выполнить произвольный
код.

### 36.3. Вердикт и научная граница

Основная метрика — average precision (средняя точность). Категория `supported`
требует достижения заранее заданного среднего порога и положительной разницы на
каждом зарегистрированном блоке; `fragile` означает достижение среднего порога без
победы на каждом блоке; `not_supported` означает недостижение среднего порога. Все
три являются корректным завершением `audit` с кодом 0, а не программной ошибкой.

Это не универсальное ранжирование моделей. Вывод относится только к входным данным,
двум фиксированным реализациям, метрике, числу разбиений, зернам и порогу конкретной
спецификации. В ST08_08 нет автоматического подбора гиперпараметров и нет нового
научного утверждения о MiniBooNE.

### 36.4. Наблюдаемая проверка

Фокусный набор дал 11/11 PASS и охватил коды `0/2/3/4/5/6`, точный состав bundle,
проверку без fit (обучения), подмену, неподдерживаемые задачи, недостаток данных,
запрет перезаписи и контролируемые внутренние ошибки без traceback (трассировки
стека). Синтетический заранее зарегистрированный нелинейный пример в чисто
установленном wheel дал 8/8 положительных блоков и среднюю разницу average precision
`0.5158023952204487` при пороге `0.05`.

Wheel `ml_cra-0.1.0.dev0-py3-none-any.whl` с SHA-256
`b596a73d1aa41ce407280350f372987cd0bc4be16cadb7674c0e22b8bba1fab2`
содержал CLI, схему и entry point. В новом окружении установились 15 точных
hash-locked зависимостей, `doctor` вернул 0 и `environment_pass=true`, но честно
сохранил `release_ready=false`.

Зарегистрированный локальный MiniBooNE-кеш дал 130064 строки, 50 признаков,
распределение 93565/36499 и ноль сетевых попыток. Отдельный двухблочный запуск
установленной команды дал `audit=0`, `verify=0`, положительную разницу в 2/2 блоках
и среднюю разницу `0.09079498654089707`. Это только программная характеристика
интерфейса; канонические научные данные, протокол и вердикт не изменялись.

`baseline` прошёл с 150 добавленными и 8 изменёнными путями, без пропусков и выхода
за область. Накопительный `pilot` сохранил восемь исторических FAIL из-за
отсутствующих старых ZIP v44, v45, v47, v48, v49, v51, v52, v53 и исторического
условия ST08_03; все текущие структурные, синтаксические, CSV, notebook,
документарные, вычислительные регрессии и 18/18 защищённых SHA-256 прошли.

### 36.5. Состояние и ограничения

ST08-FIND-03 и ST08-FIND-05 дополнительно частично разрешены: теперь существует
устанавливаемая команда и воспроизводимый ограниченный пользовательский путь.
Public-development gate всё ещё `BLOCKED`: нет ST08_09 CI/security/regression
assurance, ST08_10 RU/EN пользовательской документации и release-candidate
повторного аудита, кроссплатформенной матрицы и решения John о релизе.

ZIP-контрольная точка имеет `SKIPPED`: стадия не закрывается, внешняя передача не
авторизована, изменения обратимы, а проект теперь разрабатывается только совместно
с Codex. Производные временные CSV, bundle, wheel, wheelhouse, venv, build и
egg-info после проверки удалены; исходный MiniBooNE-кеш не изменён.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Это означает, что только ST08_08 технически выполнен и готов к решению John. Это
не означает приёмку, релиз, публикацию, поддержку иных типов задач или начало
ST08_09.

## 37. Предлагаемый следующий блок

```text
proposed_next_block: ST08_09_CI_security_and_release_candidate_assurance
ST08_09_status: proposed_not_authorized
ST08_09_implementation_started: NO
```

## 38. Задачи John

1. Принять либо вернуть на доработку только ST08_08.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только предложенный ST08_09.
4. Не публиковать `0.1.0.dev0` и не считать его релизом.

## 39. ST08_09 — CI, безопасность и проверка кандидата на выпуск

### 39.1. Полномочие и граница

John принял и закрыл ST08_08, а поручение двигаться далее разрешило ровно
`ST08_09_CI_security_and_release_candidate_assurance`. Внешний репозиторий,
публикация, выпуск, изменение научного утверждения, протокола, доказательств или
вердикта не разрешались и не выполнялись.

```text
ACCEPTED_BY_JOHN: ST08_08_universal_CLI_classification_vertical_slice
TASK_CLOSED: ST08_08_universal_CLI_classification_vertical_slice
NEXT_BLOCK_AUTHORIZED: ST08_09_CI_security_and_release_candidate_assurance
ST08_09_status: technical_pass_ready_for_john_acceptance
hosted_CI_status: configured_not_executed
external_publication_authorized: false
ST08_10_status: proposed_not_authorized
```

Практический смысл блока: локально создан и проверен воспроизводимый контур
контроля цепочки поставки, но его будущий запуск на инфраструктуре GitHub ещё не
является наблюдаемым доказательством. Следующий блок и внешние действия по-прежнему
требуют отдельного решения John.

### 39.2. Контур CI и профессиональные основания

Workflow (рабочий процесс) `.github/workflows/ci.yml` ограничен `push` и
`pull_request` ветки `main` и ручным запуском, имеет только `contents: read`, не
получает секреты, не загружает артефакты, не сохраняет checkout-учётные данные и
использует действия по полным commit SHA. В многострочных PowerShell-шагax семь
явных проверок `$LASTEXITCODE` не позволяют поздней успешной команде скрыть ранний
сбой. Фиксирована ячейка `windows-2022`, x64, CPython 3.12.10: это последний выпуск
ветки 3.12 с официальными Windows-бинарниками; поздние security-only выпуски
поставляются без Windows-инсталляторов.

Это воспроизводимая, но не полностью закрытая security-граница: 3.12.10 не
содержит исправлений из более поздних source-only выпусков 3.12. Стратегия
поддержки интерпретатора остаётся риском будущего release-candidate решения, а не
основанием объявлять безопасность Python-окружения подтверждённой.

Решения опираются на [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final),
[рекомендации GitHub по безопасному использованию Actions](https://docs.github.com/en/actions/reference/security/secure-use),
[справочник hosted runners GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners),
[официальный выпуск Python 3.12.10](https://www.python.org/downloads/release/python-31210/)
и [процесс упаковки PyPA](https://packaging.python.org/en/latest/flow/).

### 39.3. Зависимости, секреты и архивы

Отдельное окружение контроля содержит 35 точных дистрибутивов и 35 SHA-256.
Первый [pip-audit](https://pypa.github.io/pip-audit/) обнаружил в
`setuptools==82.0.1` `PYSEC-2026-3447` / `CVE-2026-59890` /
`GHSA-h35f-9h28-mq5c`: обход исключений sdist при Unicode-нормализации мог
непреднамеренно включить исключаемый файл. Это не было скрыто: текущий build
backend и lock обновлены до исправленного `setuptools==83.0.0`, историческое
доказательство ST08_07 не переписано. Повторный аудит дал 0 известных уязвимостей
для 15 runtime и 35 assurance зависимостей. Результат относится к базе advisory
на 2026-08-20, а не является бессрочной гарантией.

[detect-secrets](https://github.com/Yelp/detect-secrets) проверил 270 текстовых
файлов кандидата 23 детекторами точных форматов и дал 0 находок. Энтропийные,
keyword и public-IP плагины сознательно отключены с явными причинами в контракте;
поэтому сканирование уменьшает риск, но не доказывает абсолютное отсутствие любого
секрета. Внешний GitHub secret scanning не включён, поскольку публикация не
разрешена.

После обновления backend заново построены и проверены:

- sdist: 26 файлов, SHA-256
  `7af9de6f8381b5f26091b2386e0a07aa865d4cdc9ada8b8c8b39bd180308de3d`;
- wheel: 20 файлов, SHA-256
  `34b0fc9849e102bb25c87ab26093cc8c70e0517e2f2b512fb7a90548054c9472`.

Fail-closed (закрывающая при неопределённости) проверка отклоняет обход пути,
обратные косые черты, ссылки и иные нерегулярные tar-элементы, raw/cache/venv,
секретные и временные файлы, bytecode и отсутствие обязательных членов архива.

### 39.4. Наблюдаемая локальная проверка и ограничения

Двенадцать из двенадцати позитивных и мутационных тестов прошли. В новом локальном
CPython 3.12.0 / Windows AMD64 окружении 15 hash-locked runtime зависимостей и wheel
установились без сети; `pip check`, 11/11 CLI-тестов и `doctor=0` прошли.
`doctor` корректно оставил `release_ready=false` из-за ненаблюдавшегося hosted CI,
не включённого внешнего secret scanning, отсутствующей RU/EN документации,
непройденного release-candidate повторного аудита и отсутствия решения John.

Локальная CPython 3.12.0 ячейка остаётся единственной наблюдаемой; настроенная
CPython 3.12.10 / Windows 2022 ячейка не расширяет подтверждённую совместимость до
фактического hosted-запуска. Предупреждение joblib о невозможности определить
физические ядра привело к использованию логических ядер, но тесты не упали и эти
результаты не использованы как научное доказательство. Предупреждение сборки об
отсутствии корневого README сохранено для ST08_10.

Защищённые научные артефакты совпали 18/18; обучение, сетевой доступ к датасету,
изменение научных значений, протокола и вердикта равны нулю. ZIP пропущен: стадия
не закрывается, внешняя передача отсутствует, изменения обратимы, а работа ведётся
John и Codex с риск-ориентированными контрольными точками.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

Это означает, что ограниченная техническая задача ST08_09 выполнена и готова к
решению John. Это не означает приёмку, исполненный hosted CI, готовность к
публикации, выпуск или разрешение начать ST08_10.

## 40. Предлагаемый следующий блок

```text
proposed_next_block: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
ST08_10_status: proposed_not_authorized
ST08_10_implementation_started: NO
```

## 41. Задачи John

1. Принять либо вернуть на доработку только ST08_09.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только предложенный ST08_10.
4. Не публиковать и не выпускать ML-CRA до отдельной авторизации и прохождения
   оставшихся шлюзов.

## 42. ST08_10 — корневая двуязычная документация и согласование текущих путей

### 42.1. Полномочие и граница

John принял и закрыл `ST08_09_CI_security_and_release_candidate_assurance` и
поручил двигаться далее. По утверждённой очереди это разрешило только
`ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation`.
Регрессия, панель управления, публикация, выпуск и изменение научного
утверждения, протокола, доказательств либо вердикта не разрешались и не
выполнялись.

```text
ACCEPTED_BY_JOHN: ST08_09_CI_security_and_release_candidate_assurance
TASK_CLOSED: ST08_09_CI_security_and_release_candidate_assurance
NEXT_BLOCK_AUTHORIZED: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
ST08_10_status: technical_pass_ready_for_john_acceptance
hosted_CI_status: configured_not_executed
external_publication_authorized: false
ST08_11_status: proposed_not_authorized
```

Блок означает: ST08_09 принят John, ST08_10 локально выполнен и проверен, но ещё
не принят John. Настроенный внешний CI не запускался, публикация не разрешена, а
ST08_11 только предлагается и не может быть начат без нового решения John.

### 42.2. Пользовательский вход и инженерные основания

Созданы корневой англоязычный `README.md` и равноправный русский
`README_RU.md`. В каждом есть 12 проверяемых разделов: состояние и граница,
назначение, требования к окружению, установка, быстрый пример, входы, коды
завершения, устранение неполадок, проверка результата, научная граница,
состояние проекта и правовая/контактная информация. Три PowerShell-блока в двух
языках совпадают дословно, поэтому перевод не создаёт второй технический
протокол. `pyproject.toml` теперь использует `README.md` как полное описание
дистрибутива.

Решение опирается на официальные рекомендации GitHub о корневом README,
назначении, запуске и относительных ссылках
(https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes),
спецификацию PyPA для поля `project.readme`
(https://packaging.python.org/en/latest/specifications/pyproject-toml/),
документацию Python `venv`
(https://docs.python.org/3.12/library/venv.html), безопасную установку pip с
`--require-hashes` и `--only-binary`
(https://pip.pypa.io/en/stable/topics/secure-installs/), установку локального
проекта (https://pip.pypa.io/en/stable/topics/local-project-installs/) и
разделение обучения, практической инструкции, справки и объяснения по Diátaxis
(https://diataxis.fr/start-here/).

### 42.3. Исправление текущих путей

В действующих документах Stage 1–4 прежние пути `ml-cra_v01.zip`,
`docs/generated/` и `docs/reports/` заменены точными существующими путями в
`docs/archive/reports/`. Stage 4 теперь отделяет текущий
`docs/stages/stage_05_claim_audit_protocol.md` от архивного заменённого
`docs/archive/stages/stage_05_methodological_stress_testing_superseded.md`.
Stage 6 больше не выдаёт исторически предложенный, но не созданный
`src/mlcra/stage05/` за текущий пакет: указан реализованный
`src/mlcra/application.py`, модульный слой `src/mlcra/` и итоговый документ
Stage 7. Защищённый документ Stage 5 не переписывался; его существующая явная
архивная ссылка проверена отдельно.

Автоматический контроль `scripts/st08_10_documentation_assurance.py` подтвердил
12/12 разделов в каждой языковой версии, 3/3 идентичных блока команд, 26
разрешившихся локальных ссылок, 23 обязательных текущих фрагмента и 18/18
защищённых SHA-256. Восемь отрицательных тестов отвергают потерю раздела,
расхождение команд, сломанную ссылку, возврат старого пути и неверное описание
пакета.

### 42.4. Наблюдаемая выполнимость

Чистое временное окружение CPython 3.12.0 / Windows Server 2019 AMD64 установило
35 инструментальных и 15 runtime-зависимостей по точным версиям и SHA-256,
затем установило проект без нового разрешения зависимостей. `pip check` и
`doctor` прошли; `doctor` сообщил `environment_pass=true`, но сохранил
`release_ready=false` и пять фактических внешних ограничений.

Пользовательский пример из README дал `audit=0`, ограниченный fixture-вердикт
`supported`, ровно 8 файлов bundle (пакета доказательств), затем `verify=0` и
`status=PASS` без повторного обучения. Прикладные команды сделали 0 сетевых
попыток и не зарегистрировали научный результат. Собранные sdist/wheel имели
28/20 файлов и прошли проверку архивных путей, ссылок, обязательных членов и
байткода. Общий набор дал 31/31 PASS; поиск секретов — 277 файлов, 23 детектора,
0 находок; актуальный advisory-аудит — 15 runtime и 35 инструментальных
зависимостей, 0 известных уязвимостей на дату проверки.

Добавление новых CI-команд выявило недостаточность прежнего контроля только по
минимальному числу `$LASTEXITCODE`: удаление одного старого guard (предохранителя)
оставляло общее число выше порога. Поэтому необходимое отклонение от исходного
набора изменений усилило `scripts/st08_09_release_assurance.py`: теперь каждая
нативная команда в многострочном PowerShell-шаге обязана иметь собственную
следующую проверку кода завершения. Регрессия ST08_09 после исправления прошла
12/12.

Полное машинное доказательство находится в
`data_registry/st08_10_root_and_bilingual_user_documentation_evidence_v01.json`.
Публичный кандидат теперь содержит ровно 322 контролируемых пути, SHA-256
списка `50fe2d8425f786cfc86f7d21bcc93c074bfd766430d51e4ca088db3a98d22ea5`,
неразмеченных путей нет; прежний README-блокер снят. Публикационный шлюз остаётся
`BLOCKED` из-за ненаблюдавшегося hosted CI, не включённого внешнего поиска
секретов, отсутствующего повторного аудита кандидата, публичного репозитория и
явной авторизации John.

Baseline прошёл после удаления воспроизводимых временных окружений, сборок и
отчётов. Накопительный pilot сохраняет восемь исторических FAIL отсутствующих
старых ZIP/условия ST08_03; все текущие структурные, синтаксические, CSV,
notebook, вычислительные и 18/18 защищённых проверки проходят. ZIP-контрольная
точка пропущена: стадия не закрывается, внешней передачи нет, изменения
обратимы, а John и Codex работают с одной рабочей копией.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
```

`PASS` означает, что измеримый результат только ST08_10 получен и проверен.
`READY_FOR_JOHN_ACCEPTANCE` означает готовность к решению John, но не приёмку,
релиз, публикацию, поддержку других задач или разрешение следующего блока.

## 43. Предлагаемый следующий блок

```text
proposed_next_block: ST08_11_tabular_regression_protocol_core_and_CLI_support
ST08_11_status: proposed_not_authorized
ST08_11_implementation_started: NO
```

Предложение следует принятой продуктовой очереди: после работающей бинарной
классификации и её документации следующим отдельным расширением является
табличная регрессия. Оно потребует нового протокола и отдельной авторизации;
текущий результат сам по себе такого разрешения не даёт.

## 44. Задачи John

1. Принять либо вернуть на доработку только ST08_10.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только предложенный ST08_11.
4. Не публиковать и не выпускать ML-CRA: внешние шлюзы и отдельное решение John
   ещё отсутствуют.

## 45. ST08_11 — протокол табличной регрессии, общее ядро и CLI

### 45.1. Полномочие и граница

John принял и закрыл
`ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation`
и поручил двигаться далее. По зарегистрированной очереди это авторизовало только
`ST08_11_tabular_regression_protocol_core_and_CLI_support`. Панель, публикация,
релиз и изменение научного утверждения, протокола, доказательств или вердикта
MiniBooNE не разрешались. Поскольку John не назвал реальный регрессионный набор
данных и предметное утверждение, такой научный объект также не был выбран по
догадке.

```text
ACCEPTED_BY_JOHN: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
TASK_CLOSED: ST08_10_root_and_bilingual_user_documentation_and_current_path_reconciliation
NEXT_BLOCK_AUTHORIZED: ST08_11_tabular_regression_protocol_core_and_CLI_support
ST08_11_status: technical_pass_ready_for_john_acceptance
external_publication_authorized: false
MiniBooNE_scientific_change_authorized: false
```

Это означает, что ST08_10 принят, а ограниченный ST08_11 выполнен локально и
ожидает решения John. Блок не означает приёмку ST08_11, научную валидацию
регрессии на реальном наборе данных, готовность 1.0.0, публикацию или релиз.

### 45.2. Проспективный регрессионный протокол

До реализации зафиксирован контракт
`configs/project_readiness/st08_11_tabular_regression_protocol_core_and_CLI_support_contract_v01.json`.
Новая строгая схема
`src/mlcra/schemas/tabular_regression_claim_v01.schema.json` разрешает только
числовую конечную непостоянную цель, полные конечные числовые признаки,
`exchangeable_rows` (обменные строки), заранее заданные зерна и K-fold с 2–10
блоками. Временные, групповые, пространственно зависимые и повторные наблюдения
этот контракт намеренно не покрывает: их ошибочное перемешивание могло бы дать
утечку между обучением и оценкой.

Базовая модель — фиксированный `StandardScaler → Ridge(alpha=1, solver=svd)`,
кандидат — фиксированный `HistGradientBoostingRegressor` без early stopping
(ранней остановки). Подбора моделей и гиперпараметров нет. Это следует
результату Varma и Simon: оценка по тем же CV-результатам, по которым модель
оптимизировалась, смещена; настройка должна быть вложена в оценочный контур
(BMC Bioinformatics 7:91, DOI 10.1186/1471-2105-7-91,
https://pubmed.ncbi.nlm.nih.gov/16504092/). Здесь настройка отсутствует вообще.

Каждый блок использует одни и те же строки обучения и проверки для обеих
моделей. Основная метрика — `root_mean_squared_error` (RMSE, корень из средней
квадратичной ошибки), дополнительная — MAE (средняя абсолютная ошибка). Обе
являются потерями, где 0 — лучшее значение согласно официальной документации
scikit-learn 1.8
(https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.root_mean_squared_error.html,
https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.mean_absolute_error.html).
Поэтому `primary_delta = RMSE_baseline - RMSE_candidate`: положительная разность
однозначно означает меньшую ошибку кандидата. KFold и воспроизводимость
целочисленного `random_state` опираются на
https://scikit-learn.org/1.8/modules/generated/sklearn.model_selection.KFold.html;
Ridge и HGBR — на официальные контракты
https://scikit-learn.org/1.8/modules/generated/sklearn.linear_model.Ridge.html и
https://scikit-learn.org/1.8/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html.

### 45.3. Реализация и проверка пакета доказательств

`src/mlcra/application.py` диспетчеризует утверждение только по разрешённой
версии схемы, но классификация и регрессия проходят через одно ядро публикации
восьми файлов, запрет сети, хеширование, происхождение и `verify`. Регрессионный
`verify` не обучает модели и теперь дополнительно пересчитывает разность каждого
блока, среднее, минимум, максимум, число положительных блоков и итоговый
вердикт. Мутация с ложной разностью отклонена с кодом
`MLCRA_BUNDLE_PRIMARY_DELTA_RELATION_FAILURE`, даже когда атакующий пересчитал
самосогласованные хеши индекса и манифеста.

При первой проверке дополнение `src/mlcra/metrics.py` было отклонено, потому что
этот файл входит в 18 защищённых научных артефактов. Новая регрессионная логика
перенесена в незащищённый прикладной слой, а `metrics.py` восстановлен из
локальной контрольной точки только после совпадения SHA-256
`6a40115df49078119fa624bf0ce74f18de86f0f54362e5b41860017c29be5ab3`.
Итоговая проверка подтвердила 18/18 совпадений; изменение MiniBooNE равно нулю.

### 45.4. Наблюдаемая верификация и научная граница

Синтетический нелинейный пример 41x1 дал 8/8 положительных парных блоков,
среднюю разность RMSE `6.47927764243067` при проспективном пороге `1.0`, минимум
`3.8855420933033527`, максимум `7.761861075766374` и ограниченный fixture-вердикт
`supported`. Повторный запуск дал те же научно значимые поля после исключения
времени выполнения. Это проверка программного и протокольного поведения, а не
научный вывод о предметной области или универсальном превосходстве модели.

Исходный набор дал 41/41 PASS: 11 бинарных CLI, 10 регрессионных методов с
мутациями, 8 документационных и 12 release-assurance проверок. Русский и
английский README имеют 12/12 разделов, 3/3 побайтно одинаковых PowerShell-блока
и 28 разрешившихся локальных ссылок. Публичный манифест содержит 329 путей,
0 неразмеченных, SHA-256 списка
`869e9d50dd21ce966633a4b1addacddc6e3d57a1f290559d32c366f83f291370`;
поиск секретных шаблонов проверил 284 файла 23 детекторами без находок.

Sdist/wheel прошли проверку состава с 30/21 файлами и содержат обе схемы.
Новое чистое CPython 3.12.0 / Windows Server 2019 AMD64 окружение автономно
установило 15 зафиксированных runtime-зависимостей и локальный wheel. `pip check`,
`doctor`, 21/21 установленный CLI-тест и оба пользовательских пути
`audit → verify` прошли; прикладные команды сделали 0 сетевых попыток.

Baseline имеет PASS. Накопительный pilot сохранил только восемь известных
исторических FAIL из-за отсутствующих прежних ZIP v44/v45/v47/v48/v49/v51/v52/v53
и исторического условия ST08_03 после разрешённого создания юридических файлов;
все текущие syntax, CSV, notebook, документальные и вычислительные регрессии
прошли. ZIP ST08_11 пропущен: стадия не закрывается, внешней передачи нет,
изменения обратимы, а John и Codex работают с одной рабочей копией.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
scientific_validation_real_regression_dataset: SKIPPED_NOT_AUTHORIZED
release_1_0_0_regression_gate: BLOCKED
```

`PASS` относится к измеримому техническому результату ST08_11: схема, ядро,
CLI, пакет, мутации, документация и чистая установка работают. Значение
`SKIPPED_NOT_AUTHORIZED` означает, что реальный датасет и научное утверждение не
подменялись синтетическим примером. Практическое следствие — технический блок
готов к приёмке John, но регрессионный научный шлюз 1.0.0 остаётся закрытым.

## 46. Предлагаемый следующий блок

```text
proposed_next_block: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
ST08_11A_status: proposed_not_authorized
ST08_11A_implementation_started: NO
ST08_12_status: deferred_until_regression_scientific_dependency_is_resolved
```

Исходная очередь ставила после ST08_11 панель ST08_12. Однако начинать панель,
не закрыв обязательную для 1.0.0 отдельную научную валидацию регрессии, означало
бы закрепить интерфейс поверх неполного доказательного контура. Поэтому агент
предлагает сначала отдельный проспективный блок: John выбирает предметную задачу
и допустимый реальный набор данных; затем регистрируются лицензия, утверждение,
структура выборки, протокол разбиения, метрики и политика вердикта до загрузки и
вычисления результата. Это предложение не является авторизацией.

## 47. Задачи John

1. Принять либо вернуть на доработку только ST08_11.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли предложенный корректирующий блок
   `ST08_11A_registered_regression_dataset_claim_and_scientific_validation`.
4. Не считать синтетический `supported` научным доказательством на реальном
   наборе данных и не переходить к ST08_12, публикации или релизу без отдельных
   решений и оставшихся шлюзов.

## 48. ST08_11A — зарегистрированный реальный регрессионный контур

John принял и закрыл ST08_11, отдельно авторизовал ST08_11A и выбрал
`UCI_Wine_Quality_red_v01`. До загрузки данных зафиксированы датасет, лицензия,
утверждение, модели, 5 разбиений, пять зёрен, RMSE/MAE, порог `0.05` и правило
вердикта. Исходный UCI-файл не включён в проект.

```text
ACCEPTED_BY_JOHN: ST08_11_tabular_regression_protocol_core_and_CLI_support
TASK_CLOSED: ST08_11_tabular_regression_protocol_core_and_CLI_support
NEXT_BLOCK_AUTHORIZED: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
DATASET_SELECTED_BY_JOHN: UCI_Wine_Quality_red_v01
ST08_11A_status: technical_pass_ready_for_john_acceptance
scientific_claim_verdict: not_supported
external_publication_authorized: false
```

Человекочитаемый смысл: научная процедура выполнена корректно, но заранее
сформулированное положительное утверждение не достигло порога. Это не сбой
программы и не отрицание того, что кандидат часто лучше; это запрет назвать
наблюдаемое улучшение достаточно большим по принятому правилу.

Официальный архив UCI (DOI `10.24432/C56S3T`, CC BY 4.0) имел SHA-256
`3ed56667f4b828242bd732d7d1dd7f2861e54432239d7fa63877014cbb0304d4`;
`winequality-red.csv` —
`4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e`.
Наблюдались 1599 строк, 11 признаков, одна цель и ноль пустых либо неконечных
ячеек. Потеря-разделитель `;` заменён на `,` без фильтрации строк, столбцов или
значений; преобразованный временный вход имел SHA-256
`d22f4f11db0456ff21745d2fa96d26fa348a8cdb889efda65bde802085be45fd` и удалён.

Два запуска дали одинаковое научно значимое содержимое. Во всех 25 парных
блоках RMSE кандидата ниже RMSE Ridge; средняя разность
`RMSE_Ridge - RMSE_HGBR = 0.04573015523955133`, диапазон
`0.008473870664207461..0.08817938694191596`. Порог `0.05` не достигнут, поэтому
категория `not_supported`. Порог после результата не менялся.

Ограничение: `quality` — порядковая сенсорная оценка, хотя UCI допускает
регрессию. UCI не предоставляет производителя, партию, сорт винограда или
эксперта, поэтому обменность строк заявлена, но не доказана; вывод нельзя
переносить на белое вино, другие регионы, будущие партии или причинность.

Канонические evidence:
`data_registry/st08_11A_wine_quality_red_fold_scores_v01.csv` и
`data_registry/st08_11A_registered_regression_dataset_claim_and_scientific_validation_evidence_v01.json`.
MiniBooNE и 18 защищённых артефактов не изменяются.

## 49. Предлагаемый следующий блок

```text
proposed_next_block: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
ST08_12_status: proposed_not_authorized
```

Отдельная реальная регрессионная проверка теперь существует и честно завершена
отрицательным claim-вердиктом. Это позволяет предложить панель как следующий
продуктовый блок, но не даёт ей автоматической авторизации и не превращает
`not_supported` в положительное доказательство превосходства модели.

## 50. Задачи John

1. Принять либо вернуть ST08_11A.
2. При принятии присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли только предложенный ST08_12.
4. Не снижать порог `0.05` задним числом и не интерпретировать 25/25
   положительных разностей как выполнение заранее зарегистрированного claim.

## 51. ST08_12 — панель на общем проверенном ядре

John принял и закрыл ST08_11A и отдельно авторизовал
`ST08_12_dashboard_shared_core_and_CLI_golden_equivalence`.

```text
ACCEPTED_BY_JOHN: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
TASK_CLOSED: ST08_11A_registered_regression_dataset_claim_and_scientific_validation
NEXT_BLOCK_AUTHORIZED: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
ACCEPTED_BY_JOHN: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
TASK_CLOSED: ST08_12_dashboard_shared_core_and_CLI_golden_equivalence
ST08_12_status: accepted_and_closed_by_john
external_publication_authorized: false
```

Установленная команда `mlcra dashboard --bundle run --output-dir dashboard`
сначала применяет тот же `verify_bundle`, затем строит детерминированный JSON и
две автономные HTML-страницы. Четыре результата: `dashboard_view.json`,
`dashboard_en.html`, `dashboard_ru.html`, `dashboard_manifest.json`.
Golden equivalence означает точное повторное построение view, RU/EN HTML и
SHA-256 из неизменённого bundle; обучение и сеть равны нулю.

Панель не содержит JavaScript или сервера. Динамический текст экранируется,
HTML использует `lang`, семантические заголовки, таблицу с `th scope=col`,
текстовые статусы и адаптивную прокрутку. Отрицательный регрессионный вердикт
`not_supported` проходит тем же трактом без превращения в программную ошибку.

ST08_11A и MiniBooNE не пересчитываются и не меняются. Панель является способом
просмотра проверенного evidence, а не новым научным доказательством.

## 52. Предлагаемый следующий блок

```text
proposed_next_block: ST08_13_release_candidate_completion_security_and_readiness_reaudit
ST08_13_status: proposed_not_authorized
```

## 53. Задачи John

1. ST08_12 принят и закрыт; дополнительных действий по нему не требуется.
2. Если требуется начать ST08_13, отдельно присвоить зарезервированную метку
   авторизации следующего блока с идентификатором
   `ST08_13_release_candidate_completion_security_and_readiness_reaudit`.
3. До такой метки сохранять ST08_13 в состоянии `proposed_not_authorized`.

## 54. ST08_13 — повторный аудит кандидата на релиз

John отдельно авторизовал
`ST08_13_release_candidate_completion_security_and_readiness_reaudit`. Блок
выполнен по профилю `SCIENTIFIC_VALIDATION` как повторное применение неизменной
матрицы 24 требований: без remediation (исправления объекта проверки), без
изменения научных утверждений и без внешних действий.

Метод разделил пять классов доказательств: локальные документы и реестры,
наблюдаемое выполнение, внешние официальные основания, аналитическую
интерпретацию и неустранённую неопределённость. Для каждого требования явно
назначен `PASS`, `FAIL` или `BLOCKED`; затем независимо пересчитаны восемь
измерений, проектная завершённость и готовность к внешнему релизу. Локальный
PASS не использовался как доказательство запуска hosted CI или серверного
сканирования GitHub.

Наблюдаемые локальные результаты:

- baseline — PASS; 63 профильных теста — PASS;
- source/workflow/lock/protected assurance — PASS; 18 из 18 защищённых
  научных артефактов совпали;
- `detect-secrets 1.5.0`: 301 файл, 23 детектора, 0 находок; это ограниченный
  сигнатурный результат, а не гарантия отсутствия всех секретов;
- текущий `pip-audit`: 15 runtime и 35 assurance зависимостей, 0 известных
  уязвимостей на дату запуска; результат зависит от текущей базы advisory;
- sdist/wheel — 34/22 записи, archive assurance — PASS; новая чистая установка,
  `pip check`, `doctor`, walkthrough и 27 тестов установленного пакета — PASS;
- полный неизменённый cumulative pilot завершился кодом 1 с восемью
  историческими FAIL; 0 из 10 проверенных исторических ZIP-имён доступны;
- hosted CI не наблюдался, внешний GitHub secret scanning не включён и не
  наблюдался, публичный репозиторий не создавался.

Итог требований: `19 PASS / 2 FAIL / 3 BLOCKED / 0 SKIPPED`. Итог измерений:
`5 PASS / 2 FAIL / 1 BLOCKED`. D03 имеет FAIL из-за строгого правила REQ08;
D04 имеет BLOCKED из-за REQ12; D08 имеет FAIL из-за отсутствующих внешних
release-контролей. Поэтому отдельно получены:

```text
NEXT_BLOCK_AUTHORIZED: ST08_13_release_candidate_completion_security_and_readiness_reaudit
TECHNICAL_STATUS: FAIL
READINESS: READY_FOR_JOHN_ACCEPTANCE
PROJECT_COMPLETION_VERDICT: FAIL
EXTERNAL_RELEASE_READINESS: FAIL
RELEASE_CLASS: not_ready
```

`TECHNICAL_STATUS: FAIL` по принятой в ST08_02 конвенции описывает объект
проверки: проект нельзя считать завершённым или готовым к релизу. Сама процедура
аудита имеет отдельный `audit_procedure_status=PASS`: она выполнена по контракту,
пересчитывается и защищена отрицательными мутациями. `READY_FOR_JOHN_ACCEPTANCE`
означает, что отрицательный результат можно принять и закрыть как корректно
выполненную задачу; это не готовность к релизу. Практическое следствие —
публикация и выпуск запрещены, а John должен решить судьбу блокеров.

Канонический evidence record:
`data_registry/st08_13_release_candidate_completion_security_and_readiness_reaudit_evidence_v01.json`.
Его независимая проверка:
`scripts/st08_13_release_candidate_reaudit.py`.

## 55. Предлагаемая граница следующего блока

```text
proposed_next_block: ST08_14_public_repository_publication_and_external_release
ST08_14_status: proposed_not_authorized
```

ST08_14 не следует начинать автоматически: это внешний и потенциально
необратимый шаг, а текущий re-audit дал `not_ready`. Перед любой такой
авторизацией необходимо как минимум отдельно распорядиться REQ08/REQ12,
наблюдать hosted CI, получить репозиторное сканирование секретов и принять
осознанное release-решение.

## 56. Задачи John

1. Принять либо отклонить техническое выполнение ST08_13; при принятии отдельно
   присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
2. Подтвердить или изменить disposition недоступных исторических ZIP-шлюзов;
   агент не ослаблял REQ08/REQ12 без такого решения.
3. Не считать имя ST08_14 авторизацией публикации: текущий статус блока —
   только `proposed_not_authorized`.

## 57. ST08_13A — перспективная миграция REQ08/REQ12 на хеш-связанное состояние

John принял и закрыл отрицательный, но процедурно корректный ST08_13 и выбрал
отдельную перспективную миграцию REQ08/REQ12 на текущее хеш-связанное
каноническое состояние без переписывания исторических `FAIL`. Это решение
авторизует только локальную задачу
`ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration`; агент не
приписывает John зарезервированную метку `NEXT_BLOCK_AUTHORIZED`, которой в
сообщении не было.

```text
ACCEPTED_BY_JOHN: ST08_13_release_candidate_completion_security_and_readiness_reaudit
TASK_CLOSED: ST08_13_release_candidate_completion_security_and_readiness_reaudit
ST08_13A_authorization_basis: exact_John_decision_text_without_invented_reserved_label
ST08_13A_status: technical_pass_ready_for_john_acceptance
historical_ST08_13_REQ08: FAIL_PRESERVED
historical_ST08_13_REQ12: BLOCKED_PRESERVED
prospective_v02_REQ08: NOT_EVALUATED
prospective_v02_REQ12: NOT_EVALUATED
external_release_authorized: false
```

Практический смысл: ST08_13 остаётся неизменным историческим аудитом по v01.
Его REQ08=`FAIL`, REQ12=`BLOCKED`, итог `not_ready` и причины не исправляются
задним числом. Новый файл
`configs/project_readiness/stage08_project_completion_and_release_readiness_requirements_v02.csv`
имеет те же 24 строки; все строки, кроме REQ08 и REQ12, совпадают с v01 точно.
В целевых строках неизменны идентификатор, измерение, роль агрегации и
`design_status=NOT_EVALUATED`. Поэтому ST08_13A создаёт только будущий критерий,
но не присваивает ему результат и не выполняет новый readiness-аудит.

REQ08 v02 отделяет актуальные проверки от исторической диагностики. Для
будущего PASS нужны зелёные baseline, применимые профильные проверки и новый
контроль канонического состояния. Полный cumulative pilot по-прежнему должен
исполняться; его восемь зарегистрированных исторических FAIL обязаны совпасть
точно, а любой новый `FAIL` или `BLOCKED` отклоняется. Таким образом история не
скрыта и не превращена искусственно в PASS, но устаревшие внешние условия не
подменяют состояние текущего кода.

REQ12 v02 заменяет обязательную доступность старых внешних ZIP для будущей
оценки на версионированный CSV-манифест каждого текущего проектного файла:
repository-relative путь, SHA-256 точных байтов и размер. Из манифеста исключены
только сам манифест и связывающий его evidence record, чтобы разорвать
математический хеш-цикл; их пути и причина исключения зарегистрированы в
контракте. Публичный path manifest, 18 защищённых научных SHA-256, lock-файлы,
runtime provenance и package evidence остаются независимыми проверками, а не
заменяются одним хешем.

[NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
определяет SHA-256 и объясняет, что digest обнаруживает изменение сообщения с
очень высокой вероятностью. Поэтому здесь хеш доказывает совпадение байтов, но
не корректность, авторство или научную состоятельность. [NIST SP 800-218
SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) поддерживает защиту
release-файлов и provenance, а [NIST SP 800-53 Rev. 5 CM-2/CM-3](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
— поддержание текущей baseline-конфигурации и документированное управление
изменениями. Отсюда следует новая версия v02 при сохранении v01, а не
редактирование результата после наблюдаемого FAIL.

Исполняемый контроль
`scripts/st08_13A_current_canonical_hash_assurance.py` проверяет точные хеши
пяти исторических файлов ST08_13, разрешённую разницу v01→v02, полный состав и
хеши текущего состояния, публичный перечень, 18 защищённых артефактов, CI,
change scope и канонические документы. Отрицательные тесты отклоняют изменение
нецелевого требования, защищённого поля, пропуск/дубликат/подмену хеша или
размера, переписывание исторического статуса, внешнее действие и авторизацию
следующего блока.

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
REAUDIT_V02_PERFORMED: false
PROJECT_COMPLETION_VERDICT_CURRENTLY_REPLACED: false
EXTERNAL_ACTIONS_PERFORMED: 0
CHECKPOINT_ZIP: SKIPPED
```

`PASS` относится только к целостности миграции и новой проверяемой цепочки.
Последний фактический проектный verdict остаётся ST08_13=`FAIL/not_ready`, пока
отдельно авторизованный будущий аудит не применит v02. ZIP пропущен, потому что
John выбрал хеш-связанное локальное состояние, Stage 8 остаётся открытым,
браузерного handoff нет и внешнее действие не выполняется.

## 58. Предлагаемый следующий блок

```text
proposed_next_block: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
ST08_13B_status: proposed_not_authorized
ST08_14_status: proposed_not_authorized
```

После снятия перспективной внутренней зависимости REQ08/REQ12 остаются
внешние блокеры ST08_13: публичный репозиторий не создан, hosted CI не
наблюдался и серверное secret scanning не включено. Логически безопаснее
отдельно получить эти доказательства без публикации версии и релиза, а затем
проводить новый аудит по v02. Это предложение не разрешает создать
репозиторий, отправить код, включить внешнюю службу или выпускать ML-CRA.

## 59. Задачи John

1. Принять либо вернуть на доработку только ST08_13A.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли внешний блок ST08_13B; без такого решения
   агент не создаёт репозиторий и не отправляет файлы.
4. Не интерпретировать миграцию как новый PASS проекта: v02 ещё не применялась
   в отдельном readiness-аудите.

## 60. ST08_13B — публичный репозиторий, hosted CI и серверные меры безопасности

John принял и закрыл ST08_13A и передал точный идентификатор внешнего блока
`ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence`.
Это авторизует создание публичного `Vanargo/ML-CRA`, отправку только разрешённых
манифестом файлов, наблюдение GitHub Actions и настройку репозиторных мер
безопасности. Тег версии, GitHub Release, PyPI и научные изменения не разрешены.

```text
ACCEPTED_BY_JOHN: ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration
TASK_CLOSED: ST08_13A_REQ08_REQ12_current_canonical_hash_evidence_migration
NEXT_BLOCK_AUTHORIZED: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
ST08_13B_status: technical_pass_ready_for_john_acceptance
hosted_CI_observed: success_run_32832251575_commit_74ccb767f08def2ce4c6cf0441a2ba044db1e66a
external_release_authorized: false
```

Проверка до публикации выявила, что прежний local source assurance (локальный
контроль исходного дерева) связывал все 353 локальных пути, включая 45 путей с
явным `EXCLUDE_*`. Публикация всех 353 нарушила бы утверждённую границу, а
публикация разрешённого подмножества заставила бы старую CI сравнивать GitHub-
копию с отсутствующими запрещёнными файлами. Поэтому ST08_13B разделяет два
набора: полный локальный policy inventory (инвентарь политики) и точный
`git ls-files` inventory (инвентарь отслеживаемого публичного дерева).

`data_registry/st08_13B_publication_tree_manifest_v01.csv` хранит путь,
SHA-256 и размер каждого публикуемого файла. Сам manifest и обновляемое после
внешнего запуска evidence присутствуют в Git, но исключены из строк хешей для
разрыва цикла; их точные пути обязательны. Неизвестный, запрещённый, лишний,
пропущенный или изменённый tracked path блокирует CI.

Это решение поддерживается [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final),
[NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) и
официальной документацией GitHub по
[workflow runs](https://docs.github.com/en/rest/actions/workflow-runs),
[secret scanning](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning),
[protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
и [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository).
Внешние документы задают метод и возможности GitHub; фактический PASS может
быть назначен только после наблюдаемого run и ответов официального API.

ST08_13A остаётся неизменяемым историческим снимком и больше не исполняется как
проверка будущего текущего состояния. Hosted CI вместо него выполняет текущий
ST08_13B publication-tree gate, сохраняя отдельную проверку исторического
ST08_13 и точные SHA-256 семи артефактов ST08_13A.

## 61. Состояние внешнего выполнения ST08_13B

Публичный репозиторий `Vanargo/ML-CRA` наблюдён через официальный GitHub REST
API как открытый, активный и использующий `main` по умолчанию. Для точного
коммита `74ccb767f08def2ce4c6cf0441a2ba044db1e66a` запуск GitHub Actions
`32832251575` и задание `assurance` завершились `success`; все 20 содержательных
шагов задания также имеют `success`.

John включил через административный интерфейс GitHub Dependabot alerts, secret
scanning, push protection и private vulnerability reporting. Последнее
дополнительно подтверждено публичным REST API. Активный ruleset — набор правил —
`21408995` применяется к ветви по умолчанию без списка обхода, запрещает
удаление и force push, требует pull request, линейную историю, разрешение
обсуждений, актуальность ветви и точную проверку `assurance` от GitHub Actions.

Свежий удалённый clone восстановил тот же SHA коммита и прошёл точную проверку
публикационного дерева: 314 tracked paths, 312 хешированных файлов, 0
расхождений содержимого, 18/18 защищённых научных Git blobs без расхождений.
Теги, GitHub Releases и публикация пакета не выполнялись. Это программная и
инфраструктурная верификация; научные утверждения, протоколы и результаты не
изменялись.

Итоговая машиночитаемая запись находится в
`data_registry/st08_13B_public_repository_hosted_CI_and_security_evidence_v01.json`.
ST08_13B технически завершён и ожидает принятия John. Последний проектный
readiness-verdict остаётся историческим ST08_13=`FAIL/not_ready`; отдельный
перспективный аудит по v02 не входит в этот блок и не выполнялся.

## 62. Задачи John

1. Принять либо вернуть только ST08_13B.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Не считать публичный development repository выпуском версии.
4. Отдельно решить, авторизовать ли новый readiness-аудит по v02; он не входит
   в ST08_13B и пока не разрешён.

## 63. ST08_13C — перспективный повторный аудит кандидата v02

John принял и закрыл ST08_13B и отдельно авторизовал
`ST08_13C_prospective_release_candidate_v02_reaudit`. Задача применяет все 24
требования v02 к одному точному кандидату. Исторические v01, ST08_13, ST08_13A
и ST08_13B не переписываются; тег, GitHub Release, PyPI, обучение и изменение
научного утверждения не разрешены.

```text
ACCEPTED_BY_JOHN: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
TASK_CLOSED: ST08_13B_public_repository_bootstrap_hosted_CI_and_repository_security_evidence
NEXT_BLOCK_AUTHORIZED: ST08_13C_prospective_release_candidate_v02_reaudit
ST08_13C_profile: SCIENTIFIC_VALIDATION
PROJECT_COMPLETION_VERDICT: PASS_if_and_only_if_all_registered_candidate_observations_pass
EXTERNAL_RELEASE_READINESS: BLOCKED_until_John_release_authorization
external_release_authorized: false
```

Метод сохраняет fail-closed агрегацию: любой `FAIL` делает соответствующее
измерение `FAIL`, а отсутствие необходимого доказательства даёт `BLOCKED`.
REQ08 v02 допускает исторический ненулевой cumulative pilot только при точном
совпадении восьми зарегистрированных исторических FAIL и отсутствии нового
`FAIL` или `BLOCKED`. REQ12 v02 использует новый версионированный
`data_registry/st08_13C_release_candidate_v02_manifest_v01.csv`, потому что
ST08_13A и ST08_13B являются неизменяемыми историческими baseline — исходными
состояниями — и не могут корректно описывать добавленный ST08_13C.

Манифест связывает каждый текущий отслеживаемый путь, кроме самого манифеста и
завершаемой после hosted CI записи evidence, с SHA-256 и размером канонического
Git blob. Оба исключённых пути остаются обязательными членами дерева. Такое
версионирование следует управлению baseline и изменениями CM-2/CM-3 из
[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final),
а значение SHA-256 ограничивается обнаружением изменения байтов по
[NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final): хеш не
доказывает корректность или научную состоятельность.

[NIST AI RMF MANAGE 1.1](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
поддерживает отдельное определение, достигает ли система заявленных целей и
следует ли продолжать deployment — развёртывание. Поэтому при 24/24 `PASS`
проектная завершённость может получить `PASS`, но готовность к внешнему выпуску
остаётся `BLOCKED` единственным шлюзом
`John_release_authorization_not_granted`. Это не технический дефект и не
разрешение релиза.

## 64. Доказательный порядок и граница итогового вердикта ST08_13C

Локальная реализация и проверка кандидата предшествуют внешнему наблюдению.
Задание GitHub Actions `assurance` должно успешно выполниться на точном
хеш-связанном кандидате pull request — запроса на слияние. Это соответствует
официальной документации GitHub: required status check — обязательная проверка
статуса — должна пройти до слияния, а строгий режим требует актуальности ветви.
До наблюдаемого успешного запуска evidence имеет предварительный статус и
итоговый PASS не назначается.

После успешного hosted run окончательная запись
`data_registry/st08_13C_prospective_release_candidate_v02_reaudit_evidence_v01.json`
фиксирует идентификатор запуска и commit SHA, 24 результата, восемь измерений,
раздельные агрегаты и ограничения интерпретации. Сам hosted CI не является
независимой научной репликацией: по определению National Academies
вычислительная воспроизводимость на тех же данных и коде отличается от
репликации на новых данных. Нового обучения и нового научного verdict в
ST08_13C нет.

Итог, допустимый только после всех зарегистрированных наблюдений:

```text
TECHNICAL_STATUS: PASS
READINESS: READY_FOR_JOHN_ACCEPTANCE
REQUIREMENTS: PASS=24 FAIL=0 BLOCKED=0 SKIPPED=0
DIMENSIONS: PASS=8 FAIL=0 BLOCKED=0
PROJECT_COMPLETION_VERDICT: PASS
EXTERNAL_RELEASE_READINESS: BLOCKED
RELEASE_BLOCKERS: John_release_authorization_not_granted
RELEASE_ACTIONS_PERFORMED: 0
```

Значение `PASS` подтверждает выполнение зарегистрированной проектной границы,
но не расширяет MiniBooNE или Wine Quality claims. `BLOCKED` означает, что
внешний релиз запрещён до отдельного решения John. ZIP пропускается при
успешном защищённом pull request и проверяемом удалённом Git-восстановлении.

## 65. Задачи John

1. Опубликовать подготовленную агентом ветвь ST08_13C и открыть pull request в
   `main`, не выполняя слияние до успешного `assurance`.
2. Передать агенту ссылку на pull request или успешный run, чтобы завершить
   точную запись внешнего доказательства.
3. После итогового отчёта принять либо вернуть ST08_13C; только John может
   присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
4. Не считать принятие ST08_13C разрешением выпуска: оно требует отдельного
   явного решения.

## 66. ST08_14 — проектирование границы выпуска 0.1.0

John принял и закрыл `ST08_13C_prospective_release_candidate_v02_reaudit` и
авторизовал
`ST08_14_release_0_1_0_scope_channel_and_execution_contract_design`. Профиль
`CHANGE` разрешает только локальный контракт, исполняемую проверку,
доказательную запись, новый манифест текущего дерева и каноническую регистрацию.
Версия пакета, CITATION release fields — поля выпуска в CITATION — тег,
GitHub Release, TestPyPI, PyPI и научные артефакты защищены от изменения.

```text
ACCEPTED_BY_JOHN: ST08_13C_prospective_release_candidate_v02_reaudit
TASK_CLOSED: ST08_13C_prospective_release_candidate_v02_reaudit
NEXT_BLOCK_AUTHORIZED: ST08_14_release_0_1_0_scope_channel_and_execution_contract_design
ST08_14_profile: CHANGE
release_authorized: false
release_actions_performed: 0
```

### 66.1. MAPE-K и решение о последовательности

Monitor — наблюдение — зафиксировал `0.1.0.dev0`, отсутствие тегов и GitHub
Releases, проектный PASS ST08_13C и единственный owner gate — шлюз владельца.
Analyze — анализ — отклонил немедленный `1.0.0`, потому что SemVer связывает
его со стабильным публичным API, а принятый release train — релизный поезд —
требует сначала `0.1.0`. Объединённый немедленный `0.1.0` также отклонён:
обратимые метаданные нельзя безопасно смешивать с труднообратимой публикацией.

Plan — план — разделяет пять этапов: контракт; финализация `0.1.0`; повторный
аудит точного кандидата; GitHub Release; опциональная PyPI-публикация. Execute
— выполнение — текущего блока создаёт только первый этап. Knowledge — знания —
сохраняет матрицу решения, источники, манифест, проверки и остаточные риски.
Взвешенные оценки вариантов равны `1.40`, `2.60` и `5.00`; выбран поэтапный
вариант. Эти оценки являются прозрачным инженерным средством для текущего
контекста, а не универсальным эмпирическим рейтингом.

### 66.2. Зафиксированная релизная граница

- первый поддерживаемый выпуск: `0.1.0`;
- будущий тег: `v0.1.0` на точном прошедшем аудит commit SHA;
- основной канал: GitHub Release;
- последовательность GitHub: draft → приложить и проверить активы →
  опубликовать immutable release;
- обязательные активы: `ml_cra-0.1.0.tar.gz`,
  `ml_cra-0.1.0-py3-none-any.whl`, `SHA256SUMS`;
- PyPI и TestPyPI: `deferred_not_authorized`;
- рекомендуемая будущая PyPI-аутентификация: Trusted Publishing GitHub
  Actions/OIDC с отдельным минимально привилегированным workflow — рабочим
  процессом — и ручным owner approval — подтверждением владельца;
- `1.0.0`: только после выпуска `0.1.0`, disposition — разбора — последующих
  замечаний и отдельного решения John о стабильном публичном API.

Метод следует официальному PyPA packaging flow — процессу упаковки — с
разделением исходного дерева, `sdist`, `wheel` и загрузки. GitHub рекомендует
для неизменяемых выпусков сначала черновик со всеми активами. NIST SSDF требует
защищать release-релевантные файлы и происхождение. SHA-256 по FIPS 180-4
обнаруживает изменение байтов, но не доказывает корректность или научную
состоятельность.

### 66.3. Целостность и граница доказательства

`data_registry/st08_14_release_0_1_0_contract_manifest_v01.csv` связывает
текущее отслеживаемое дерево каноническими Git-blob SHA-256 и размерами. Сам
манифест и завершаемое evidence — свидетельство — являются двумя
зарегистрированными исключениями для разрыва хеш-цикла, но остаются
обязательными tracked paths — отслеживаемыми путями.

Шесть артефактов ST08_13C защищены точными каноническими SHA-256; 18 научных
артефактов также остаются неизменными. Текущий CI заменяет ST08_13C как
current-state gate — шлюз текущего состояния — на ST08_14, сохраняя ST08_13C
как историческое доказательство. Ни хеш, ни GitHub attestation — подтверждение
происхождения — не заменяют программную проверку, научную валидацию и решение
John о выпуске.

## 67. Предлагаемый следующий блок

```text
proposed_next_block: ST08_14A_release_0_1_0_candidate_finalization
ST08_14A_status: proposed_not_authorized
release_authorized: false
```

ST08_14A должен локально изменить метаданные разработки на финальную версию
`0.1.0`, подготовить согласованные двуязычные release notes, собрать и
проверить будущие активы без тега и публикации. После него необходим отдельный
ST08_14B — повторный аудит финального дерева; только отдельный ST08_14C может
получить право выполнить внешний GitHub Release. PyPI остаётся возможным
ST08_14D и требует самостоятельного решения John.

## 68. Задачи John

1. Принять либо вернуть только ST08_14.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли ST08_14A; текущая задача не даёт права
   менять версию, создавать тег или публиковать выпуск.

## 69. ST08_14A — финализация локального кандидата 0.1.0

John принял и закрыл `ST08_14_release_0_1_0_scope_channel_and_execution_contract_design`
и отдельно авторизовал `ST08_14A_release_0_1_0_candidate_finalization`.
Профиль `CHANGE` разрешает заменить только метаданные версии разработки на
`0.1.0`, подготовить двуязычные примечания и воспроизводимо собрать локальные
активы. Тег, GitHub Release, TestPyPI, PyPI, ST08_14B и изменение научного
состояния не разрешены.

```text
ACCEPTED_BY_JOHN: ST08_14_release_0_1_0_scope_channel_and_execution_contract_design
TASK_CLOSED: ST08_14_release_0_1_0_scope_channel_and_execution_contract_design
NEXT_BLOCK_AUTHORIZED: ST08_14A_release_0_1_0_candidate_finalization
ST08_14A_profile: CHANGE
release_authorized: false
release_actions_performed: 0
```

### 69.1. Метаданные и граница утверждения

`pyproject.toml`, runtime — исполняемая среда — и `CITATION.cff` согласованы с
версией `0.1.0`; классификатор зрелости изменён с Pre-Alpha на Alpha. Поле
`date-released` намеренно отсутствует: CFF 1.2 определяет его как дату
фактического выпуска, которого ST08_14A не выполняет. Двуязычный файл
`RELEASE_NOTES_0.1.0.md` описывает функции, поддерживаемую среду, ограничения и
научную границу без универсализации результатов MiniBooNE и UCI Wine Quality.

Решение следует официальным спецификациям
[PyPA project metadata](https://packaging.python.org/en/latest/specifications/pyproject-toml/),
[Core Metadata](https://packaging.python.org/en/latest/specifications/core-metadata/)
и [CFF 1.2 schema guide](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md).
Версия `0.1.0` является финальным идентификатором пакета, но сама по себе не
утверждает стабильность API уровня `1.0.0` и не доказывает публикацию.

### 69.2. Воспроизводимые локальные активы

Кандидат строится дважды из канонического Git index — индекса Git — при
`SOURCE_DATE_EPOCH=1787616000`. Наблюдаемый wheel совпал побайтно без
дополнительной обработки. Обычные gzip/sdist-байты не совпали из-за изменчивых
служебных полей, поэтому контракт явно регистрирует нормализацию только
несемантических `mtime`, владельца, порядка и gzip-заголовка с сохранением
путей, байтов файлов, каталогов и прав доступа. Символические ссылки,
устройства, FIFO и небезопасные пути запрещены.

Такой обмен единой временной меткой использует спецификацию
[SOURCE_DATE_EPOCH](https://reproducible-builds.org/specs/source-date-epoch/), а
структура исходного архива проверяется по официальной
[PyPA sdist specification](https://packaging.python.org/en/latest/specifications/source-distribution-format/).
Две нормализованные копии `sdist` и две копии wheel обязаны иметь одинаковые
SHA-256. `SHA256SUMS` связывает только байты активов: по
[NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) хеш
обнаруживает изменение, но не заменяет программную проверку или научную
валидацию.

Итоговый локальный набор состоит ровно из `ml_cra-0.1.0.tar.gz`,
`ml_cra-0.1.0-py3-none-any.whl` и `SHA256SUMS`. Он исключён из Git и может быть
точно перестроен; ZIP не нужен при защищённом удалённом Git и успешной полной
проверке.

## 70. Предлагаемый следующий блок

```text
proposed_next_block: ST08_14B_release_0_1_0_execution_security_preflight
ST08_14B_status: proposed_not_authorized
release_authorized: false
```

ST08_14B должен отдельно повторно проверить точное финальное дерево и
операционную безопасность будущего выпуска. Только более поздний и отдельно
авторизованный ST08_14C может создавать тег и GitHub Release; PyPI остаётся
отложенным.

## 71. Задачи John

1. Принять либо вернуть только ST08_14A после итогового технического отчёта.
2. При принятии только John может присвоить `ACCEPTED_BY_JOHN` и `TASK_CLOSED`.
3. Отдельно решить, авторизовать ли ST08_14B; текущий блок не разрешает ни его
   выполнение, ни тег, ни публикацию.
