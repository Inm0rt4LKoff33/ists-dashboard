"""Lectura de cada tipo de reporte desde su formato original de Excel.

Cada lector devuelve (DataFrame con los encabezados originales, título del
documento). No limpia ni renombra: eso es trabajo de transform.py. Separarlo
permite cambiar la limpieza sin tocar cómo se lee cada formato, y viceversa.
"""
import re

import pandas as pd

PERIOD_RE = re.compile(r"[A-ZÁÉÍÓÚÑ]+\s+\d{4}\s*-\s*[A-ZÁÉÍÓÚÑ]+\s+\d{4}", re.IGNORECASE)


def _find_row(raw, predicate, limit=40):
    for i in range(min(limit, len(raw))):
        values = {str(v).strip().upper() for v in raw.iloc[i] if pd.notna(v)}
        if predicate(values):
            return i
    raise ValueError("No se encontró la fila de encabezado esperada")


def _find_title(raw, limit=20):
    """Primer texto de las filas superiores que contenga un rango de periodo."""
    for i in range(min(limit, len(raw))):
        for v in raw.iloc[i]:
            if isinstance(v, str) and PERIOD_RE.search(v):
                return v
    return None


def read_matriculas(path):
    df = pd.read_excel(path, sheet_name=0, dtype=object)
    return df, None  # el periodo viene en su propia columna PERIODO


def read_retiros(path):
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype=object)
    title = _find_title(raw)
    h = _find_row(raw, lambda vals: {"CEDULA", "MOTIVO"} <= vals)

    df = raw.iloc[h + 1:].copy()
    df.columns = [str(v).strip() if pd.notna(v) else f"_vacia_{i}" for i, v in enumerate(raw.iloc[h])]
    # Las filas de resumen ("TOTAL DE RETIRADOS: 1") solo traen un valor suelto;
    # un registro real llena varias columnas a la vez.
    df = df[df.notna().sum(axis=1) >= 3]
    return df.reset_index(drop=True), title


def read_aptitud(path):
    raw = pd.read_excel(path, sheet_name=0, header=None, dtype=object)
    title = _find_title(raw)
    h = _find_row(raw, lambda vals: {"N°", "PROM"} <= vals)

    # Encabezado en dos filas: la de categorías (h-1) está fusionada
    # verticalmente con la de columnas (h) para campos como DEUDAS o TUTOR
    # PROYECTO, que no tienen sub-etiqueta propia.
    cat_row, col_row = raw.iloc[h - 1], raw.iloc[h]
    headers, seen = [], {}
    for i in raw.columns:
        v = col_row[i] if pd.notna(col_row[i]) else cat_row[i]
        name = str(v).strip() if pd.notna(v) else f"_vacia_{i}"
        seen[name] = seen.get(name, 0) + 1
        headers.append(name if seen[name] == 1 else f"{name}_{seen[name]}")

    df = raw.iloc[h + 1:].copy()
    df.columns = headers

    # Filas-banner de carrera: "N°" no es numérico (trae el nombre de la
    # carrera, celda fusionada a lo ancho). Se baja como columna CARRERA.
    is_banner = pd.to_numeric(df["N°"], errors="coerce").isna()
    df["CARRERA"] = df["N°"].where(is_banner).ffill()
    df = df[~is_banner & df["N°"].notna()]
    return df.reset_index(drop=True), title


READERS = {
    "matriculas": read_matriculas,
    "retiros": read_retiros,
    "aptitud": read_aptitud,
}
