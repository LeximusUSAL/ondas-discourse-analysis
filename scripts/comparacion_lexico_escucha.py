#!/usr/bin/env python3
"""
Comparación del léxico COMPLETO de la escucha musical (7 categorías)
entre dos corpus:
- ONDAS (1925-1935): revista de radio
- El Sol (1918-1932): periódico generalista, sección musical

Mismos criterios, lemas y variantes que analisis_discurso_ondas.py
Genera: comparacion_lexico_escucha.html + .json
"""

import os
import re
import json
from collections import Counter, defaultdict

# ============================================================
# CONFIGURACIÓN
# Ajustar estas rutas a la ubicación local de los corpus.
# ============================================================

DIR_ONDAS = "corpus/ONDAS_TXT/"            # Transcripciones TXT del corpus ONDAS (1925-1935)
DIR_ELSOL = "corpus/EL_SOL_TXT/"           # Transcripciones TXT del corpus El Sol (1918-1932)
SALIDA_HTML = "salida/comparacion_lexico_escucha.html"
SALIDA_JSON = "salida/comparacion_lexico_escucha.json"

# Las 7 categorías semánticas (idénticas a analisis_discurso_ondas.py)
CATEGORIAS = {
    'PERCEPCIÓN AUDITIVA': {
        'escuchar': ['escuchar', 'escuchando', 'escucharon', 'escuchaba', 'escuchamos',
                     'escuchó', 'escucha', 'escuchas', 'escucharse', 'escuchado'],
        'oír': ['oír', 'oyen', 'oyendo', 'oyeron', 'oímos', 'oyó', 'oído',
                'oiga', 'oigan'],
        'oyente/s': ['oyente', 'oyentes'],
        'audición/es': ['audición', 'audiciones'],
        'auditor/es': ['auditor', 'auditores'],
        'auditorio': ['auditorio'],
        'radioyente/s': ['radioyente', 'radioyentes'],
        'radioescucha/s': ['radioescucha', 'radioescuchas'],
        'percibir': ['percibir', 'percibe', 'percibido'],
    },
    'ACTO DE ESCUCHA': {
        'concierto/s': ['concierto', 'conciertos'],
        'recital/es': ['recital', 'recitales'],
        'sesión/es': ['sesión', 'sesiones'],
        'emisión/es': ['emisión', 'emisiones'],
        'transmisión/es': ['transmisión', 'transmisiones'],
        'retransmisión/es': ['retransmisión', 'retransmisiones'],
        'programa/s': ['programa', 'programas'],
        'programación': ['programación'],
        'velada/s': ['velada', 'veladas'],
    },
    'DISPOSITIVOS DE ESCUCHA': {
        'radio': ['radio'],
        'radiodifusión': ['radiodifusión'],
        'radiotelefonía': ['radiotelefonía'],
        'radiofonía': ['radiofonía'],
        'altavoz/ces': ['altavoz', 'altavoces'],
        'auricular/es': ['auricular', 'auriculares'],
        'cascos': ['cascos'],
        'micrófono/s': ['micrófono', 'micrófonos'],
        'aparato/s': ['aparato', 'aparatos'],
        'receptor/es': ['receptor', 'receptores'],
        'antena/s': ['antena', 'antenas'],
        'válvula/s': ['válvula', 'válvulas'],
        'galena': ['galena'],
        'gramófono/s': ['gramófono', 'gramófonos'],
        'fonógrafo/s': ['fonógrafo', 'fonógrafos'],
        'disco/s': ['disco', 'discos'],
        'estudio/s': ['estudio', 'estudios'],
        'emisora/s': ['emisora', 'emisoras'],
    },
    'EMOCIONES Y SENSACIONES': {
        'emoción': ['emoción', 'emociones', 'emocionante', 'emocionado', 'emocionar'],
        'sentir': ['sentir', 'sentimiento', 'sentimientos', 'sentido'],
        'impresión': ['impresión', 'impresiones', 'impresionante', 'impresionar'],
        'conmover': ['conmover', 'conmovedor', 'conmovido', 'conmoción'],
        'entusiasmo': ['entusiasmo', 'entusiasta', 'entusiasmado', 'entusiasmar'],
        'admiración': ['admiración', 'admirar', 'admirable', 'admirado'],
        'deleite': ['deleite', 'deleitar', 'deleitarse'],
        'goce/gozo': ['goce', 'gozar', 'gozo'],
        'placer': ['placer'],
        'encanto': ['encanto', 'encantador', 'encantar'],
        'fascinación': ['fascinación', 'fascinante', 'fascinar'],
        'éxtasis': ['éxtasis', 'extasis'],
    },
    'VALORACIÓN ESTÉTICA': {
        'belleza': ['belleza', 'bello', 'bella', 'bellas', 'bellos', 'bellísimo', 'bellísima'],
        'hermosura': ['hermoso', 'hermosa', 'hermosura', 'hermosísimo'],
        'sublime': ['sublime', 'sublimidad'],
        'grandioso/a': ['grandioso', 'grandiosa', 'grandiosidad'],
        'exquisito/a': ['exquisito', 'exquisita', 'exquisitez'],
        'magnífico/a': ['magnífico', 'magnífica', 'magnificencia'],
        'espléndido/a': ['espléndido', 'espléndida', 'esplendor'],
        'maravilla': ['maravilloso', 'maravillosa', 'maravilla'],
        'prodigio': ['prodigioso', 'prodigiosa', 'prodigio'],
        'genio': ['genial', 'genio', 'genialidad'],
        'soberbio/a': ['soberbio', 'soberbia'],
        'extraordinario/a': ['extraordinario', 'extraordinaria'],
    },
    'RESPUESTA DEL PÚBLICO': {
        'aplauso/s': ['aplauso', 'aplausos', 'aplaudir', 'aplaudido', 'aplaudieron'],
        'ovación/es': ['ovación', 'ovaciones', 'ovacionado', 'ovacionar'],
        'éxito/s': ['éxito', 'éxitos', 'exitoso'],
        'triunfo/s': ['triunfo', 'triunfos', 'triunfal', 'triunfar'],
        'aclamación': ['aclamación', 'aclamar', 'aclamado'],
        'público/s': ['público', 'públicos'],
        'audiencia': ['audiencia'],
        'estruendoso/a': ['estruendoso', 'estruendosa'],
        'clamor': ['clamoroso', 'clamorosa', 'clamor'],
        'bis': ['bis'],
        'repetición': ['repetición'],
    },
    'CUALIDADES SONORAS': {
        'sonido/s': ['sonido', 'sonidos', 'sonar', 'sonoro', 'sonora', 'sonoridad'],
        'voz/voces': ['voz', 'voces'],
        'timbre/s': ['timbre', 'timbres'],
        'tono/s': ['tono', 'tonos', 'tonal', 'tonalidad'],
        'armonía': ['armonía', 'armónico', 'armónica', 'armonioso'],
        'melodía': ['melodía', 'melódico', 'melódica', 'melodioso'],
        'ritmo': ['ritmo', 'rítmico', 'rítmica'],
        'acorde/s': ['acorde', 'acordes'],
        'nota/s': ['nota', 'notas'],
        'frase/s': ['frase', 'frases'],
        'acento/s': ['acento', 'acentos'],
        'matiz/matices': ['matiz', 'matices'],
        'vibración/es': ['vibración', 'vibraciones', 'vibrar', 'vibrante'],
    },
}

# Términos representativos para concordancias (2 por categoría)
CONCORDANCIA_TERMS = {
    'PERCEPCIÓN AUDITIVA': ['escuchar', 'oír', 'oyente', 'audición'],
    'ACTO DE ESCUCHA': ['concierto', 'recital', 'programa', 'emisión'],
    'DISPOSITIVOS DE ESCUCHA': ['radio', 'disco', 'gramófono', 'emisora'],
    'EMOCIONES Y SENSACIONES': ['emoción', 'sentir', 'entusiasmo', 'admiración'],
    'VALORACIÓN ESTÉTICA': ['belleza', 'sublime', 'genio', 'maravilla'],
    'RESPUESTA DEL PÚBLICO': ['aplauso', 'ovación', 'éxito', 'triunfo'],
    'CUALIDADES SONORAS': ['melodía', 'ritmo', 'armonía', 'voz'],
}

CAT_IDS = {
    'PERCEPCIÓN AUDITIVA': 'percepcion',
    'ACTO DE ESCUCHA': 'acto',
    'DISPOSITIVOS DE ESCUCHA': 'dispositivos',
    'EMOCIONES Y SENSACIONES': 'emociones',
    'VALORACIÓN ESTÉTICA': 'valoracion',
    'RESPUESTA DEL PÚBLICO': 'respuesta',
    'CUALIDADES SONORAS': 'cualidades',
}


# ============================================================
# CARGA DE CORPUS
# ============================================================

def cargar_corpus(directorio, nombre):
    archivos = []
    for root, dirs, files in os.walk(directorio):
        for fname in sorted(files):
            if not fname.endswith('.txt'):
                continue
            ruta = os.path.join(root, fname)
            try:
                with open(ruta, 'r', encoding='utf-8', errors='replace') as f:
                    contenido = f.read()
            except Exception:
                continue
            m = re.search(r'(\d{4})', fname)
            year = int(m.group(1)) if m else 0
            archivos.append({
                'filename': fname, 'year': year,
                'contenido_lower': contenido.lower(),
                'palabras': len(contenido.split()),
            })
    total = sum(a['palabras'] for a in archivos)
    print(f"  {nombre}: {len(archivos)} archivos, {total:,} palabras")
    return archivos


# ============================================================
# ANÁLISIS COMPLETO (7 CATEGORÍAS)
# ============================================================

def analizar_escucha_completo(archivos, nombre):
    total_palabras = sum(a['palabras'] for a in archivos)
    resultados = {}
    total_global = 0

    for cat_nombre, lemas in CATEGORIAS.items():
        conteo = Counter()
        por_año = defaultdict(lambda: Counter())

        for lema, variantes in lemas.items():
            total_lema = 0
            for archivo in archivos:
                for var in variantes:
                    n = len(re.findall(r'\b' + re.escape(var) + r'\b', archivo['contenido_lower']))
                    if n > 0:
                        total_lema += n
                        por_año[archivo['year']][lema] += n
            if total_lema > 0:
                conteo[lema] = total_lema

        cat_total = sum(conteo.values())
        total_global += cat_total
        resultados[cat_nombre] = {
            'total': cat_total,
            'relativo': (cat_total / total_palabras * 10000) if total_palabras else 0,
            'lemas': conteo.most_common(),
            'por_año': {str(k): dict(v) for k, v in sorted(por_año.items())},
        }
        print(f"    {cat_nombre}: {cat_total:,}")

    # Concordancias
    concordancias = {}
    for cat, terms in CONCORDANCIA_TERMS.items():
        concordancias[cat] = {}
        for termino in terms:
            concs = []
            for archivo in archivos:
                pattern = r'(.{0,80}\b' + re.escape(termino) + r'\b.{0,80})'
                for m in re.findall(pattern, archivo['contenido_lower'])[:3]:
                    concs.append({
                        'archivo': archivo['filename'],
                        'año': archivo['year'],
                        'contexto': m.strip().replace('\n', ' ')
                    })
            concordancias[cat][termino] = concs[:12]

    return {
        'total_palabras': total_palabras,
        'total_archivos': len(archivos),
        'total_global': total_global,
        'categorias': resultados,
        'concordancias': concordancias,
    }


# ============================================================
# GENERACIÓN HTML
# ============================================================

def generar_html(ondas, elsol):

    cat_nombres = list(CATEGORIAS.keys())
    cat_totales_ondas = [ondas['categorias'][c]['total'] for c in cat_nombres]
    cat_totales_elsol = [elsol['categorias'][c]['total'] for c in cat_nombres]
    cat_rel_ondas = [ondas['categorias'][c]['relativo'] for c in cat_nombres]
    cat_rel_elsol = [elsol['categorias'][c]['relativo'] for c in cat_nombres]

    # Años compartidos
    todos_años = set()
    for c in cat_nombres:
        todos_años.update(int(k) for k in ondas['categorias'][c]['por_año'] if k != '0')
        todos_años.update(int(k) for k in elsol['categorias'][c]['por_año'] if k != '0')
    todos_años = sorted(todos_años)

    # Evolución total por año
    ondas_evol = []
    elsol_evol = []
    for y in todos_años:
        ys = str(y)
        o = sum(sum(ondas['categorias'][c]['por_año'].get(ys, {}).values()) for c in cat_nombres)
        e = sum(sum(elsol['categorias'][c]['por_año'].get(ys, {}).values()) for c in cat_nombres)
        ondas_evol.append(o)
        elsol_evol.append(e)

    # Nav links por categoría
    nav_cats = "".join(f'<a href="#{CAT_IDS[c]}">{c.split()[0]}</a>' for c in cat_nombres)

    # Secciones por categoría
    secciones_cats = ""
    chart_scripts = ""

    colores_7 = ['#800020','#1a1a2e','#2d6a4f','#d4a373','#457b9d','#e76f51','#6d6875',
                 '#264653','#e9c46a','#f4a261','#2a9d8f','#023047','#8338ec','#fb5607',
                 '#3a86ff','#606c38','#bc6c25','#dda15e']

    for idx, cat in enumerate(cat_nombres):
        cid = CAT_IDS[cat]
        o_data = ondas['categorias'][cat]
        e_data = elsol['categorias'][cat]
        lemas_cat = list(CATEGORIAS[cat].keys())

        o_vals = [dict(o_data['lemas']).get(l, 0) for l in lemas_cat]
        e_vals = [dict(e_data['lemas']).get(l, 0) for l in lemas_cat]
        o_rel = [(dict(o_data['lemas']).get(l, 0) / ondas['total_palabras'] * 10000) for l in lemas_cat]
        e_rel = [(dict(e_data['lemas']).get(l, 0) / elsol['total_palabras'] * 10000) for l in lemas_cat]

        # Tabla
        filas = ""
        for lema in lemas_cat:
            o_v = dict(o_data['lemas']).get(lema, 0)
            e_v = dict(e_data['lemas']).get(lema, 0)
            vars_str = ", ".join(CATEGORIAS[cat][lema])
            filas += f'<tr><td><strong>{lema}</strong></td><td class="vars">{vars_str}</td><td class="num">{o_v:,}</td><td class="num">{e_v:,}</td></tr>\n'

        # Concordancias
        conc_html = ""
        if cat in ondas['concordancias']:
            conc_html += '<div class="conc-grid">\n<div class="conc-panel">\n<h4 class="ondas-color">ONDAS</h4>\n'
            for term, ejemplos in ondas['concordancias'][cat].items():
                if not ejemplos:
                    continue
                conc_html += f'<p class="conc-term">«{term}» ({len(ejemplos)} ej.)</p><ul>\n'
                for ej in ejemplos[:5]:
                    ctx = ej['contexto'].replace(term, f'<strong class="ondas-color">{term}</strong>')
                    conc_html += f'<li><em>[{ej["año"]}]</em> ...{ctx}...</li>\n'
                conc_html += '</ul>\n'
            conc_html += '</div>\n<div class="conc-panel">\n<h4 class="elsol-color">El Sol</h4>\n'
            for term, ejemplos in elsol['concordancias'].get(cat, {}).items():
                if not ejemplos:
                    continue
                conc_html += f'<p class="conc-term">«{term}» ({len(ejemplos)} ej.)</p><ul>\n'
                for ej in ejemplos[:5]:
                    ctx = ej['contexto'].replace(term, f'<strong class="elsol-color">{term}</strong>')
                    conc_html += f'<li><em>[{ej["año"]}]</em> ...{ctx}...</li>\n'
                conc_html += '</ul>\n'
            conc_html += '</div>\n</div>\n'

        secciones_cats += f"""
<section class="section" id="{cid}">
    <h2>{idx+3}. {cat}</h2>
    <div class="stat-grid">
        <div class="stat-card"><div class="number ondas-color">{o_data['total']:,}</div><div class="label">ONDAS</div></div>
        <div class="stat-card"><div class="number elsol-color">{e_data['total']:,}</div><div class="label">El Sol</div></div>
        <div class="stat-card"><div class="number ondas-color">{o_data['relativo']:.1f}‱</div><div class="label">ONDAS relativa</div></div>
        <div class="stat-card"><div class="number elsol-color">{e_data['relativo']:.1f}‱</div><div class="label">El Sol relativa</div></div>
    </div>
    <div class="charts-duo">
        <div class="chart-container"><canvas id="chart_{cid}_abs"></canvas></div>
        <div class="chart-container"><canvas id="chart_{cid}_rel"></canvas></div>
    </div>
    <table>
        <tr><th>Lema</th><th>Variantes</th><th class="num">ONDAS</th><th class="num">El Sol</th></tr>
        {filas}
        <tr class="total-row"><td>TOTAL</td><td></td><td class="num">{o_data['total']:,}</td><td class="num">{e_data['total']:,}</td></tr>
    </table>
    <h3>Concordancias</h3>
    {conc_html}
</section>
"""

        chart_scripts += f"""
new Chart(document.getElementById('chart_{cid}_abs'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(lemas_cat)}, datasets: [
        {{ label: 'ONDAS', data: {json.dumps(o_vals)}, backgroundColor: ONDAS_BG, borderColor: ONDAS_C, borderWidth: 1 }},
        {{ label: 'El Sol', data: {json.dumps(e_vals)}, backgroundColor: ELSOL_BG, borderColor: ELSOL_C, borderWidth: 1 }}
    ]}},
    options: {{ responsive: true, plugins: {{ title: {{ display: true, text: '{cat} — frecuencias absolutas' }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});
new Chart(document.getElementById('chart_{cid}_rel'), {{
    type: 'bar',
    data: {{ labels: {json.dumps(lemas_cat)}, datasets: [
        {{ label: 'ONDAS (‱)', data: {json.dumps([round(x,2) for x in o_rel])}, backgroundColor: ONDAS_BG, borderColor: ONDAS_C, borderWidth: 1 }},
        {{ label: 'El Sol (‱)', data: {json.dumps([round(x,2) for x in e_rel])}, backgroundColor: ELSOL_BG, borderColor: ELSOL_C, borderWidth: 1 }}
    ]}},
    options: {{ responsive: true, plugins: {{ title: {{ display: true, text: '{cat} — frecuencias relativas (‱)' }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});
"""

    # Etiquetas cortas en dos líneas para legibilidad en gráficos
    cat_labels_map = {
        'PERCEPCIÓN AUDITIVA': 'Percepción\\nauditiva',
        'ACTO DE ESCUCHA': 'Acto de\\nescucha',
        'DISPOSITIVOS DE ESCUCHA': 'Dispositivos\\nde escucha',
        'EMOCIONES Y SENSACIONES': 'Emociones y\\nsensaciones',
        'VALORACIÓN ESTÉTICA': 'Valoración\\nestética',
        'RESPUESTA DEL PÚBLICO': 'Respuesta\\ndel público',
        'CUALIDADES SONORAS': 'Cualidades\\nsonoras',
    }
    cat_labels_cortas = [cat_labels_map.get(c, c) for c in cat_nombres]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Léxico de la Escucha Musical: ONDAS vs El Sol</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Crimson Text', serif; background: #faf9f6; color: #1a1a1a; line-height: 1.6; }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white; text-align: center; padding: 50px 20px;
        }}
        .header h1 {{ font-family: 'EB Garamond', serif; font-size: 2.5rem; margin-bottom: 10px; }}
        .header p {{ font-size: 1.1rem; opacity: 0.85; max-width: 750px; margin: 0 auto; }}
        nav {{
            background: #1a1a2e; padding: 10px 20px; text-align: center;
            position: sticky; top: 0; z-index: 100; flex-wrap: wrap;
        }}
        nav a {{
            color: #d4a373; text-decoration: none; margin: 4px 10px;
            font-size: 0.9rem; font-weight: 600; display: inline-block;
        }}
        nav a:hover {{ color: white; }}
        .section {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}
        .section h2 {{
            font-family: 'EB Garamond', serif; font-size: 1.8rem;
            color: #1a1a2e; border-bottom: 2px solid #d4a373;
            padding-bottom: 10px; margin-bottom: 25px;
        }}
        .section h3 {{ font-family: 'EB Garamond', serif; font-size: 1.3rem; color: #333; margin: 25px 0 15px; }}
        .stat-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px; margin-bottom: 25px;
        }}
        .stat-card {{
            background: white; border-radius: 10px; padding: 18px;
            text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .stat-card .number {{ font-size: 1.8rem; font-weight: 700; }}
        .stat-card .label {{ font-size: 0.82rem; color: #666; margin-top: 4px; }}
        .ondas-color {{ color: #800020; }}
        .elsol-color {{ color: #1a5276; }}
        .chart-container {{ background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); min-height: 350px; }}
        .chart-container-wide {{ background: white; border-radius: 10px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); min-height: 380px; }}
        .chart-container-radar {{ background: white; border-radius: 10px; padding: 20px; margin: 15px auto; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 600px; min-height: 420px; }}
        .charts-duo {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        @media (max-width: 900px) {{ .charts-duo {{ grid-template-columns: 1fr; }} }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        th {{ background: #1a1a2e; color: white; padding: 8px 12px; text-align: left; font-size: 0.85rem; }}
        td {{ padding: 7px 12px; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
        td.num, th.num {{ text-align: right; }}
        td.vars {{ font-size: 0.8em; color: #888; }}
        tr:hover {{ background: #fdf6ec; }}
        tr.total-row {{ font-weight: bold; background: #f5f5f5; }}
        .nota {{ background: #fff8e7; border-left: 4px solid #d4a373; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; font-size: 0.95rem; }}
        .conc-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px; }}
        @media (max-width: 768px) {{ .conc-grid {{ grid-template-columns: 1fr; }} }}
        .conc-panel {{ background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); font-size: 0.88rem; }}
        .conc-panel ul {{ line-height: 1.7; padding-left: 18px; }}
        .conc-panel li {{ margin-bottom: 6px; }}
        .conc-term {{ font-weight: 600; margin: 12px 0 4px; }}
        .legend-box {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; margin-right: 6px; vertical-align: middle; }}
        footer {{ background: #1a1a2e; color: white; text-align: center; padding: 25px; font-size: 0.85rem; opacity: 0.8; }}
    </style>
</head>
<body>

<div class="header">
    <h1>Léxico de la Escucha Musical</h1>
    <p>Comparación de 7 categorías semánticas en dos corpus de prensa española: <em>ONDAS</em> (revista radiofónica, 1925-1935) y <em>El Sol</em> (periódico generalista, 1918-1932)</p>
</div>

<nav>
    <a href="#corpus">Corpus</a>
    <a href="#panorama">Panorama</a>
    {nav_cats}
</nav>

<!-- 1. CORPUS -->
<section class="section" id="corpus">
    <h2>1. Los dos corpus</h2>
    <div class="stat-grid">
        <div class="stat-card"><div class="number ondas-color">{ondas['total_archivos']}</div><div class="label"><span class="legend-box" style="background:#800020"></span>ONDAS — archivos</div></div>
        <div class="stat-card"><div class="number ondas-color">{ondas['total_palabras']:,}</div><div class="label">ONDAS — palabras</div></div>
        <div class="stat-card"><div class="number elsol-color">{elsol['total_archivos']}</div><div class="label"><span class="legend-box" style="background:#1a5276"></span>El Sol — archivos</div></div>
        <div class="stat-card"><div class="number elsol-color">{elsol['total_palabras']:,}</div><div class="label">El Sol — palabras</div></div>
    </div>
    <div class="nota">
        <strong>ONDAS</strong> (Madrid, 1925-1935): revista semanal dedicada a la radiodifusión y la música por radio. {ondas['total_archivos']} números transcritos, {ondas['total_palabras']:,} palabras.<br>
        <strong>El Sol</strong> (Madrid, 1918-1932): diario generalista con sección musical fija. {elsol['total_archivos']} textos transcritos, {elsol['total_palabras']:,} palabras.<br><br>
        Los corpus comparten el periodo 1925-1932. Se aplican los mismos 84 lemas agrupados en 7 categorías semánticas. Las frecuencias relativas se expresan por cada 10.000 palabras (‱) para compensar la diferencia de tamaño.
    </div>
</section>

<!-- 2. PANORAMA -->
<section class="section" id="panorama">
    <h2>2. Panorama general: las 7 categorías</h2>
    <div class="stat-grid">
        <div class="stat-card"><div class="number ondas-color">{ondas['total_global']:,}</div><div class="label">ONDAS — total léxico escucha</div></div>
        <div class="stat-card"><div class="number elsol-color">{elsol['total_global']:,}</div><div class="label">El Sol — total léxico escucha</div></div>
        <div class="stat-card"><div class="number ondas-color">{ondas['total_global']/ondas['total_palabras']*10000:.1f}‱</div><div class="label">ONDAS — densidad relativa</div></div>
        <div class="stat-card"><div class="number elsol-color">{elsol['total_global']/elsol['total_palabras']*10000:.1f}‱</div><div class="label">El Sol — densidad relativa</div></div>
    </div>
    <div class="chart-container-radar"><canvas id="chartRadar"></canvas></div>
    <div class="charts-duo">
        <div class="chart-container"><canvas id="chartCatAbs"></canvas></div>
        <div class="chart-container"><canvas id="chartCatRel"></canvas></div>
    </div>
    <h3>Evolución temporal global</h3>
    <div class="chart-container-wide"><canvas id="chartEvolGlobal"></canvas></div>
</section>

<!-- SECCIONES POR CATEGORÍA -->
{secciones_cats}

<footer>
    Análisis comparativo del léxico de la escucha musical — Proyecto LexiMus / MUSLYME — Universidad de Salamanca<br>
    84 lemas · 7 categorías semánticas · Generado automáticamente · Enero 2026
</footer>

<script>
const ONDAS_C = '#800020';
const ELSOL_C = '#1a5276';
const ONDAS_BG = 'rgba(128, 0, 32, 0.65)';
const ELSOL_BG = 'rgba(26, 82, 118, 0.65)';

// Etiquetas cortas para los gráficos panorámicos
const catLabels = {json.dumps(cat_labels_cortas)};

// Radar
new Chart(document.getElementById('chartRadar'), {{
    type: 'radar',
    data: {{
        labels: catLabels,
        datasets: [
            {{ label: 'ONDAS (‱)', data: {json.dumps([round(x,1) for x in cat_rel_ondas])}, borderColor: ONDAS_C, backgroundColor: 'rgba(128,0,32,0.15)', pointBackgroundColor: ONDAS_C, borderWidth: 2 }},
            {{ label: 'El Sol (‱)', data: {json.dumps([round(x,1) for x in cat_rel_elsol])}, borderColor: ELSOL_C, backgroundColor: 'rgba(26,82,118,0.15)', pointBackgroundColor: ELSOL_C, borderWidth: 2 }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: true,
        plugins: {{
            title: {{ display: true, text: 'Perfil comparado (frecuencia relativa ‱)', font: {{ size: 14 }} }},
            legend: {{ labels: {{ font: {{ size: 13 }} }} }}
        }},
        scales: {{
            r: {{
                pointLabels: {{ font: {{ size: 12 }} }},
                ticks: {{ font: {{ size: 10 }} }}
            }}
        }}
    }}
}});

// Categorías absolutas
new Chart(document.getElementById('chartCatAbs'), {{
    type: 'bar',
    data: {{
        labels: catLabels,
        datasets: [
            {{ label: 'ONDAS', data: {json.dumps(cat_totales_ondas)}, backgroundColor: ONDAS_BG, borderColor: ONDAS_C, borderWidth: 1 }},
            {{ label: 'El Sol', data: {json.dumps(cat_totales_elsol)}, backgroundColor: ELSOL_BG, borderColor: ELSOL_C, borderWidth: 1 }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{
            title: {{ display: true, text: 'Frecuencias absolutas por categoría', font: {{ size: 14 }} }},
            legend: {{ labels: {{ font: {{ size: 12 }} }} }}
        }},
        scales: {{
            y: {{ ticks: {{ font: {{ size: 12 }}, autoSkip: false }} }},
            x: {{ ticks: {{ font: {{ size: 11 }} }} }}
        }}
    }}
}});

// Categorías relativas
new Chart(document.getElementById('chartCatRel'), {{
    type: 'bar',
    data: {{
        labels: catLabels,
        datasets: [
            {{ label: 'ONDAS (‱)', data: {json.dumps([round(x,1) for x in cat_rel_ondas])}, backgroundColor: ONDAS_BG, borderColor: ONDAS_C, borderWidth: 1 }},
            {{ label: 'El Sol (‱)', data: {json.dumps([round(x,1) for x in cat_rel_elsol])}, backgroundColor: ELSOL_BG, borderColor: ELSOL_C, borderWidth: 1 }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{
            title: {{ display: true, text: 'Frecuencias relativas (por 10.000 palabras)', font: {{ size: 14 }} }},
            legend: {{ labels: {{ font: {{ size: 12 }} }} }}
        }},
        scales: {{
            y: {{ ticks: {{ font: {{ size: 12 }}, autoSkip: false }} }},
            x: {{ ticks: {{ font: {{ size: 11 }} }} }}
        }}
    }}
}});

// Evolución global
new Chart(document.getElementById('chartEvolGlobal'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(todos_años)},
        datasets: [
            {{ label: 'ONDAS', data: {json.dumps(ondas_evol)}, borderColor: ONDAS_C, backgroundColor: 'rgba(128,0,32,0.1)', fill: true, tension: 0.3 }},
            {{ label: 'El Sol', data: {json.dumps(elsol_evol)}, borderColor: ELSOL_C, backgroundColor: 'rgba(26,82,118,0.1)', fill: true, tension: 0.3 }}
        ]
    }},
    options: {{ responsive: true, plugins: {{ title: {{ display: true, text: 'Evolución temporal: total léxico de escucha' }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

// Charts por categoría
{chart_scripts}
</script>
</body>
</html>"""

    return html


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("LÉXICO DE LA ESCUCHA: COMPARACIÓN ONDAS vs EL SOL")
    print("7 categorías semánticas · 84 lemas")
    print("=" * 60)

    print("\nCargando corpus...")
    arch_ondas = cargar_corpus(DIR_ONDAS, "ONDAS")
    arch_elsol = cargar_corpus(DIR_ELSOL, "El Sol")

    print("\nAnalizando ONDAS...")
    res_ondas = analizar_escucha_completo(arch_ondas, "ONDAS")

    print("\nAnalizando El Sol...")
    res_elsol = analizar_escucha_completo(arch_elsol, "El Sol")

    # Resumen
    print(f"\n{'='*60}")
    print(f"{'Categoría':<28} {'ONDAS':>8} {'El Sol':>8} {'ONDAS‱':>8} {'ElSol‱':>8}")
    print(f"{'-'*28} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for cat in CATEGORIAS:
        o = res_ondas['categorias'][cat]
        e = res_elsol['categorias'][cat]
        print(f"{cat:<28} {o['total']:>8,} {e['total']:>8,} {o['relativo']:>7.1f} {e['relativo']:>7.1f}")
    print(f"{'-'*28} {'-'*8} {'-'*8}")
    print(f"{'TOTAL':<28} {res_ondas['total_global']:>8,} {res_elsol['total_global']:>8,}")

    # JSON
    with open(SALIDA_JSON, 'w', encoding='utf-8') as f:
        json.dump({'ondas': res_ondas, 'el_sol': res_elsol}, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON: {SALIDA_JSON}")

    # HTML
    html = generar_html(res_ondas, res_elsol)
    with open(SALIDA_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  HTML: {SALIDA_HTML}")
    print("=" * 60)
