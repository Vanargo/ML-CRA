# Evidence record — агентная синхронизация baseline после ST07_06

## 1. Идентификация

```text
record_id: ST07_06_agent_baseline_reconciliation_v01
pilot_status: ready_for_john_acceptance
source_baseline: ml-cra_v13
source_archive_sha256: 753f11009e1976b207ab509bd522da533ff8042703f135c5c25f055ea4d79e8e
scientific_claim_changed: false
scientific_artifacts_changed: false
stage07_next_block_authorized: false
```

Цель пилота: проверить агентный контур ML-CRA на реальной, но ограниченной задаче — синхронизировать канонические документы с уже реализованным и принятым John блоком `ST07_06_cost_quality_audit_extraction`.

## 2. Основания

Локальные источники:

- `roadmap.md` baseline v13 называл ST07_06 следующим шагом;
- `docs/stages/stage_07_code_modularization.md` baseline v13 фиксировал состояние только после ST07_05;
- `src/mlcra/verdicts.py` baseline v13 уже содержал `build_cost_quality_audit(...)`;
- `notebooks/04_dataset_smoke_experiments.ipynb` baseline v13 уже использовал модульный вызов;
- `data_registry/openml_miniboone_stage05_cost_quality_audit.csv` является каноническим результатом 18 × 40;
- `docs/stages/stage_06_packaging_and_publication.md` называл три обязательных nested-артефакта путями, отсутствующими в архиве.

Пользовательское основание: в чате `ML-CRA/Модульная упаковка вычислительного слоя 3.0` John сообщил, что изменения применены, результат совпал с ожидаемым, и разрешил двигаться дальше.

Аналитический вывод: baseline v13 содержал не незавершённую реализацию, а документально незакрытый принятый результат.

## 3. Разрешённый и фактический scope

Машинно-читаемый список разрешённых файлов: `docs/agent/pilot_change_scope_v01.csv`.

Добавлены:

- `AGENTS.md`;
- `.agents/skills/ml-cra-stage-gate/SKILL.md`;
- `.agents/skills/ml-cra-stage-gate/agents/openai.yaml`;
- `docs/agent/baseline_manifest_v13.csv`;
- `docs/agent/pilot_change_scope_v01.csv`;
- `docs/agent/agent_verification_environment_v01.csv`;
- `docs/agent/ST07_06_agent_baseline_reconciliation_evidence.md`;
- `scripts/agent_verify.py`.

Изменены:

- `roadmap.md`;
- `docs/stages/stage_06_packaging_and_publication.md`;
- `docs/stages/stage_07_code_modularization.md`.

Не изменены:

- `src/mlcra/*.py` и `src/mlcra/data_registry/*.py`;
- все `notebooks/*.ipynb`;
- все исходные `configs/*.csv` и `data_registry/*.csv`;
- все файлы `docs/archive/`;
- claim, protocol, model space, verdict policy и численные результаты.

## 4. Выполненные изменения

### 4.1. Агентный контракт

`AGENTS.md` фиксирует миссию, иерархию источников истины, автономность внутри одного принятого блока, обязательную остановку на stage boundary, требования к полному чтению необходимых файлов, цитированию, неопределённости, верификации, evidence record и контрольной точке.

### 4.2. Project skill

`.agents/skills/ml-cra-stage-gate/SKILL.md` реализует MAPE-K/stage-gate workflow:

```text
authority → monitor → analyze → plan → execute → verify/validate → knowledge/evidence → John gate
```

Skill создан штатным Skill Creator и прошёл `quick_validate.py`:

```text
Skill is valid!
```

Публичный plugin не создан: workflow относится к одному проекту и ещё проходит первый эксплуатационный пилот. Repo-local skills предназначены именно для проектных повторяемых процессов: https://learn.chatgpt.com/docs/build-skills.

### 4.3. Контрольный контур

`scripts/agent_verify.py` проверяет:

1. исходный manifest и разрешённый change scope;
2. синтаксис Python без создания новых `pyc`;
3. структуру CSV с автоматическим выбором разделителя из `,`, `;`, tab;
4. JSON/nbformat-4 структуру notebook и фактическую инвентаризацию основной тетради;
5. обязательные пути;
6. отсутствие ошибочных путей Stage 6 и наличие канонического статуса ST07_06;
7. regression equality ST07_04–ST07_06.

На первом предварительном прогоне валидатор ошибочно счёл исторический `openml_first_diagnostic_notebook_plan.csv` некорректным, потому что первоначальная реализация предполагала разделитель `,`. Проверка была исправлена на детерминированный выбор согласованного разделителя. Это изменение исправляет только новый инструмент контроля и не изменяет проектные CSV.

### 4.4. Документальная синхронизация

Stage 6:

- обязательные пути исправлены на фактические `openml_miniboone_nested_outer_scores.csv`, `openml_miniboone_nested_selected_params.csv`, `openml_miniboone_nested_summary.csv`;
- code audit ST06_05 явно обозначен как исторический снимок, а не описание состояния после Stage 7.

Stage 7 и roadmap:

- добавлен `ST07_06_status: accepted_by_john`;
- зафиксированы модульная функция, notebook-вызов и регрессионное равенство 18 × 40;
- историческая инвентаризация ST07_02 51/11/40 отделена от текущей 52/11/41;
- `execution_count: null` последней ячейки зафиксирован как ограничение notebook provenance;
- следующий блок установлен в `decision_pending`, а не выбран агентом.

## 5. «Как было → Как стало» для Python/notebook

Исходные Python-файлы и notebook не изменялись.

Единственный новый Python-файл:

### Как было

```text
scripts/agent_verify.py: файл отсутствовал
```

### Как стало

```text
scripts/agent_verify.py: создан как детерминированный read-only валидатор baseline и pilot
```

Полное каноническое содержание находится непосредственно в `scripts/agent_verify.py`; файл не заменяет научный код и не записывает результаты в `data_registry/`.

## 6. Результаты проверок

Команда:

```bash
python scripts/agent_verify.py --mode pilot
```

Фактический окончательный результат (exit code 0):

| Проверка | Результат | Значение |
|---|---|---|
| Baseline/change scope | PASS | 158 manifest rows; 3 разрешённых modified; 8 разрешённых added; 0 missing; 0 out-of-scope |
| Python syntax | PASS | 8 `.py` файлов |
| CSV structure | PASS | 76 CSV, согласованные строки после определения разделителя |
| Notebook structure | PASS | 4 непустых JSON; основная тетрадь 52/11/41; 1 ожидаемо пустая |
| Required paths | PASS | 8 обязательных путей |
| Documentary consistency | PASS | Stage 6 paths и ST07_06 status согласованы |
| ST07_04 regression | PASS | 19 × 24; columns equal; table equal |
| ST07_05 regression | PASS | 22 × 23; columns equal; table equal |
| ST07_06 regression | PASS | 18 × 40; columns equal; table equal |

Отдельный отчёт передачи контрольной точки не создавался, поскольку
checkpoint ZIP не был разрешён. Результаты pilot зафиксированы в настоящем
evidence record.

## 7. Тип и предел доказательства

Выполнены:

- configuration/baseline audit;
- статическая синтаксическая верификация;
- documentary consistency verification;
- golden-master regression verification;
- структурная проверка CSV и notebook JSON.

Не выполнены и не заявляются:

- повторное обучение моделей;
- независимая научная валидация MiniBooNE claim;
- Jupyter-выполнение всего notebook;
- `nbformat.validate`, потому что пакет `nbformat` отсутствует;
- lint и type checking, потому что `ruff` и `mypy` отсутствуют;
- восстановление исторической среды первоначального эксперимента.

Среда проверок записана в `docs/agent/agent_verification_environment_v01.csv` и обозначена только как `agent_verification_environment`.

## 8. Решение по `.codex/config.toml`

Файл `.codex/config.toml` не создан. Текущий пилот не требует изменения модели, MCP, hooks, сети, sandbox или approval policy. Workflow-граница 2A уже выражена в `AGENTS.md` и skill; расширять технические разрешения ради неё не требуется.

Это соответствует принципу минимальных полномочий. Project config Codex применяется только в доверенных проектах и должен содержать подтверждённые repo-specific настройки: https://learn.chatgpt.com/docs/config-file/config-basic.

## 9. Оставшиеся неопределённости и отложенные задачи

1. Точные версии исходной научной среды Stage 5 неизвестны.
2. Последняя ячейка notebook хранит outputs при `execution_count: null`; её метаданные не являются самостоятельным доказательством свежего запуска.
3. Пустые PMLB notebook и три `data_registry` module stubs не классифицированы John как intentional/deferred.
4. Следующий блок Stage 7 не определён.
5. Переход автономности с 2A на 2В не разрешён этим пилотом.

## 10. Локальная onboarding-проверка

### 10.1. Идентификация и среда

```text
block_id: AGENT_ONBOARDING_FIX_02_LOCAL_ARTIFACT_CLASSIFICATION
wmi_os_caption: Майкрософт Windows Server 2019 Standard
wmi_os_version: 10.0.17763
wmi_os_build_number: 17763
wmi_os_product_type: 3
wmi_os_architecture: 64-разрядная
python_platform_observation: Windows-2019Server-10.0.17763-SP0
python_win32_ver_observation: ('2019Server', '10.0.17763', 'SP0', 'Multiprocessor Free')
os_identification_status: reconciled
python_executable: ml-cra-venv/Scripts/python.exe
python_version: 3.12.0
pandas_version: 3.0.2
numpy_version: 2.4.4
scikit_learn_version: 1.8.0
scientific_claim_changed: false
scientific_artifacts_changed: false
stage07_next_block_authorized: false
post_evidence_pilot: pass
onboarding_status: PASS_ONBOARDING
checkpoint_created: false
```

Буквальный вывод `Win32_OperatingSystem`:

```text
Caption        : Майкрософт Windows Server 2019 Standard
Version        : 10.0.17763
BuildNumber    : 17763
ProductType    : 3
OSArchitecture : 64-разрядная
```

Буквальный вывод Python runtime:

```text
platform=Windows-2019Server-10.0.17763-SP0
win32_ver=('2019Server', '10.0.17763', 'SP0', 'Multiprocessor Free')
```

`Win32_OperatingSystem` используется как источник инвентаризационных сведений
об установленной Windows. `platform.platform()` и `platform.win32_ver()`
сохраняются как независимые наблюдения Python runtime. Источники согласуются
по серверному выпуску Windows 2019, версии `10.0.17763` и build `17763`;
различаются только локализованная подпись WMI и нормализованное представление
Python. Расхождение представления reconciled и не влияет на результаты pilot,
которые зависят от проверенного Python-окружения и файловых контрактов проекта,
а не от маркетингового имени ОС.

Среда относится только к локальной агентной верификации. Она не
реконструирует историческую среду научных экспериментов Stage 5.

### 10.2. Причина исходного FAIL и исправление

Первоначальный onboarding-запуск выполнял рекурсивный inventory всего
`PROJECT_ROOT`. Из-за этого локальное окружение `ml-cra-venv` ошибочно
участвовало в baseline/change-scope audit как 19 677 добавленных файлов, из
которых 19 669 считались out-of-scope.

В `scripts/agent_verify.py` введён единый project inventory. Он:

- обнаруживает `ml-cra-venv` по имени и любое виртуальное окружение по
  `pyvenv.cfg` в его корне;
- исключает виртуальные окружения из baseline/change-scope inventory, поиска
  CSV, поиска notebook и рекурсивного подсчёта файлов проекта;
- исключает только `__pycache__`, `*.pyc`, `*.pyo`, `.pytest_cache`,
  `.mypy_cache`, `.ruff_cache` и `.ipynb_checkpoints`;
- не исключает неизвестные каталоги;
- сохраняет исходный manifest из 158 записей и строгий критерий
  `out_of_scope=0`;
- выводит число проигнорированных локальных файлов и найденные корни
  виртуальных окружений.

После исправления inventory были выявлены три отдельные незарегистрированные
локальные артефакта в `agent/`. John классифицировал их как не входящие в
принятую версию ML-CRA v14 и распорядился консервативно переместить весь
каталог за пределы корня проекта без удаления и без добавления путей в
manifest, change scope или исключения verifier.

### 10.3. Локальные артефакты и карантин

| Исходный путь | Размер, байт | SHA-256 до перемещения | SHA-256 после перемещения | Сравнение с каноническим файлом |
|---|---:|---|---|---|
| `agent/AGENTS.md` | 5164 | `d831090dac721cdc7f4cad17d41f192a575c922ef8fab0519faee9970b48b207` | `d831090dac721cdc7f4cad17d41f192a575c922ef8fab0519faee9970b48b207` | побайтно отличается от корневого `AGENTS.md` (`7afcdea8651510d2261d79d46dbb9e60598e433dd6977ca241e1a8167ffd0804`) |
| `agent/ML-CRA_agent_setup_support_plan_v01.md` | 19296 | `8a39fa18e6934ea1efe037157feaaa6eb39318d97a59111437fa0984080aa127` | `8a39fa18e6934ea1efe037157feaaa6eb39318d97a59111437fa0984080aa127` | каноническая пара не задана |
| `agent/SKILL.md` | 5219 | `6e9d9fcdd6212759631b72714ad67fe539fd22f77b9926420a95601b527decde` | `6e9d9fcdd6212759631b72714ad67fe539fd22f77b9926420a95601b527decde` | побайтно идентичен `.agents/skills/ml-cra-stage-gate/SKILL.md` |

Путь карантина:

```text
C:\Users\Vanargo\Desktop\ML-CRA_local_artifacts_20260720\agent
```

После перемещения исходный каталог `C:\Users\Vanargo\Desktop\ML-CRA\agent`
отсутствует. В карантине присутствуют ровно три ожидаемых файла без
подкаталогов; все SHA-256 совпадают с pre-move значениями. Содержимое не
копировалось обратно в проект и не применялось к каноническим файлам.

### 10.4. Pilot после карантинизации

Команда выполнена через существующий интерпретатор с process-local
`PYTHONDONTWRITEBYTECODE=1`:

```powershell
.\ml-cra-venv\Scripts\python.exe scripts\agent_verify.py --mode pilot
```

Фактический результат первого запуска после карантинизации (exit code 0):

| Проверка | Результат | Значение |
|---|---|---|
| Baseline/change scope | PASS | `manifest_rows=158; modified=3; added=8; missing=0; out_of_scope=0` |
| Python syntax | PASS | `files=8` |
| CSV structure | PASS | `files=76` |
| Notebook structure | PASS | `nonempty_json_valid=4; main_inventory=52/11/41; expected_empty=1` |
| Required paths | PASS | `paths=8` |
| Documentary consistency | PASS | Stage 6 paths и ST07_06 status согласованы |
| ST07_04 regression | PASS | `(19, 24); equal=True; columns=True` |
| ST07_05 regression | PASS | `(22, 23); equal=True; columns=True` |
| ST07_06 regression | PASS | `(18, 40); equal=True; columns=True` |
| BLOCKED | отсутствуют | Все зависимости доступны в `ml-cra-venv` |

Verifier сообщил:

```text
ignored_local_files=26843
virtual_environment_roots=['ml-cra-venv']
```

Перед перемещением и обновлением evidence зафиксирован агрегированный SHA-256
84 scientific artifacts:

```text
dd1458865422cdd1c1cb26e38f48ddc10e5d91b09f3e419034c55cb72b599cf3
```

Повторный pilot после обновления evidence завершён с exit code 0 и теми же
PASS-результатами. Финальное сравнение подтвердило неизменность всех 84
scientific artifacts:

```text
post_scientific_files: 84
post_scientific_sha256_aggregate: dd1458865422cdd1c1cb26e38f48ddc10e5d91b09f3e419034c55cb72b599cf3
scientific_sha256_matches_pre_move: true
protected_project_files: 165
protected_project_sha256_matches_pre_move: true
venv_files: 26839
venv_metadata_matches_pre_move: true
```

## 11. Задачи John

1. Проверить итоговый onboarding-отчёт, агентный контракт и результаты pilot.
2. Принять либо вернуть на корректировку evidence record.
3. Не считать следующий блок Stage 7 разрешённым до отдельного решения.
