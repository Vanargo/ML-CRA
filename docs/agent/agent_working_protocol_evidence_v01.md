# Evidence record — постоянный рабочий протокол агента ML-CRA

## 1. Идентификация

```text
record_id: ML_CRA_AGENT_WORKING_PROTOCOL_V01
task_profile: CHANGE
technical_status: PASS
readiness: READY_FOR_JOHN_ACCEPTANCE
source_checkpoint: ml-cra_v15.zip
source_checkpoint_sha256: c6c5ada1e6be92fea21d6e6a59b1bf8f3e875d5983629a87f692cb2b02376603
result_checkpoint: ml-cra_v16.zip
result_checkpoint_sha256: recorded_after_archive_sealing_in_external_handoff
scientific_claim_changed: false
scientific_artifacts_changed: false
stage07_state_changed: false
next_block_authorized: false
```

Цель: зафиксировать утверждённый John рабочий протокол в `AGENTS.md`,
проектном навыке, постоянном рабочем контракте и шаблонах задач, обеспечить его
машинно проверяемую трассируемость и подготовить значимую ZIP-контрольную точку.

## 2. Разрешение и принятые решения

John явно разрешил эту отдельную изменяющую задачу сообщением «Приступай».
Ранее John выбрал вариант A по всем семи вопросам:

1. после формирования планируемого набора агент сразу выполняет изменения;
2. необходимый незапланированный файл допустим без расширения цели;
3. обязательна самопроверка, а независимое ревью высокорискового блока требует
   предварительного разрешения;
4. окончательное принятие и закрытие остаются за John;
5. ZIP создаётся для стадий, значимых блоков и принятых воспроизводимых
   состояний;
6. полный раздел «Дополнительно» хранится в постоянном контракте;
7. используется единое ядро и четыре профиля задач.

Структурные решения также сопоставлены с:

- `bio_inspired_project_engineering_standard_v02.md`;
- OpenAI Best practices:
  `https://learn.chatgpt.com/guides/best-practices`;
- OpenAI Custom instructions with AGENTS.md:
  `https://learn.chatgpt.com/docs/agent-configuration/agents-md`;
- OpenAI Build skills:
  `https://learn.chatgpt.com/docs/build-skills`.

## 3. Планируемый набор изменений

Изменить:

- `AGENTS.md`;
- `.agents/skills/ml-cra-stage-gate/SKILL.md`;
- `.agents/skills/ml-cra-stage-gate/agents/openai.yaml`.

Добавить:

- `docs/agent/ml_cra_agent_working_contract_v01.md`;
- `docs/agent/task_templates/task_core_v01.md`;
- четыре профильных шаблона;
- настоящий evidence record — доказательную запись.

Изначально не планировалось изменение `scripts/agent_verify.py` и создание
`docs/agent/agent_working_protocol_change_scope_v01.csv`.

## 4. Обоснованное уточнение планируемого набора

После внесения документов штатная baseline-проверка вернула `FAIL`, потому что
`scripts/agent_verify.py` был жёстко связан только с
`docs/agent/pilot_change_scope_v01.csv` предыдущего пилота. Новые файлы были
правильно классифицированы как выходящие за старый список.

В соответствии с разрешённым правилом о необходимом незапланированном файле
план был уточнён:

- добавлен отдельный машинно-читаемый список текущей задачи;
- верификатор получил повторяемый параметр `--additional-scope`, принимающий
  только существующий CSV внутри корня проекта;
- старый список пилота и его исторический смысл не изменены.

Это уточнение необходимо для проверяемости уже разрешённой цели, не меняет
научный scope — научные границы, Stage 7 или защищённые артефакты.

## 5. Фактический журнал изменений

Изменены:

- `AGENTS.md` — добавлены постоянные исполняемые правила утверждённого
  рабочего цикла;
- `.agents/skills/ml-cra-stage-gate/SKILL.md` — процедура расширена до одной
  измеримой профилированной задачи;
- `.agents/skills/ml-cra-stage-gate/agents/openai.yaml` — метаданные приведены
  в соответствие с обновлённым навыком и явным `$ml-cra-stage-gate`;
- `scripts/agent_verify.py` — добавлена безопасная поддержка дополнительных
  списков разрешённых изменений.

Добавлены:

- `docs/agent/ml_cra_agent_working_contract_v01.md`;
- `docs/agent/task_templates/task_core_v01.md`;
- `docs/agent/task_templates/analysis_only_v01.md`;
- `docs/agent/task_templates/change_v01.md`;
- `docs/agent/task_templates/scientific_validation_v01.md`;
- `docs/agent/task_templates/checkpoint_v01.md`;
- `docs/agent/agent_working_protocol_change_scope_v01.csv`;
- `docs/agent/agent_working_protocol_evidence_v01.md`.

Сопоставление с планом:

```text
modified_existing_files: 4
added_files: 8
missing_prechange_files: 0
unexpected_files_after_scope_update: 0
```

Отклонение от первоначального плана ограничено верификатором и отдельным
машинно-читаемым списком. Причина и соответствие семи условиям
незапланированного файла зафиксированы в разделе 4.

## 6. Проверки

| Проверка | Результат |
|---|---|
| Исходный `python scripts/agent_verify.py --mode baseline` | `PASS`, до изменения |
| Исходный `python scripts/agent_verify.py --mode pilot` | все проверки `PASS`, до изменения |
| Диагностический запуск после добавления документов со старым списком | ожидаемый `FAIL`: шесть новых файлов вне старого списка |
| `quick_validate.py .agents/skills/ml-cra-stage-gate` | `PASS`, `Skill is valid!` |
| `python scripts/agent_verify.py --mode baseline --additional-scope docs/agent/agent_working_protocol_change_scope_v01.csv` | `PASS`; 158 строк manifest, 2 списка, 3 изменённых и 16 добавленных относительно baseline v13, пропущенных и незаявленных файлов нет |
| Та же команда в режиме `--mode pilot` | все проверки `PASS` |
| Python syntax | `PASS`, 8 файлов |
| CSV structure | `PASS`, 77 файлов |
| Notebook structure | `PASS`, 4 валидных непустых notebook, один ожидаемый пустой placeholder |
| Documentary consistency | `PASS`, Stage 6 и статус ST07_06 согласованы |
| Stage 7 regression | `PASS`: ST07_04 19 × 24, ST07_05 22 × 23, ST07_06 18 × 40; значения и столбцы совпадают |
| Структура протокола | `PASS`, 11 обязательных файлов и 4 профиля |
| Размер `AGENTS.md` | `PASS`, 9341 байт при лимите 32768 |
| Метаданные навыка | `PASS`, корректный frontmatter и UI metadata |
| Канонические положения «Дополнительно» | `PASS`, обязательные формулировки присутствуют |
| Внутренние ссылки | `PASS`, зарегистрированные относительные пути существуют |
| Защита `--additional-scope` от пути вне проекта | `PASS`, отказ с exit code 2 |
| Сопоставление фактического журнала с уточнёнными границами | `PASS`, 4 изменённых + 8 добавленных, удалений нет |

Среда финальной проверки:

```text
python: 3.12.13
platform: Linux-6.12.13-x86_64-with-glibc2.39
new_models_trained: false
```

## 7. `Как было → Как стало` для `.py`

Изменён только `scripts/agent_verify.py`.

### 7.1. Передача одного или нескольких списков разрешённых изменений

Как было:

```python
def check_change_scope(
    strict: bool,
    current: dict[str, Path],
) -> tuple[Check, dict[str, list[str]]]:
    manifest_rows = read_contract_csv(MANIFEST_PATH)
    scope_rows = read_contract_csv(SCOPE_PATH)
```

Как стало:

```python
def check_change_scope(
    strict: bool,
    current: dict[str, Path],
    scope_paths: list[Path],
) -> tuple[Check, dict[str, list[str]]]:
    manifest_rows = read_contract_csv(MANIFEST_PATH)
    scope_rows = [
        row
        for scope_path in scope_paths
        for row in read_contract_csv(scope_path)
    ]
```

### 7.2. Диагностика количества применённых списков

Как было:

```python
    detail = (
        f"manifest_rows={len(manifest_rows)}; modified={len(modified)}; "
        f"added={len(added)}; missing={len(missing)}; "
        f"out_of_scope={len(out_of_scope_modified) + len(out_of_scope_added)}"
    )
```

Как стало:

```python
    detail = (
        f"manifest_rows={len(manifest_rows)}; scope_files={len(scope_paths)}; "
        f"modified={len(modified)}; "
        f"added={len(added)}; missing={len(missing)}; "
        f"out_of_scope={len(out_of_scope_modified) + len(out_of_scope_added)}"
    )
```

### 7.3. Безопасный CLI-параметр и передача списков

Как было:

```python
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "pilot"), required=True)
    args = parser.parse_args()

    inventory = build_project_inventory()
    checks: list[Check] = []
    scope_check, scope_details = check_change_scope(
        strict=args.mode == "pilot",
        current=inventory.files,
    )
```

Как стало:

```python
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "pilot"), required=True)
    parser.add_argument(
        "--additional-scope",
        action="append",
        default=[],
        metavar="PROJECT_RELATIVE_CSV",
        help="add a project-relative change-scope CSV to the pilot scope",
    )
    args = parser.parse_args()

    scope_paths = [SCOPE_PATH]
    for relative_scope in args.additional_scope:
        candidate = (PROJECT_ROOT / relative_scope).resolve()
        try:
            candidate.relative_to(PROJECT_ROOT)
        except ValueError:
            parser.error(f"additional scope must be inside project root: {relative_scope}")
        if not candidate.is_file():
            parser.error(f"additional scope does not exist: {relative_scope}")
        scope_paths.append(candidate)

    inventory = build_project_inventory()
    checks: list[Check] = []
    scope_check, scope_details = check_change_scope(
        strict=args.mode == "pilot",
        current=inventory.files,
        scope_paths=scope_paths,
    )
```

## 8. Научные и проектные ограничения

- Новые модели не обучались.
- Claim, protocol, seeds, splits, model space, metric directions, verdict
  policy и научные CSV не изменялись.
- Статус `ST07_06` и `stage07_next_block: decision_pending` не изменялись.
- Настоящий блок не разрешает продолжение Stage 7.

## 9. Остаточные риски и неопределённости

- `contract_id: ML_CRA_AGENT_WORKING_CONTRACT_V01` остаётся
  `canonical_pending_john_acceptance` до решения John.
- Проверена структура и внутренняя согласованность шаблонов, но их
  эксплуатационная эффективность окончательно оценивается на последующих
  реальных задачах.
- Независимое ревью не выполнялось: блок классифицирован как изменение
  проектного управления без изменения научного содержания, а отдельная
  высокорисковая проверка John не разрешал.
- SHA-256 `ml-cra_v16.zip` вычисляется после герметизации архива и поэтому
  передаётся внешним итоговым сообщением, а не записывается внутрь самого
  архива.

## 10. Задачи John

1. После передачи результата принять либо вернуть рабочий протокол.
2. Явно объявить настоящую задачу закрытой после принятия.
3. Не считать возможный следующий шаг разрешённым без отдельной постановки.
