from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

from mlcra.application import MlcraApplicationError, build_dashboard_view


FILES = ("dashboard_view.json", "dashboard_en.html", "dashboard_ru.html", "dashboard_manifest.json")


def _error(code: str, field: str, expected: Any, actual: Any) -> None:
    raise MlcraApplicationError(
        exit_code=6 if code.startswith("MLCRA_DASHBOARD_INTEGRITY") else 3,
        error_code=code,
        phase="dashboard",
        artifact_or_field=field,
        expected=expected,
        actual=actual,
        severity="error",
        action_taken="dashboard_publication_stopped",
        user_action="Повторно создайте панель из неизменённого проверенного bundle.",
        rule_source="ST08_12.dashboard_contract",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def _cell(value: Any) -> str:
    if isinstance(value, float):
        value = f"{value:.6f}"
    return html.escape(str(value), quote=True)


def render_html(view: dict[str, Any], locale: str) -> str:
    if locale not in {"en", "ru"}:
        raise ValueError("locale must be en or ru")
    ru = locale == "ru"
    title = "Панель доказательств ML-CRA" if ru else "ML-CRA evidence dashboard"
    labels = {
        "summary": "Итог" if ru else "Summary",
        "claim": "Утверждение" if ru else "Claim",
        "verdict": "Вердикт" if ru else "Verdict",
        "metric": "Основная метрика" if ru else "Primary metric",
        "delta": "Средняя разность" if ru else "Mean delta",
        "threshold": "Порог" if ru else "Threshold",
        "folds": "Парные блоки" if ru else "Paired folds",
        "scope": "Граница вывода" if ru else "Scope limit",
        "details": "Результаты блоков" if ru else "Fold results",
        "seed": "Зерно" if ru else "Seed",
        "fold": "Блок" if ru else "Fold",
        "baseline": "Метрики baseline" if ru else "Baseline metrics",
        "candidate": "Метрики кандидата" if ru else "Candidate metrics",
        "warning": "Ограничения" if ru else "Limitations",
    }
    rows = []
    for row in view["folds"]:
        rows.append(
            "<tr>"
            f"<td>{_cell(row['seed'])}</td><td>{_cell(row['fold'])}</td>"
            f"<td><code>{_cell(json.dumps(row['baseline_metrics'], sort_keys=True))}</code></td>"
            f"<td><code>{_cell(json.dumps(row['candidate_metrics'], sort_keys=True))}</code></td>"
            f"<td>{_cell(row['primary_delta'])}</td></tr>"
        )
    warnings = "".join(f"<li>{_cell(item['message_ru'])}</li>" for item in view["warnings"])
    return f"""<!doctype html>
<html lang="{locale}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>{_cell(title)}</title><style>
:root{{--ink:#172033;--muted:#526077;--paper:#fff;--panel:#f3f6fb;--line:#c7d0df;--accent:#164e63}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--panel);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:2rem}}h1,h2{{line-height:1.2}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}}
.card,section{{background:var(--paper);border:1px solid var(--line);border-radius:.7rem;padding:1rem;margin-bottom:1rem}}
.label{{color:var(--muted);font-size:.9rem}}.value{{font-size:1.25rem;font-weight:700;overflow-wrap:anywhere}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{border:1px solid var(--line);padding:.55rem;text-align:left;vertical-align:top}}th{{background:#e6edf6}}code{{white-space:normal;overflow-wrap:anywhere}}
@media(max-width:700px){{main{{padding:.75rem}}.table-wrap{{overflow-x:auto}}}}
</style></head><body><main><h1>{_cell(title)}</h1>
<section aria-labelledby="summary"><h2 id="summary">{_cell(labels['summary'])}</h2><div class="cards">
<div class="card"><div class="label">{_cell(labels['claim'])}</div><div class="value">{_cell(view['claim_id'])}</div></div>
<div class="card"><div class="label">{_cell(labels['verdict'])}</div><div class="value">{_cell(view['verdict'])}</div></div>
<div class="card"><div class="label">{_cell(labels['metric'])}</div><div class="value">{_cell(view['primary_metric'])}</div></div>
<div class="card"><div class="label">{_cell(labels['delta'])}</div><div class="value">{_cell(view['mean_primary_delta'])}</div></div>
<div class="card"><div class="label">{_cell(labels['threshold'])}</div><div class="value">{_cell(view['minimum_mean_delta'])}</div></div>
<div class="card"><div class="label">{_cell(labels['folds'])}</div><div class="value">{_cell(view['positive_primary_delta_folds'])}/{_cell(view['fold_count'])}</div></div>
</div><p><strong>{_cell(labels['scope'])}:</strong> {_cell(view['scope_limit'])}</p></section>
<section aria-labelledby="details"><h2 id="details">{_cell(labels['details'])}</h2><div class="table-wrap"><table><thead><tr>
<th scope="col">{_cell(labels['seed'])}</th><th scope="col">{_cell(labels['fold'])}</th><th scope="col">{_cell(labels['baseline'])}</th><th scope="col">{_cell(labels['candidate'])}</th><th scope="col">Delta</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section aria-labelledby="warnings"><h2 id="warnings">{_cell(labels['warning'])}</h2><ul>{warnings}</ul></section>
</main></body></html>"""


def run_dashboard(bundle_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    if output.exists():
        _error("MLCRA_DASHBOARD_OUTPUT_EXISTS", "output_dir", "nonexistent path", str(output))
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    try:
        view = build_dashboard_view(bundle_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir()
        _json(staging / "dashboard_view.json", view)
        (staging / "dashboard_en.html").write_text(render_html(view, "en"), encoding="utf-8", newline="\n")
        (staging / "dashboard_ru.html").write_text(render_html(view, "ru"), encoding="utf-8", newline="\n")
        hashes = {name: _sha256(staging / name) for name in FILES[:-1]}
        _json(staging / "dashboard_manifest.json", {"schema_version": "mlcra_dashboard_manifest_v01", "source_bundle_verified": True, "model_fit_performed": False, "network_access_performed": False, "artifact_hashes": hashes})
        verify_dashboard_output(bundle_path, staging)
        os.replace(staging, output)
        return {"command": "dashboard", "status": "PASS", "exit_code": 0, "claim_id": view["claim_id"], "verdict": view["verdict"], "output_dir": str(output), "model_fit_performed": False}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify_dashboard_output(bundle_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    if not output.is_dir() or sorted(path.name for path in output.iterdir()) != sorted(FILES):
        _error("MLCRA_DASHBOARD_INTEGRITY_FILE_SET", "dashboard.files", sorted(FILES), "missing_or_extra")
    expected_view = build_dashboard_view(bundle_path)
    actual_view = json.loads((output / "dashboard_view.json").read_text(encoding="utf-8"))
    if actual_view != expected_view:
        _error("MLCRA_DASHBOARD_INTEGRITY_GOLDEN_MISMATCH", "dashboard_view.json", expected_view, actual_view)
    if (output / "dashboard_en.html").read_text(encoding="utf-8") != render_html(expected_view, "en") or (output / "dashboard_ru.html").read_text(encoding="utf-8") != render_html(expected_view, "ru"):
        _error("MLCRA_DASHBOARD_INTEGRITY_HTML_MISMATCH", "dashboard_html", "exact render from verified view", "mismatch")
    manifest = json.loads((output / "dashboard_manifest.json").read_text(encoding="utf-8"))
    observed = {name: _sha256(output / name) for name in FILES[:-1]}
    if manifest.get("artifact_hashes") != observed or manifest.get("model_fit_performed") is not False or manifest.get("network_access_performed") is not False:
        _error("MLCRA_DASHBOARD_INTEGRITY_MANIFEST_MISMATCH", "dashboard_manifest.json", observed, manifest)
    return {"status": "PASS", "claim_id": expected_view["claim_id"], "verdict": expected_view["verdict"], "files": len(FILES), "model_fit_performed": False}
