# ONDAS Discourse Analysis

*[Leer en español](README.md)*

Discourse analysis of the Spanish radio magazine **ONDAS** (Madrid, 1925-1935)
and comparison with the newspaper **El Sol** (1918-1932): coverage of opera,
most frequently cited composers and performers, and the lexicon of musical
listening.

**LexiMus** Project — Universidad de Salamanca
("LexiMus: Léxico y ontología de la música en español", PID2022-139589NB-C33).

## Published analyses

- [Main page / interactive analyses](https://leximususal.github.io/ondas-discourse-analysis/)
- [ONDAS discourse analysis](analisis_discurso_ondas_EN.html) ([ES](analisis_discurso_ondas.html))
- [Listening lexicon comparison (ONDAS / El Sol)](comparacion_lexico_escucha_EN.html) ([ES](comparacion_lexico_escucha.html))
- [Musical genre classification criteria](criterios_generos_EN.html) ([ES](criterios_generos.html))

## Repository structure

- [`scripts/`](scripts/) — Python code used for the analyses (see [`scripts/README.md`](scripts/README.md)).
- [`datos/`](datos/) — raw data (JSON), reference lists and full methodology
  (see [`datos/README.md`](datos/README.md), in Spanish).

## Methodology: rationale for using regular expressions and dictionaries instead of BERT-based models

Before publishing this analysis, the team assessed whether using
transformer-based language models — or other tools available within the
project, such as spaCy or our own `LexiMus-BETO-per-v1` model — would offer
any advantage over the method actually applied, which is based on regular
expressions and lexical variant lists.

The validation carried out shows that both approaches produce statistically
equivalent results: across the 46 lemmas analysed, no conclusion of the study
changes when a BERT-based disambiguation model is introduced. Given this
equivalence, the method based on regular expressions and dictionaries is
preferable for this use case, owing to its replicability, its full manual
auditability, and the absence of biases imported from models trained on
domains other than the corpus under study (for example, a general-purpose
model misclassifies the lemma "auditor" by associating it with the sense of
"financial auditor," common in contemporary Spanish but absent from this
corpus). The structural reason behind these results is that **the corpus
analysed is exclusively musical**: since it is already thematically
delimited, the lexical ambiguity that would justify a more complex
disambiguation method barely arises.

The full explanation, with tables and results (in Spanish), is available in
[`datos/README.md`](datos/README.md), along with the scripts and JSON
results of the validation tests in
[`datos/pruebas_regex_vs_bert/`](datos/pruebas_regex_vs_bert/).

---
LexiMus Project — Universidad de Salamanca
