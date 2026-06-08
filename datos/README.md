# Datos y metodología

Esta carpeta reúne los materiales de apoyo de los análisis publicados en este
repositorio: la metodología detallada, los listados de referencia, los datos
en bruto (JSON) generados por los scripts, y — en
[`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/) — las pruebas de validación
que comparan nuestro método (expresiones regulares + diccionarios) con
modelos de lenguaje basados en *transformers* (BERT).

- [`METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt`](METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt) — descripción completa de fuentes, criterios y proceso del análisis de discurso.
- [`listado_operas_ondas.txt`](listado_operas_ondas.txt) — listado de referencia de óperas mencionadas en el corpus ONDAS.
- [`analisis_discurso_ondas.json`](analisis_discurso_ondas.json) / [`comparacion_lexico_escucha.json`](comparacion_lexico_escucha.json) — resultados completos en bruto de ambos análisis.
- [`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/) — **pruebas de validación: ¿da un modelo BERT resultados distintos a los de nuestro método basado en regex y diccionarios?** (ver explicación abajo).

---

## ¿Por qué seguimos usando expresiones regulares y diccionarios, y no BERT ni nuestro propio modelo de lenguaje?

Esta es una pregunta legítima — y nos la hicimos nosotros mismos antes de
publicar este análisis: trabajamos habitualmente con *transformers*, con
spaCy y tenemos nuestro propio modelo NER afinado para prensa musical
española ([`LexiMus-BETO-per-v1`](https://huggingface.co/LexiMusUSAL/LexiMus-BETO-per-v1)).
¿Por qué entonces seguir contando palabras con `re.finditer` y listas de
variantes escritas a mano, en lugar de usar herramientas de aprendizaje
profundo más "modernas"?

Hicimos la prueba — con rigor, no de oídas — y la respuesta tiene dos partes:

1. **Empíricamente, los resultados son estadísticamente equivalentes**: un
   modelo de desambiguación contextual basado en *embeddings* de oración no
   cambia ninguna conclusión del análisis original (ver pruebas más abajo).
2. **Y, siendo los resultados equivalentes, el método basado en regex y
   diccionarios no es solo "suficientemente bueno": es la opción
   *superior* para este caso de uso concreto.** No por nostalgia
   metodológica, sino por razones técnicas concretas que detallamos a
   continuación, con datos.

### La clave: nuestro corpus es monotemático — es **solo musical**

Este es el factor que lo explica casi todo, y conviene decirlo alto y claro:
**ni ONDAS ni la selección de El Sol que usamos aquí son corpus de prensa
generalista.** ONDAS es íntegramente una revista de radio y música; la
selección de El Sol corresponde específicamente a sus secciones y crónicas
musicales. Es decir: **el corpus ya ha sido curado para excluir el ruido
temático** que es la verdadera fuente de los problemas de polisemia.

¿Por qué importa esto? Porque la polisemia de una palabra no es un problema
fijo del léxico — depende del *abanico de temas* que puede aparecer en el
texto que se analiza:

- En un corpus de prensa generalista (política + economía + sociedad +
  deportes + cultura...), la palabra **"concierto"** aparecerá tanto en
  reseñas musicales como en noticias sobre el "concierto económico vasco".
  Ahí sí hace falta desambiguar.
- En un corpus exclusivamente musical, "concierto" aparece prácticamente
  siempre en su sentido musical — no porque la palabra haya dejado de ser
  polisémica en español, sino porque **el otro sentido casi nunca tiene
  ocasión de aparecer** en un texto que ya trata solo de música.

La prueba de validación lo confirma con números: de los lemas que
identificamos *a priori* como de "alto riesgo" de polisemia en español
general — "concierto", "auditor", "género/genio", "soberbio", "sesión",
"impresión", "cascos", "aparato"... — la inmensa mayoría puntuó entre el
**94 % y el 100 %** de uso en sentido musical/de escucha *dentro de este
corpus* (ver tabla más abajo). El riesgo de polisemia que existe en el
diccionario casi no se materializa aquí, precisamente porque **el contexto
temático que lo activaría ha sido eliminado en el proceso de curación del
corpus**, antes incluso de ejecutar un solo script.

Esto tiene una consecuencia metodológica importante: **un método de
desambiguación sofisticado solo aporta valor cuando hay ambigüedad real que
desambiguar.** Aplicarlo a un corpus que ya viene filtrado temáticamente es
como llevar paraguas dentro de casa — no hace daño, pero tampoco soluciona
nada que no estuviera ya resuelto.

### La prueba: ¿cambia algo si usamos BERT para desambiguar?

Para no quedarnos en la intuición, hicimos la prueba real. Construimos un
sistema de desambiguación contextual (*word-sense disambiguation*) basado en
*embeddings* de oración — comparando, para cada aparición de un lema, su
similitud coseno con dos conjuntos de frases-ancla ("sentido musical/de
escucha" vs. "otro sentido") usando un *sentence-transformer* multilingüe
(`paraphrase-multilingual-MiniLM-L12-v2`).

En lugar de aplicar la prueba indiscriminadamente a los 84 lemas del
"léxico de la escucha", hicimos primero un **triaje lingüístico**: de los 84,
seleccionamos los **31 lemas con riesgo real de polisemia** en español
general de 1918-1935 (p. ej. *concierto* económico/musical, *cascos* de
caballería/auriculares, *soberbia* como defecto/*soberbio* como elogio,
*auditor* de cuentas/oyente, *impresión* tipográfica/emocional...) y les
aplicamos un muestreo completo (200 contextos por lema y corpus). A otros 7
lemas de bajo riesgo les aplicamos una validación puntual más pequeña
(*spot-check*, 70 muestras) para confirmar que, en efecto, su sentido es
prácticamente unívoco. En total: **46 de los 84 lemas** sometidos a prueba
con BERT — sumando los 8 de la prueba piloto inicial.

**Resultado: en los 46 lemas probados, la conclusión comparativa entre ONDAS
y El Sol no cambia ni una sola vez.** Las densidades relativas (‱) ajustadas
por desambiguación BERT son, en la inmensa mayoría de los casos, casi
idénticas a las obtenidas por conteo directo con regex:

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

Las mayores correcciones que encontró el modelo —y aun así, ninguna cambia
ninguna conclusión— son:

| Lema | Corpus | % sentido musical (BERT) | Densidad bruta → ajustada (‱) |
|---|---|---:|---|
| estudio/s | El Sol | 76,0 % | 4,98 → 3,79 |
| público/s | El Sol | 84,0 % | 14,30 → 12,02 |
| nota/s | El Sol | 86,8 % | 2,56 → 2,23 |
| aparato/s | ONDAS | 83,0 % | 1,12 → 0,93 |

Es decir: incluso en el peor de los casos, el ajuste por desambiguación
mueve la densidad relativa entre un 13 % y un 24 % — y **nunca llega a
invertir ninguna comparación entre corpus.** Las conclusiones publicadas
("ONDAS menciona X con más frecuencia relativa que El Sol", etc.) son
exactamente las mismas con o sin BERT.

### Cuando dos métodos dan el mismo resultado, gana el más simple — y aquí no es solo "igual de bueno", es mejor

Llegados a este punto, la pregunta relevante no es "¿podríamos usar BERT?"
(podemos, lo hemos probado) sino "¿deberíamos?". Y la respuesta es no, por
varias razones que pesan a favor de regex + diccionarios — no en contra de
los modelos de lenguaje en general, sino **para esta tarea concreta sobre
este tipo de corpus concreto**:

**1. Replicabilidad total y determinismo.**
Un patrón `re.finditer(r'\bconcierto\b', texto)` da exactamente el mismo
resultado hoy, dentro de cinco años y en cualquier ordenador, con Python de
serie. Un resultado basado en *embeddings* depende de la versión exacta del
modelo, de la versión de las librerías (`transformers`, `torch`, `spaCy`...),
del hardware (CPU/GPU/Apple Silicon dan resultados ligeramente distintos por
precisión numérica) y de semillas aleatorias de muestreo. Para un proyecto de
Humanidades Digitales que aspira a que otros investigadores **repliquen
exactamente** los recuentos publicados, esto no es un detalle menor: es la
diferencia entre un método citable y reproducible y uno que, en la práctica,
solo es repetible "más o menos".

**2. Trazabilidad y auditoría manual, palabra por palabra.**
Cada recuento de nuestro método se puede verificar a mano: el patrón regex
que generó cada coincidencia, la posición exacta en el texto, el contexto de
±60 caracteres — todo es inspeccionable por un filólogo sin necesidad de
confiar en una "caja negra". Un modelo de *embeddings* no ofrece esa
trazabilidad: solo se puede preguntar "¿por qué ha clasificado esta frase
así?" mediante más modelos o heurísticas adicionales, nunca con una
respuesta exacta y verificable. En un campo —la Filología y las Humanidades
Digitales— donde la verificabilidad del dato es la base de la credibilidad
académica, esto inclina la balanza decisivamente.

**3. Coste computacional desproporcionado para el beneficio obtenido.**
Contar las ~24.000 apariciones de los 84 lemas en 3,08 millones de palabras
con regex tarda **segundos**, sin GPU, sin descargar nada. La prueba con
BERT —limitada a 46 de los 84 lemas, con muestras de 200 contextos como
máximo— necesitó cargar un modelo de *embeddings*, vectorizar más de 15.000
fragmentos de texto y varios minutos de cómputo acelerado por GPU... para
confirmar que el resultado es, en la práctica, el mismo. Multiplicar ese
coste por los 84 lemas y por cada futura actualización del corpus no se
traduce en ninguna ganancia real de precisión.

**4. Los modelos genéricos importan sesgos de fuera del dominio — y eso
genera errores nuevos que el método simple no tiene.**
Aquí no nos quedamos en la teoría: lo documentamos con un caso real. El lema
**"auditor/es"** es el que peor parado sale en la prueba BERT (≈60-77 % de
"sentido musical" estimado). Revisamos a mano una muestra de los contextos
que el modelo clasificó como "no musicales" — y **son, casi todos, falsos
negativos**: frases como *"la captación de auditores"* o *"el favor de los
auditores [de Wagner]"* son inequívocamente del sentido "oyente/audiencia",
pero el modelo —entrenado mayoritariamente con español contemporáneo, donde
"auditor" significa casi siempre "auditor de cuentas"— las empuja hacia el
cluster equivocado por una asociación que nada tiene que ver con nuestro
corpus ni con 1925. **El modelo no solo no mejora el recuento: introduce un
error sistemático que el método de regex, precisamente por no tener
"intuiciones" semánticas heredadas de otros dominios, no comete.** El
detalle completo de esta revisión manual, con los fragmentos de texto
exactos, está documentado en la conversación de desarrollo y resumido en
[`bert_wsd_resultados_full.json`](pruebas_regex_vs_bert/bert_wsd_resultados_full.json).

**5. Ni siquiera nuestro propio modelo afinado es la herramienta adecuada
para esta tarea — y eso también lo comprobamos antes de descartarlo.**
Antes de concluir, probamos también a usar
[`LexiMus-BETO-per-v1`](https://huggingface.co/LexiMusUSAL/LexiMus-BETO-per-v1)
—nuestro propio BETO afinado sobre El Sol y ONDAS, con un 94,3 % de
precisión validada manualmente en su tarea de origen— como motor de
desambiguación. El resultado fue claramente negativo, y por una razón técnica
de fondo: es un modelo de **clasificación de tokens** (NER de personas:
COMPOSITOR/INTÉRPRETE/CANTANTE/AGRUPACIÓN), no un *sentence-encoder*. Sus
representaciones internas, extraídas por *mean-pooling*, muestran la
**anisotropía** típica de los modelos BERT que no se entrenan con un
objetivo de similitud semántica: la similitud coseno entre *"Escuchamos un
concierto por la radio anoche"* y *"El ciclista ganó la etapa de montaña"*
—dos frases sin ninguna relación— es **0,977**, prácticamente idéntica a la
de dos frases musicales entre sí (0,915). Usado así, el modelo clasificaba
"escuchar" —¡en una revista de radio!— como sentido musical solo en un 2 % de
los casos. Es decir: **ni siquiera disponiendo de un modelo propio,
afinado en nuestro propio corpus, hay un atajo de aprendizaje profundo que
mejore lo que ya hace una lista de variantes y una expresión regular bien
construidas.** (Lo usamos, en cambio, correctamente, para la tarea para la
que sí está entrenado: ver más abajo.)

### Pero entonces, ¿para qué sirve nuestro modelo de lenguaje (LexiMus-BETO-per-v1)?

Para lo que se entrenó: identificar personas y agrupaciones musicales con
vocabulario abierto (no limitado a una lista cerrada). Lo aplicamos —de
forma complementaria, no para sustituir el método de recuento del léxico de
escucha— sobre una muestra de 400 párrafos del corpus ONDAS, y lo cruzamos
con los listados cerrados que usa `analizar_autores_interpretes()`. Esto sí
reveló información nueva y útil:

| Categoría | Menciones detectadas | Coinciden con el listado cerrado | Fuera del listado (el regex original nunca las contaría) |
|---|---:|---:|---:|
| COMPOSITOR | 301 | 193 (60 nombres) | 108 (88 nombres) — incluye Stravinsky, Sibelius, Borodin, Elgar, Puccini, Lehár... |
| CANTANTE | 46 | 5 (5 nombres) | 41 (39 nombres) |
| INTÉRPRETE | 44 | 14 (14 nombres) | 30 (28 nombres) — incluye Fernández Arbós, José Cubiles... |
| AGRUPACIÓN | 71 | 0 | 71 (39 nombres) — Trio Iberia, Cobla Barcelona, Banda Nacional Republicana... |

Aquí el modelo **sí aporta**, porque identificar personas con vocabulario
abierto es justo el problema para el que un NER entrenado supera a una lista
cerrada: encontró compositores, intérpretes y, sobre todo, agrupaciones
musicales con nombre propio que el listado de referencia original no recogía.
(También detectamos un sesgo del propio NER que conviene anotar: confunde
ocasionalmente personajes de ópera —Wotan, Brünnhilde, Sigfrido— con
cantantes reales, al aparecer en resúmenes de argumento. Cualquier ampliación
de los listados a partir de esta vía debería filtrar estos casos a mano.)

Esto, lejos de contradecir lo anterior, lo confirma: **la elección de
método no depende de la "modernidad" de la herramienta, sino de si el
problema concreto necesita lo que esa herramienta resuelve.** Para
"¿es este uso de 'concierto' musical o económico, en un corpus que ya
solo habla de música?", regex + diccionarios + criterio filológico
es la herramienta correcta, más rápida, más transparente y, como
demuestra el caso de "auditor", más fiable. Para "¿qué personas con
nombre propio aparecen en este texto, sin limitarnos a una lista
cerrada?", el NER es la herramienta correcta. Usar BERT para lo
primero no habría sido más "riguroso": habría sido usar un martillo
de precisión para una tarea que ya resuelve, mejor, un destornillador.

### Pruebas y datos disponibles para su verificación

Todo lo descrito aquí es reproducible. En [`pruebas_regex_vs_bert/`](pruebas_regex_vs_bert/):

- [`bert_wsd_test.py`](pruebas_regex_vs_bert/bert_wsd_test.py) / [`bert_wsd_resultados.json`](pruebas_regex_vs_bert/bert_wsd_resultados.json) — prueba piloto de desambiguación (8 lemas).
- [`bert_wsd_test_full.py`](pruebas_regex_vs_bert/bert_wsd_test_full.py) / [`bert_wsd_resultados_full.json`](pruebas_regex_vs_bert/bert_wsd_resultados_full.json) — prueba extendida a las 7 categorías del léxico de la escucha (38 lemas adicionales, con triaje de riesgo de polisemia documentado en el propio script).
- [`bert_ner_validacion.py`](pruebas_regex_vs_bert/bert_ner_validacion.py) / [`bert_ner_resultados.json`](pruebas_regex_vs_bert/bert_ner_resultados.json) — validación cruzada de menciones de personas/agrupaciones con `LexiMus-BETO-per-v1` frente a los listados cerrados del script original.

---
Proyecto LexiMus / MUSLYME — Universidad de Salamanca
