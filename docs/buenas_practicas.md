# Pautas y buenas prácticas del proyecto

Este documento explica **por qué** el proyecto está armado como está. Cada
práctica indica dónde se aplica en el código, para que puedas verla
funcionando y defenderla en tus informes de pasantía.

## 1. Fases de un proyecto de datos

| Fase | Pregunta que responde | En este proyecto |
|---|---|---|
| 1. Necesidad | ¿Qué decisión se quiere tomar con los datos? | Reuniones con el tutor: qué indicadores necesita la institución |
| 2. Inventario | ¿Qué datos existen, quién los genera y cada cuánto? | Los 3 reportes Excel, uno por periodo |
| 3. Exploración (EDA) | ¿Cómo son realmente los datos? ¿Qué problemas traen? | `notebooks/` |
| 4. Contrato | ¿Qué estructura debe cumplir cada fuente? | `etl/config.py` |
| 5. Pipeline (ETL) | ¿Cómo se pasa de crudo a confiable, siempre igual? | `etl/` |
| 6. Modelo | ¿Cómo se organizan las tablas para analizarlas? | Modelo estrella en `curated/` |
| 7. Visualización | ¿Qué ve el usuario final? | Power BI ([power_bi.md](power_bi.md)) |
| 8. Validación | ¿Los números son correctos? ¿Se entienden? | Pruebas + revisión con el tutor |
| 9. Operación | ¿Quién lo actualiza, cómo y cada cuánto? | README "Uso en cada periodo" |

El error más común es saltar de la fase 2 a la 7: se arma el dashboard
directo sobre el Excel crudo. Funciona la primera vez y se rompe en el
siguiente periodo.

## 2. Prácticas aplicadas

### Arquitectura por capas
`data/raw/` → `data/processed/` → `data/curated/`. También se la conoce
como arquitectura *medallion* (bronce, plata, oro).
**Por qué:** cada capa tiene una sola responsabilidad. Si la limpieza tiene
un error, se corrige y se regenera todo desde `raw/`, sin pedir de nuevo los
archivos a la institución.

### Datos crudos inmutables
Nada en `raw/` se edita, ni a mano ni desde el código.
**Por qué:** es la fuente de verdad. Si se corrige algo directamente en el
Excel, después no hay forma de saber qué decía el original ni de reproducir
el resultado.

### Contrato de datos
`etl/config.py` declara cada columna esperada, su nombre estándar, su tipo y
si es un dato personal. Un archivo al que le falta una columna obligatoria se
rechaza con un mensaje claro.
**Por qué:** el dashboard depende de que las columnas existan y se llamen
igual en todos los periodos. Es mejor detectar el cambio al cargar el
archivo que encontrarse un gráfico en blanco frente a las autoridades.

### Nombres estandarizados
Columnas en `snake_case`, sin tildes ni espacios (`fecha_inscripcion`, no
`FECHA INSCRIPCIÓN `). La comparación de encabezados ignora mayúsculas,
tildes y espacios dobles (`transform.norm_key`).
**Por qué:** los encabezados del Excel original tenían espacios invisibles
al final y tildes inconsistentes; eso rompe fórmulas y consultas sin que se
note.

### Valores normalizados y catálogo de equivalencias
Los textos se llevan a una forma única (`transform.normalize_category`):
mayúsculas, sin tildes, sin espacios de más, con los "vacíos disfrazados"
(`N/A`, `-`) convertidos en vacíos reales. Las variantes que la
normalización no puede resolver sola (dos nombres para la misma carrera) se
unifican con un catálogo explícito, `CATEGORY_ALIASES` en `etl/config.py`.
**Por qué:** Power BI compara textos tal cual. Si una carrera llega como
"Tecnología" en un archivo y "TECNOLOGIA" en otro, aparece dos veces en los
filtros, la relación con `dim_carrera` falla y los totales se parten. El
catálogo deja la decisión ("¿estas dos son la misma carrera?") escrita y
revisable, en lugar de enterrada en el código.

### Privacidad desde el diseño
- **Minimización:** al dataset de consumo solo llega lo que el análisis
  necesita. Nombres, correos, teléfonos, direcciones y fecha de nacimiento
  se descartan (rol `pii` en el contrato).
- **Seudonimización:** la cédula se reemplaza por un hash SHA-256 con una
  "sal" secreta (`transform.pseudonymize`). El mismo estudiante tiene el
  mismo `id_estudiante` en los tres reportes, lo que permite cruzarlos, pero
  no se puede recuperar la cédula sin conocer la sal.
- **Texto libre sensible:** el motivo de retiro puede contener datos de salud;
  se convierte a una categoría (`SALUD`, `ECONOMICO`, …) y el detalle se
  descarta.

**Por qué:** en Ecuador rige la Ley Orgánica de Protección de Datos
Personales (2021), y la ficha del reto pide priorizar la protección de datos.
Además, un dashboard sin datos personales se puede mostrar sin riesgo.

**Pendiente para producción:** la sal no debe quedar en el código. Defínela
como variable de entorno `ISTS_SALT` con un valor secreto, guárdala en un
lugar seguro, y no la cambies después (si cambia, todos los IDs cambian).

### Calidad de datos explícita
Las reglas de `transform._quality_rules` (rangos de edad, duplicados, valores
centinela como `0` en el año de graduación, consistencia entre "matriculado"
y su fecha) generan incidencias en `curated/calidad_datos.csv` en lugar de
corregir o descartar en silencio.
**Por qué:** un dato dudoso que se "arregla" sin avisar es peor que uno que
falla. El reporte de calidad también es un insumo para la institución: le
muestra qué mejorar en la captura de datos.

### Tolerancia a fallos por archivo
Un archivo dañado o que no cumple el contrato se rechaza, y los demás se
procesan igual (`run.py`).
**Por qué:** un error en el reporte de retiros no debería impedir actualizar
el de matrículas.

### Idempotencia
Correr el pipeline una o diez veces produce el mismo resultado: `curated/`
se reconstruye entera desde `processed/`, y los archivos duplicados o
reemplazados se detectan (`run.py`).
**Por qué:** en la operación real alguien va a correrlo dos veces "por si
acaso". Eso no puede duplicar matrículas en el informe.

### Linaje y trazabilidad
Cada fila lleva `archivo_origen` y `fecha_carga`. `curated/manifest.json`
registra qué archivos se procesaron, su estado y su huella SHA-256.
**Por qué:** cuando alguien pregunte "¿de dónde sale este número?", se puede
responder con exactitud.

### Formato columnar (Parquet)
Las capas `processed/` y `curated/` se guardan en Parquet. El Excel de
`curated/` existe solo porque Power BI gratuito necesita un archivo para subir.
**Por qué:** Parquet guarda los tipos de dato (una cédula no se convierte en
número), comprime mucho y lo leen todas las herramientas de Big Data (Spark,
DuckDB, Power BI, pandas).

### Modelo estrella
Tablas de hechos (`fact_*`: eventos que se cuentan) y de dimensiones
(`dim_*`: catálogos por los que se filtra).
**Por qué:** es el modelo para el que Power BI está optimizado. Permite que un
solo filtro de periodo o carrera afecte a todos los reportes, y las medidas
salen simples.

### Pruebas automáticas
`tests/test_pipeline.py` comprueba las funciones de limpieza, que las
muestras reales cumplan el contrato sin datos personales, y los escenarios de
operación (reprocesar, duplicado, versión corregida, archivo borrado) sobre
una copia temporal.
**Por qué:** cada vez que modifiques el pipeline, `python -m pytest` te
confirma en segundos que no rompiste algo que ya funcionaba.

### Control de versiones sin datos
El proyecto está en git, pero `data/` está excluido (`.gitignore`).
**Por qué:** el código se versiona y se comparte; los datos institucionales
nunca deben terminar en un repositorio.
**Ojo:** los notebooks guardan sus resultados (tablas con valores) dentro del
`.ipynb`. Antes de subirlos a un repositorio compartido, límpialos con
**Kernel → Restart & Clear Output**, o automatízalo con la herramienta
`nbstripout`.

## 3. ¿Esto es Big Data?

Hoy el volumen es pequeño: cientos de filas, no millones. Lo que sí aplica
de Big Data son las **prácticas**: capas, contratos, formatos columnares,
idempotencia, linaje y privacidad. Son las mismas que se usan con volúmenes
grandes, y por eso el proyecto puede crecer sin rediseñarse:

| Si el volumen o la frecuencia crecen | Se cambia | Se mantiene |
|---|---|---|
| Muchos periodos o sedes | pandas → DuckDB o Spark para transformar | contrato, capas, pruebas |
| Actualización frecuente | ejecución manual → programada (cron, Airflow) | `python -m etl.run` como unidad |
| Varios usuarios | carpeta local → almacenamiento en la nube (OneDrive, data lake) | estructura raw/processed/curated |
| Power BI Pro | informe personal → compartido con la institución | el mismo `observatorio_ists.xlsx` en OneDrive |

## 4. Próximos pasos de la versión de prueba

1. Subir `observatorio_ists.xlsx` a OneDrive, conectarlo desde Power BI y
   armar el informe ([power_bi.md](power_bi.md)), verificando los puntos
   marcados.
2. Probar el reemplazo con un periodo ficticio.
3. Validar los indicadores con el tutor: que las definiciones (por ejemplo,
   tasa de matriculación = matriculados / inscritos) coincidan con las
   oficiales.
4. Pedir a la institución archivos de periodos anteriores, para tener series
   de tiempo reales.
5. Definir `ISTS_SALT` y hacer el primer commit.
