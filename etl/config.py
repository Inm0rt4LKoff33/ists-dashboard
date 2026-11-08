"""Rutas del proyecto y contrato de datos de cada tipo de reporte.

El contrato dice, para cada columna del archivo original: con qué nombre
estándar queda (snake_case, sin tildes), qué tipo debe tener y qué rol cumple.
Cualquier archivo nuevo se valida contra esto antes de entrar al dataset.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"              # capa cruda: archivos tal como llegan, nunca se modifican
PROCESSED = DATA / "processed"  # capa limpia: un parquet por archivo de origen
CURATED = DATA / "curated"      # capa de consumo: lo que se sube a Power BI

CURATED_XLSX = CURATED / "observatorio_ists.xlsx"
QUALITY_REPORT = CURATED / "calidad_datos.csv"
MANIFEST = CURATED / "manifest.json"

# Sal para seudonimizar cédulas. En producción debe venir de una variable de
# entorno y no guardarse en el repositorio; si cambia, cambian todos los IDs.
SALT = os.environ.get("ISTS_SALT", "cambiar-esta-sal-en-produccion")

# Nombres distintos que significan lo mismo, por columna. Se aplican después
# de normalizar (mayúsculas, sin tildes), así que basta una entrada por
# variante. Cuando el pipeline avise "carrera_similar" en calidad_datos.csv,
# confirma con la institución y agrega aquí la equivalencia. Ejemplo:
#   "carrera": {"ENFERMERIA": "TECNICO SUPERIOR EN ENFERMERIA"},
CATEGORY_ALIASES = {
    "carrera": {},
    "sede_retiro": {"SEDE MACHALA": "MACHALA"},
}

# Roles de columna:
#   id     -> identificador personal; se reemplaza por un hash (id_estudiante)
#   pii    -> dato personal que no necesita el informe; se elimina
#   string / int / float / date / flag -> dato analítico con ese tipo
#   ("string" = texto normalizado: MAYÚSCULAS sin tildes; "flag" = SI/NO)
SCHEMAS = {
    "matriculas": {
        "required": ["FECHA INSCRIPCION", "CARRERA", "PERIODO", "MATRICULADO"],
        "columns": {
            "FECHA INSCRIPCION": ("fecha_inscripcion", "date"),
            "TIPO DE DOCUMENTO": ("tipo_documento", "string"),
            "NUMERO DE DOCUMENTO": ("numero_documento", "id"),
            "NOMBRES Y APELLIDOS": ("nombres_apellidos", "pii"),
            "ESTADO CIVIL": ("estado_civil", "string"),
            "NACIONALIDAD": ("nacionalidad", "string"),
            "SEXO": ("sexo", "string"),
            "CORREO": ("correo", "pii"),
            "TELEFONO CELULAR": ("telefono_celular", "pii"),
            "TELEFONO FIJO": ("telefono_fijo", "pii"),
            "DIRECCION": ("direccion", "pii"),
            "PROVINCIA, CANTON, PARROQUIA": ("ubicacion", "string"),
            "NACIMIENTO": ("fecha_nacimiento", "pii"),  # la edad ya basta para el análisis
            "EDAD": ("edad", "int"),
            "CARRERA": ("carrera", "string"),
            "MODALIDAD": ("modalidad", "string"),
            "SECCION": ("seccion", "string"),
            "ANO DE GRADUACION DE COLEGIO": ("anio_graduacion_colegio", "int"),
            "NOMBRE DE COLEGIO": ("colegio", "string"),
            "COMO NOS CONOCIO": ("canal_captacion", "string"),
            "RAZONES POR QUE INSCRIBIRSE": ("razon_inscripcion", "string"),
            "TRABAJA - DONDE?": ("trabaja", "string"),
            "CONTACTOS": ("contactos", "pii"),
            "CENTRO DE INFORMACION": ("centro_informacion", "string"),
            "PERSONA REGISTRO INTERESADO": ("persona_registro", "pii"),
            "PERSONA CREO INSCRIPCION": ("persona_inscripcion", "pii"),
            "PERIODO": ("periodo_texto", "string"),
            "MATRICULADO": ("matriculado", "flag"),
            "FECHA MATRICULA": ("fecha_matricula", "date"),
            "FECHA PAGO MAT.": ("fecha_pago_matricula", "date"),
            "ULTIMA MATRICULA": ("nivel_matricula", "string"),
            "OPCION DE PAGO": ("opcion_pago", "string"),
            "RETIRADO": ("retirado", "flag"),
            "TIPO RETIRO": ("tipo_retiro", "string"),
        },
    },
    "aptitud": {
        "required": ["N°", "PROM", "APTO GENERAL"],
        "columns": {
            "N°": ("numero_lista", "int"),
            "CEDULA": ("cedula", "id"),
            "APELLIDOS": ("apellidos", "pii"),
            "NOMBRES": ("nombres", "pii"),
            "A1.1": ("ingles_a1_1", "flag"),
            "A1.2": ("ingles_a1_2", "flag"),
            "A2.1": ("ingles_a2_1", "flag"),
            "A2.2": ("ingles_a2_2", "flag"),
            "NIVEL I": ("ingles_nivel_i", "flag"),
            "NIVEL II": ("ingles_nivel_ii", "flag"),
            "PROM": ("promedio", "float"),
            "COND_N": ("condicion_notas", "string"),
            "S1": ("seminario_1", "flag"),
            "S2": ("seminario_2", "flag"),
            "S3": ("seminario_3", "flag"),
            "H_PP": ("horas_practicas", "float"),
            "N_PP": ("nota_practicas", "float"),
            "H_VIN": ("horas_vinculacion", "float"),
            "N_VIN": ("nota_vinculacion", "float"),
            "DEUDAS": ("tiene_deudas", "flag"),
            "APTO GENERAL": ("apto_general", "flag"),
            "TIPO DE PROYEC. TITULACION": ("tipo_proyecto_titulacion", "string"),
            "ESTADO DEL PROYECTO": ("estado_proyecto", "string"),
            "TUTOR PROYECTO": ("tutor_proyecto", "string"),
            "CARRERA": ("carrera", "string"),  # reconstruida desde las filas-banner
        },
    },
    "retiros": {
        "required": ["CEDULA", "CARRERA", "FECHA", "MOTIVO"],
        "columns": {
            "RETIRADO": ("nombre_retirado", "pii"),
            "CEDULA": ("cedula", "id"),
            "NIVEL": ("nivel", "string"),
            "SEDE": ("sede_retiro", "string"),
            "SECCION": ("seccion", "string"),
            "CARRERA": ("carrera", "string"),
            "FECHA": ("fecha_retiro", "date"),
            # Texto libre que puede contener datos de salud: se categoriza y se
            # descarta el detalle (ver transform.categorize_withdrawal).
            "MOTIVO": ("motivo_detalle", "pii"),
        },
    },
}
