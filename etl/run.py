"""Ejecuta el pipeline completo: raw -> processed -> curated.

Uso:  python -m etl.run
"""
import hashlib
import json

import pandas as pd

from .config import CURATED, MANIFEST, PROCESSED, QUALITY_REPORT, RAW, SCHEMAS
from .extract import READERS
from .load import build_curated, write_processed
from .transform import similar_careers, transform

SUPPORTED = {".xlsx", ".xls"}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _remove_orphans(report_type, live_stems):
    """Si un archivo se borró de raw/, su versión limpia tampoco debe seguir en el dataset."""
    for parquet in (PROCESSED / report_type).glob("*.parquet"):
        if parquet.stem not in live_stems:
            parquet.unlink()


def run():
    loaded_at = pd.Timestamp.now().floor("s")
    issues, manifest = [], []

    for report_type in SCHEMAS:
        # En una instalación nueva estas carpetas todavía no existen (data/ no
        # se versiona). Crearlas aquí evita un primer intento confuso de
        # "0 archivos procesados" sin ninguna pista de por qué.
        (RAW / report_type).mkdir(parents=True, exist_ok=True)
        sources = sorted(p for p in (RAW / report_type).glob("*") if p.suffix.lower() in SUPPORTED and not p.name.startswith("~$"))
        _remove_orphans(report_type, {p.stem for p in sources})
        seen_hashes, period_owner = {}, {}

        # Del más reciente al más antiguo: ante un mismo periodo cargado dos
        # veces, gana la última versión subida.
        for path in sorted(sources, key=lambda p: p.stat().st_mtime, reverse=True):
            digest = _sha256(path)
            entry = {"tipo": report_type, "archivo": path.name, "sha256": digest, "procesado_en": str(loaded_at)}
            processed_path = PROCESSED / report_type / f"{path.stem}.parquet"

            if digest in seen_hashes:
                issues.append({"nivel": "AVISO", "archivo": path.name, "regla": "archivo_duplicado",
                               "detalle": f"Idéntico a {seen_hashes[digest]}; se ignora"})
                processed_path.unlink(missing_ok=True)
                manifest.append({**entry, "estado": "DUPLICADO", "filas": 0})
                continue
            seen_hashes[digest] = path.name

            try:
                raw_df, title = READERS[report_type](path)
                clean, file_issues = transform(report_type, raw_df, title, path.name, loaded_at)
                issues += file_issues
                if clean is None:
                    entry.update(estado="RECHAZADO", filas=0)
                else:
                    overlap = {p: period_owner[p] for p in clean["periodo"].unique() if p in period_owner}
                    if overlap:
                        issues.append({"nivel": "AVISO", "archivo": path.name, "regla": "periodo_repetido",
                                       "detalle": f"El periodo {', '.join(overlap)} ya viene en {', '.join(set(overlap.values()))} (más reciente); se ignora este archivo"})
                        processed_path.unlink(missing_ok=True)
                        entry.update(estado="REEMPLAZADO", filas=0)
                    else:
                        period_owner.update({p: path.name for p in clean["periodo"].unique()})
                        write_processed(report_type, path.stem, clean)
                        entry.update(estado="OK", filas=len(clean))
            except Exception as exc:  # un archivo dañado no debe frenar al resto
                issues.append({"nivel": "ERROR", "archivo": path.name, "regla": "lectura", "detalle": str(exc)})
                entry.update(estado="ERROR", filas=0)
            manifest.append(entry)

    counts = build_curated()
    if counts.get("dim_carrera"):
        for group in similar_careers(pd.read_parquet(CURATED / "dim_carrera.parquet")["carrera"]):
            issues.append({"nivel": "AVISO", "archivo": "(todos)", "regla": "carrera_similar",
                           "detalle": f"¿Son la misma carrera? {' | '.join(group)}. Si lo son, agrégalas a CATEGORY_ALIASES en etl/config.py"})

    pd.DataFrame(issues, columns=["nivel", "archivo", "regla", "detalle"]).to_csv(QUALITY_REPORT, index=False)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Archivos procesados:")
    for e in manifest:
        print(f"  [{e['estado']:9}] {e['tipo']:10} {e['archivo']:30} {e['filas']} filas")
    print("\nTablas para Power BI (data/curated/observatorio_ists.xlsx):")
    for name, n in counts.items():
        print(f"  {name:18} {n} filas")
    errors = sum(1 for i in issues if i["nivel"] == "ERROR")
    print(f"\nIncidencias de calidad: {len(issues)} ({errors} errores) -> {QUALITY_REPORT.relative_to(QUALITY_REPORT.parents[2])}")
    return manifest, issues


if __name__ == "__main__":
    run()
