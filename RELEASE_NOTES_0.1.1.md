# ML-CRA 0.1.1 corrective candidate notes

These notes describe a local candidate. They do not create a tag, a GitHub
Release, or a TestPyPI/PyPI publication.

## English

### Correction

Version `0.1.1` corrects the documented `v0.1.0` pre-release snapshot state.
The `mlcra doctor` schema remains `mlcra_doctor_report_v01`; existing keys,
commands, inputs, outputs, and exit codes are preserved. When the packaged
technical content has no known static blocker, the report now contains:

```json
{
  "release_ready": true,
  "release_blockers": [],
  "release_readiness_scope": "packaged_content_only_no_publication_authority"
}
```

These values describe packaged-content readiness only. They never authorize a
tag, GitHub Release, TestPyPI upload, or PyPI upload. Owner authorization remains
an external repository-governance decision.

### Preserved scope and compatibility boundary

The supported boundary remains Windows x64 with CPython `>=3.12,<3.13`, local
binary tabular classification, bounded exchangeable-row tabular regression,
and a local static English/Russian dashboard. The MiniBooNE and UCI Wine
Quality evidence remains bounded to its registered protocols. This correction
does not claim a universally best model, cross-platform support, new scientific
validation, or stable `1.0.0` API status.

### Local candidate assets and verification

ST08_15A builds the following three local assets twice from the canonical Git
index with a fixed `SOURCE_DATE_EPOCH`:

- `ml_cra-0.1.1.tar.gz`;
- `ml_cra-0.1.1-py3-none-any.whl`;
- `SHA256SUMS`.

The normalized source distributions and wheels must be byte-identical between
the two builds. Verify the two distributable assets from their containing
directory with:

```powershell
Get-FileHash ml_cra-0.1.1.tar.gz,ml_cra-0.1.1-py3-none-any.whl -Algorithm SHA256
```

Then compare both values with `SHA256SUMS`. Installation and command examples
remain in [README.md](README.md) and [README_RU.md](README_RU.md). License,
citation, dataset attribution, and security reporting are defined by
[LICENSE](LICENSE), [CITATION.cff](CITATION.cff),
[DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md), and
[SECURITY.md](SECURITY.md).

### Known limits and deferred actions

The immutable `v0.1.0` tag, release body, and assets are not changed. This
candidate has no release date in `CITATION.cff` because it has not been
published. TestPyPI, PyPI, the `v0.1.1` tag, and the `v0.1.1` GitHub Release are
deferred to separately authorized blocks.

## Русский

Эти примечания описывают локальный кандидат: для него не создавались тег,
GitHub Release или публикация TestPyPI/PyPI.

### Коррекция

Версия `0.1.1` исправляет документированное предрелизное состояние снимка
`v0.1.0`. Схема `mlcra doctor` остаётся `mlcra_doctor_report_v01`; существующие
ключи, команды, входы, выходы и коды завершения сохраняются. Когда в
техническом содержимом пакета нет известного статического блокера, отчёт теперь
содержит:

```json
{
  "release_ready": true,
  "release_blockers": [],
  "release_readiness_scope": "packaged_content_only_no_publication_authority"
}
```

Эти значения описывают только готовность содержимого пакета. Они никогда не
разрешают тег, GitHub Release, загрузку в TestPyPI или PyPI. Полномочие владельца
остаётся внешним решением управления репозиторием.

### Сохранённые границы и совместимость

Поддерживаемая граница остаётся прежней: Windows x64, CPython
`>=3.12,<3.13`, локальная бинарная табличная классификация, ограниченная
табличная регрессия с обменными строками и локальная статическая панель на
английском/русском языках. Доказательства MiniBooNE и UCI Wine Quality остаются
ограничены зарегистрированными протоколами. Коррекция не заявляет универсально
лучшую модель, межплатформенную поддержку, новую научную валидацию или
стабильность API уровня `1.0.0`.

### Локальные активы кандидата и проверка

ST08_15A дважды собирает из канонического Git index — индекса — с фиксированным
`SOURCE_DATE_EPOCH` три локальных актива:

- `ml_cra-0.1.1.tar.gz`;
- `ml_cra-0.1.1-py3-none-any.whl`;
- `SHA256SUMS`.

Нормализованные исходные архивы и wheel должны попарно совпасть побайтово.
Проверьте два распространяемых актива из содержащего их каталога:

```powershell
Get-FileHash ml_cra-0.1.1.tar.gz,ml_cra-0.1.1-py3-none-any.whl -Algorithm SHA256
```

Затем сравните оба значения с `SHA256SUMS`. Установка и примеры команд остаются
в [README.md](README.md) и [README_RU.md](README_RU.md). Лицензия, цитирование,
атрибуция наборов данных и сообщение об уязвимостях определены в
[LICENSE](LICENSE), [CITATION.cff](CITATION.cff),
[DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md) и [SECURITY.md](SECURITY.md).

### Известные ограничения и отложенные действия

Неизменяемые тег, release body — описание выпуска — и активы `v0.1.0` не
изменяются. В `CITATION.cff` нет даты выпуска этого кандидата, потому что он не
опубликован. TestPyPI, PyPI, тег `v0.1.1` и GitHub Release `v0.1.1` отложены до
отдельно авторизованных блоков.
