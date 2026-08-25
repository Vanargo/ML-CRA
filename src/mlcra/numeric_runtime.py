from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
from typing import Any, Iterator

import pandas as pd
from threadpoolctl import threadpool_info, threadpool_limits

from mlcra.validation import require_non_empty, require_unique_key


PROSPECTIVE_PROTOCOL_ID = "miniboone_nested_cv_v02"
BASE_PROTOCOL_ID = "miniboone_nested_cv_v01"
RUNTIME_CONTRACT_ID = "miniboone_nested_numeric_runtime_v01"
RUNTIME_CONTRACT_STATUS = "prospective_locked_before_run"
RUNTIME_CONTRACT_ARTIFACT_NAME = "MiniBooNE numeric runtime contract"

REQUIRED_RUNTIME_CONTRACT_COLUMNS = [
    "runtime_contract_id",
    "protocol_id",
    "base_protocol_id",
    "status",
    "user_api",
    "thread_limit",
    "backend_key",
    "internal_api",
    "prefix",
    "version",
    "threading_layer",
    "architecture",
    "library_filename",
    "backend_match_policy",
    "backend_identity_fields",
    "enforcement_api",
    "golden_policy",
    "cross_environment_policy",
    "source_reference",
]

BACKEND_IDENTITY_FIELDS = (
    "internal_api",
    "prefix",
    "version",
    "threading_layer",
    "architecture",
    "library_filename",
)
BACKEND_IDENTITY_FIELDS_TEXT = ";".join(BACKEND_IDENTITY_FIELDS)


@dataclass(frozen=True, order=True)
class NumericBackendIdentity:
    internal_api: str
    prefix: str
    version: str
    threading_layer: str
    architecture: str
    library_filename: str


@dataclass(frozen=True)
class NumericBackendSpec:
    backend_key: str
    identity: NumericBackendIdentity


@dataclass(frozen=True)
class NumericBackendRuntime:
    identity: NumericBackendIdentity
    num_threads: int


@dataclass(frozen=True)
class NumericRuntimeContract:
    runtime_contract_id: str
    protocol_id: str
    base_protocol_id: str
    status: str
    user_api: str
    thread_limit: int
    backend_match_policy: str
    enforcement_api: str
    golden_policy: str
    cross_environment_policy: str
    expected_backends: tuple[NumericBackendSpec, ...]


def _one_constant_value(rows: pd.DataFrame, column: str) -> str:
    values = [str(value).strip() for value in rows[column].tolist()]
    if any(not value for value in values):
        raise ValueError(
            f"Столбец {column} численного runtime-контракта не должен "
            "содержать пустые значения"
        )
    unique_values = set(values)
    if len(unique_values) != 1:
        raise ValueError(
            f"Столбец {column} должен иметь одно значение на runtime-контракт"
        )
    return values[0]


def _positive_integer(raw_value: Any, *, name: str) -> int:
    if isinstance(raw_value, bool) or isinstance(raw_value, Integral):
        value = int(raw_value)
    else:
        text = str(raw_value).strip()
        if not text.isdigit():
            raise ValueError(f"{name} должен быть положительным целым числом")
        value = int(text)
    if value < 1:
        raise ValueError(f"{name} должен быть положительным целым числом")
    return value


def build_numeric_runtime_contract(
    contract_df: pd.DataFrame,
    runtime_contract_id: str,
    protocol_id: str,
) -> NumericRuntimeContract:
    """Build the prospective fail-fast numeric execution contract."""
    if not isinstance(contract_df, pd.DataFrame):
        raise TypeError("contract_df должен быть pandas.DataFrame")
    if list(contract_df.columns) != REQUIRED_RUNTIME_CONTRACT_COLUMNS:
        raise ValueError(
            "Столбцы численного runtime-контракта должны точно совпадать "
            "с зарегистрированной схемой и порядком"
        )
    for value, name in (
        (runtime_contract_id, "runtime_contract_id"),
        (protocol_id, "protocol_id"),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} должен быть непустой строкой")

    contract_rows = contract_df[
        contract_df["runtime_contract_id"].eq(runtime_contract_id)
    ].copy()
    require_non_empty(contract_rows, RUNTIME_CONTRACT_ARTIFACT_NAME)
    if not contract_rows["protocol_id"].eq(protocol_id).all():
        raise ValueError(
            "runtime_contract_id связан с другим или неоднозначным protocol_id"
        )
    require_unique_key(
        contract_rows,
        ["runtime_contract_id", "backend_key"],
        RUNTIME_CONTRACT_ARTIFACT_NAME,
    )

    constant_values = {
        column: _one_constant_value(contract_rows, column)
        for column in (
            "runtime_contract_id",
            "protocol_id",
            "base_protocol_id",
            "status",
            "user_api",
            "thread_limit",
            "backend_match_policy",
            "backend_identity_fields",
            "enforcement_api",
            "golden_policy",
            "cross_environment_policy",
        )
    }
    expected_constants = {
        "runtime_contract_id": RUNTIME_CONTRACT_ID,
        "protocol_id": PROSPECTIVE_PROTOCOL_ID,
        "base_protocol_id": BASE_PROTOCOL_ID,
        "status": RUNTIME_CONTRACT_STATUS,
        "user_api": "blas",
        "thread_limit": "1",
        "backend_match_policy": "exact_identity",
        "backend_identity_fields": BACKEND_IDENTITY_FIELDS_TEXT,
        "enforcement_api": "threadpoolctl.threadpool_limits",
        "golden_policy": "preserve_existing_v01_golden",
        "cross_environment_policy": "blocked_without_separate_calibration",
    }
    if constant_values != expected_constants:
        differences = {
            key: (constant_values[key], expected_value)
            for key, expected_value in expected_constants.items()
            if constant_values[key] != expected_value
        }
        raise ValueError(
            "Численный runtime-контракт не соответствует авторизованной "
            f"проспективной политике: {differences}"
        )

    expected_backends: list[NumericBackendSpec] = []
    observed_identities: set[NumericBackendIdentity] = set()
    for _, row in contract_rows.iterrows():
        backend_key = str(row["backend_key"]).strip()
        source_reference = str(row["source_reference"]).strip()
        if not backend_key or not source_reference:
            raise ValueError(
                "backend_key и source_reference должны быть непустыми"
            )
        identity_values = {
            field: str(row[field]).strip()
            for field in BACKEND_IDENTITY_FIELDS
        }
        if any(not value for value in identity_values.values()):
            raise ValueError(
                "Поля точной идентичности численного backend не должны "
                "быть пустыми"
            )
        identity = NumericBackendIdentity(**identity_values)
        if identity in observed_identities:
            raise ValueError(
                "Точная идентичность численного backend должна быть уникальной"
            )
        observed_identities.add(identity)
        expected_backends.append(
            NumericBackendSpec(backend_key=backend_key, identity=identity)
        )

    return NumericRuntimeContract(
        runtime_contract_id=constant_values["runtime_contract_id"],
        protocol_id=constant_values["protocol_id"],
        base_protocol_id=constant_values["base_protocol_id"],
        status=constant_values["status"],
        user_api=constant_values["user_api"],
        thread_limit=_positive_integer(
            constant_values["thread_limit"],
            name="thread_limit",
        ),
        backend_match_policy=constant_values["backend_match_policy"],
        enforcement_api=constant_values["enforcement_api"],
        golden_policy=constant_values["golden_policy"],
        cross_environment_policy=constant_values[
            "cross_environment_policy"
        ],
        expected_backends=tuple(
            sorted(expected_backends, key=lambda spec: spec.backend_key)
        ),
    )


def _runtime_from_threadpool_info(row: dict[str, Any]) -> NumericBackendRuntime:
    identity_values = {
        "internal_api": str(row.get("internal_api") or "").strip(),
        "prefix": str(row.get("prefix") or "").strip(),
        "version": str(row.get("version") or "").strip(),
        "threading_layer": str(row.get("threading_layer") or "").strip(),
        "architecture": str(row.get("architecture") or "").strip(),
        "library_filename": Path(str(row.get("filepath") or "")).name,
    }
    if any(not value for value in identity_values.values()):
        raise RuntimeError(
            "threadpoolctl вернул неполную идентичность BLAS backend: "
            f"{identity_values}"
        )
    num_threads = _positive_integer(
        row.get("num_threads"),
        name="threadpoolctl num_threads",
    )
    return NumericBackendRuntime(
        identity=NumericBackendIdentity(**identity_values),
        num_threads=num_threads,
    )


def capture_blas_runtime() -> tuple[NumericBackendRuntime, ...]:
    """Capture loaded BLAS controllers without retaining absolute paths."""
    runtimes = [
        _runtime_from_threadpool_info(row)
        for row in threadpool_info()
        if row.get("user_api") == "blas"
    ]
    if not runtimes:
        raise RuntimeError(
            "Не обнаружен загруженный BLAS backend; точный runtime-контракт "
            "не может быть проверен"
        )
    identities = [runtime.identity for runtime in runtimes]
    if len(identities) != len(set(identities)):
        raise RuntimeError(
            "threadpoolctl вернул дублированную идентичность BLAS backend"
        )
    return tuple(sorted(runtimes, key=lambda runtime: runtime.identity))


def _validate_backend_identity(
    contract: NumericRuntimeContract,
    observed: tuple[NumericBackendRuntime, ...],
) -> None:
    expected_identities = tuple(
        sorted(spec.identity for spec in contract.expected_backends)
    )
    observed_identities = tuple(runtime.identity for runtime in observed)
    if observed_identities != expected_identities:
        raise RuntimeError(
            "Фактический BLAS backend не совпадает с точным проспективным "
            f"контрактом. expected={expected_identities}; "
            f"observed={observed_identities}"
        )


def require_numeric_runtime_contract(
    protocol_id: str,
    contract: NumericRuntimeContract | None,
) -> NumericRuntimeContract | None:
    """Require the registered contract for the prospective v02 protocol."""
    if contract is None:
        if protocol_id == PROSPECTIVE_PROTOCOL_ID:
            raise ValueError(
                "miniboone_nested_cv_v02 требует явный численный "
                "runtime-контракт"
            )
        return None
    if contract.protocol_id != protocol_id:
        raise ValueError(
            "protocol_id не соответствует численному runtime-контракту"
        )
    return contract


@contextmanager
def enforced_numeric_runtime(
    contract: NumericRuntimeContract,
) -> Iterator[tuple[NumericBackendRuntime, ...]]:
    """Enforce and verify the prospective BLAS thread limit, then restore it."""
    if not isinstance(contract, NumericRuntimeContract):
        raise TypeError("contract должен быть NumericRuntimeContract")
    before = capture_blas_runtime()
    _validate_backend_identity(contract, before)
    before_threads = tuple(runtime.num_threads for runtime in before)

    try:
        with threadpool_limits(
            limits=contract.thread_limit,
            user_api=contract.user_api,
        ):
            during = capture_blas_runtime()
            _validate_backend_identity(contract, during)
            invalid_limits = [
                runtime.num_threads
                for runtime in during
                if runtime.num_threads != contract.thread_limit
            ]
            if invalid_limits:
                raise RuntimeError(
                    "Ограничение BLAS-потоков не было фактически применено: "
                    f"expected={contract.thread_limit}; "
                    f"observed={invalid_limits}"
                )
            yield during
    finally:
        after = capture_blas_runtime()
        _validate_backend_identity(contract, after)
        after_threads = tuple(runtime.num_threads for runtime in after)
        if after_threads != before_threads:
            raise RuntimeError(
                "threadpoolctl не восстановил исходное число BLAS-потоков: "
                f"before={before_threads}; after={after_threads}"
            )


def numeric_runtime_evidence_rows(
    contract: NumericRuntimeContract,
    observed: tuple[NumericBackendRuntime, ...],
) -> list[dict[str, Any]]:
    """Build machine-readable provenance rows for an enforced runtime."""
    _validate_backend_identity(contract, observed)
    spec_by_identity = {
        spec.identity: spec for spec in contract.expected_backends
    }
    return [
        {
            "runtime_contract_id": contract.runtime_contract_id,
            "protocol_id": contract.protocol_id,
            "base_protocol_id": contract.base_protocol_id,
            "backend_key": spec_by_identity[runtime.identity].backend_key,
            "user_api": contract.user_api,
            "internal_api": runtime.identity.internal_api,
            "prefix": runtime.identity.prefix,
            "version": runtime.identity.version,
            "threading_layer": runtime.identity.threading_layer,
            "architecture": runtime.identity.architecture,
            "library_filename": runtime.identity.library_filename,
            "num_threads": runtime.num_threads,
            "thread_limit": contract.thread_limit,
            "contract_status": contract.status,
        }
        for runtime in observed
    ]
