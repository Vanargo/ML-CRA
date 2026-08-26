# Инструкция будущего выпуска ML-CRA 0.1.0 через GitHub

## Статус и граница полномочий

Этот документ является проверяемой инструкцией, а не разрешением на выпуск. В рамках
`ST08_14B_release_0_1_0_execution_security_preflight` запрещено создавать тег `v0.1.0`,
GitHub Release, загружать артефакты или публиковать пакет. Выполнение допускается только в
отдельно авторизованном John блоке ST08_14C.

## Обязательные предварительные условия

1. Зафиксировать точный commit `main`, предназначенный для выпуска.
2. Убедиться, что обязательная проверка `assurance` завершилась `success` именно для этого commit.
3. Убедиться, что тег `v0.1.0` и GitHub Release `v0.1.0` ещё не существуют.
4. В `Settings → General → Releases` убедиться, что включено `Release immutability`
   (неизменяемость выпусков).
5. В `Settings → Advanced Security` убедиться, что включены secret scanning (поиск секретов),
   push protection (защита при отправке), Dependabot alerts и private vulnerability reporting
   (закрытая отправка сообщений об уязвимостях).
6. Установить GitHub CLI и выполнить `gh auth status`; не помещать токен в командную строку,
   файлы проекта, журналы CI или снимки экрана.
7. Из точного Git index дважды построить кандидат командой ST08_14B и проверить три файла:
   `ml_cra-0.1.0.tar.gz`, `ml_cra-0.1.0-py3-none-any.whl`, `SHA256SUMS`.

Если хотя бы одно условие не подтверждено, выпуск останавливается без создания тега или draft.

## Будущая последовательность ST08_14C

Порядок является существенным:

1. Проверить точный commit, успешный `assurance` и отсутствие существующих тега/релиза.
2. Повторно построить и проверить три точных артефакта.
3. Создать draft GitHub Release (черновик выпуска) для нового тега `v0.1.0`, направленного на
   точный проверенный commit. Не публиковать draft на этом шаге.
4. До публикации прикрепить все три артефакта.
5. Сверить имена, размеры и SHA-256 обоих дистрибутивов со строками `SHA256SUMS`.
6. Один раз опубликовать draft при включённой неизменяемости выпусков.
7. После публикации выполнить:

   ```powershell
   gh release verify v0.1.0 --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.0 .\dist\st08_14C-release\ml_cra-0.1.0.tar.gz --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.0 .\dist\st08_14C-release\ml_cra-0.1.0-py3-none-any.whl --repo Vanargo/ML-CRA
   gh release verify-asset v0.1.0 .\dist\st08_14C-release\SHA256SUMS --repo Vanargo/ML-CRA
   ```

8. Зарегистрировать URL выпуска, тег, точный commit, имена/размеры/SHA-256 артефактов,
   результаты четырёх команд проверки и сведения об автоматическом release attestation
   (удостоверении происхождения выпуска).

## Остановка и восстановление

- До публикации ошибочный draft следует оставить неопубликованным и исправить только после
  повторной проверки; удаление или пересоздание — отдельное внешнее действие John.
- После публикации неизменяемый выпуск нельзя считать редактируемым рабочим объектом. Любая
  ошибка означает остановку и отдельное решение John; нельзя молча заменять файлы или тег.
- PyPI и TestPyPI не входят в этот процесс и остаются отложенными.
- SHA-256 подтверждает совпадение байтов, но не доказывает корректность программы или научного
  вывода.

## Официальные основания

- [GitHub: verifying release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity)
- [GitHub: preventing release changes](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)
- [GitHub: immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [GitHub: artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final)
- [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
