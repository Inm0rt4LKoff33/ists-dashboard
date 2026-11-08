"""Escritura de las capas processed/ (por archivo) y curated/ (para Power BI)."""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from .config import CURATED, CURATED_XLSX, PROCESSED

FACT_SHEETS = {"matriculas": "matriculas", "retiros": "retiros", "aptitud": "aptitud"}


def write_processed(report_type, source_stem, df):
    folder = PROCESSED / report_type
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{source_stem}.parquet"
    df.to_parquet(path, index=False)
    return path


def _read_layer(report_type):
    files = sorted((PROCESSED / report_type).glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def build_curated():
    """Reconstruye la capa de consumo completa desde processed/ (idempotente)."""
    CURATED.mkdir(parents=True, exist_ok=True)
    facts = {t: _read_layer(t) for t in FACT_SHEETS}

    # Dimensiones compartidas: permiten que un solo filtro de periodo o de
    # carrera en Power BI afecte a las tres tablas a la vez (modelo estrella).
    # En una instalación nueva, sin ningún archivo cargado todavía, las tres
    # facts vienen vacías: el resultado debe ser un dim_ vacío, no un error.
    period_parts = [f[["periodo", "periodo_inicio", "sede"]] for f in facts.values() if not f.empty]
    periods = pd.concat(period_parts, ignore_index=True) if period_parts else pd.DataFrame(
        columns=["periodo", "periodo_inicio", "sede"]
    )
    dim_periodo = (
        periods.sort_values("periodo_inicio").drop_duplicates("periodo").reset_index(drop=True)
    )
    # Power BI decide si la primera fila es encabezado comparándola con las
    # demás: si todo es texto no puede distinguirlo y deja "Column1" con
    # "carrera" como dato. La columna de fecha resuelve esa ambigüedad.
    career_parts = [f[["carrera", "periodo_inicio"]] for f in facts.values() if "carrera" in f]
    careers = pd.concat(career_parts, ignore_index=True) if career_parts else pd.DataFrame(
        columns=["carrera", "periodo_inicio"]
    )
    dim_carrera = (
        careers.dropna(subset=["carrera"])
        .groupby("carrera", as_index=False)["periodo_inicio"].min()
        .rename(columns={"periodo_inicio": "primer_periodo_inicio"})
    )

    tables = {"dim_periodo": dim_periodo, "dim_carrera": dim_carrera}
    tables.update({f"fact_{name}": facts[t] for t, name in FACT_SHEETS.items()})

    for name, df in tables.items():
        df.to_parquet(CURATED / f"{name}.parquet", index=False)

    with pd.ExcelWriter(CURATED_XLSX, engine="openpyxl") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
    _as_excel_tables(CURATED_XLSX, tables)
    return {name: len(df) for name, df in tables.items()}


def _as_excel_tables(path, tables):
    """Formatea cada hoja como Tabla de Excel: Power BI las detecta por nombre."""
    wb = load_workbook(path)
    for name, df in tables.items():
        if df.empty:
            continue
        ws = wb[name]
        ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
        table = Table(displayName=name, ref=ref)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
        ws.add_table(table)
    wb.save(path)
