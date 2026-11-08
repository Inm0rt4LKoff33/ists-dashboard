import shutil

import pandas as pd
import pytest

from etl import config, load, run
from etl.extract import READERS
from etl.transform import (categorize_withdrawal, normalize_category, normalize_id, parse_period,
                           pseudonymize, similar_careers, transform)

RAW = config.RAW
SAMPLES = {
    "matriculas": RAW / "matriculas" / "matriculas.xlsx",
    "aptitud": RAW / "aptitud" / "final.xlsx",
    "retiros": RAW / "retiros" / "retiro.xlsx",
}
PII_COLUMNS = {"nombres_apellidos", "correo", "telefono_celular", "telefono_fijo", "direccion",
               "contactos", "apellidos", "nombres", "nombre_retirado", "motivo_detalle",
               "numero_documento", "cedula", "fecha_nacimiento"}


def test_parse_period():
    p = parse_period("PROCESO DE TITULACIÓN  PERIODO NOVIEMBRE 2026 - MARZO 2027 MACHALA")
    assert p["periodo"] == "NOVIEMBRE 2026 - MARZO 2027"
    assert p["periodo_inicio"] == pd.Timestamp("2026-11-01")
    assert p["sede"] == "MACHALA"
    assert parse_period("sin periodo") is None


def test_parse_period_uses_canonical_month_names():
    a = parse_period("PERIODO SETIEMBRE 2026 - FEBRERO 2027")
    b = parse_period("periodo Sep 2026 - feb 2027")
    assert a["periodo"] == b["periodo"] == "SEPTIEMBRE 2026 - FEBRERO 2027"


@pytest.mark.parametrize("raw,expected", [
    ("Tecnología Superior en Ciberseguridad ", "TECNOLOGIA SUPERIOR EN CIBERSEGURIDAD"),
    ("TECNOLOGIA  SUPERIOR EN CIBERSEGURIDAD", "TECNOLOGIA SUPERIOR EN CIBERSEGURIDAD"),
    ("Diseño Gráfico", "DISEÑO GRAFICO"),
    ("ESPAñOL/ESPAñOLA", "ESPAÑOL/ESPAÑOLA"),
    ("Pingüino -", "PINGUINO"),
    ("N/A", pd.NA),
    ("   ", pd.NA),
])
def test_normalize_category(raw, expected):
    assert normalize_category(raw) is expected if expected is pd.NA else normalize_category(raw) == expected


def test_similar_careers_are_detected():
    assert similar_careers(["ENFERMERIA", "TECNICO SUPERIOR EN ENFERMERIA", "GASTRONOMIA"]) == [
        ["ENFERMERIA", "TECNICO SUPERIOR EN ENFERMERIA"]]


def test_normalize_id_keeps_leading_zero():
    assert normalize_id(748662468) == "0748662468"
    assert normalize_id("0748662468") == "0748662468"
    assert normalize_id(748662468.0) == "0748662468"


def test_pseudonymize_is_stable_and_hides_id():
    assert pseudonymize("0748662468") == pseudonymize("0748662468")
    assert "0748662468" not in pseudonymize("0748662468")


def test_categorize_withdrawal():
    assert categorize_withdrawal("RETIRO POR MOTIVO DE EMBARAZO DE ALTO RIESGO") == "SALUD"
    assert categorize_withdrawal(None) == "SIN DATO"


@pytest.mark.parametrize("report_type,expected_rows", [("matriculas", 40), ("aptitud", 15), ("retiros", 1)])
def test_real_samples_meet_contract(report_type, expected_rows):
    raw_df, title = READERS[report_type](SAMPLES[report_type])
    clean, issues = transform(report_type, raw_df, title, "x.xlsx", pd.Timestamp("2026-01-01"))
    assert clean is not None, issues
    assert len(clean) == expected_rows
    assert not PII_COLUMNS & set(clean.columns)
    assert clean["periodo"].notna().all()
    assert clean["carrera"].notna().all()


def test_matriculas_gets_spanish_month_label():
    raw_df, title = READERS["matriculas"](SAMPLES["matriculas"])
    clean, issues = transform("matriculas", raw_df, title, "x.xlsx", pd.Timestamp("2026-01-01"))
    assert clean["mes_inscripcion"].notna().all()
    assert not any(m[:1].isdigit() for m in clean["mes_inscripcion"])  # nunca "6 2026", siempre el nombre
    # El nombre del mes en español debe coincidir con mes_inscripcion_inicio, sin depender del idioma del sistema.
    MESES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
             "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    for _, r in clean.iterrows():
        if pd.isna(r["fecha_inscripcion"]):
            continue
        esperado = f"{MESES[r['mes_inscripcion_inicio'].month - 1]} {r['mes_inscripcion_inicio'].year}"
        assert r["mes_inscripcion"] == esperado


def test_missing_required_column_is_rejected():
    raw_df, title = READERS["matriculas"](SAMPLES["matriculas"])
    clean, issues = transform("matriculas", raw_df.drop(columns=["CARRERA"]), title, "x.xlsx", pd.Timestamp.now())
    assert clean is None
    assert issues[0]["regla"] == "columnas_requeridas"


def test_messy_values_are_normalized_or_reported():
    raw_df, title = READERS["matriculas"](SAMPLES["matriculas"])
    raw_df = raw_df.copy()
    raw_df.loc[0, "CARRERA"] = " diseño  gráfico "
    raw_df.loc[1, "CARRERA"] = "Diseño Grafico"
    raw_df.loc[2, "EDAD"] = "veinte"
    raw_df.loc[3, "FECHA INSCRIPCION"] = "15/03/2026"
    clean, issues = transform("matriculas", raw_df, title, "x.xlsx", pd.Timestamp.now())
    assert set(clean.loc[:1, "carrera"]) == {"DISEÑO GRAFICO"}
    assert pd.isna(clean.loc[2, "edad"])
    assert any(i["regla"] == "valor_invalido" and "edad" in i["detalle"] for i in issues)
    assert clean.loc[3, "fecha_inscripcion"] == pd.Timestamp("2026-03-15")


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Copia los datos reales a una carpeta temporal y apunta el pipeline ahí."""
    raw = tmp_path / "raw"
    shutil.copytree(RAW, raw)
    paths = {
        "RAW": raw, "PROCESSED": tmp_path / "processed", "CURATED": tmp_path / "curated",
        "CURATED_XLSX": tmp_path / "curated" / "observatorio_ists.xlsx",
        "QUALITY_REPORT": tmp_path / "curated" / "calidad.csv", "MANIFEST": tmp_path / "curated" / "manifest.json",
    }
    for module in (run, load):
        for name, value in paths.items():
            if hasattr(module, name):
                monkeypatch.setattr(module, name, value)
    paths["CURATED"].mkdir()
    return paths


def _fact_rows(paths, sheet):
    return len(pd.read_excel(paths["CURATED_XLSX"], sheet_name=sheet))


def test_fresh_install_with_no_files_does_not_crash(sandbox):
    """Instalación nueva: las carpetas raw/<tipo> existen pero están vacías."""
    for p in (sandbox["RAW"] / t for t in ("matriculas", "retiros", "aptitud")):
        for f in p.glob("*"):
            f.unlink()
    manifest, issues = run.run()
    assert manifest == []
    for sheet in ("dim_periodo", "dim_carrera", "fact_matriculas", "fact_retiros", "fact_aptitud"):
        assert _fact_rows(sandbox, sheet) == 0


def test_pipeline_is_idempotent(sandbox):
    run.run()
    run.run()
    assert _fact_rows(sandbox, "fact_matriculas") == 40


def test_every_curated_table_has_a_non_text_column(sandbox):
    """Si una tabla es solo texto, Power BI no reconoce la fila de encabezados."""
    run.run()
    for sheet, df in pd.read_excel(sandbox["CURATED_XLSX"], sheet_name=None).items():
        assert not df.empty, sheet
        assert any(not pd.api.types.is_string_dtype(df[c]) and df[c].dtype != object for c in df), sheet


def test_duplicate_file_is_ignored(sandbox):
    src = sandbox["RAW"] / "matriculas" / "matriculas.xlsx"
    shutil.copy(src, src.with_name("matriculas_copia.xlsx"))
    _, issues = run.run()
    assert _fact_rows(sandbox, "fact_matriculas") == 40
    assert any(i["regla"] == "archivo_duplicado" for i in issues)


def test_corrected_version_of_same_period_replaces_older(sandbox):
    import os
    from openpyxl import load_workbook

    src = sandbox["RAW"] / "aptitud" / "final.xlsx"
    corrected = src.with_name("final_corregido.xlsx")
    wb = load_workbook(src)
    wb.active["K5"] = 40  # PROM del primer estudiante corregido
    wb.save(corrected)
    os.utime(src, (1, 1))  # el original queda como el más antiguo

    _, issues = run.run()
    aptitud = pd.read_excel(sandbox["CURATED_XLSX"], sheet_name="fact_aptitud")
    assert len(aptitud) == 15
    assert set(aptitud["archivo_origen"]) == {"final_corregido.xlsx"}
    assert any(i["regla"] == "periodo_repetido" for i in issues)


def test_removed_raw_file_disappears_from_curated(sandbox):
    run.run()
    (sandbox["RAW"] / "retiros" / "retiro.xlsx").unlink()
    run.run()
    assert pd.read_excel(sandbox["CURATED_XLSX"], sheet_name="fact_retiros").empty
