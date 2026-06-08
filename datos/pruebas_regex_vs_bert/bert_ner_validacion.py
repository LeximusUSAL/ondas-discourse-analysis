#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validación cruzada con LexiMus-BETO-per-v1 (modelo NER propio del proyecto,
ajustado sobre El Sol/ONDAS 1918-1935; precisión validada manualmente: 94.3%)

Objetivo: comprobar si el método de conteo de menciones del script original
(contar_menciones_nombre / analizar_autores_interpretes), que busca en el
texto un LISTADO CERRADO de nombres predefinidos vía regex, se deja nombres
de compositores/cantantes/intérpretes/agrupaciones FUERA de ese listado
(falsos negativos por vocabulario cerrado) -- usando para ello un NER de
"vocabulario abierto" entrenado específicamente para detectar estas
categorías en este mismo tipo de texto.

Procedimiento:
  1. Cargar LexiMus-BETO-per-v1 + Entity Ruler (modo de uso documentado
     por el propio modelo, cargar_modelo.py).
  2. Tomar una muestra aleatoria de párrafos del corpus ONDAS.
  3. Extraer entidades COMPOSITOR / INTERPRETE / CANTANTE / AGRUPACION.
  4. Cruzar cada entidad con los listados cerrados que usa el script
     original (listado_compositores_ondas.txt, listado_cantantes_ondas.txt,
     listado_interpretes_instrumentos_ondas.txt) para ver cuántas SON
     nuevas (no estaban en el listado -> el regex nunca las habría contado).
"""
import os, re, csv, random, json
from pathlib import Path
from collections import Counter, defaultdict
import spacy

random.seed(42)

DIR_ONDAS = "corpus/ONDAS_TXT/"
RUTA_MODELO = "modelo/LexiMus-BETO-per-v1"
RUTA_CSV = "modelo/LexiMus-BETO-per-v1/entidades_ner_leximus.csv"
DIR_LISTADOS = "datos/listados_referencia_personas"

N_PARRAFOS = 400
ETIQUETAS = {"COMPOSITOR", "INTERPRETE", "CANTANTE", "AGRUPACION"}

# ── 1) Cargar modelo + entity ruler (igual que cargar_modelo.py del propio repo) ──
def cargar_patrones_csv(ruta_csv):
    patrones, vistos = [], set()
    with open(ruta_csv, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            etq = fila["etiqueta"]
            if etq not in ETIQUETAS:
                continue
            textos = {fila["texto"].strip()}
            if fila.get("variante_limpia", "").strip():
                textos.add(fila["variante_limpia"].strip())
            for t in textos:
                if not t or len(t) < 2:
                    continue
                clave = (t.lower(), etq)
                if clave in vistos:
                    continue
                vistos.add(clave)
                patrones.append({"label": etq, "pattern": t})
    return patrones

print("Cargando LexiMus-BETO-per-v1 + Entity Ruler...")
nlp = spacy.load(RUTA_MODELO)
if "entity_ruler" in nlp.component_names:
    nlp.remove_pipe("entity_ruler")
ruler = nlp.add_pipe("entity_ruler", last=True, config={"overwrite_ents": False})
ruler.add_patterns(cargar_patrones_csv(RUTA_CSV))
print(f"Listo: NER transformer + Entity Ruler ({len(ruler)} patrones)")

# ── 2) Cargar listados cerrados que usa el script original ──
def cargar_listado_cerrado(ruta):
    nombres = set()
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            m = re.match(r'\s*\d+\.\s*(.+)', linea.strip())
            if m:
                nombres.add(m.group(1).strip().lower())
    return nombres

listado_compositores = cargar_listado_cerrado(os.path.join(DIR_LISTADOS, "listado_compositores_ondas.txt"))
listado_cantantes    = cargar_listado_cerrado(os.path.join(DIR_LISTADOS, "listado_cantantes_ondas.txt"))
listado_interpretes  = cargar_listado_cerrado(os.path.join(DIR_LISTADOS, "listado_interpretes_instrumentos_ondas.txt"))
print(f"Listados cerrados originales: {len(listado_compositores)} compositores, "
      f"{len(listado_cantantes)} cantantes, {len(listado_interpretes)} intérpretes")

LISTADOS_POR_ETIQUETA = {
    'COMPOSITOR': listado_compositores,
    'CANTANTE': listado_cantantes,
    'INTERPRETE': listado_interpretes,
    'AGRUPACION': set(),  # el script original no usa listado cerrado de agrupaciones (solo el Sexteto vía regex)
}

def en_listado(nombre, etiqueta):
    nombre_l = nombre.lower().strip()
    listado = LISTADOS_POR_ETIQUETA.get(etiqueta, set())
    if nombre_l in listado:
        return True
    # coincidencia parcial: el listado tiene "nombre apellido", la entidad puede ser solo "apellido"
    return any(nombre_l in entrada or entrada.endswith(' ' + nombre_l) for entrada in listado)

# ── 3) Muestra de párrafos del corpus ONDAS y extracción NER ──
def cargar_parrafos(directorio, n):
    parrafos = []
    for root, _, files in os.walk(directorio):
        for fname in sorted(files):
            if not fname.endswith('.txt'):
                continue
            with open(os.path.join(root, fname), encoding='utf-8', errors='replace') as f:
                texto = f.read()
            for p in re.split(r'\n\s*\n', texto):
                p = p.strip().replace('\n', ' ')
                if len(p) > 80:
                    parrafos.append(p)
    random.shuffle(parrafos)
    return parrafos[:n]

print(f"\nMuestreando {N_PARRAFOS} párrafos de ONDAS y extrayendo entidades...")
parrafos = cargar_parrafos(DIR_ONDAS, N_PARRAFOS)

contador_por_etiqueta = Counter()
nuevas = defaultdict(Counter)       # entidad detectada que NO está en el listado cerrado
conocidas = defaultdict(Counter)    # entidad detectada que SÍ está en el listado cerrado
ejemplos_nuevas = defaultdict(list)

for doc in nlp.pipe(parrafos, batch_size=32):
    for ent in doc.ents:
        if ent.label_ not in ETIQUETAS:
            continue
        contador_por_etiqueta[ent.label_] += 1
        nombre = ent.text.strip()
        if en_listado(nombre, ent.label_):
            conocidas[ent.label_][nombre] += 1
        else:
            nuevas[ent.label_][nombre] += 1
            if len(ejemplos_nuevas[ent.label_]) < 25:
                ini = max(0, ent.start_char - 50)
                fin = min(len(doc.text), ent.end_char + 50)
                ejemplos_nuevas[ent.label_].append((nombre, doc.text[ini:fin].replace('\n',' ')))

print("\n" + "="*90)
print(f"RESULTADOS sobre {len(parrafos)} párrafos de ONDAS (LexiMus-BETO-per-v1, NER + Entity Ruler)")
print("="*90)
for etq in ['COMPOSITOR', 'CANTANTE', 'INTERPRETE', 'AGRUPACION']:
    total = contador_por_etiqueta[etq]
    n_conocidas = sum(conocidas[etq].values())
    n_nuevas = sum(nuevas[etq].values())
    distintas_conocidas = len(conocidas[etq])
    distintas_nuevas = len(nuevas[etq])
    print(f"\n[{etq}]  menciones detectadas: {total}")
    print(f"   - YA estaban en el listado cerrado del script original: {n_conocidas} menciones / {distintas_conocidas} nombres distintos")
    print(f"   - NO estaban en el listado cerrado (el regex original NUNCA las habría contado): "
          f"{n_nuevas} menciones / {distintas_nuevas} nombres distintos")
    if nuevas[etq]:
        top = nuevas[etq].most_common(10)
        print(f"   - Nombres nuevos más frecuentes: {top}")

print("\n" + "-"*90)
print("MUESTRA DE ENTIDADES 'NUEVAS' (fuera del listado cerrado) CON CONTEXTO -- revisión cualitativa")
print("(sirve para distinguir: (a) nombres reales que el listado cerrado se dejó fuera,")
print(" de (b) posibles falsos positivos del NER -- topónimos, títulos de obras, etc.)")
print("-"*90)
for etq in ['COMPOSITOR', 'CANTANTE', 'INTERPRETE', 'AGRUPACION']:
    if not ejemplos_nuevas[etq]:
        continue
    print(f"\n[{etq}]")
    for nombre, ctx in ejemplos_nuevas[etq][:12]:
        print(f"   '{nombre}'  ->  ...{ctx}...")

with open('salida/bert_ner_resultados.json', 'w', encoding='utf-8') as f:
    json.dump({
        'n_parrafos': len(parrafos),
        'por_etiqueta': {
            etq: {
                'total_menciones': contador_por_etiqueta[etq],
                'conocidas_en_listado': dict(conocidas[etq]),
                'nuevas_fuera_listado': dict(nuevas[etq]),
            } for etq in ETIQUETAS
        }
    }, f, ensure_ascii=False, indent=2)
print("\nGuardado en salida/bert_ner_resultados.json")
