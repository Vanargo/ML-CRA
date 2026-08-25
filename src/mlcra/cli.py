from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence

from mlcra.application import (
    MlcraApplicationError,
    doctor_report,
    run_audit,
    software_version,
    verify_bundle,
)
from mlcra.dashboard import run_dashboard


class MlcraArgumentParser(argparse.ArgumentParser):
    """Convert command-line usage failures to the registered diagnostic contract."""

    def error(self, message: str) -> None:
        raise MlcraApplicationError(
            exit_code=2,
            error_code="MLCRA_COMMAND_LINE_USAGE_ERROR",
            phase="argument_parsing",
            artifact_or_field="command_line_arguments",
            expected="a supported subcommand with all required options and valid choices",
            actual=message,
            severity="error",
            action_taken="operation_stopped_before_input_processing",
            user_action="Исправьте аргументы по выводу mlcra --help и повторите команду.",
            rule_source="ST08_04.cli_contract.exit_codes.2",
        )


def _add_common_options(parser: argparse.ArgumentParser, *, suppress_defaults: bool) -> None:
    default: Any = argparse.SUPPRESS if suppress_defaults else "text"
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default=default,
        help="Формат ответа: text или json.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=argparse.SUPPRESS if suppress_defaults else False,
        help="Не использовать цветное оформление (текущая версия и так не использует цвет).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = MlcraArgumentParser(
        prog="mlcra",
        description="Аудит ограниченного утверждения и автономная панель проверенного результата.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {software_version()}")
    _add_common_options(parser, suppress_defaults=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Выполнить новый ограниченный аудит.", allow_abbrev=False)
    audit.add_argument("--spec", required=True, help="Локальная JSON-спецификация claim.")
    audit.add_argument("--data", required=True, help="Локальный UTF-8 CSV.")
    audit.add_argument("--output-dir", required=True, help="Новый каталог evidence bundle.")
    _add_common_options(audit, suppress_defaults=True)

    verify = subparsers.add_parser("verify", help="Проверить существующий bundle без обучения.", allow_abbrev=False)
    verify.add_argument("--bundle", required=True, help="Каталог существующего bundle.")
    _add_common_options(verify, suppress_defaults=True)

    doctor = subparsers.add_parser("doctor", help="Проверить окружение и показать блокеры релиза.", allow_abbrev=False)
    _add_common_options(doctor, suppress_defaults=True)
    dashboard = subparsers.add_parser("dashboard", help="Создать проверенную автономную RU/EN HTML-панель.", allow_abbrev=False)
    dashboard.add_argument("--bundle", required=True, help="Каталог существующего проверяемого bundle.")
    dashboard.add_argument("--output-dir", required=True, help="Новый каталог автономной панели.")
    _add_common_options(dashboard, suppress_defaults=True)
    return parser


def _requested_format(arguments: Sequence[str]) -> str:
    for index, argument in enumerate(arguments):
        if argument == "--format" and index + 1 < len(arguments):
            return "json" if arguments[index + 1] == "json" else "text"
        if argument.startswith("--format="):
            return "json" if argument.partition("=")[2] == "json" else "text"
    return "text"


def _emit_success(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    if payload["command"] == "audit":
        print(
            "Аудит завершён: "
            f"claim={payload['claim_id']}; verdict={payload['verdict']}; "
            f"metric={payload['primary_metric']}; mean_delta={payload['mean_primary_delta']:.6f}; "
            f"bundle={payload['bundle']}. {payload['scope_limit']}"
        )
    elif payload["command"] == "verify":
        print(
            "Проверка bundle пройдена: "
            f"claim={payload['claim_id']}; verdict={payload['verdict']}; "
            f"artifacts={payload['verified_artifacts']}; fit_performed=false."
        )
    elif payload["command"] == "dashboard":
        print(
            "Панель создана: "
            f"claim={payload['claim_id']}; verdict={payload['verdict']}; "
            f"fit_performed=false; output_dir={payload['output_dir']}."
        )
    else:
        print(
            "Проверка окружения завершена: "
            f"environment_pass={str(payload['environment_pass']).lower()}; "
            f"release_ready={str(payload['release_ready']).lower()}; "
            f"release_blockers={len(payload['release_blockers'])}."
        )


def _emit_error(error: MlcraApplicationError, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(error.diagnostic, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    else:
        diagnostic = error.diagnostic
        print(
            f"Ошибка {diagnostic['error_code']} на этапе {diagnostic['phase']}: "
            f"поле/артефакт={diagnostic['artifact_or_field']}; "
            f"ожидалось={diagnostic['expected']}; получено={diagnostic['actual']}. "
            f"Действие пользователя: {diagnostic['user_action']}",
            file=sys.stderr,
        )


def main(argv: Sequence[str] | None = None) -> int:
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    output_format = _requested_format(raw_arguments)
    try:
        args = parser.parse_args(raw_arguments)
        output_format = getattr(args, "format", output_format)
        if args.command == "audit":
            result = run_audit(args.spec, args.data, args.output_dir)
            _emit_success(result, output_format)
            return 0
        if args.command == "verify":
            result = verify_bundle(args.bundle)
            _emit_success(result, output_format)
            return 0
        if args.command == "dashboard":
            result = run_dashboard(args.bundle, args.output_dir)
            _emit_success(result, output_format)
            return 0
        report = doctor_report()
        report["command"] = "doctor"
        report["exit_code"] = 0 if report["environment_pass"] else 5
        _emit_success(report, output_format)
        return int(report["exit_code"])
    except MlcraApplicationError as error:
        _emit_error(error, output_format)
        return error.exit_code
    except Exception as error:  # pragma: no cover - final safety boundary
        internal = MlcraApplicationError(
            exit_code=6,
            error_code="MLCRA_INTERNAL_INVARIANT_FAILURE",
            phase="internal",
            artifact_or_field="unhandled_exception",
            expected="controlled execution without uncaught traceback",
            actual=f"{type(error).__name__}: {error}",
            severity="error",
            action_taken="operation_stopped_without_success_publication",
            user_action="Сохраните диагностическое сообщение и сообщите сопровождающему проекта.",
            rule_source="ST08_04.cli_contract.diagnostic_contract",
        )
        _emit_error(internal, output_format)
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
