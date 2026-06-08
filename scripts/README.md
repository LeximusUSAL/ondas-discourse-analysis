# Herramientas de análisis

Scripts en Python utilizados para generar los análisis publicados en este repositorio.

## `analisis_discurso_ondas.py`

Análisis de discurso del corpus ONDAS (1925-1935): porcentaje de contenido dedicado a
ópera, autores/intérpretes más citados, léxico de la escucha musical y estadísticas
generales del corpus. Genera `analisis_discurso_ondas.html` + `.json`.

## `comparacion_lexico_escucha.py`

Comparación del léxico de la escucha musical (7 categorías semánticas, 84 lemas) entre
los corpus ONDAS (1925-1935) y El Sol (1918-1932), con frecuencias absolutas y relativas
(‱) y concordancias contextuales. Genera `comparacion_lexico_escucha.html` + `.json`.
Usa los mismos criterios y lemas que `analisis_discurso_ondas.py`.

## Requisitos

- Python 3
- Librerías de la biblioteca estándar (`os`, `re`, `json`, `csv`, `collections`, `datetime`)

## Configuración

Antes de ejecutar, edita las constantes de la sección `CONFIGURACIÓN` al inicio de cada
script para que apunten a tu copia local de los corpus en texto plano (TXT):

- `CORPUS_DIR` / `DIR_ONDAS`: transcripciones del corpus ONDAS (revista de radio, Madrid 1925-1935)
- `DIR_ELSOL`: transcripciones del corpus El Sol (periódico, Madrid 1918-1932)
- `CSV_IMAGENES`: índice de catalogación de imágenes de la revista (solo `analisis_discurso_ondas.py`)
- `OUTPUT_DIR` / `SALIDA_HTML` / `SALIDA_JSON`: carpeta/archivos de salida

Los listados de referencia (cantantes, compositores, intérpretes, óperas) usados por
`analisis_discurso_ondas.py` deben colocarse en `OUTPUT_DIR`; un ejemplo
(`listado_operas_ondas.txt`) está incluido en [`../datos/`](../datos/).

Véase [`METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt`](../datos/METODOLOGIA_ANALISIS_DISCURSO_ONDAS.txt)
para la descripción completa de fuentes, criterios y proceso.

---
Proyecto LexiMus — Universidad de Salamanca
