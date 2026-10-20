# ML-CRA 1.0.0 candidate release notes

These tracked notes describe an unreleased local candidate. They do not claim
that tag `v1.0.0`, a GitHub Release, TestPyPI publication, or PyPI publication
exists. Publication requires separate owner acceptance and authorization after
the final candidate re-audit.

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

### Remaining release gates

This candidate has consistent `1.0.0` package, runtime, citation, maturity, and
bilingual documentation metadata. It is not a release asset. A separately
authorized final re-audit must still verify protected artifacts, dependencies,
security, clean installation, CLI/dashboard behavior, scientific boundaries,
and two byte-identical builds before John can accept API stability and
authorize immutable GitHub publication. TestPyPI and PyPI are not part of the
`1.0.0` completion criteria.

## Русский

Эти отслеживаемые примечания описывают неопубликованный локальный кандидат.
Они не утверждают существование тега `v1.0.0`, GitHub Release или публикации в
TestPyPI/PyPI. Публикация требует отдельного принятия и разрешения владельца
после финального повторного аудита кандидата.

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

### Оставшиеся шлюзы выпуска

У кандидата согласованы версия пакета и runtime, данные цитирования,
классификатор зрелости и двуязычная документация `1.0.0`. Он не является
активом выпуска. Отдельно авторизованный финальный повторный аудит ещё должен
проверить защищённые артефакты, зависимости, безопасность, чистую установку,
поведение CLI/dashboard, научные границы и две побайтово совпадающие сборки.
Только после этого John сможет принять стабильность API и разрешить
неизменяемую публикацию GitHub. TestPyPI и PyPI не входят в критерии завершения
`1.0.0`.
