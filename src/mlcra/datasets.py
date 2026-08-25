from __future__ import annotations

import hashlib
import json
import shutil
import socket
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MINIBOONE_CANDIDATE_ID = "openml_miniboone_41150"
MINIBOONE_DATASET_ID = 41150
MINIBOONE_DATASET_NAME = "MiniBooNE"
MINIBOONE_TARGET_NAME = "signal"
MINIBOONE_FEATURE_NAMES = tuple(f"ParticleID_{index}" for index in range(50))
MINIBOONE_EXPECTED_ROWS = 130_064
MINIBOONE_EXPECTED_TARGET_COUNTS = {"False": 93_565, "True": 36_499}
MINIBOONE_CACHE_FILES = {
    "description.xml": (
        2_186,
        "fb36ca8533b5d8e114820e075ed50bfdb5182dc83daf5de1e9ef9c7ae555bffd",
    ),
    "dataset_41150.pkl.py3": (
        52_158_469,
        "02967c5cb06f77e3ee78ddb0d723ea6046525bbc4e21f353a66bb5f3878530d8",
    ),
    "dataset_41150.pq": (
        51_836_292,
        "d6e1dd4c395e1ef456a048b55e10ed662e30203e8ebab2f3216f680c9d439646",
    ),
}


class OfflineNetworkAccessError(RuntimeError):
    """Raised before an attempted network operation can leave the process."""


@dataclass
class OfflineNetworkEvidence:
    attempts: int = 0


@dataclass(frozen=True)
class MiniBooNECacheEvidence:
    cache_server_dir: str
    cache_manifest_sha256: str
    cache_file_count: int
    network_attempts: int
    dataset_rows: int
    feature_count: int
    target_false_count: int
    target_true_count: int
    dataset_content_sha256: str


def _block_network(
    evidence: OfflineNetworkEvidence,
    operation: str,
    target: Any,
) -> None:
    evidence.attempts += 1
    raise OfflineNetworkAccessError(
        f"ST07_17 запрещает сеть: operation={operation}; target={target!r}"
    )


@contextmanager
def deny_network_access() -> Iterator[OfflineNetworkEvidence]:
    """Fail closed on DNS resolution or socket connection attempts."""
    evidence = OfflineNetworkEvidence()
    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo

    class GuardedSocket(original_socket):
        def connect(self, address: Any) -> None:
            _block_network(evidence, "socket.connect", address)

        def connect_ex(self, address: Any) -> int:
            _block_network(evidence, "socket.connect_ex", address)
            raise AssertionError("unreachable")

    def blocked_create_connection(*args: Any, **kwargs: Any) -> None:
        target = args[0] if args else kwargs
        _block_network(evidence, "socket.create_connection", target)

    def blocked_getaddrinfo(*args: Any, **kwargs: Any) -> None:
        target = args[:2] if args else kwargs
        _block_network(evidence, "socket.getaddrinfo", target)

    socket.socket = GuardedSocket
    socket.create_connection = blocked_create_connection
    socket.getaddrinfo = blocked_getaddrinfo
    try:
        yield evidence
    finally:
        socket.socket = original_socket
        socket.create_connection = original_create_connection
        socket.getaddrinfo = original_getaddrinfo


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cache_file_rows(dataset_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for filename, (expected_size, expected_sha256) in MINIBOONE_CACHE_FILES.items():
        path = dataset_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Обязательный MiniBooNE cache-файл отсутствует: {path}")
        observed_size = path.stat().st_size
        observed_sha256 = _sha256_file(path)
        if observed_size != expected_size or observed_sha256 != expected_sha256:
            raise ValueError(
                "MiniBooNE cache-файл не совпадает с зарегистрированным "
                f"ST07_17 состоянием: {filename}; size={observed_size}; "
                f"sha256={observed_sha256}"
            )
        rows.append(
            {
                "filename": filename,
                "size": observed_size,
                "sha256": observed_sha256,
            }
        )
    return rows


def _manifest_sha256(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        rows,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _openml_root_from_server_cache(server_cache_dir: Path) -> Path:
    resolved = server_cache_dir.resolve()
    if tuple(part.lower() for part in resolved.parts[-3:]) != (
        "org",
        "openml",
        "www",
    ):
        raise ValueError(
            "cache_server_dir должен оканчиваться точным путём org/openml/www"
        )
    return resolved.parents[2]


def _dataset_content_sha256(X: pd.DataFrame, y: np.ndarray) -> str:
    values = np.ascontiguousarray(X.to_numpy(dtype=np.float64, copy=True))
    target = np.ascontiguousarray(y, dtype=np.int64)
    header = json.dumps(
        {
            "columns": list(X.columns),
            "shape": list(X.shape),
            "value_dtype": str(values.dtype),
            "target_dtype": str(target.dtype),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(header)
    digest.update(values.tobytes(order="C"))
    digest.update(target.tobytes(order="C"))
    return digest.hexdigest()


def load_miniboone_from_openml_cache(
    cache_server_dir: Path,
) -> tuple[
    dict[str, Any],
    pd.DataFrame,
    np.ndarray,
    list[str],
    MiniBooNECacheEvidence,
]:
    """Load registered MiniBooNE from an exact cache without network fallback."""
    import openml

    server_cache = Path(cache_server_dir).resolve()
    _openml_root_from_server_cache(server_cache)
    source_dataset_dir = server_cache / "datasets" / str(MINIBOONE_DATASET_ID)
    before_rows = _cache_file_rows(source_dataset_dir)
    cache_manifest_sha256 = _manifest_sha256(before_rows)

    original_server_cache = Path(openml.config.get_cache_directory()).resolve()
    original_root = _openml_root_from_server_cache(original_server_cache)
    with tempfile.TemporaryDirectory(prefix="mlcra_st0717_openml_") as temp_name:
        temp_root = Path(temp_name) / "cache_root"
        staged_dataset_dir = (
            temp_root
            / "org"
            / "openml"
            / "www"
            / "datasets"
            / str(MINIBOONE_DATASET_ID)
        )
        staged_dataset_dir.mkdir(parents=True)
        for filename in MINIBOONE_CACHE_FILES:
            shutil.copy2(source_dataset_dir / filename, staged_dataset_dir / filename)

        try:
            openml.config.set_root_cache_directory(str(temp_root))
            with deny_network_access() as network_evidence:
                dataset = openml.datasets.get_dataset(
                    MINIBOONE_DATASET_ID,
                    download_data=True,
                    cache_format="pickle",
                    download_qualities=False,
                    download_features_meta_data=False,
                    download_all_files=False,
                    force_refresh_cache=False,
                )
                X_raw, y_raw, _, _ = dataset.get_data(
                    dataset_format="dataframe",
                    target=dataset.default_target_attribute,
                )
        finally:
            openml.config.set_root_cache_directory(str(original_root))

    if network_evidence.attempts != 0:
        raise OfflineNetworkAccessError(
            "Успешный cache load не должен содержать сетевых попыток"
        )
    if int(dataset.dataset_id) != MINIBOONE_DATASET_ID:
        raise ValueError("OpenML вернул неожиданный dataset_id")
    if dataset.name != MINIBOONE_DATASET_NAME:
        raise ValueError("OpenML вернул неожиданное имя dataset")
    if dataset.default_target_attribute != MINIBOONE_TARGET_NAME:
        raise ValueError("OpenML вернул неожиданный default target")

    target_text = pd.Series(y_raw).astype(str)
    counts = target_text.value_counts().sort_index().to_dict()
    if counts != MINIBOONE_EXPECTED_TARGET_COUNTS:
        raise ValueError(
            "Распределение MiniBooNE target не совпадает с контрактом: "
            f"{counts}"
        )
    mapped_target = target_text.map({"False": 0, "True": 1}).to_numpy()
    bundle, X, y, feature_names = prepare_miniboone_candidate(
        X_raw,
        mapped_target,
    )
    if len(X) != MINIBOONE_EXPECTED_ROWS:
        raise ValueError(
            f"MiniBooNE должен иметь {MINIBOONE_EXPECTED_ROWS} строк"
        )

    after_rows = _cache_file_rows(source_dataset_dir)
    if after_rows != before_rows:
        raise RuntimeError("Исходный OpenML cache изменился во время чтения")
    evidence = MiniBooNECacheEvidence(
        cache_server_dir=str(server_cache),
        cache_manifest_sha256=cache_manifest_sha256,
        cache_file_count=len(before_rows),
        network_attempts=network_evidence.attempts,
        dataset_rows=len(X),
        feature_count=len(feature_names),
        target_false_count=counts["False"],
        target_true_count=counts["True"],
        dataset_content_sha256=_dataset_content_sha256(X, y),
    )
    return bundle, X, y, feature_names, evidence


def prepare_miniboone_candidate(
    X_raw: pd.DataFrame,
    y_raw: Any,
    *,
    candidate_id: str = MINIBOONE_CANDIDATE_ID,
    dataset_id: int = MINIBOONE_DATASET_ID,
    dataset_name: str = MINIBOONE_DATASET_NAME,
    target_name: str = MINIBOONE_TARGET_NAME,
) -> tuple[dict[str, Any], pd.DataFrame, np.ndarray, list[str]]:
    """Validate and prepare the registered MiniBooNE feature/target contract."""
    if not isinstance(X_raw, pd.DataFrame):
        raise TypeError("X_raw должен быть pandas.DataFrame")
    expected_features = list(MINIBOONE_FEATURE_NAMES)
    if list(X_raw.columns) != expected_features:
        raise ValueError(
            "MiniBooNE требует точный порядок ParticleID_0 ... ParticleID_49"
        )
    if X_raw.empty:
        raise ValueError("MiniBooNE X_raw не должен быть пустым")
    if X_raw.isna().any().any():
        raise ValueError("MiniBooNE X_raw не должен содержать пропуски")

    X = X_raw.copy()
    for column in expected_features:
        X[column] = pd.to_numeric(X[column], errors="raise")
    if any(not pd.api.types.is_numeric_dtype(X[column]) for column in X):
        raise TypeError("Все признаки MiniBooNE должны быть числовыми")

    y_series = pd.Series(y_raw, name=target_name)
    if len(y_series) != len(X) or y_series.isna().any():
        raise ValueError("MiniBooNE y должен совпадать по длине и не иметь пропусков")
    y_numeric = pd.to_numeric(y_series, errors="raise").to_numpy()
    if set(np.unique(y_numeric).tolist()) != {0, 1}:
        raise ValueError("MiniBooNE target должен иметь точное кодирование False=0;True=1")
    y = y_numeric.astype(np.int64, copy=False)

    if candidate_id != MINIBOONE_CANDIDATE_ID:
        raise ValueError("Неожиданный candidate_id для MiniBooNE")
    if dataset_id != MINIBOONE_DATASET_ID:
        raise ValueError("Неожиданный OpenML dataset id для MiniBooNE")
    if dataset_name != MINIBOONE_DATASET_NAME or target_name != MINIBOONE_TARGET_NAME:
        raise ValueError("Имя dataset или target не соответствует контракту MiniBooNE")

    bundle = {
        "candidate_id": candidate_id,
        "did": dataset_id,
        "dataset_name": dataset_name,
        "target_name": target_name,
        "target_metadata": {
            "target_class_0": "False",
            "target_class_1": "True",
            "positive_class_assumption": "True",
        },
    }
    return bundle, X, y, expected_features


def build_miniboone_control_estimators(random_state: int) -> dict[str, Any]:
    """Build the two registered untuned control estimators."""
    if isinstance(random_state, bool) or not isinstance(random_state, int):
        raise TypeError("random_state должен быть целым числом")
    if random_state < 0:
        raise ValueError("random_state не должен быть отрицательным")
    return {
        "dummy_prior": DummyClassifier(strategy="prior"),
        "logistic_regression": Pipeline(
            steps=[
                ("standard_scaler", StandardScaler()),
                (
                    "logistic_regression",
                    LogisticRegression(
                        max_iter=1000,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }
