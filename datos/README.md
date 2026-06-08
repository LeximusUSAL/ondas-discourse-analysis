# Datos y metodología

Esta carpeta reúne los materiales de apoyo de los análisis publicados en este
repositorio: la metodología detallada, los listados de referencia, los datos
en bruto (JSON) generados por los scripts y, en
[`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/), las pruebas de validación
que comparan el método empleado (expresiones regulares y diccionarios) con
modelos de lenguaje basados en *transformers* (BERT).

- [`METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt`](METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt) — descripción completa de fuentes, criterios y proceso del análisis de discurso.
- [`listado_operas_ondas.txt`](listado_operas_ondas.txt) — listado de referencia de óperas mencionadas en el corpus de ONDAS.
- [`analisis_discurso_ondas.json`](analisis_discurso_ondas.json) / [`comparacion_lexico_escucha.json`](comparacion_lexico_escucha.json) — resultados completos en bruto de ambos análisis.
- [`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/) — pruebas de validación: comparación de los resultados obtenidos mediante un modelo BERT y mediante el método basado en expresiones regulares y diccionarios (véase la explicación a continuación).

---

## Justificación metodológica: expresiones regulares y diccionarios frente a BERT y modelos de lenguaje propios

Se trata de una cuestión que el equipo se planteó antes de la publicación de
este análisis: en el proyecto se emplean habitualmente modelos basados en
*transformers*, así como spaCy y un modelo de reconocimiento de entidades
propio, afinado para prensa musical española
([`LexiMus-BETO-per-v1`](https://huggingface.co/LexiMusUSAL/LexiMus-BETO-per-v1)).
Cabe preguntarse, por tanto, por qué se mantiene un método basado en
`re.finditer` y listas de variantes elaboradas manualmente, en lugar de
recurrir a herramientas de aprendizaje profundo más recientes.

Para responder a esta cuestión de forma empírica se llevó a cabo una
validación, cuyos resultados pueden resumirse en dos puntos:

1. Los resultados obtenidos son, desde un punto de vista estadístico,
   equivalentes: la introducción de un modelo de desambiguación contextual
   basado en *embeddings* de oración no modifica ninguna conclusión del
   análisis original (véanse las pruebas más abajo).
2. **Dada esta equivalencia, el método basado en expresiones regulares y
   diccionarios no resulta simplemente "suficiente", sino preferible para
   este caso de uso concreto**, por razones técnicas que se exponen a
   continuación con los datos correspondientes.

### El factor determinante: un corpus monotemático, exclusivamente musical

Este factor explica, en gran medida, los resultados descritos: **ni el
corpus de ONDAS ni la selección empleada de El Sol constituyen corpus de
prensa generalista.** ONDAS es, en su totalidad, una revista de radio y
música; la selección de El Sol corresponde específicamente a sus secciones y
crónicas musicales. Es decir, **el corpus ha sido delimitado de antemano
para excluir el ruido temático**, que constituye el origen real de los
problemas de polisemia.

La razón es la siguiente: la polisemia de una palabra no constituye un
problema inherente al léxico, sino que depende del *conjunto de temas*
susceptibles de aparecer en el texto analizado:

- En un corpus de prensa generalista (política, economía, sociedad,
  deportes, cultura...), la palabra **"concierto"** puede aparecer tanto en
  reseñas musicales como en noticias relativas al "concierto económico
  vasco". En ese contexto, la desambiguación resulta necesaria.
- En un corpus exclusivamente musical, "concierto" aparece, en la práctica,
  casi siempre en su sentido musical — no porque la palabra haya dejado de
  ser polisémica en español, sino porque **el otro sentido apenas tiene
  ocasión de aparecer** en un texto que versa únicamente sobre música.

La prueba de validación confirma esta hipótesis con datos concretos: de los
lemas identificados *a priori* como de riesgo elevado de polisemia en
español general — "concierto", "auditor", "género/genio", "soberbio",
"sesión", "impresión", "cascos", "aparato", entre otros —, la mayoría obtuvo
entre el **94 % y el 100 %** de uso en sentido musical o de escucha *dentro
de este corpus* (véase la tabla más abajo). El riesgo de polisemia presente
en el diccionario apenas llega a materializarse, precisamente porque **el
contexto temático que lo activaría fue eliminado durante la delimitación del
corpus**, con anterioridad a la ejecución de cualquier script de análisis.

De ello se desprende una consecuencia metodológica relevante: **un método de
desambiguación más complejo solo aporta valor cuando existe una ambigüedad
real que resolver.** Su aplicación a un corpus ya delimitado temáticamente
no introduce errores, pero tampoco resuelve ningún problema que no
estuviera ya resuelto por la propia composición del corpus.

### Diseño de la prueba de validación con BERT

Con el fin de contrastar empíricamente esta hipótesis, se construyó un
sistema de desambiguación contextual (*word-sense disambiguation*) basado en
*embeddings* de oración: para cada aparición de un lema, se calculó su
similitud coseno respecto a dos conjuntos de frases de referencia ("sentido
musical/de escucha" frente a "otro sentido"), empleando un
*sentence-transformer* multilingüe (`paraphrase-multilingual-MiniLM-L12-v2`).

En lugar de aplicar la prueba de manera indiscriminada a los 84 lemas del
"léxico de la escucha", se realizó previamente un **triaje lingüístico**: de
los 84 lemas, se seleccionaron los **31 lemas con riesgo real de polisemia**
en el español general de 1918-1935 (por ejemplo, *concierto* en su sentido
económico o musical, *cascos* de caballería o auriculares, *soberbia* como
defecto frente a *soberbio* como elogio, *auditor* de cuentas u oyente,
*impresión* tipográfica o emocional, entre otros), a los que se aplicó un
muestreo completo (200 contextos por lema y corpus). A otros 7 lemas de bajo
riesgo se les aplicó una validación puntual de menor tamaño (*spot-check*,
70 muestras), con el fin de confirmar que su sentido resulta, en la
práctica, unívoco. En conjunto, **46 de los 84 lemas** fueron sometidos a la
prueba con BERT, incluyendo los 8 de la prueba piloto inicial.

**Resultado: en los 46 lemas analizados, la conclusión comparativa entre
ONDAS y El Sol no varía en ningún caso.** Las densidades relativas (‱)
ajustadas mediante desambiguación con BERT resultan, en la gran mayoría de
los casos, prácticamente idénticas a las obtenidas mediante conteo directo
con expresiones regulares:

| Lema | Corpus | % en sentido musical/escucha (BERT) | Densidad bruta → ajustada (‱) |
|---|---|---:|---|
| concierto/s | ONDAS / El Sol | 100,0 % / 100,0 % | 23,17→23,17 / 29,49→29,49 |
| genio | ONDAS / El Sol | 100,0 % / 97,5 % | 3,47→3,47 / 1,99→1,94 |
| soberbio/a | ONDAS / El Sol | 96,2 % / 97,7 % | 0,30→0,29 / 0,98→0,96 |
| emisión/es | ONDAS / El Sol | 98,0 % / 95,9 % | 19,96→19,56 / 0,37→0,35 |
| sesión/es | ONDAS / El Sol | 94,5 % / 97,0 % | 2,47→2,33 / 1,27→1,23 |
| impresión | ONDAS / El Sol | 98,5 % / 96,0 % | 1,28→1,26 / 1,75→1,69 |
| voz/voces | ONDAS / El Sol | 100,0 % / 99,2 % | 4,50→4,50 / 4,53→4,49 |
| radio | ONDAS / El Sol | 100,0 % / 100,0 % | 47,51→47,51 / 1,60→1,60 |

(Tabla completa con los 46 lemas, sus 7 categorías semánticas, conteos
brutos, proporciones, densidades y muestreo: véanse
[`bert_wsd_resultados.json`](pruebas_regex_vs_bert/bert_wsd_resultados.json)
y [`bert_wsd_resultados_full.json`](pruebas_regex_vs_bert/bert_wsd_resultados_full.json).)

Las correcciones de mayor magnitud introducidas por el modelo —que, aun así,
no alteran ninguna conclusión— son las siguientes:

| Lema | Corpus | % sentido musical (BERT) | Densidad bruta → ajustada (‱) |
|---|---|---:|---|
| estudio/s | El Sol | 76,0 % | 4,98 → 3,79 |
| público/s | El Sol | 84,0 % | 14,30 → 12,02 |
| nota/s | El Sol | 86,8 % | 2,56 → 2,23 |
| aparato/s | ONDAS | 83,0 % | 1,12 → 0,93 |

Es decir, incluso en el caso más desfavorable, el ajuste por desambiguación
modifica la densidad relativa entre un 13 % y un 24 %, **sin llegar en
ningún caso a invertir una comparación entre corpus.** Las conclusiones
publicadas (por ejemplo, que ONDAS presenta una frecuencia relativa de un
determinado lema superior a la de El Sol) son las mismas con independencia
de si se aplica o no la desambiguación mediante BERT.

### Ante resultados equivalentes, razones para preferir el método más simple

Llegados a este punto, la cuestión relevante no es si resulta posible
emplear BERT — se ha comprobado que sí —, sino si resulta preferible
hacerlo. Las razones que se exponen a continuación indican que no es así, y
que el método basado en expresiones regulares y diccionarios resulta
preferible. Esta conclusión no constituye un argumento contra los modelos de
lenguaje en general, sino una valoración referida **a esta tarea concreta y
a este tipo de corpus**:

**1. Replicabilidad y determinismo.**
Un patrón como `re.finditer(r'\bconcierto\b', texto)` produce exactamente el
mismo resultado en el momento actual, dentro de varios años y en cualquier
equipo, con una instalación estándar de Python. Un resultado basado en
*embeddings*, en cambio, depende de la versión exacta del modelo empleado,
de la versión de las bibliotecas utilizadas (`transformers`, `torch`,
`spaCy`, etc.), del hardware (CPU, GPU o Apple Silicon producen resultados
ligeramente distintos por motivos de precisión numérica) y de las semillas
aleatorias empleadas en el muestreo. Para un proyecto de Humanidades
Digitales que pretende que otros investigadores puedan **replicar con
exactitud** los recuentos publicados, esta diferencia resulta significativa:
separa un método citable y reproducible de otro que, en la práctica, solo
resulta repetible de manera aproximada.

**2. Trazabilidad y posibilidad de auditoría manual.**
Cada recuento obtenido mediante este método puede verificarse de forma
manual: el patrón de expresión regular que generó cada coincidencia, la
posición exacta en el texto y el contexto de ±60 caracteres son datos
plenamente inspeccionables por un investigador, sin necesidad de recurrir a
un sistema opaco. Un modelo basado en *embeddings* no ofrece ese mismo grado
de trazabilidad: la pregunta de por qué una frase ha sido clasificada de una
determinada manera solo puede abordarse mediante modelos o heurísticas
adicionales, sin que ello proporcione una respuesta exacta y verificable. En
un ámbito —la Filología y las Humanidades Digitales— en el que la
verificabilidad del dato constituye la base de la credibilidad académica,
esta consideración resulta determinante.

**3. Coste computacional desproporcionado en relación con el beneficio obtenido.**
El recuento de las aproximadamente 24.000 apariciones de los 84 lemas en
3,08 millones de palabras mediante expresiones regulares requiere
**segundos**, sin necesidad de GPU ni de descargar ningún modelo. La prueba
con BERT —limitada a 46 de los 84 lemas, con un máximo de 200 contextos por
lema— exigió cargar un modelo de *embeddings*, vectorizar más de 15.000
fragmentos de texto y varios minutos de cómputo acelerado por GPU, con el
fin de confirmar que el resultado es, en la práctica, el mismo. Extender
este coste a los 84 lemas y a cada futura actualización del corpus no se
traduciría en ninguna ganancia real de precisión.

**4. Los modelos de propósito general incorporan sesgos procedentes de otros
dominios, lo que genera errores que el método basado en expresiones
regulares no presenta.**
Esta cuestión se documenta aquí mediante un caso concreto. El lema
**"auditor/es"** es el que obtiene los resultados menos favorables en la
prueba con BERT (aproximadamente entre el 60 % y el 77 % de uso estimado en
sentido musical). La revisión manual de una muestra de los contextos
clasificados por el modelo como "no musicales" muestra que **se trata, en su
mayoría, de falsos negativos**: expresiones como *"la captación de
auditores"* o *"el favor de los auditores [de Wagner]"* corresponden
inequívocamente al sentido de "oyente" o "audiencia", pero el modelo
—entrenado mayoritariamente con español contemporáneo, donde "auditor" se
emplea casi siempre con el sentido de "auditor de cuentas"— las asigna al
grupo semántico incorrecto, por una asociación ajena tanto al corpus como al
periodo histórico analizado (1925). **El modelo no solo no mejora el
recuento, sino que introduce un error sistemático que el método basado en
expresiones regulares, al no incorporar asociaciones semánticas procedentes
de otros dominios, no presenta.** El detalle completo de esta revisión
manual, con los fragmentos de texto correspondientes, se resume en
[`bert_wsd_resultados_full.json`](pruebas_regex_vs_bert/bert_wsd_resultados_full.json).

**5. El modelo de lenguaje propio tampoco constituye una herramienta
adecuada para esta tarea.**
Se evaluó asimismo la posibilidad de emplear
[`LexiMus-BETO-per-v1`](https://huggingface.co/LexiMusUSAL/LexiMus-BETO-per-v1)
—modelo BETO afinado sobre los corpus de El Sol y ONDAS, con una precisión
del 94,3 % validada manualmente en su tarea original— como motor de
desambiguación. El resultado fue negativo, por una razón técnica de fondo:
se trata de un modelo de **clasificación de tokens** (reconocimiento de
entidades de tipo persona: COMPOSITOR, INTÉRPRETE, CANTANTE, AGRUPACIÓN), no
de un *sentence-encoder*. Sus representaciones internas, obtenidas mediante
*mean-pooling*, presentan la **anisotropía** característica de los modelos
BERT que no han sido entrenados con un objetivo de similitud semántica: la
similitud coseno entre las frases *"Escuchamos un concierto por la radio
anoche"* y *"El ciclista ganó la etapa de montaña"* —sin relación semántica
entre sí— alcanza un valor de **0,977**, prácticamente idéntico al obtenido
entre dos frases de contenido musical (0,915). En estas condiciones, el
modelo clasificaba la palabra "escuchar" —en una revista de radio— como uso
de sentido musical en solo el 2 % de los casos. Es decir, **ni siquiera un
modelo propio, afinado sobre el corpus de trabajo, ofrece una alternativa
basada en aprendizaje profundo que mejore los resultados obtenidos mediante
una lista de variantes y una expresión regular adecuadamente construidas.**
El modelo se emplea, en cambio, de forma adecuada en la tarea para la que
fue entrenado, como se describe a continuación.

### Aplicación del modelo de lenguaje propio (LexiMus-BETO-per-v1) en una tarea distinta

El modelo resulta adecuado para la tarea para la que fue entrenado: la
identificación de personas y agrupaciones musicales con vocabulario abierto,
no limitado a una lista cerrada. Se aplicó —con carácter complementario, no
como sustituto del método de recuento del léxico de la escucha— sobre una
muestra de 400 párrafos del corpus de ONDAS, y se contrastó con los listados
cerrados empleados por la función `analizar_autores_interpretes()`. Este
análisis aportó información adicional de interés:

| Categoría | Menciones detectadas | Coinciden con el listado cerrado | Fuera del listado (el método basado en regex no las contabilizaría) |
|---|---:|---:|---:|
| COMPOSITOR | 301 | 193 (60 nombres) | 108 (88 nombres) — incluye Stravinsky, Sibelius, Borodin, Elgar, Puccini, Lehár... |
| CANTANTE | 46 | 5 (5 nombres) | 41 (39 nombres) |
| INTÉRPRETE | 44 | 14 (14 nombres) | 30 (28 nombres) — incluye Fernández Arbós, José Cubiles... |
| AGRUPACIÓN | 71 | 0 | 71 (39 nombres) — Trio Iberia, Cobla Barcelona, Banda Nacional Republicana... |

En este caso, el modelo **aporta valor añadido**, dado que la identificación
de personas con vocabulario abierto es precisamente el tipo de problema en
el que un sistema de reconocimiento de entidades supera a una lista cerrada:
se identificaron compositores, intérpretes y, en particular, agrupaciones
musicales con nombre propio que el listado de referencia original no
recogía. Cabe señalar asimismo un sesgo presente en el propio sistema de
reconocimiento de entidades: en ocasiones confunde personajes de ópera
—Wotan, Brünnhilde, Sigfrido— con intérpretes reales, al aparecer estos
nombres en resúmenes de argumento. Cualquier ampliación de los listados de
referencia a partir de estos resultados debería someterse a una revisión
manual previa.

Este resultado no contradice lo expuesto anteriormente, sino que lo
confirma: **la elección de método no depende de la actualidad de la
herramienta empleada, sino de si el problema concreto requiere aquello que
dicha herramienta resuelve.** Para determinar si un uso de "concierto"
corresponde al ámbito musical o económico en un corpus que trata
exclusivamente de música, el método basado en expresiones regulares,
diccionarios y criterio filológico constituye la herramienta más adecuada:
más rápida, más transparente y, como muestra el caso de "auditor", más
fiable. Para identificar qué personas con nombre propio aparecen en un texto
sin limitarse a una lista cerrada, el sistema de reconocimiento de entidades
resulta la herramienta apropiada. El empleo de BERT para la primera tarea no
habría supuesto un incremento del rigor metodológico, sino la aplicación de
un procedimiento más complejo a un problema que un método más simple
resuelve de forma adecuada.

### Pruebas y datos disponibles para su verificación

Los resultados descritos en este documento son reproducibles. En
[`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/) se incluyen los
siguientes materiales:

- [`bert_wsd_test.py`](pruebas_regex_vs_bert/bert_wsd_test.py) / [`bert_wsd_resultados.json`](pruebas_regex_vs_bert/bert_wsd_resultados.json) — prueba piloto de desambiguación (8 lemas).
- [`bert_wsd_test_full.py`](pruebas_regex_vs_bert/bert_wsd_test_full.py) / [`bert_wsd_resultados_full.json`](pruebas_regex_vs_bert/bert_wsd_resultados_full.json) — prueba extendida a las 7 categorías del léxico de la escucha (38 lemas adicionales, con el triaje de riesgo de polisemia documentado en el propio script).
- [`bert_ner_validacion.py`](pruebas_regex_vs_bert/bert_ner_validacion.py) / [`bert_ner_resultados.json`](pruebas_regex_vs_bert/bert_ner_resultados.json) — validación cruzada de menciones de personas y agrupaciones con `LexiMus-BETO-per-v1` frente a los listados cerrados del script original.

---
Proyecto LexiMus — Universidad de Salamanca
