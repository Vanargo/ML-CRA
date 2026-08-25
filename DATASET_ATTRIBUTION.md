# Атрибуция набора данных MiniBooNE

## Область действия

ML-CRA распространяет собственный программный код и документацию по лицензии
MIT, указанной в `LICENSE`. Эта лицензия **не** перелицензирует MiniBooNE,
материалы UCI/OpenML или права третьих лиц. Проект не включает исходный набор
данных, локальный кэш OpenML или иные построчные копии MiniBooNE.

Настоящее уведомление реализует консервативное релизное решение ST08_05:
текущая страница первичного источника UCI указывает CC BY 4.0, тогда как запись
зеркала OpenML 41150 указывает CC0; доказательство полномочий загрузившего лица
на отказ от всех релевантных прав не установлено. Поэтому ML-CRA применяет к
публикуемым материалам происхождения MiniBooNE условия атрибуции CC BY 4.0, не
выдавая это инженерное управление риском за юридическое заключение
([контракт ST08_05](configs/project_readiness/st08_05_miniboone_lineage_license_attribution_and_release_asset_disposition_v01.json),
разделы `license_metadata_conflict` и `required_attribution`).

## Требуемая атрибуция

> Roe, B. (2005). MiniBooNE particle identification [Dataset]. UCI Machine
> Learning Repository. <https://doi.org/10.24432/C5QC87>.

- Автор набора данных: Byron Roe.
- Название: *MiniBooNE particle identification*.
- Первичный источник: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/199/miniboone+particle+identification).
- DOI: <https://doi.org/10.24432/C5QC87>.
- Условия, применяемые ML-CRA к публикационным материалам происхождения
  MiniBooNE: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Использованное зеркало: OpenML, dataset ID `41150`; запись OpenML указывает
  UCI как исходный источник.

## Изменения и производные материалы

OpenML представляет 130 064 строк данных как классификационный набор в формате
ARFF с целевой переменной `signal` и признаками `ParticleID_0`–`ParticleID_49`.
ML-CRA отображает `False`/`True` в `0`/`1` и публикует только протоколы,
производные доказательства оценки моделей и ограниченные выводы — не исходные
строки набора данных. Это описание и требуемый текст уведомления зафиксированы
в [контракте ST08_05](configs/project_readiness/st08_05_miniboone_lineage_license_attribution_and_release_asset_disposition_v01.json),
раздел `required_attribution`.

Использование этих материалов не означает одобрения ML-CRA со стороны Byron
Roe, UCI, MiniBooNE, OpenML или Creative Commons.

## Цитирование OpenML

> Vanschoren, J., van Rijn, J. N., Bischl, B., & Torgo, L. (2013). OpenML:
> Networked Science in Machine Learning. *SIGKDD Explorations*, 15(2).
> <https://doi.org/10.1145/2641190.2641198>.

## Нормативные источники

- [CC BY 4.0: юридический текст](https://creativecommons.org/licenses/by/4.0/legalcode.en).
- [CC BY 4.0: официальное краткое изложение](https://creativecommons.org/licenses/by/4.0/).
- [UCI: MiniBooNE particle identification](https://archive.ics.uci.edu/dataset/199/miniboone+particle+identification).
- [OpenML: API-запись dataset 41150](https://www.openml.org/api/v1/json/data/41150).
- [OpenML: условия и цитирование](https://beta.openml.org/terms).

Краткое изложение условий CC не заменяет юридический текст. Это уведомление —
инженерная мера управления происхождением и релизным риском, а не юридическая
консультация.

## Атрибуция UCI Wine Quality для ST08_11A

ST08_11A использует только красный вариант `winequality-red.csv` для
ограниченной научной валидации регрессионного контура. Проект не включает
исходный архив или построчную копию набора данных; зарегистрированы официальный
адрес, имя файла, преобразование разделителя и SHA-256.

> Cortez, P., Cerdeira, A., Almeida, F., Matos, T., & Reis, J. (2009). Wine
> Quality [Dataset]. UCI Machine Learning Repository.
> <https://doi.org/10.24432/C56S3T>.

- Официальная карточка: <https://archive.ics.uci.edu/dataset/186/wine+quality>.
- Лицензия набора данных: [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
- Использованный файл: `winequality-red.csv` из официального архива UCI.
- Изменение для приложения: разделённый точкой с запятой UTF-8 файл без
  фильтрации строк, столбцов или значений преобразован в UTF-8 CSV с запятыми и
  LF; исходный и преобразованный SHA-256 зарегистрированы в evidence ST08_11A.
- Публикуются только протокол, парные агрегированные оценки и ограниченный
  вердикт, а не исходные строки.

Связанная предметная статья: Cortez et al., “Modeling wine preferences by data
mining from physicochemical properties”, *Decision Support Systems* 47(4),
2009, <https://doi.org/10.1016/j.dss.2009.05.016>.
