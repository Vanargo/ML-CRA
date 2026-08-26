# ML-CRA 0.1.0 candidate release notes / Примечания к кандидату ML-CRA 0.1.0

## English

### Candidate status

These notes describe the finalized local candidate for the first supported
ML-CRA version, `0.1.0`. ST08_14A does not create tag `v0.1.0`, publish a
GitHub Release, or upload a package to TestPyPI or PyPI. The exact release tag
and commit SHA must be recorded only by a separately authorized ST08_14C after
the exact final candidate passes ST08_14B.

### Supported scope

- Windows x64 with CPython `>=3.12,<3.13`;
- local UTF-8 CSV input and versioned JSON claim specifications;
- bounded binary tabular classification with fixed allowlisted models;
- bounded tabular regression only under the explicit `exchangeable_rows`
  assumption and fixed allowlisted models;
- `mlcra audit`, `mlcra verify`, `mlcra doctor`, and local static bilingual
  `mlcra dashboard` workflows;
- no network access during the supported audit, verification, doctor, or
  dashboard operations.

### Scientific boundary

ML-CRA audits whether registered evidence supports a bounded claim. It does not
select a universally best model. The registered MiniBooNE and UCI Wine Quality
red results remain limited to their datasets, protocols, metrics, model spaces,
assumptions, and verdict policies. Synthetic walkthroughs verify software
behavior and are not new scientific validation.

### Candidate assets and verification

The release contract requires exactly:

- `ml_cra-0.1.0.tar.gz`;
- `ml_cra-0.1.0-py3-none-any.whl`;
- `SHA256SUMS`.

ST08_14A builds two independent copies from the canonical Git index with
`SOURCE_DATE_EPOCH=1787616000`, normalizes non-semantic `sdist` archive
metadata, and requires byte-identical SHA-256 digests. `SHA256SUMS` records the
candidate bytes. These hashes prove byte integrity, not correctness or
scientific validity. ST08_14B must re-audit the exact candidate, and ST08_14C
must rebuild and verify the assets against the exact authorized tag.

PowerShell verification command:

```powershell
Get-FileHash ml_cra-0.1.0.tar.gz,ml_cra-0.1.0-py3-none-any.whl -Algorithm SHA256
```

### Installation and use

Until an external release is separately authorized, use the reconstructible
source installation and quick start in [README.md](README.md). The future wheel
must be installed together with the exact runtime lock; unsupported Python or
platform combinations are not claimed.

### Known limitations and deferred channels

Multiclass classification, time-series or grouped regression, arbitrary model
imports, pickle/joblib inputs, URLs, automatic hyperparameter search, an
interactive or hosted dashboard, and a hosted service are unsupported. PyPI and
TestPyPI remain deferred and unauthorized. See [SECURITY.md](SECURITY.md),
[LICENSE](LICENSE), [CITATION.cff](CITATION.cff), and
[DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md).

## Русский

### Статус кандидата

Эти примечания описывают финализированный локальный кандидат первого
поддерживаемого выпуска ML-CRA `0.1.0`. ST08_14A не создаёт тег `v0.1.0`, не
публикует GitHub Release и не загружает пакет в TestPyPI или PyPI. Точный тег и
SHA коммита разрешено зарегистрировать только отдельно авторизованному ST08_14C
после прохождения точным финальным кандидатом аудита ST08_14B.

### Поддерживаемая область

- Windows x64 с CPython `>=3.12,<3.13`;
- локальный UTF-8 CSV и версионированные JSON-спецификации утверждения;
- ограниченная бинарная табличная классификация с фиксированными разрешёнными
  моделями;
- ограниченная табличная регрессия только при явном допущении
  `exchangeable_rows` и с фиксированными разрешёнными моделями;
- сценарии `mlcra audit`, `mlcra verify`, `mlcra doctor` и локальной статической
  двуязычной панели `mlcra dashboard`;
- отсутствие сетевого доступа при поддерживаемых audit, verify, doctor и
  dashboard.

### Граница научного вывода

ML-CRA проверяет, поддерживают ли зарегистрированные доказательства
ограниченное утверждение, и не выбирает универсально лучшую модель.
Зарегистрированные результаты MiniBooNE и красной разновидности UCI Wine
Quality ограничены своими данными, протоколами, метриками, пространствами
моделей, допущениями и политиками вердикта. Синтетические пошаговые сценарии
проверяют работу программы и не являются новой научной валидацией.

### Активы кандидата и проверка

Контракт выпуска требует ровно:

- `ml_cra-0.1.0.tar.gz`;
- `ml_cra-0.1.0-py3-none-any.whl`;
- `SHA256SUMS`.

ST08_14A строит две независимые копии из канонического индекса Git с
`SOURCE_DATE_EPOCH=1787616000`, нормализует несемантические метаданные архива
`sdist` и требует побитового совпадения SHA-256. `SHA256SUMS` фиксирует байты
кандидата. Хеши доказывают целостность байтов, но не корректность или научную
состоятельность. ST08_14B должен повторно проверить точный кандидат, а ST08_14C
— повторно собрать и сверить активы с точным разрешённым тегом.

Команда проверки PowerShell:

```powershell
Get-FileHash ml_cra-0.1.0.tar.gz,ml_cra-0.1.0-py3-none-any.whl -Algorithm SHA256
```

### Установка и использование

До отдельной авторизации внешнего выпуска используйте воспроизводимую установку
из исходников и быстрый старт из [README_RU.md](README_RU.md). Будущий wheel
нужно устанавливать вместе с точным runtime lock (фиксированным списком
зависимостей); поддержка иных Python или платформ не заявляется.

### Известные ограничения и отложенные каналы

Многоклассовая классификация, временная или групповая регрессия, произвольный
импорт моделей, входы pickle/joblib, URL, автоматический подбор
гиперпараметров, интерактивная или размещённая панель и размещённый сервис не
поддерживаются. PyPI и TestPyPI остаются отложенными и не разрешёнными. См.
[SECURITY.md](SECURITY.md), [LICENSE](LICENSE), [CITATION.cff](CITATION.cff) и
[DATASET_ATTRIBUTION.md](DATASET_ATTRIBUTION.md).
