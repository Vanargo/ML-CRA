# ML-CRA 1.0.0 release notes

These tracked notes define the owner-authorized immutable GitHub Release
`v1.0.0`. The canonical distribution record is
https://github.com/Vanargo/ML-CRA/releases/tag/v1.0.0; if that record is absent,
release execution has not completed. TestPyPI and PyPI remain deferred.

## English

### Stable bounded public contract

Version `1.0.0` defines ML-CRA as a bounded offline evidence auditor: it tests
whether registered experimental evidence supports a stated machine-learning
claim. Stable means compatibility within the declared public contract and
supported cell; it does not mean universal model superiority, broad platform
support, or demonstrated mass adoption.

The frozen command surface is `mlcra audit`, `mlcra verify`, `mlcra doctor`,
and `mlcra dashboard`. The claim schemas remain
`binary_classification_claim_v01` and `tabular_regression_claim_v01`; the
doctor and dashboard reports remain `mlcra_doctor_report_v01` and
`mlcra_dashboard_report_v01`. Exit codes remain `0`, `2`, `3`, `4`, `5`, and
`6` with their documented meanings. Audit bundles, SHA-256 manifests,
machine-readable results, and the static bilingual dashboard retain their
existing meanings.

### Supported cell and scientific boundary

The supported cell remains Windows x64 with CPython `>=3.12,<3.13`. The fixed
allowlisted binary-classification and exchangeable-row tabular-regression
families are unchanged. Multiclass, time-series, grouped, repeated-measure, and
spatial protocols; arbitrary model imports; remote URLs; hosted services; and
automatic model discovery remain out of scope. Existing MiniBooNE and UCI Wine
Quality findings remain limited to their registered data, protocols, seeds,
splits, metrics, rounding rules, and verdict policies.

### Release execution and verification

John accepted the stable bounded API after the final candidate re-audit.
ST08_16C builds the exact protected release tree twice with one declared
`SOURCE_DATE_EPOCH`, requires byte-identical normalized sdist and wheel output,
binds all three assets with SHA-256, and verifies the published immutable
release attestation. TestPyPI and PyPI remain deferred and are not part of the
`1.0.0` completion criteria.

## Русский

Эти отслеживаемые примечания определяют авторизованный владельцем неизменяемый
GitHub Release `v1.0.0`. Каноническая запись распространения находится по
адресу https://github.com/Vanargo/ML-CRA/releases/tag/v1.0.0; если она
отсутствует, выполнение выпуска ещё не завершено. TestPyPI и PyPI остаются
отложенными.

### Стабильный ограниченный публичный контракт

Версия `1.0.0` определяет ML-CRA как ограниченный офлайн-аудитор доказательств:
он проверяет, поддерживают ли зарегистрированные экспериментальные
доказательства заявленное утверждение машинного обучения. Стабильность означает
совместимость внутри объявленного публичного контракта и поддерживаемой ячейки,
а не универсальное превосходство модели, широкую поддержку платформ или
доказанное массовое использование.

Замороженная поверхность команд — `mlcra audit`, `mlcra verify`,
`mlcra doctor` и `mlcra dashboard`. Схемы утверждений остаются
`binary_classification_claim_v01` и `tabular_regression_claim_v01`; схемы
отчётов doctor и dashboard — `mlcra_doctor_report_v01` и
`mlcra_dashboard_report_v01`. Коды завершения `0`, `2`, `3`, `4`, `5` и `6`
сохраняют документированный смысл. Пакеты аудита, SHA-256-манифесты,
машиночитаемые результаты и статическая двуязычная панель сохраняют прежний
смысл.

### Поддерживаемая ячейка и научная граница

Поддерживаемая ячейка остаётся Windows x64 и CPython `>=3.12,<3.13`.
Фиксированные разрешённые семейства бинарной классификации и табличной
регрессии с обменными строками не меняются. Многоклассовые, временные,
групповые, повторные и пространственные протоколы, произвольный импорт моделей,
удалённые URL, размещённые сервисы и автоматический поиск моделей остаются вне
границ. Выводы MiniBooNE и UCI Wine Quality по-прежнему ограничены
зарегистрированными данными, протоколами, зернами, разбиениями, метриками,
правилами округления и политиками вердикта.

### Выполнение и проверка выпуска

John принял стабильный ограниченный API после финального повторного аудита
кандидата. ST08_16C дважды собирает точное защищённое дерево выпуска с одним
объявленным `SOURCE_DATE_EPOCH`, требует побайтового совпадения нормализованных
sdist и wheel, связывает все три актива SHA-256 и проверяет аттестацию
опубликованного неизменяемого выпуска. TestPyPI и PyPI остаются отложенными и
не входят в критерии завершения `1.0.0`.
