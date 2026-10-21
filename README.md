# Observatorio de Datos Académicos — ISTS (versión de prueba)

Pipeline que toma los reportes Excel del instituto (matrículas, retiros,
aptitud/titulación), los limpia, protege los datos personales y los consolida
en un único archivo listo para construir el dashboard en **Power BI Service**
(licencia gratuita), conectado al archivo en OneDrive.

```
 data/raw/            data/processed/          data/curated/                 Power BI
 (tal como llegan) -> (limpio, 1 parquet   ->  (modelo para el informe)  ->  (dashboard)
                       por archivo)            observatorio_ists.xlsx
        └────────────── python -m etl.run ──────────────┘     OneDrive (reemplazar)
```

## Uso en cada periodo

1. Copia el Excel nuevo en la carpeta de su tipo, **sin modificarlo**:
   `data/raw/matriculas/`, `data/raw/retiros/` o `data/raw/aptitud/`.
   Usa un nombre que indique el periodo, por ejemplo `matriculas_2027-1.xlsx`.
2. Ejecuta el pipeline:

   ```bash
   source .venv/bin/activate
   python -m etl.run
   ```

3. Revisa `data/curated/calidad_datos.csv`. Si hay filas `ERROR`, ese archivo
   no entró al dataset; corrige y vuelve al paso 2.
4. En onedrive.com, sube `data/curated/observatorio_ists.xlsx` a la carpeta
   del observatorio y elige **Reemplazar**. Power BI toma los datos nuevos
   desde ahí. El paso a paso está en [docs/power_bi.md](docs/power_bi.md).

Reglas que aplica el pipeline sin que tengas que hacer nada:

- **Volver a correrlo no duplica datos**: la capa `curated/` se reconstruye
  entera cada vez.
- **Archivo repetido** (mismo contenido, otro nombre): se ignora y se avisa.
- **Versión corregida de un periodo ya cargado**: gana el archivo más
  reciente y se avisa. Borra el viejo de `raw/` para no confundirte.
- **Archivo borrado de `raw/`**: desaparece también del dataset.
- **Textos normalizados**: todo texto sale en MAYÚSCULAS, sin tildes (la Ñ
  se conserva) y sin espacios de más. "Tecnología ", "TECNOLOGIA" y
  "tecnologia" quedan como el mismo valor, y valores como `N/A` o `-` quedan
  vacíos. Los nombres de periodo también se unifican ("SETIEMBRE" y "Sep"
  → "SEPTIEMBRE").
- **Números y fechas**: acepta `8,5` como 8.5 y fechas escritas como
  `15/03/2026`. Un valor que no se puede convertir queda vacío y se avisa
  (`valor_invalido`).
- **Carreras con nombres parecidos** ("ENFERMERIA" y "TECNICO SUPERIOR EN
  ENFERMERIA"): se avisa (`carrera_similar`). Si son la misma, agrega la
  equivalencia en `CATEGORY_ALIASES` de `etl/config.py`.
- **Archivo que no cumple el contrato** (le faltan columnas obligatorias, no
  tiene periodo, etc.): se rechaza y queda registrado en `calidad_datos.csv`.
  Los demás archivos se procesan igual.

## Qué sale en `observatorio_ists.xlsx`

| Tabla | Contenido |
|---|---|
| `fact_matriculas` | Una fila por inscripción |
| `fact_retiros` | Una fila por retiro, con el motivo categorizado (SALUD, ECONÓMICO, …) |
| `fact_aptitud` | Una fila por estudiante en proceso de titulación |
| `dim_periodo` | Periodos académicos presentes, con su fecha de inicio para ordenar |
| `dim_carrera` | Carreras presentes en cualquiera de los tres reportes, con el inicio del primer periodo en que aparecen |

No incluye nombres, cédulas, correos, teléfonos, direcciones ni el texto
libre del motivo de retiro. Cada estudiante se identifica con
`id_estudiante`, un código derivado de su cédula: es el mismo en los tres
reportes, pero no permite recuperar la cédula.

## Estructura

```
etl/
  config.py      rutas y contrato de datos (columnas, tipos, datos personales)
  extract.py     un lector por formato de reporte
  transform.py   limpieza, seudonimización, periodo y reglas de calidad
  load.py        escribe processed/ y reconstruye curated/
  run.py         orquesta todo y deja manifest + reporte de calidad
tests/           pruebas automáticas (python -m pytest)
notebooks/       análisis exploratorio (EDA) de cada fuente
docs/            guía de Power BI y buenas prácticas del proyecto
data/            (fuera de git) raw/ processed/ curated/ clean/ .originals-backup/
```

`data/clean/` lo generan los notebooks de EDA y no forma parte del pipeline.
`data/.originals-backup/` guarda los archivos tal como los entregó la
institución, antes de rellenar los campos anonimizados con datos ficticios.

## Agregar un tipo de reporte nuevo

1. Define su contrato en `etl/config.py` (`SCHEMAS`).
2. Escribe su lector en `etl/extract.py` y regístralo en `READERS`.
3. Crea `data/raw/<tipo>/` y agrega una prueba en `tests/`.

## Desarrollo

```bash
source .venv/bin/activate
pip install -r requirements.txt   # pipeline
python -m pytest                  # pruebas
```

Antes de pasar a producción, define la variable de entorno `ISTS_SALT` con un
valor secreto (ver [docs/buenas_practicas.md](docs/buenas_practicas.md)).
