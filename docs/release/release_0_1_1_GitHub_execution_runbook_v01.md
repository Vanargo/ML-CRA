# Инструкция будущего выпуска ML-CRA 0.1.1 через GitHub

## Статус и граница полномочий

Этот документ является проверяемой инструкцией, а не разрешением на выпуск.
`ST08_15B_v0_1_1_final_candidate_reaudit_and_security_preflight` не разрешает
изменять release-state — состояние выпуска — в исходниках, создавать тег
`v0.1.1`, GitHub Release, загружать активы или публиковать пакет. Действия ниже
допускаются только в отдельно авторизованном John блоке ST08_15C.

## Почему требуется переход состояния

Текущие `README.md`, `README_RU.md`, `RELEASE_NOTES_0.1.1.md` и `CITATION.cff`
правдиво описывают локальный неопубликованный кандидат. Публикация этого дерева
без перехода сделает утверждения «не опубликован» ложными и повторит известный
дефект формулировки v0.1.0. Поэтому текущие локальные активы являются
воспроизводимым preflight — предварительным — кандидатом, но не готовыми к
немедленной загрузке release-активами.

## Обязательные предварительные условия ST08_15C

1. John отдельно авторизовал ST08_15C вместе с узкой финализацией четырёх
   release-state поверхностей.
2. `README.md` и `README_RU.md` больше не называют v0.1.1 неопубликованным
   локальным кандидатом и точно описывают канал GitHub Release без заявления
   PyPI или стабильности 1.0.0.
3. `RELEASE_NOTES_0.1.1.md` переведён из candidate-снимка в финальные
   двуязычные notes — примечания — без изменения научного scope — границы.
4. Если в `CITATION.cff` добавляется `date-released`, она должна быть реальной
   датой выполнения выпуска; выдуманная или будущая дата запрещена. Поле
   необязательно и не должно добавляться, если точная дата ещё неизвестна.
5. Все изменения зафиксированы в отдельном commit — фиксации — и прошли pull
   request с обязательным `assurance` именно для точного SHA.
6. Из точного проверенного Git index дважды построены и зарегистрированы
   `ml_cra-0.1.1.tar.gz`, `ml_cra-0.1.1-py3-none-any.whl` и `SHA256SUMS`.
7. Тег и GitHub Release `v0.1.1` отсутствуют; `v0.1.0` остаётся неизменяемым.
8. Ruleset `main`, secret scanning, push protection, Dependabot alerts,
   private vulnerability reporting и Release immutability подтверждены.

Если хотя бы одно условие не подтверждено, выполнение останавливается без
создания тега или draft — черновика.

## Будущая последовательность ST08_15C

Порядок существенен:

1. Финализировать четыре release-state поверхности в разрешённых границах.
2. Зафиксировать переход, открыть PR и дождаться успешного `assurance` точного
   commit.
3. Повторно построить из этого commit два совпадающих комплекта трёх активов.
4. Убедиться в отсутствии `v0.1.1` и повторно проверить репозиторные меры.
5. Создать draft GitHub Release для нового тега `v0.1.1`, направленного на
   точный проверенный commit; не публиковать draft на этом шаге.
6. До публикации прикрепить все три актива.
7. Сверить имена, размеры и SHA-256 дистрибутивов со строками `SHA256SUMS`.
8. Один раз опубликовать draft при включённой неизменяемости выпусков.
9. После публикации выполнить:

   ```powershell
   gh release verify v0.1.1 --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.1 .\dist\st08_15C-release\ml_cra-0.1.1.tar.gz --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.1 .\dist\st08_15C-release\ml_cra-0.1.1-py3-none-any.whl --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.1 .\dist\st08_15C-release\SHA256SUMS --repo Vanargo/ML-CRA
   ```

10. Зарегистрировать URL, release ID, тег, точный commit/tree, дату, имена,
    размеры, SHA-256, результаты четырёх команд и release attestation —
    удостоверение происхождения выпуска.

## Остановка и восстановление

- До публикации ошибочный draft не публикуется; его исправление, удаление или
  пересоздание выполняется только в явно разрешённых границах ST08_15C.
- После публикации тег и активы неизменяемы. Нельзя молча заменять их для
  исправления текста или байтов.
- TestPyPI и PyPI не входят в ST08_15C и остаются отдельным решением John.
- SHA-256 подтверждает совпадение байтов, но не доказывает корректность,
  научную состоятельность или отсутствие неизвестных уязвимостей.

## Официальные основания

- [PyPA: Packaging flow](https://packaging.python.org/en/latest/flow/)
- [GitHub: immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [GitHub: verifying release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity)
- [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
- [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
