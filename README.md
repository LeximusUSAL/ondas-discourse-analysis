# ONDAS Discourse Analysis

Análisis de discurso del corpus de la revista **ONDAS** (Madrid, 1925-1935) y
comparación con el periódico **El Sol** (1918-1932): presencia de la ópera,
autores e intérpretes más citados, y léxico de la escucha musical.

Proyecto **LexiMus** — Universidad de Salamanca
("LexiMus: Léxico y ontología de la música en español", PID2022-139589NB-C33).

## Análisis publicados

- [Página principal / análisis interactivos](https://leximususal.github.io/ondas-discourse-analysis/)
- [Análisis de discurso ONDAS](analisis_discurso_ondas.html) ([EN](analisis_discurso_ondas_EN.html))
- [Comparación del léxico de la escucha (ONDAS / El Sol)](comparacion_lexico_escucha.html) ([EN](comparacion_lexico_escucha_EN.html))
- [Criterios de clasificación de géneros musicales](criterios_generos.html) ([EN](criterios_generos_EN.html))

## Estructura del repositorio

- [`scripts/`](scripts/) — código Python empleado en los análisis (véase [`scripts/README.md`](scripts/README.md)).
- [`datos/`](datos/) — datos en bruto (JSON), listados de referencia y metodología completa
  (véase [`datos/README.md`](datos/README.md)).

## Metodología: justificación del uso de expresiones regulares y diccionarios frente a modelos basados en BERT

Antes de la publicación de este análisis se evaluó si el empleo de modelos de
lenguaje basados en *transformers* —u otras herramientas disponibles en el
proyecto, como spaCy o el modelo propio `LexiMus-BETO-per-v1`— ofrecería
ventajas frente al método aplicado, basado en expresiones regulares y listas
de variantes léxicas.

La validación realizada muestra que ambos enfoques producen resultados
estadísticamente equivalentes: en los 46 lemas analizados, ninguna conclusión
del estudio varía al introducir un modelo de desambiguación basado en BERT.
Dada esta equivalencia, el método basado en expresiones regulares y
diccionarios resulta preferible para este caso de uso, por su replicabilidad,
su posibilidad de auditoría manual completa y la ausencia de sesgos
introducidos por modelos entrenados sobre dominios distintos al del corpus de
trabajo (a modo de ejemplo, un modelo de propósito general clasifica
incorrectamente el lema "auditor" al asociarlo al sentido de "auditor de
cuentas", habitual en el español contemporáneo pero inexistente en este
corpus). La razón estructural que explica estos resultados es que **el corpus
analizado es exclusivamente musical**: al estar ya delimitado temáticamente,
la ambigüedad léxica que justificaría el empleo de un método de
desambiguación más complejo apenas llega a producirse.

Véase la explicación completa, con tablas y resultados, en
[`datos/README.md`](datos/README.md), así como los scripts y los resultados en
formato JSON de las pruebas de validación en
[`datos/pruebas_regex_vs_bert/`](datos/pruebas_regex_vs_bert/).

---
Proyecto LexiMus — Universidad de Salamanca
