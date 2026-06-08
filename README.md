# ONDAS Discourse Analysis

Análisis de discurso del corpus de la revista **ONDAS** (Madrid, 1925-1935) y
comparación con el periódico **El Sol** (1918-1932): presencia de la ópera,
autores e intérpretes más citados, y léxico de la escucha musical.

Proyecto **LexiMus / MUSLYME** — Universidad de Salamanca
("LexiMus: Léxico y ontología de la música en español", PID2022-139589NB-C33).

## Ver los análisis (web)

➡ **[Página principal / análisis interactivos](https://leximususal.github.io/ondas-discourse-analysis/)**

- [Análisis de discurso ONDAS](analisis_discurso_ondas.html) ([EN](analisis_discurso_ondas_EN.html))
- [Comparación del léxico de la escucha (ONDAS / El Sol)](comparacion_lexico_escucha.html) ([EN](comparacion_lexico_escucha_EN.html))
- [Criterios de clasificación de géneros musicales](criterios_generos.html) ([EN](criterios_generos_EN.html))

## Estructura del repositorio

- [`scripts/`](scripts/) — código Python de los análisis (ver [`scripts/README.md`](scripts/README.md)).
- [`datos/`](datos/) — datos en bruto (JSON), listados de referencia y **metodología completa**
  (ver [`datos/README.md`](datos/README.md)).

## Metodología: ¿por qué expresiones regulares y diccionarios, y no BERT?

Una pregunta que nos hicimos —y respondimos con pruebas, no de oídas— antes de
publicar este análisis: ¿por qué seguir contando con expresiones regulares y
listas de variantes en lugar de usar *transformers*, spaCy o nuestro propio
modelo de lenguaje (`LexiMus-BETO-per-v1`)?

**Respuesta corta**: probamos BERT y nuestro propio modelo, y los resultados
fueron estadísticamente equivalentes — sin que ninguna conclusión cambiara en
46 lemas analizados. Siendo los resultados iguales, el método basado en regex y
diccionarios es la opción *superior* para este caso, por ser totalmente
replicable, auditable a mano y libre de sesgos importados de otros dominios
(p. ej., un modelo general clasifica mal "auditor" porque en español
contemporáneo asocia la palabra a "auditor de cuentas", un sentido que no
existe en nuestro corpus). Y la razón estructural de que esto funcione tan bien
es que **nuestro corpus es exclusivamente musical**: al estar ya curado para
excluir cualquier otro tema, la ambigüedad léxica que justificaría un método
de desambiguación más complejo apenas llega a producirse.

📄 **[Lectura completa, con tablas, datos y pruebas (`datos/README.md`)](datos/README.md)**
🧪 **[Scripts y resultados JSON de las pruebas BERT vs. regex (`datos/pruebas_regex_vs_bert/`)](datos/pruebas_regex_vs_bert/)**

---
Proyecto LexiMus / MUSLYME — Universidad de Salamanca
