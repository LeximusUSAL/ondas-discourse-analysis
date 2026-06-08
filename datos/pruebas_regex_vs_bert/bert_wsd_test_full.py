#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prueba extendida (todas las categorías): desambiguación contextual por
similitud de embeddings de oración (encoder multilingüe calibrado para
similitud semántica) para el resto de lemas del "léxico de escucha",
comparando ONDAS vs El Sol.

Estrategia de precisión:
  1) Triaje lingüístico previo: solo se aplica WSD a lemas con riesgo
     real de polisemia/ambigüedad contextual en este corpus (p.ej.
     "concierto" económico vs musical, "cascos" de caballería vs auriculares,
     "soberbio" elogioso vs "soberbia" como defecto, "auditor" de cuentas
     vs oyente...). Para los de bajo riesgo se hace un spot-check más
     pequeño, que confirma que el recuento por regex ya es fiable
     (proporción de sentido relevante ~100%).
  2) Clasificación por similitud coseno a dos clusters de frases-ancla
     ("musical/escucha" vs "otro sentido"), usando
     paraphrase-multilingual-MiniLM-L12-v2 (sentence-transformer
     entrenado para similitud semántica).

Nota sobre LexiMus-BETO-per-v1 (modelo propio solicitado): se evaluó su
uso como segundo encoder para esta tarea y se descartó por una razón
técnica de fondo -- ver "NOTA METODOLÓGICA" más abajo. Se usa en su
lugar, correctamente, en bert_ner_validacion.py para la tarea para la
que SÍ fue entrenado (NER de personas/agrupaciones musicales).
"""
import os, re, json, random
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

random.seed(42)
torch.manual_seed(42)

DIR_ONDAS = "corpus/ONDAS_TXT/"
DIR_ELSOL = "corpus/EL_SOL_TXT/"
RUTA_BETO = "modelo/LexiMus-BETO-per-v1"  # pipeline spaCy descargado con huggingface_hub.snapshot_download(repo_id="LexiMusUSAL/LexiMus-BETO-per-v1")

MAX_SAMPLES_RIESGO = 200   # lemas con riesgo real de ambigüedad -> muestreo completo
MAX_SAMPLES_SPOT   = 70    # lemas de bajo riesgo -> validación puntual (spot-check)

# ─────────────────────────────────────────────────────────────────────────────
# 1) TRIAJE: lemas con riesgo real de polisemia / desplazamiento de sentido
#    en un corpus de prensa generalista + musical de 1918-1935
# ─────────────────────────────────────────────────────────────────────────────
LEMAS_RIESGO = {
    # PERCEPCIÓN AUDITIVA — riesgo: sentidos no auditivos muy frecuentes
    'escuchar':        ['escuchar'],
    'oír':             ['oír', 'oir'],
    'percibir':        ['percibir'],          # "percibir un sueldo/una pensión"
    'auditor/es':      ['auditor', 'auditores'],  # auditor de cuentas / de guerra
    # ACTO DE ESCUCHA — riesgo: sentidos jurídicos/políticos/genéricos
    'concierto/s':     ['concierto', 'conciertos'],     # concierto económico/político
    'sesión/es':       ['sesión', 'sesiones', 'sesion', 'sesiones'],  # sesión de Cortes/cine
    'emisión/es':      ['emisión', 'emisiones', 'emision', 'emisiones'],  # emisión de bonos/gases
    'transmisión/es':  ['transmisión', 'transmisiones', 'transmision', 'transmisiones'],  # transmisión de poderes
    'velada/s':        ['velada', 'veladas'],           # velada literaria/benéfica no musical
    'programación':    ['programación', 'programacion'],
    # DISPOSITIVOS DE ESCUCHA — riesgo: homónimos muy comunes
    'cascos':          ['cascos'],            # cascos de caballería / botellas, no auriculares
    'aparato/s':       ['aparato', 'aparatos'],  # aparato digestivo/del Estado/crítico
    'disco/s':         ['disco', 'discos'],   # disco (atletismo), disco de tráfico
    'auricular/es':    ['auricular', 'auriculares'],  # adjetivo médico "región auricular"
    'receptor/es':     ['receptor', 'receptores'],    # receptor = destinatario (cartas, pagos)
    'antena/s':        ['antena', 'antenas'], # antena de insecto (zoología)
    'válvula/s':       ['válvula', 'válvulas', 'valvula', 'valvulas'],  # válvula cardíaca/de motor
    'galena':          ['galena'],            # mineral de plomo (minería) vs detector de radio
    # EMOCIONES Y SENSACIONES — riesgo: verbos/sustantivos muy polisémicos
    'sentir':          ['sentir', 'siente', 'sintió', 'sintio', 'sienten', 'sentía', 'sentia'],
    'impresión':       ['impresión', 'impresion', 'impresiones'],  # imprenta/tipografía
    'encanto':         ['encanto', 'encantos'],  # encanto de una persona/lugar, no musical
    'placer':          ['placer', 'placeres'],   # placer genérico no musical
    # VALORACIÓN ESTÉTICA — riesgo: sentidos opuestos o no estéticos
    'genio':           ['genio', 'genios'],       # "genio" = mal carácter / genialidad
    'soberbio/a':      ['soberbio', 'soberbia', 'soberbios', 'soberbias'],  # soberbia = orgullo (negativo)
    'maravilla':       ['maravilla', 'maravillas'],  # maravilla = planta/flor; asombro genérico
    'prodigio':        ['prodigio', 'prodigios'],
    # RESPUESTA DEL PÚBLICO — riesgo: usos no relacionados con espectáculos
    'bis':             ['bis'],          # "10 bis" (numeración), "in extremis" latinismos
    'clamor':          ['clamor'],       # clamor político/social, no de público en sala
    'éxito/s':         ['éxito', 'éxitos', 'exito', 'exitos'],  # éxito genérico (deportivo, comercial)
    # CUALIDADES SONORAS — riesgo: sentidos no acústicos muy frecuentes
    'acento/s':        ['acento', 'acentos'],   # acento regional/ortográfico, no musical
    'matiz/matices':   ['matiz', 'matices'],    # matiz genérico (político, de opinión)
}

# Lemas de bajo riesgo -> validación puntual (spot-check), uno por categoría
LEMAS_SPOT = {
    'oyente/s':         ['oyente', 'oyentes'],
    'retransmisión/es': ['retransmisión', 'retransmisiones', 'retransmision', 'retransmisiones'],
    'micrófono/s':      ['micrófono', 'micrófonos', 'microfono', 'microfonos'],
    'entusiasmo':       ['entusiasmo'],
    'belleza':          ['belleza', 'bellezas'],
    'aplauso/s':        ['aplauso', 'aplausos'],
    'melodía':          ['melodía', 'melodías', 'melodia', 'melodias'],
}

# ─────────────────────────────────────────────────────────────────────────────
# 2) ANCLAS — ampliadas para cubrir las 7 categorías semánticas
#    (no solo dispositivos/percepción, también emociones, valoración estética,
#    respuesta del público y cualidades sonoras), con pares de contraste que
#    usan las MISMAS palabras ambiguas en sentido musical y no musical.
# ─────────────────────────────────────────────────────────────────────────────
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
    "El pianista demostró ser un genio de la interpretación y arrancó ovaciones del público.",
    "La velada musical resultó soberbia y llena de matices expresivos.",
    "El tenor tuvo que repetir el aria ante el clamor del público, que pidió un bis.",
    "La belleza de su fraseo y la emoción de su canto causaron un éxito extraordinario.",
    "El crítico sintió una honda impresión ante la interpretación y la calificó de prodigio.",
    "Los acordes finales produjeron un éxtasis y un goce difíciles de describir.",
    "El placer de escuchar aquella sinfonía por la radio fue un verdadero encanto para el auditorio.",
    "La emisión musical de esta noche incluirá un recital de canto y piano.",
    "Aquel virtuoso del violín posee un acento expresivo y un fraseo lleno de matices.",
    "La maravilla de su voz y la armonía del conjunto entusiasmaron al auditorio.",
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
    "El concierto económico vasco fue firmado por el ministro de Hacienda.",
    "Convocaron una sesión extraordinaria de las Cortes para debatir el presupuesto.",
    "El genio de aquel hombre era difícil de soportar, pues siempre estaba de mal humor.",
    "Su soberbia y su desprecio por los demás le granjearon muchos enemigos.",
    "El ciclista logró un éxito notable al ganar la etapa de montaña.",
    "Sintió un fuerte dolor en la pierna tras la caída y tuvo que retirarse.",
    "El perito redactó un informe e impresión del inmueble para la subasta.",
    "El paisaje de la sierra ofrecía una maravilla de colores al atardecer.",
    "El auditor de cuentas revisó el balance de la sociedad antes de la junta.",
    "Llevaba unos cascos de cuero que protegían la cabeza del jinete.",
]

# ─────────────────────────────────────────────────────────────────────────────
# 3) DOS ENCODERS DE ORACIONES
# ─────────────────────────────────────────────────────────────────────────────
device = "mps" if torch.backends.mps.is_available() else "cpu"

print("Cargando encoder genérico (paraphrase-multilingual-MiniLM-L12-v2)...")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
tok_mini = AutoTokenizer.from_pretrained(MODEL_NAME)
model_mini = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()

def embed_minilm(texts, batch_size=64):
    vecs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        enc = tok_mini(batch, padding=True, truncation=True, max_length=64, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model_mini(**enc).last_hidden_state
        mask = enc["attention_mask"].unsqueeze(-1).expand(out.size()).float()
        summed = (out * mask).sum(1)
        counts = mask.sum(1).clamp(min=1e-9)
        mean_pooled = summed / counts
        norm = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
        vecs.append(norm.cpu().numpy())
    return np.concatenate(vecs, 0)

print("Embebiendo frases-ancla...")
emb_mini_musical = embed_minilm(ANCLAS_MUSICAL)
emb_mini_otro    = embed_minilm(ANCLAS_OTRO)

# NOTA METODOLÓGICA IMPORTANTE (verificada empíricamente antes de este run):
# Se probó también un "ensemble" añadiendo LexiMus-BETO-per-v1 como segundo
# encoder de oraciones (mean-pooling de su capa transformer). Resultado: sus
# embeddings en bruto muestran fuerte ANISOTROPÍA típica de BERT sin objetivo
# de similitud de oraciones -- p.ej. la similitud coseno entre "Escuchamos un
# concierto por la radio anoche" y "El ciclista ganó la etapa de montaña" es
# 0.977 (prácticamente idéntica a la de dos frases musicales entre sí, 0.915).
# Es decir, NO es un encoder de oraciones calibrado y produce clasificaciones
# casi degeneradas (p.ej. "escuchar" -> ~2% sentido musical, evidentemente
# erróneo en una revista de radio). Usarlo así habría EMPEORADO la precisión.
#
# LexiMus-BETO-per-v1 es un modelo de TOKEN-CLASSIFICATION (NER de personas:
# COMPOSITOR/INTERPRETE/CANTANTE/AGRUPACION), no un sentence-encoder. Su uso
# correcto y "más preciso" en este contexto es para lo que fue entrenado: se
# emplea por separado (ver bert_ner_validacion.py) para validar/contrastar los
# recuentos de menciones de personas del script original (basados en regex),
# que es exactamente la tarea para la que el modelo fue ajustado y evaluado
# (94.3% de precisión validada por revisión humana).
print(f"(LexiMus-BETO-per-v1 disponible en {RUTA_BETO}; se usa en script aparte para su tarea real -- NER de personas -- y no aquí, ver nota arriba)")

def clasificar(contextos):
    """True si el contexto está más cerca (similitud coseno media) del cluster musical/escucha."""
    if not contextos:
        return []
    emb = embed_minilm(contextos)
    sim_musical = (emb @ emb_mini_musical.T).mean(axis=1)
    sim_otro = (emb @ emb_mini_otro.T).mean(axis=1)
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


def extraer_contextos(archivos, variantes):
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


def procesar_lema(lema, variantes, max_samples, grupo):
    fila = {'grupo': grupo}
    for nombre, archivos, total_palabras in (("ONDAS", arch_ondas, pal_ondas), ("El Sol", arch_elsol, pal_elsol)):
        contextos = extraer_contextos(archivos, variantes)
        n_total = len(contextos)
        muestra = contextos if n_total <= max_samples else random.sample(contextos, max_samples)
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
        print(f"  [{grupo:10s}] {lema:16s} {nombre:7s}: bruto={n_total:6d} -> sentido relevante ~ {prop_musical*100:5.1f}%  ajustado~{n_ajustado}")
    return fila


resultados = {}
print("\n--- LEMAS DE RIESGO (muestreo completo) ---")
for lema, variantes in LEMAS_RIESGO.items():
    resultados[lema] = procesar_lema(lema, variantes, MAX_SAMPLES_RIESGO, 'riesgo')

print("\n--- LEMAS DE BAJO RIESGO (validación puntual / spot-check) ---")
for lema, variantes in LEMAS_SPOT.items():
    resultados[lema] = procesar_lema(lema, variantes, MAX_SAMPLES_SPOT, 'spot-check')

print("\n" + "="*100)
print("RESUMEN: densidad relativa (per10000) ANTES (regex bruto) vs DESPUÉS (BERT-ajustado)")
print("="*100)
print(f"{'Lema':16s} {'grupo':11s} {'ONDAS bruto':>12s} {'ONDAS ajus.':>12s} {'ElSol bruto':>12s} {'ElSol ajus.':>12s}  {'¿Cambia dominante?'}")
cambios = []
for lema, fila in resultados.items():
    ob, oa = fila['ONDAS']['densidad_bruta_o/ooo'], fila['ONDAS']['densidad_ajustada_o/ooo']
    eb, ea = fila['El Sol']['densidad_bruta_o/ooo'], fila['El Sol']['densidad_ajustada_o/ooo']
    dom_bruto = "ONDAS" if ob > eb else "El Sol"
    dom_ajus = "ONDAS" if oa > ea else "El Sol"
    cambia = dom_bruto != dom_ajus
    if cambia:
        cambios.append(lema)
    marca = "SI ⚠" if cambia else "no"
    print(f"{lema:16s} {fila['grupo']:11s} {ob:>12.2f} {oa:>12.2f} {eb:>12.2f} {ea:>12.2f}  {marca}")

print(f"\nLemas en los que el corpus dominante CAMBIA tras el ajuste BERT: {cambios if cambios else 'NINGUNO'}")

with open('salida/bert_wsd_resultados_full.json', 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
print("\nGuardado en salida/bert_wsd_resultados_full.json")
