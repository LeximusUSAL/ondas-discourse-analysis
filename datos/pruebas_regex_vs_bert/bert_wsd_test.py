#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba: desambiguación contextual con embeddings BERT multilingües
para los lemas más polisémicos del léxico de escucha, comparando
ONDAS vs El Sol, y viendo cuánto cambian las densidades relativas
respecto al conteo por patrones (regex) del script original.
"""
import os, re, json, random
from collections import defaultdict
import torch
from transformers import AutoTokenizer, AutoModel

random.seed(42)
torch.manual_seed(42)

DIR_ONDAS = "corpus/ONDAS_TXT/"
DIR_ELSOL = "corpus/EL_SOL_TXT/"

MAX_SAMPLES = 250  # muestreo por lema y corpus (prueba, no censo exhaustivo)

# Lemas polisémicos seleccionados (alto volumen + sentido ambiguo en español general)
LEMAS = {
    'radio':    ['radio'],
    'estudio/s':['estudio', 'estudios'],
    'programa/s':['programa', 'programas'],
    'tono/s':   ['tono', 'tonos'],
    'nota/s':   ['nota', 'notas'],
    'frase/s':  ['frase', 'frases'],
    'público/s':['público', 'públicos'],
    'voz/voces':['voz', 'voces'],
}

# Frases-ancla: sentido "escucha/musical/radiofónico" vs "otro sentido"
ANCLAS_MUSICAL = [
    "Escuchamos un concierto por la radio anoche.",
    "El estudio de grabación transmitió la audición musical.",
    "El programa radiofónico incluía una selección de ópera.",
    "La soprano cantó en un tono agudo y brillante.",
    "Cada nota de la melodía sonaba con gran emoción.",
    "La frase musical se repite varias veces en la sinfonía.",
    "El público aplaudió con entusiasmo al final del concierto.",
    "Su voz de tenor llenó la sala con un timbre cálido.",
    "La orquesta interpretó la pieza ante un auditorio entregado.",
    "El locutor presentó el programa de música clásica desde el estudio.",
]
ANCLAS_OTRO = [
    "El radio del círculo mide diez centímetros.",
    "Terminó sus estudios de derecho en la universidad.",
    "El programa del partido prometía reformas económicas.",
    "Adoptó un tono serio al hablar de política.",
    "Hizo una nota en su cuaderno para recordarlo.",
    "La frase del discurso fue muy comentada en la prensa.",
    "El público en general desconoce esta nueva ley.",
    "No tengo voz ni voto en esa decisión del comité.",
    "El gobierno anunció un nuevo plan de obras públicas.",
    "El estudio de abogados llevó el caso ante el tribunal.",
]

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
print(f"Cargando modelo {MODEL_NAME} ...")
tok = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = model.to(device).eval()

def embed(texts, batch_size=64):
    vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        enc = tok(batch, padding=True, truncation=True, max_length=64, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).expand(out.size()).float()
        summed = (out * mask).sum(1)
        counts = mask.sum(1).clamp(min=1e-9)
        mean_pooled = summed / counts
        norm = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
        vecs.append(norm.cpu())
    return torch.cat(vecs, 0)

print("Embebiendo frases-ancla...")
emb_musical = embed(ANCLAS_MUSICAL)
emb_otro = embed(ANCLAS_OTRO)

def clasificar(contextos):
    """Devuelve lista de bool: True si más cercano (similitud coseno media) al cluster musical."""
    if not contextos:
        return []
    emb = embed(contextos)
    sim_musical = (emb @ emb_musical.T).mean(dim=1)
    sim_otro = (emb @ emb_otro.T).mean(dim=1)
    return (sim_musical > sim_otro).tolist()


def cargar_corpus(directorio):
    archivos = []
    for root, _, files in os.walk(directorio):
        for fname in sorted(files):
            if not fname.endswith('.txt'):
                continue
            try:
                with open(os.path.join(root, fname), 'r', encoding='utf-8', errors='replace') as f:
                    contenido = f.read()
            except Exception:
                continue
            archivos.append({'filename': fname, 'contenido_lower': contenido.lower(),
                             'palabras': len(contenido.split())})
    return archivos


def extraer_contextos(archivos, variantes, ventana=8):
    """Todas las ocurrencias con ventana de palabras de contexto."""
    contextos = []
    pattern = r'\b(' + '|'.join(re.escape(v) for v in variantes) + r')\b'
    for a in archivos:
        texto = a['contenido_lower']
        for m in re.finditer(pattern, texto):
            ini, fin = m.span()
            ctx = texto[max(0, ini-60):fin+60].replace('\n', ' ').strip()
            contextos.append(ctx)
    return contextos


print("\nCargando corpus...")
arch_ondas = cargar_corpus(DIR_ONDAS)
arch_elsol = cargar_corpus(DIR_ELSOL)
pal_ondas = sum(a['palabras'] for a in arch_ondas)
pal_elsol = sum(a['palabras'] for a in arch_elsol)
print(f"  ONDAS: {len(arch_ondas)} archivos, {pal_ondas:,} palabras")
print(f"  El Sol: {len(arch_elsol)} archivos, {pal_elsol:,} palabras")

resultados = {}
for lema, variantes in LEMAS.items():
    fila = {}
    for nombre, archivos, total_palabras in (("ONDAS", arch_ondas, pal_ondas), ("El Sol", arch_elsol, pal_elsol)):
        contextos = extraer_contextos(archivos, variantes)
        n_total = len(contextos)
        muestra = contextos if n_total <= MAX_SAMPLES else random.sample(contextos, MAX_SAMPLES)
        clases = clasificar(muestra)
        prop_musical = sum(clases) / len(clases) if clases else 0.0
        n_ajustado = round(n_total * prop_musical)
        fila[nombre] = {
            'n_bruto': n_total,
            'muestra': len(muestra),
            'prop_sentido_musical': round(prop_musical, 3),
            'n_ajustado_estimado': n_ajustado,
            'densidad_bruta_o/ooo': round(n_total / total_palabras * 10000, 2),
            'densidad_ajustada_o/ooo': round(n_ajustado / total_palabras * 10000, 2),
        }
        print(f"  {lema:12s} {nombre:7s}: bruto={n_total:6d}  →  sentido musical/escucha ≈ {prop_musical*100:5.1f}%  →  ajustado≈{n_ajustado}")
    resultados[lema] = fila

print("\n" + "="*70)
print("RESUMEN: densidad relativa (‱) ANTES (regex bruto) vs DESPUÉS (BERT-ajustado)")
print("="*70)
print(f"{'Lema':12s} {'ONDAS bruto':>12s} {'ONDAS ajus.':>12s} {'ElSol bruto':>12s} {'ElSol ajus.':>12s}  {'¿Cambia el dominante?'}")
for lema, fila in resultados.items():
    ob, oa = fila['ONDAS']['densidad_bruta_o/ooo'], fila['ONDAS']['densidad_ajustada_o/ooo']
    eb, ea = fila['El Sol']['densidad_bruta_o/ooo'], fila['El Sol']['densidad_ajustada_o/ooo']
    dom_bruto = "ONDAS" if ob > eb else "El Sol"
    dom_ajus = "ONDAS" if oa > ea else "El Sol"
    cambia = "SÍ ⚠" if dom_bruto != dom_ajus else "no"
    print(f"{lema:12s} {ob:>12.2f} {oa:>12.2f} {eb:>12.2f} {ea:>12.2f}  {cambia}")

with open('salida/bert_wsd_resultados.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
print("\nGuardado en salida/bert_wsd_resultados.json")
