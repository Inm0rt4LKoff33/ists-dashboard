"""Limpieza y estandarización de un reporte ya leído, contra su contrato."""
import hashlib
import re
import unicodedata
from datetime import date

import pandas as pd

from .config import CATEGORY_ALIASES, SALT, SCHEMAS
from .extract import PERIOD_RE

MONTH_NAMES = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO",
               "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
# Se reconoce el mes por sus 3 primeras letras: NOV, Noviembre, SETIEMBRE...
MONTHS = {name[:3]: i for i, name in enumerate(MONTH_NAMES, start=1)} | {"SET": 9}
NULL_TOKENS = {"", "-", "--", ".", "N/A", "NA", "S/N", "S/D", "NULL", "NONE", "NAN", "#N/A"}
FLAG_TRUE = {"SI", "SÍ", "S", "X", "1", "TRUE", "VERDADERO"}
FLAG_FALSE = {"NO", "N", "0", "FALSE", "FALSO"}

WITHDRAWAL_CATEGORIES = [
    ("SALUD", ("EMBARAZO", "SALUD", "ENFERMEDAD", "MEDIC", "CALAMIDAD")),
    ("ECONOMICO", ("ECONOM", "PAGO", "DEUDA", "FINANC")),
    ("LABORAL", ("TRABAJO", "LABORAL", "HORARIO")),
    ("ACADEMICO", ("ACADEM", "CARRERA", "CAMBIO", "NOTAS", "REPROB")),
]


def norm_key(text):
    """Clave de comparación de encabezados: mayúsculas, sin tildes ni espacios dobles."""
    s = unicodedata.normalize("NFD", str(text).upper())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def clean_text(value):
    if pd.isna(value):
        return pd.NA
    s = re.sub(r"\s+", " ", str(value)).strip()
    return s if s else pd.NA


def normalize_category(value):
    """Forma única de un texto: 'Tecnología ', 'TECNOLOGIA' y 'tecnologia' -> 'TECNOLOGIA'.

    Mayúsculas, sin tildes ni diéresis (la Ñ se conserva), espacios simples y
    sin signos sueltos al inicio o al final. Así Power BI no parte una misma
    carrera o categoría en dos valores distintos.
    """
    s = clean_text(value)
    if pd.isna(s):
        return pd.NA
    s = unicodedata.normalize("NFD", s.upper())
    s = re.sub(r"(?<!N)[\u0300-\u036f]|(?<=N)[\u0300-\u0302\u0304-\u036f]", "", s)
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\s+", " ", s).strip(" -,;:_")
    return pd.NA if s in NULL_TOKENS else s


def apply_aliases(series, column):
    """Unifica nombres distintos de una misma cosa según CATEGORY_ALIASES (config)."""
    aliases = {normalize_category(k): normalize_category(v) for k, v in CATEGORY_ALIASES.get(column, {}).items()}
    return series.replace(aliases) if aliases else series


DEGREE_PREFIX = re.compile(r"^(TECNOLOGIA|TECNICO|TECNICA|TECNOLOGO)( SUPERIOR)?( UNIVERSITARIA)?( EN| DE)? ")


def similar_careers(careers):
    """Grupos de carreras que parecen la misma con distinto nombre ('ENFERMERIA' y 'TECNICO SUPERIOR EN ENFERMERIA')."""
    groups = {}
    for c in careers:
        groups.setdefault(DEGREE_PREFIX.sub("", c), []).append(c)
    return [sorted(g) for g in groups.values() if len(g) > 1]


def parse_period(text):
    """'PERIODO NOVIEMBRE 2026 - MARZO 2027 MACHALA' -> periodo, fecha de inicio y sede."""
    if not isinstance(text, str):
        return None
    m = PERIOD_RE.search(text.upper())
    if not m:
        return None
    bounds = []
    for part in m.group(0).split("-"):
        month, year = part.split()
        if norm_key(month)[:3] not in MONTHS:
            return None
        bounds.append((MONTHS[norm_key(month)[:3]], int(year)))
    (m1, y1), (m2, y2) = bounds
    return {
        # Nombre canónico: "SETIEMBRE" y "SEPTIEMBRE" dan el mismo periodo.
        "periodo": f"{MONTH_NAMES[m1 - 1]} {y1} - {MONTH_NAMES[m2 - 1]} {y2}",
        "periodo_inicio": pd.Timestamp(date(y1, m1, 1)),
        "sede": normalize_category(text[m.end():]),
    }


def normalize_id(value):
    """Cédula como texto de 10 dígitos, aunque Excel la haya guardado como número."""
    if pd.isna(value):
        return pd.NA
    s = str(value).strip()
    if re.fullmatch(r"\d+(\.0+)?", s):
        s = s.split(".")[0].zfill(10)
    return s or pd.NA


def pseudonymize(value):
    """Hash estable: la misma cédula da el mismo id en todos los reportes, sin revelarla."""
    if pd.isna(value):
        return pd.NA
    return hashlib.sha256(f"{SALT}:{value}".encode()).hexdigest()[:16]


def to_flag(value):
    if pd.isna(value):
        return pd.NA
    s = norm_key(value)
    if s in FLAG_TRUE:
        return "SI"
    if s in FLAG_FALSE:
        return "NO"
    return pd.NA


def categorize_withdrawal(text):
    if pd.isna(text):
        return "SIN DATO"
    t = norm_key(text)
    for category, keywords in WITHDRAWAL_CATEGORIES:
        if any(k in t for k in keywords):
            return category
    return "OTRO"


def _issue(issues, level, source, rule, detail):
    issues.append({"nivel": level, "archivo": source, "regla": rule, "detalle": detail})


def _to_number(series):
    """Acepta números de Excel y textos como '8,5' o ' 15 '."""
    as_text = series.map(lambda v: v.strip().replace(",", ".") if isinstance(v, str) else v)
    return pd.to_numeric(as_text, errors="coerce")


def _cast(series, role):
    series = series.map(lambda v: pd.NA if isinstance(v, str) and normalize_category(v) is pd.NA else v)
    if role == "date":
        # Fechas reales de Excel o texto día/mes/año (formato de Ecuador).
        return pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")
    if role == "int":
        return _to_number(series).round().astype("Int64")
    if role == "float":
        return _to_number(series).astype("Float64")
    if role == "flag":
        return series.map(to_flag).astype("string")
    if role == "id":
        return series.map(normalize_id).astype("string")
    return series.map(normalize_category).astype("string")


def _report_invalid(original, cast, name, source, issues):
    """Un valor que no se pudo convertir queda vacío: se avisa en lugar de perderlo en silencio."""
    lost = original.map(lambda v: not (pd.isna(v) or (isinstance(v, str) and normalize_category(v) is pd.NA))) & cast.isna()
    if lost.any():
        examples = ", ".join(repr(v) for v in original[lost].astype(str).unique()[:3])
        _issue(issues, "AVISO", source, "valor_invalido", f"{name}: {lost.sum()} valores no válidos quedaron vacíos (ej. {examples})")


def transform(report_type, df, title, source_name, loaded_at):
    """Devuelve (DataFrame limpio o None si el archivo no cumple el contrato, incidencias)."""
    schema = SCHEMAS[report_type]
    issues = []
    by_key = {norm_key(c): c for c in df.columns}

    missing = [k for k in schema["required"] if k not in by_key]
    if missing:
        _issue(issues, "ERROR", source_name, "columnas_requeridas", f"Faltan: {', '.join(missing)}")
        return None, issues
    if df.empty:
        _issue(issues, "ERROR", source_name, "sin_filas", "El archivo no tiene registros")
        return None, issues

    known = set(schema["columns"])
    for key, original in by_key.items():
        if key.startswith("_VACIA_"):
            if df[original].notna().any():
                _issue(issues, "AVISO", source_name, "columna_sin_nombre", f"Columna sin encabezado con datos ({original})")
            continue
        if key in known or re.fullmatch(r".+_\d+", key):  # duplicados de celdas fusionadas
            continue
        _issue(issues, "AVISO", source_name, "columna_no_reconocida", f"'{original}' no está en el contrato; se descarta")

    out = pd.DataFrame(index=df.index)
    for key, (name, role) in schema["columns"].items():
        if key not in by_key:
            _issue(issues, "AVISO", source_name, "columna_opcional_ausente", f"'{key}' no vino en el archivo")
            continue
        col = df[by_key[key]]
        if role == "pii":
            continue
        out[name] = _cast(col, role)
        if role in ("date", "int", "float", "flag"):
            _report_invalid(col, out[name], name, source_name, issues)
        if role == "string":
            out[name] = apply_aliases(out[name], name)

    if report_type == "retiros":
        out["motivo_categoria"] = df[by_key["MOTIVO"]].map(categorize_withdrawal).astype("string")

    if report_type == "matriculas" and "fecha_inscripcion" in out:
        # Power BI muestra los meses de su jerarquía automática en el idioma de
        # la cuenta (inglés), no en el de los datos. Se genera aquí en español,
        # con su columna de orden, para no depender de esa configuración.
        inicio_mes = out["fecha_inscripcion"].dt.to_period("M").dt.to_timestamp()
        out["mes_inscripcion_inicio"] = inicio_mes
        out["mes_inscripcion"] = inicio_mes.map(
            lambda d: f"{MONTH_NAMES[d.month - 1]} {d.year}" if pd.notna(d) else pd.NA
        ).astype("string")

    for id_col in [n for n, r in schema["columns"].values() if r == "id"]:
        if id_col in out:
            out.insert(0, "id_estudiante", out.pop(id_col).map(pseudonymize).astype("string"))

    # Periodo: por fila en matrículas, desde el título del documento en el resto.
    if "periodo_texto" in out:
        parsed = out.pop("periodo_texto").map(parse_period)
    else:
        parsed = pd.Series([parse_period(title)] * len(out), index=out.index)
    if parsed.isna().any():
        _issue(issues, "ERROR", source_name, "periodo", "No se pudo identificar el periodo académico")
        return None, issues
    period_df = pd.DataFrame(parsed.tolist(), index=out.index)
    out["periodo"] = period_df["periodo"].astype("string")
    out["periodo_inicio"] = pd.to_datetime(period_df["periodo_inicio"])
    if "sede" not in out:
        out["sede"] = apply_aliases(period_df["sede"].astype("string"), "sede")

    _quality_rules(report_type, out, source_name, issues)

    out["archivo_origen"] = source_name
    out["fecha_carga"] = loaded_at
    lead = ["id_estudiante", "periodo", "periodo_inicio", "sede", "carrera"]
    ordered = [c for c in lead if c in out] + [c for c in out if c not in lead]
    return out[ordered].reset_index(drop=True), issues


def _quality_rules(report_type, out, source, issues):
    if "anio_graduacion_colegio" in out:
        zeros = (out["anio_graduacion_colegio"] == 0).sum()
        if zeros:
            out.loc[out["anio_graduacion_colegio"] == 0, "anio_graduacion_colegio"] = pd.NA
            _issue(issues, "AVISO", source, "valor_centinela", f"anio_graduacion_colegio = 0 en {zeros} filas; se trató como dato faltante")
    if "edad" in out:
        bad = (~out["edad"].between(15, 80) & out["edad"].notna()).sum()
        if bad:
            _issue(issues, "AVISO", source, "rango_edad", f"{bad} filas con edad fuera de 15-80")
    if "id_estudiante" in out:
        dup = out["id_estudiante"].dropna().duplicated().sum()
        if dup:
            _issue(issues, "AVISO", source, "duplicados", f"{dup} estudiantes repetidos en el mismo archivo")
        nulls = out["id_estudiante"].isna().sum()
        if nulls:
            _issue(issues, "AVISO", source, "id_faltante", f"{nulls} filas sin cédula")
    if report_type == "matriculas":
        inconsistent = ((out["matriculado"] == "NO") & out["fecha_matricula"].notna()).sum()
        if inconsistent:
            _issue(issues, "AVISO", source, "consistencia", f"{inconsistent} no matriculados con fecha de matrícula")
