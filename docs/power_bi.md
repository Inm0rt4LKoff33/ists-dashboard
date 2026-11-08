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

## 6. Agregar un reporte de un tipo que no existía

Hay dos situaciones muy distintas que parecen lo mismo ("un Excel nuevo"):

- **Un periodo más de un reporte que ya conoces** (otro archivo de
  matrículas, retiros o aptitud): es el caso de la sección 5. Se copia a
  `data/raw/<tipo>/`, se corre el pipeline y el archivo que subes a OneDrive
  **sigue siendo el mismo `observatorio_ists.xlsx`**, solo que con más filas.
  No tocas nada en Power BI.
- **Un reporte de un tipo nuevo** (por ejemplo, evaluación docente o uso del
  EVA, que no están en el contrato actual): esto sí requiere cambios, pero
  **tampoco es un archivo nuevo para Power BI**. Sigue siendo el mismo
  `observatorio_ists.xlsx`; lo que cambia es que ese archivo trae una hoja
  (tabla) más.

Pasos para el segundo caso:

1. En el proyecto, sigue "Agregar un tipo de reporte nuevo" del
   [README](../README.md): declara el contrato en `etl/config.py`, el lector
   en `etl/extract.py` y regístralo en `FACT_SHEETS` (`etl/load.py`).
2. Corre el pipeline. `observatorio_ists.xlsx` ahora trae una tabla
   `fact_<tipo>` nueva, además de las que ya tenía.
3. Sube el archivo a OneDrive **con el mismo nombre de siempre** (reemplazar,
   igual que en la sección 5). No crees un archivo ni un modelo semántico
   aparte: todo sigue viviendo en el mismo Excel.
4. Aquí está el punto importante: **"Actualizar ahora" no agrega tablas
   nuevas al modelo**, solo refresca los datos de las tablas que el modelo ya
   conoce. Para que Power BI vea la tabla nueva, entra al modelo semántico →
   **⋯ → Editar tablas** (o **Transformar datos** / **Obtener datos → Excel**
   sobre el mismo archivo) y selecciona también la tabla nueva
   **(verificar)**. El nombre exacto de esta opción varía según la versión.
5. Si la tabla nueva comparte `periodo` y `carrera` con las demás, créale sus
   relaciones hacia `dim_periodo` y `dim_carrera` (sección 2), y arma su
   página en el informe (sección 4) y sus medidas si las necesita (sección 3).

En resumen: **nunca reemplazas el archivo "por completo" en el sentido de
borrar y empezar un modelo nuevo.** Siempre es el mismo archivo y el mismo
modelo semántico; lo único que cambia entre un periodo normal y un reporte
nuevo es si, además de reemplazar el archivo, tienes que entrar al modelo a
decirle que ahora existe una tabla más.

## 7. Navegación e interactividad avanzada

Esta sección va sobre la experiencia del informe ya armado (sección 4): un
panel de navegación tipo "app", botones, filtros que solo afectan a una
página, una página de detalle al hacer clic en un dato, y tooltips propios.
Todo esto se hace con el editor web, sin Power BI Desktop.

### 7.1 Ocultar las pestañas nativas (opcional)

Por defecto, Power BI pone una pestaña por página abajo del lienzo. Si vas a
armar tu propio panel de navegación, conviene ocultar esas pestañas para que
no queden duplicadas con tus botones:

1. Clic derecho sobre la pestaña de la página → **Ocultar página**.
2. La página sigue existiendo y tú (como editor) la sigues viendo atenuada
   en la lista; quien solo consume el informe ya no la ve como pestaña, pero
   sí puede llegar a ella por un botón o un navegador de páginas.

Hazlo en todas las páginas **excepto** la primera (la que se abre al entrar).

### 7.2 Panel de navegación automático: el visual "Navegador de páginas"

Es la forma más rápida de tener un menú lateral o superior, y se actualiza
solo si agregas, quitas o reordenas páginas (no hay que mantenerlo a mano):

1. En **Visualizaciones**, busca **Navegador de páginas** y arrástralo al
   lienzo (por ejemplo, una franja angosta a la izquierda).
2. En el panel de formato: **Páginas** controla qué páginas incluye (puedes
   excluir alguna) **(verificar)**; **Diseño** cambia entre horizontal y
   vertical; **Relleno** y **Texto** dejan ponerle íconos o solo texto, y
   resaltar la página activa con otro color.
3. Copia este visual (Ctrl+C) y pégalo (Ctrl+V) en cada página, en la misma
   posición, para que el menú se vea igual en todo el informe. Power BI no
   tiene "páginas maestras" en la licencia gratuita: cada copia es
   independiente, así que si lo cambias de estilo, repite el cambio en cada
   página.

### 7.3 Panel manual con botones (más control que el navegador automático)

Úsalo si quieres agrupar botones con un título, un ícono de inicio, o
separar "páginas" de "acciones" (como un botón de reinicio, sección 7.4):

1. **Insertar → Botones** → elige un estilo en blanco o uno con ícono.
2. En el panel de formato del botón, pestaña **Acción**: actívala,
   **Tipo = Página**, **Destino =** la página de destino.
3. Repite un botón por página, alinéalos con **Formato → Organizar →
   Alinear** y **Distribuir**, y agrúpalos (selección múltiple → clic
   derecho → **Agrupar**) para moverlos juntos.
4. Igual que el navegador automático, se copia y pega en cada página. Para
   marcar "en qué página estoy", distingue en cada copia el botón de esa
   página con otro color de relleno (es manual: no se resalta solo).

### 7.4 Botón para restablecer filtros (marcadores / bookmarks)

Los marcadores (**Ver → Marcadores**) guardan el estado de filtros y
selección de una página, y un botón puede volver a ese estado con un clic.
Ejemplo útil: un botón "Restablecer filtros" en la página Resumen.

1. Entra a la página sin ningún filtro de segmentador aplicado.
2. **Ver → Marcadores → Agregar**. Dale un nombre, por ejemplo
   `Resumen - sin filtros`.
3. En las opciones del marcador (⋯), confirma que **Datos** esté marcado
   (captura los filtros/selecciones) — así el marcador "recuerda" el estado
   sin filtros.
4. Inserta un botón de texto "Restablecer filtros". **Acción → Tipo =
   Marcador → Marcador =** el que creaste.

El mismo mecanismo sirve para mostrar/ocultar un panel (por ejemplo, un
panel de ayuda): agrupa los objetos del panel, crea un marcador con el panel
visible y otro con el panel oculto (usando el **panel de Selección**, **Ver
→ Selección**, para cambiar el ícono del ojo), y un botón que alterne entre
ambos.

### 7.5 Filtros que solo afectan a una página

Ya viste el segmentador normal (sección 4), que por defecto solo filtra la
página donde está. Para decidir con más control qué segmentador aparece y
filtra en qué páginas, usa **Ver → Sincronizar segmentaciones**:

- Junto a cada segmentador aparecen dos columnas por página:
  **Sincronizar** (si esa página se filtra también) y **Visible** (si el
  segmentador se muestra ahí).
- Para un filtro global de verdad (como `dim_periodo[periodo]`): pon
  Sincronizar y Visible en las 4 páginas.
- Para un filtro que solo tiene sentido en una página (como
  `fact_aptitud[estado_proyecto]` en Titulación): dejas Sincronizar y
  Visible marcados solo en esa página, y lo quitas de las demás.

Si en lugar de un segmentador interactivo quieres un filtro fijo que el
usuario no pueda tocar (por ejemplo, excluir filas sin carrera en una
página puntual), arrastra el campo al panel **Filtros**, en el bloque
**Filtros de esta página** (no **de este objeto visual** ni **de todas las
páginas**).

### 7.6 Ir al detalle: página de "profundización" (drillthrough)

Permite hacer clic derecho sobre un dato (por ejemplo, una barra de
"Inscripciones por carrera") y saltar a una página de detalle ya filtrada
por esa carrera, sin que el usuario arme el filtro a mano.

1. Crea una página nueva, por ejemplo **"Detalle de carrera"**, y ocúltala
   (sección 7.1): a esta página solo se llega haciendo clic derecho.
2. En el panel **Filtros** de esa página, arrastra `dim_carrera[carrera]` al
   bloque **Agregar categorías de profundización**.
3. Power BI agrega un botón **Atrás** automático en la esquina. Arma ahí
   visuales de detalle que crucen los tres reportes para una sola carrera:
   por ejemplo, una tabla con sus inscripciones, su tasa de aptitud y sus
   retiros.
4. Pruébalo en la página Resumen: clic derecho sobre una barra de
   "Inscripciones por carrera" → **Detalles → Detalle de carrera**. La
   página nueva se abre ya filtrada a esa carrera.

### 7.7 Información al pasar el mouse: tooltip con tu propia página

En vez del tooltip estándar (una cajita con el valor), puedes mostrar una
mini página al pasar el mouse sobre un dato:

1. Crea una página pequeña, por ejemplo **"Tooltip carrera"**. En
   **Formato de la página → Tamaño**, elige **Personalizado** y usa algo
   como 320 × 240 px.
2. En **Formato de la página → Información de la página**, activa
   **Permitir usar como información sobre herramientas**.
3. Agrégale 1-2 visuales pequeños (una tarjeta con la tasa de aptitud de la
   carrera, por ejemplo) y ocúltala (sección 7.1).
4. En el visual donde quieres que aparezca (otra vez, "Inscripciones por
   carrera"): **Formato → Información sobre herramientas → Tipo = Página de
   informe → Página = Tooltip carrera**.

**(verificar)** estos tres (marcadores, profundización y tooltip de página)
son funciones estándar del editor, pero no pude confirmar que se vean
exactamente igual en una cuenta gratuita dentro de **Mi área de trabajo**;
si algún panel no aparece con ese nombre, búscalo en la pestaña de formato
de la página o del visual, el nombre cambia poco entre versiones.

### 7.8 Evitar que un clic filtre visuales que no debería

Por defecto, hacer clic en un dato de un visual resalta o filtra a los
demás visuales de la página. Si un gráfico no debería reaccionar a ese
clic, selecciona el visual que originó el clic → **Formato → Editar
interacciones**; sobre cada otro visual aparecen tres íconos para elegir
**Filtrar**, **Resaltar** o **Ninguna**.

### 7.9 Orden sugerido para armarlo

No hace falta todo a la vez. Un orden razonable, de más a menos impacto por
el tiempo que toma:

1. Navegador de páginas (7.2) en las 4 páginas — 15-20 minutos, impacto
   visual inmediato.
2. Ocultar pestañas nativas (7.1), una vez el navegador ya funciona.
3. Sincronizar segmentadores (7.5) para que el filtro de periodo/carrera
   sea realmente global.
4. Página de profundización por carrera (7.6).
5. Botón de restablecer filtros (7.4).
6. Tooltips personalizados (7.7) — es el más cosmético, déjalo para el
   final.

## Limitaciones de la licencia gratuita

- La subida a OneDrive sigue siendo manual (desde Linux no hay cliente
  oficial de OneDrive que sincronice una carpeta).
- El informe no se puede compartir para que otros lo abran. Para mostrarlo,
  usa **Exportar → PDF** o **PowerPoint**. Compartir requiere licencia
  **Pro**.
- El archivo en OneDrive no contiene datos personales (los quita el
  pipeline), pero sigue siendo información institucional: no lo compartas
  desde OneDrive con personas fuera de la institución.
