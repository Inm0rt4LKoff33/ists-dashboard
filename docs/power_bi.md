# Dashboard en Power BI Service (licencia gratuita)

Guía para construir el dashboard en app.powerbi.com con
`data/curated/observatorio_ists.xlsx`. Todo se hace en el navegador.

> Los pasos se basan en cómo funciona Power BI Service hoy, pero no pude
> probarlos en tu cuenta. Algunas opciones cambian de nombre o de lugar según
> el idioma y la versión. Los puntos que conviene verificar en la primera
> prueba están marcados con **(verificar)**.

## 1. Primera carga (desde OneDrive)

El archivo vive en tu **OneDrive** y Power BI se conecta a él. Así, cuando
reemplazas el archivo en OneDrive, Power BI toma los datos nuevos solo, sin
volver a armar nada.

**1a. Subir el archivo a OneDrive** (una sola vez)

1. Entra a onedrive.com con tu cuenta institucional.
2. Crea una carpeta, por ejemplo `Observatorio ISTS`.
3. **Cargar → Archivos** → `data/curated/observatorio_ists.xlsx`.

**1b. Conectar Power BI al archivo**

1. En app.powerbi.com → menú izquierdo → **Mi área de trabajo**.
2. **+ Nuevo elemento** (o **Nuevo**) → **Modelo semántico** → **Excel**.
3. Elige **OneDrive para el trabajo o la escuela** (no "Examinar este
   dispositivo") → la carpeta → `observatorio_ists.xlsx`.
4. Aparece un elemento de tipo **Modelo semántico** con una tabla por cada
   Tabla de Excel: `fact_matriculas`, `fact_retiros`, `fact_aptitud`,
   `dim_periodo` y `dim_carrera`.
5. Para hacer los gráficos: en ese modelo semántico, **⋯ (Más opciones) →
   Crear informe**. Se abre el lienzo con el panel de **Datos** a la derecha.

Si en el paso 3 eliges "Examinar este dispositivo", Power BI guarda una
copia y pierde la conexión: cada periodo tendrías que volver a subirlo.

Power BI Desktop no sirve en este equipo: solo existe para Windows.

## 2. Modelo de datos: relaciones

El archivo viene preparado como **modelo estrella**: las tablas `fact_`
guardan los hechos y las `dim_` los catálogos que las conectan. Así, un solo
filtro de periodo o de carrera filtra los tres reportes a la vez.

Abre el modelo semántico → **Abrir modelo de datos** **(verificar)** y crea
estas relaciones, todas de uno a varios, desde la dimensión hacia el hecho:

| Desde | Hacia |
|---|---|
| `dim_periodo[periodo]` | `fact_matriculas[periodo]`, `fact_retiros[periodo]`, `fact_aptitud[periodo]` |
| `dim_carrera[carrera]` | `fact_matriculas[carrera]`, `fact_retiros[carrera]`, `fact_aptitud[carrera]` |

En `dim_periodo`, configura **Ordenar por columna** de `periodo` usando
`periodo_inicio`, para que los periodos salgan en orden cronológico y no
alfabético.

Si tu licencia no te deja editar el modelo en la web, igual puedes armar
el informe con una tabla por visual. Lo único que pierdes son los filtros
cruzados entre reportes.

## 3. Medidas

Las medidas son cálculos reutilizables. Defínelas una vez en el modelo, en
lugar de calcular en cada gráfico. Créalas con **Nueva medida** **(verificar)**:

```dax
Inscripciones = COUNTROWS ( fact_matriculas )

Matriculados =
    CALCULATE ( COUNTROWS ( fact_matriculas ), fact_matriculas[matriculado] = "SI" )

Tasa de matriculación = DIVIDE ( [Matriculados], [Inscripciones] )

Retiros = COUNTROWS ( fact_retiros )

En titulación = COUNTROWS ( fact_aptitud )

Aptos =
    CALCULATE ( COUNTROWS ( fact_aptitud ), fact_aptitud[apto_general] = "SI" )

Tasa de aptitud = DIVIDE ( [Aptos], [En titulación] )

Promedio de notas = AVERAGE ( fact_aptitud[promedio] )
```

Si no puedes crear medidas, arrastra las columnas al visual y elige el tipo
de resumen (Recuento, Promedio). Funciona igual, pero cada visual lleva su
propio cálculo.

## 4. Informe sugerido

Cuatro páginas: una ejecutiva (Resumen) y una por reporte. Antes de empezar
conviene tener las relaciones (sección 2) y las medidas (sección 3).

### 4.1 Cómo funciona el editor

Abre el modelo semántico → **⋯ → Crear informe** (o, si ya lo creaste, abre
el informe → **Editar**). A la derecha hay tres paneles:

- **Datos:** tus tablas. Al desplegar una, ves sus columnas y medidas.
- **Visualizaciones:** los tipos de gráfico arriba. Debajo, los "pozos"
  donde se colocan los campos (**Eje X**, **Eje Y**, **Leyenda**,
  **Valores**, **Campo**…). El ícono de pincel (**Dar formato al objeto
  visual**) cambia títulos, colores y etiquetas.
- **Filtros:** filtros del visual, de la página o de todo el informe.

Para crear cualquier gráfico:

1. Haz clic en un espacio vacío del lienzo.
2. Elige el tipo de gráfico en **Visualizaciones**.
3. Arrastra los campos desde **Datos** a cada pozo.
4. Ajusta el tamaño con las esquinas y cambia el título con el pincel →
   **General → Título**.

Las páginas se agregan con el **+** de la barra inferior. Para cambiarle el
nombre a una página, haz doble clic en su pestaña.

**Regla de oro del modelo estrella:** en segmentadores y ejes de carrera o
periodo, usa siempre las columnas de `dim_carrera` y `dim_periodo`, nunca
`carrera` o `periodo` de las tablas `fact_`. Solo así un filtro afecta a los
tres reportes a la vez.

### 4.2 Página "Resumen"

| Visual | Tipo | Campos |
|---|---|---|
| Inscripciones | Tarjeta | Campo: medida `Inscripciones` |
| Tasa de matriculación | Tarjeta | Campo: `Tasa de matriculación` |
| Retiros | Tarjeta | Campo: `Retiros` |
| Tasa de aptitud | Tarjeta | Campo: `Tasa de aptitud` |
| Filtro de periodo | Segmentación | Campo: `dim_periodo[periodo]` |
| Filtro de carrera | Segmentación | Campo: `dim_carrera[carrera]` |
| Inscripciones por carrera | Gráfico de barras agrupadas | Eje Y: `dim_carrera[carrera]` · Eje X: `Inscripciones` |

- Pon las 4 tarjetas en fila arriba, los segmentadores a la izquierda y las
  barras abajo.
- Para que las tasas se vean como porcentaje, selecciona la medida en
  **Datos** y, en la cinta **Herramientas de medición**, cambia el
  **Formato** a **Porcentaje** **(verificar)**.
- Para que los segmentadores filtren todas las páginas: **Ver → Sincronizar
  segmentaciones** **(verificar)**. Si no aparece, arrastra
  `dim_periodo[periodo]` a **Filtros → Filtros en todas las páginas**.

### 4.3 Página "Matrículas"

| Visual | Tipo | Campos |
|---|---|---|
| Inscritos vs. matriculados por carrera | Barras agrupadas | Eje Y: `dim_carrera[carrera]` · Eje X: `Inscripciones` y `Matriculados` |
| Canal de captación | Barras agrupadas | Eje Y: `fact_matriculas[canal_captacion]` · Eje X: `Inscripciones` |
| Inscripciones en el tiempo | Gráfico de líneas | Eje X: `fact_matriculas[fecha_inscripcion]` · Eje Y: `Inscripciones` |
| Sexo | Gráfico de anillos | Leyenda: `fact_matriculas[sexo]` · Valores: `Inscripciones` |
| Sección | Gráfico de columnas agrupadas | Eje X: `fact_matriculas[seccion]` · Eje Y: `Inscripciones` · Leyenda: `fact_matriculas[matriculado]` |
| Plan de pago | Barras agrupadas | Eje Y: `fact_matriculas[opcion_pago]` · Eje X: `Matriculados` |

- **Línea de tiempo:** Power BI convierte la fecha en una jerarquía (Año →
  Trimestre → Mes → Día). En el pozo **Eje X**, quita **Trimestre** y
  **Día** con la X de cada uno para ver las inscripciones por mes.
- **Ordenar las barras:** en cada gráfico de barras, **⋯ del visual →
  Ordenar eje → `Inscripciones`, descendente**.

### 4.4 Página "Retiros"

| Visual | Tipo | Campos |
|---|---|---|
| Total de retiros | Tarjeta | Campo: `Retiros` |
| Motivo | Barras agrupadas | Eje Y: `fact_retiros[motivo_categoria]` · Eje X: `Retiros` |
| Retiros por carrera | Barras agrupadas | Eje Y: `dim_carrera[carrera]` · Eje X: `Retiros` |
| Nivel en que se retiran | Columnas agrupadas | Eje X: `fact_retiros[nivel]` · Eje Y: `Retiros` |

Con los datos de prueba hay un solo retiro, así que los gráficos se verán
casi vacíos. Esa es justamente la prueba de que el informe muestra lo que
hay, sin inventar datos.

### 4.5 Página "Titulación"

| Visual | Tipo | Campos |
|---|---|---|
| En titulación / Aptos / Tasa de aptitud | 3 tarjetas | `En titulación`, `Aptos`, `Tasa de aptitud` |
| Promedio por carrera | Barras agrupadas | Eje Y: `dim_carrera[carrera]` · Eje X: `Promedio de notas` |
| Estado del proyecto | Gráfico de anillos | Leyenda: `fact_aptitud[estado_proyecto]` · Valores: `En titulación` |
| Tipo de titulación | Barras agrupadas | Eje Y: `fact_aptitud[tipo_proyecto_titulacion]` · Eje X: `En titulación` |
| Requisitos pendientes | Matriz | Filas: `dim_carrera[carrera]` · Columnas: `fact_aptitud[apto_general]` · Valores: `En titulación` |
| Vinculación | Tabla | `dim_carrera[carrera]`, promedio de `horas_vinculacion`, promedio de `nota_vinculacion` |

En la tabla de Vinculación, al arrastrar `horas_vinculacion` Power BI la
suma por defecto. Cámbialo con la flecha del campo en el pozo →
**Promedio**.

### 4.6 Si no puedes crear medidas

Usa las columnas directamente y cambia el tipo de resumen con la flecha del
campo en el pozo:

| En lugar de… | Usa… |
|---|---|
| `Inscripciones` | `fact_matriculas[id_estudiante]` → **Recuento** |
| `Matriculados` | Lo mismo, con un filtro del visual: `matriculado` es `SI` |
| `Retiros` | `fact_retiros[id_estudiante]` → **Recuento** |
| `En titulación` | `fact_aptitud[id_estudiante]` → **Recuento** |
| `Promedio de notas` | `fact_aptitud[promedio]` → **Promedio** |
| Tasas | No hay equivalente directo. Usa un gráfico de **barras 100 % apiladas** con `matriculado` (o `apto_general`) en la leyenda: muestra la proporción de SI y NO |

### 4.7 Guardar y presentar

- **Archivo → Guardar** con un nombre fijo, por ejemplo "Observatorio
  ISTS". No cambies el nombre después: al actualizar los datos (sección 5),
  el informe se mantiene.
- Para presentarlo: **Exportar → PDF** o **PowerPoint**. Con licencia
  gratuita no se puede compartir el enlace.
- Diseño: deja los segmentadores siempre en el mismo lugar en todas las
  páginas, usa a lo sumo 6 visuales por página y pon títulos que digan qué
  se mide ("Inscripciones por carrera", no "Gráfico 1").

## 5. Actualizar con un periodo nuevo

1. Corre el pipeline (ver README) para generar el nuevo
   `observatorio_ists.xlsx`.
2. En onedrive.com, abre la carpeta y sube el archivo **con el mismo nombre**.
   OneDrive pregunta qué hacer: elige **Reemplazar**. No lo borres antes de
   subir el nuevo: OneDrive guarda una versión nueva del mismo archivo, y la
   conexión de Power BI se mantiene.
3. Power BI revisa el archivo en OneDrive aproximadamente cada hora y
   actualiza el modelo y el informe **(verificar)**. Para no esperar, en
   **Mi área de trabajo** → modelo semántico → **Actualizar ahora**
   **(verificar)**.
4. El informe sigue funcionando porque el pipeline garantiza que las tablas y
   columnas se llamen siempre igual. Si algún visual se rompe, revisa si
   cambiaste algo en `etl/config.py`.

Comprueba esto en la primera prueba con un periodo ficticio: duplica un
archivo de `data/raw/`, cámbiale el periodo en el título, corre el pipeline,
reemplaza el archivo en OneDrive y mira si el periodo nuevo aparece en el
informe.

Si OneDrive guarda versiones anteriores, también te sirve de respaldo: en
onedrive.com → archivo → **Historial de versiones** puedes volver a la carga
de un periodo anterior.

## Limitaciones de la licencia gratuita

- La subida a OneDrive sigue siendo manual (desde Linux no hay cliente
  oficial de OneDrive que sincronice una carpeta).
- El informe no se puede compartir para que otros lo abran. Para mostrarlo,
  usa **Exportar → PDF** o **PowerPoint**. Compartir requiere licencia
  **Pro**.
- El archivo en OneDrive no contiene datos personales (los quita el
  pipeline), pero sigue siendo información institucional: no lo compartas
  desde OneDrive con personas fuera de la institución.
