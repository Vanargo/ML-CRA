# ML-CRA 0.1.1 release notes

These tracked notes describe the owner-authorized immutable GitHub Release
`v0.1.1`. Release execution is complete only when the canonical
[GitHub record](https://github.com/Vanargo/ML-CRA/releases/tag/v0.1.1) exists
and the ST08_15C evidence records successful release and asset verification.
No TestPyPI or PyPI publication is included.

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

### Release assets and verification

ST08_15C builds the following three release assets twice from the exact assured
Git tree with a fixed `SOURCE_DATE_EPOCH`:

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
source tree intentionally has no `date-released` in `CITATION.cff`: the exact
external publication timestamp is created only after these bytes have passed
the protected pull request, and is recorded by GitHub and the ST08_15C evidence
instead of being guessed in advance. TestPyPI and PyPI remain deferred and
require a separate owner decision.

## Русский

Эти отслеживаемые примечания описывают авторизованный владельцем неизменяемый
GitHub Release `v0.1.1`. Выполнение выпуска завершено только тогда, когда
существует каноническая
[запись GitHub](https://github.com/Vanargo/ML-CRA/releases/tag/v0.1.1), а
доказательства ST08_15C фиксируют успешную проверку выпуска и активов.
Публикация в TestPyPI или PyPI сюда не входит.

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

### Активы выпуска и проверка

ST08_15C дважды собирает из точного проверенного Git-дерева с фиксированным
`SOURCE_DATE_EPOCH` три актива выпуска:

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
изменяются. В исходном дереве намеренно нет `date-released` в `CITATION.cff`:
точное время внешней публикации возникает только после проверки этих байтов
через защищённый pull request и фиксируется GitHub и доказательствами ST08_15C,
а не угадывается заранее. TestPyPI и PyPI остаются отложенными и требуют
отдельного решения владельца.
