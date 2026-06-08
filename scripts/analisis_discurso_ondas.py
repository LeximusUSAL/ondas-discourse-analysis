#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS DE DISCURSO DEL CORPUS ONDAS (1925-1935)
==================================================
Procesamiento exhaustivo de 473 transcripciones de noticias musicales.

Análisis:
1. Porcentaje de artículos dedicados a ópera vs resto
2. Autores e intérpretes más citados en los textos
3. Léxico de la escucha musical (oír, escuchar, sentir, emociones)
4. Estadísticas generales del corpus

Proyecto LexiMus / MUSLYME - Universidad de Salamanca
"""

import os
import re
import json
import csv
from collections import Counter, defaultdict
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# Ajustar estas rutas a la ubicación local de los corpus y listados.
# ============================================================
CORPUS_DIR = "corpus/ONDAS_TXT"                                    # Transcripciones TXT del corpus ONDAS (1925-1935, 472 núms.)
CSV_IMAGENES = "datos/indice_imagenes_ondas_completo.csv"          # Índice de imágenes de la revista (catalogación)
OUTPUT_DIR = "salida"                                              # Carpeta de salida para HTML/JSON/listados generados

# Listados de referencia
LISTADO_CANTANTES = os.path.join(OUTPUT_DIR, "listado_cantantes_ondas.txt")
LISTADO_COMPOSITORES = os.path.join(OUTPUT_DIR, "listado_compositores_ondas.txt")
LISTADO_INTERPRETES = os.path.join(OUTPUT_DIR, "listado_interpretes_instrumentos_ondas.txt")
LISTADO_OPERAS = os.path.join(OUTPUT_DIR, "listado_operas_ondas.txt")


# ============================================================
# FUNCIONES DE CARGA
# ============================================================

def cargar_listado(filepath):
    """Carga un listado TXT y extrae los nombres."""
    nombres = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Líneas con formato "N. Nombre" o "N. Nombre - Instrumento"
            # Separar por " - " (con espacios) para no romper nombres como "Radio-París"
            match = re.match(r'^\d+\.\s+(.+?)(?:\s+-\s+.+)?$', line)
            if match:
                nombre = match.group(1).strip()
                # Excluir palabras genéricas que no son nombres de persona/agrupación
                if nombre.lower() in ('radio',):
                    continue
                nombres.append(nombre)
    return nombres


def cargar_operas(filepath):
    """Carga el listado de óperas."""
    operas = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            match = re.match(r'^\d+\.\s+(.+)$', line)
            if match:
                operas.append(match.group(1).strip())
    return operas


def cargar_corpus(corpus_dir):
    """Carga todos los archivos TXT del corpus. Devuelve lista de diccionarios."""
    archivos = []
    for filename in sorted(os.listdir(corpus_dir)):
        if not filename.endswith('.txt'):
            continue
        filepath = os.path.join(corpus_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            contenido = f.read()

        # Extraer fecha del nombre de archivo
        # Formatos: 1925_05_23_ONDAS.txt o 1925-08-30_ONDAS.txt
        date_match = re.match(r'(\d{4})[_-](\d{2})[_-](\d{2})', filename)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
        else:
            year, month, day = 0, 0, 0

        archivos.append({
            'filename': filename,
            'year': year,
            'month': month,
            'day': day,
            'contenido': contenido,
            'contenido_lower': contenido.lower(),
            'palabras': len(contenido.split()),
            'lineas': contenido.count('\n') + 1
        })
    return archivos


def cargar_csv_imagenes(csv_path):
    """Carga el CSV de imágenes."""
    registros = []
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) >= 4:
                registros.append({
                    'categoria': row[0].strip() if row[0] else '',
                    'fecha': row[1].strip() if row[1] else '',
                    'titulo': row[2].strip() if row[2] else '',
                    'nombres': row[3].strip() if len(row) > 3 and row[3] else '',
                    'profesion': row[4].strip() if len(row) > 4 and row[4] else '',
                    'obras': row[5].strip() if len(row) > 5 and row[5] else '',
                    'genero': row[6].strip() if len(row) > 6 and row[6] else '',
                    'origen': row[7].strip() if len(row) > 7 and row[7] else '',
                    'tipo_musica': row[8].strip() if len(row) > 8 and row[8] else '',
                })
    return registros


# ============================================================
# 1. ANÁLISIS DE ÓPERA vs RESTO
# ============================================================

def analizar_opera_vs_resto(archivos, operas):
    """
    Analiza el porcentaje de artículos/secciones dedicados a ópera.
    Detecta secciones dentro de cada archivo (delimitadas por ===).
    """
    # Términos de ópera ampliados
    terminos_opera = [
        'ópera', 'opera', 'óperas', 'operas',
        'soprano', 'sopranos', 'tenor', 'tenores',
        'barítono', 'baritono', 'barítonos', 'baritonos',
        'bajo', 'contralto', 'contraltos',
        'mezzosoprano', 'mezzo-soprano', 'mezzo',
        'bel canto', 'belcanto',
        'aria', 'arias', 'cavatina', 'cavatinas',
        'recitativo', 'recitativos',
        'acto primero', 'acto segundo', 'acto tercero',
        'libreto', 'libretos', 'libretista',
        'teatro real', 'liceo', 'gran teatro del liceo',
        'teatro de la ópera',
        'diva', 'divas', 'prima donna',
    ]

    # Nombres de óperas del listado oficial
    operas_lower = [o.lower() for o in operas]

    total_secciones = 0
    secciones_opera = 0
    archivos_con_opera = 0
    archivos_sin_opera = 0

    # Conteo por año
    opera_por_año = defaultdict(lambda: {'opera': 0, 'no_opera': 0, 'total': 0})

    # Detalle de cada archivo
    detalle_archivos = []

    for archivo in archivos:
        contenido = archivo['contenido']
        contenido_lower = archivo['contenido_lower']

        # Dividir en secciones (delimitadas por === SECCIÓN: ... === o similar)
        secciones = re.split(r'===+\s*', contenido)
        secciones = [s.strip() for s in secciones if s.strip() and len(s.strip()) > 50]

        if not secciones:
            secciones = [contenido]

        n_opera_en_archivo = 0
        n_total_en_archivo = len(secciones)

        for seccion in secciones:
            total_secciones += 1
            seccion_lower = seccion.lower()

            es_opera = False

            # Verificar si la sección menciona una ópera del listado
            for opera_name in operas_lower:
                if len(opera_name) > 3:
                    # Buscar como palabra completa para evitar falsos positivos
                    pattern = r'\b' + re.escape(opera_name) + r'\b'
                    if re.search(pattern, seccion_lower):
                        es_opera = True
                        break

            # Verificar términos operísticos (necesita al menos 2 coincidencias
            # o 1 mención directa de "ópera")
            if not es_opera:
                coincidencias_opera = 0
                for termino in terminos_opera:
                    if termino in seccion_lower:
                        if termino in ('ópera', 'opera', 'óperas', 'operas'):
                            es_opera = True
                            break
                        coincidencias_opera += 1
                if coincidencias_opera >= 3:
                    es_opera = True

            if es_opera:
                secciones_opera += 1
                n_opera_en_archivo += 1

        if n_opera_en_archivo > 0:
            archivos_con_opera += 1
        else:
            archivos_sin_opera += 1

        year = archivo['year']
        opera_por_año[year]['opera'] += n_opera_en_archivo
        opera_por_año[year]['no_opera'] += (n_total_en_archivo - n_opera_en_archivo)
        opera_por_año[year]['total'] += n_total_en_archivo

        detalle_archivos.append({
            'archivo': archivo['filename'],
            'year': year,
            'secciones_totales': n_total_en_archivo,
            'secciones_opera': n_opera_en_archivo,
        })

    # Contar menciones individuales de cada ópera en todo el corpus
    menciones_operas = Counter()
    texto_completo_lower = ' '.join(a['contenido_lower'] for a in archivos)
    for opera_name in operas:
        if len(opera_name) > 3:
            pattern = r'\b' + re.escape(opera_name.lower()) + r'\b'
            count = len(re.findall(pattern, texto_completo_lower))
            if count > 0:
                menciones_operas[opera_name] = count

    return {
        'total_archivos': len(archivos),
        'archivos_con_opera': archivos_con_opera,
        'archivos_sin_opera': archivos_sin_opera,
        'total_secciones': total_secciones,
        'secciones_opera': secciones_opera,
        'secciones_no_opera': total_secciones - secciones_opera,
        'porcentaje_secciones_opera': round(secciones_opera / total_secciones * 100, 2) if total_secciones > 0 else 0,
        'porcentaje_archivos_con_opera': round(archivos_con_opera / len(archivos) * 100, 2) if archivos else 0,
        'opera_por_año': dict(opera_por_año),
        'menciones_operas_individuales': menciones_operas.most_common(),
        'detalle_archivos': detalle_archivos,
    }


# ============================================================
# 2. AUTORES E INTÉRPRETES MÁS CITADOS
# ============================================================

# Variantes españolas de nombres de compositores extranjeros.
# En la prensa española de 1925-1935 los nombres de pila se traducían
# sistemáticamente al español.
VARIANTES_ESPAÑOLAS = {
    'johann sebastian bach': ['juan sebastián bach', 'juan sebastian bach',
                              'sebastián bach', 'sebastian bach',
                              'j. s. bach', 's. bach'],
    'johan christian bach': ['juan cristián bach', 'juan cristian bach',
                             'cristián bach', 'cristian bach',
                             'j. c. bach', 'c. bach'],
    'wolfgang amadeus mozart': ['wolfango amadeo mozart'],
    'ludwig van beethoven': ['ludovico van beethoven'],
    'ludwing van beethoven': ['ludovico van beethoven'],
    'georg friedrich händel': ['jorge federico haendel', 'jorge federico händel'],
    'christoph willibald gluck': ['cristóbal willibald gluck'],
    'carl maría von weber': ['carlos maría von weber', 'carlos maria von weber'],
    'felix mendelssohn': ['félix mendelssohn'],
    'frederic chopin': ['federico chopin'],
    'franz liszt': ['francisco liszt'],
    'franz schubert': ['francisco schubert'],
    'robert schumann': ['roberto schumann'],
    'johannes brahms': ['juan brahms'],
    'richard wagner': ['ricardo wagner'],
    'richard strauss': ['ricardo strauss'],
    'jean sibelius': ['juan sibelius'],
    'jean-philippe rameau': ['juan felipe rameau'],
    'claude debussy': ['claudio debussy'],
    'paul dukas': ['pablo dukas'],
    'igor stravinsky': ['ígor stravinsky'],
    'giacomo puccini': ['jaime puccini'],
    'giacomo meyerbeer': ['jaime meyerbeer'],
    'giuseppe verdi': ['josé verdi'],
    'gioachino rossini': ['joaquín rossini'],
    'gaetano donizetti': ['cayetano donizetti'],
    'georges bizet': ['jorge bizet'],
    'jules massenet': ['julio massenet'],
    'camile saint-saëns': ['camilo saint-saëns', 'camilo saint-saens'],
    'hector berlioz': ['héctor berlioz'],
    'edvard grieg': ['eduardo grieg'],
    'prior ilyich tchaikowsky': ['pedro ilich tchaikowsky', 'pedro tchaikowsky',
                                  'piotr tchaikowsky', 'tchaikovsky', 'tchaikowski'],
    'modest mussorgsky': ['modesto mussorgsky', 'modesto moussorgsky'],
    'rimsky korsakov': ['rimsky-korsakov', 'rimski-korsakov'],
    'antonín dvorack': ['antonio dvorack', 'antonio dvorak', 'dvorák'],
    'arnold schoenberg': ['arnoldo schoenberg'],
    'carl otto nicolai': ['carlos otto nicolai'],
    'marc-antoine charpentier': ['marco antonio charpentier'],
    'francois couperin': ['francisco couperin'],
    'joseph haydn': ['josé haydn'],
    'françois-adrien boieldieu': ['francisco adrián boieldieu'],
    'vincenzo bellini': ['vicente bellini'],
    'jacinto guerrero': ['maestro guerrero'],
}


def contar_menciones_nombre(nombre, texto_lower, solo_nombre_completo=False,
                            apellidos_compartidos=None):
    """Cuenta menciones de un nombre en el texto.

    Si solo_nombre_completo=True, solo busca el nombre completo (para cantantes
    y otros donde los apellidos solos generan falsos positivos).
    Si False, busca también por apellido cuando es suficientemente específico
    (para compositores famosos como Beethoven, Wagner, etc.).
    También busca variantes españolas del nombre (Juan Sebastián Bach, etc.).

    apellidos_compartidos: set de apellidos que comparten varios compositores
    del listado. Si el apellido del nombre está en este set, no se usa la
    búsqueda por apellido solo (porque no se puede desambiguar).
    """
    count = 0
    nombre_lower = nombre.lower()
    if apellidos_compartidos is None:
        apellidos_compartidos = set()

    # Buscar nombre completo siempre
    if len(nombre_lower) > 3:
        pattern = r'\b' + re.escape(nombre_lower) + r'\b'
        count += len(re.findall(pattern, texto_lower))

    # Buscar variantes españolas del nombre
    for variante in VARIANTES_ESPAÑOLAS.get(nombre_lower, []):
        pattern_var = r'\b' + re.escape(variante) + r'\b'
        count += len(re.findall(pattern_var, texto_lower))

    if solo_nombre_completo:
        return count

    # Para compositores: buscar también por apellido si es muy específico
    partes = nombre_lower.split()
    # Manejar nombres con comillas (apodos): "Niño de Chamberí"
    if '"' in nombre_lower:
        # Buscar el apodo
        apodo_match = re.search(r'"([^"]+)"', nombre_lower)
        if apodo_match:
            apodo = apodo_match.group(1)
            if len(apodo) > 4:
                pattern_apodo = r'\b' + re.escape(apodo) + r'\b'
                count = max(count, len(re.findall(pattern_apodo, texto_lower)))
        return count

    if len(partes) >= 2:
        apellido = partes[-1]

        # No usar apellido solo si lo comparten varios compositores
        if apellido in apellidos_compartidos:
            return count

        # Solo usar apellido para compositores/directores de fama mundial
        # con apellidos inequívocos (no españoles comunes)
        apellidos_excluidos = {
            'de', 'del', 'la', 'el', 'los', 'las', 'von', 'van', 'di',
            'fall',  # Leo Fall - "fall" es palabra inglesa
            'campo', 'forns', 'boito',
        }
        # Apellidos cortos (< 5 caracteres) que sí deben buscarse
        # porque identifican inequívocamente a un compositor
        apellidos_cortos_permitidos = {'raff'}
        permitido = (
            apellido not in apellidos_excluidos
            and (len(apellido) >= 5 or apellido in apellidos_cortos_permitidos)
        )
        if permitido:
            pattern_apellido = r'\b' + re.escape(apellido) + r'\b'
            count_apellido = len(re.findall(pattern_apellido, texto_lower))
            count = max(count, count_apellido)

    return count


def analizar_autores_interpretes(archivos, cantantes, compositores, interpretes):
    """Cuenta menciones de cada persona en todo el corpus."""
    texto_completo = ' '.join(a['contenido_lower'] for a in archivos)

    # Detectar apellidos compartidos entre compositores
    from collections import Counter as _Counter
    _apellidos = []
    for c in compositores:
        partes = c.lower().split()
        if len(partes) >= 2:
            _apellidos.append(partes[-1])
    apellidos_compartidos = {a for a, n in _Counter(_apellidos).items() if n > 1}

    # Compositores: permitir búsqueda por apellido (Beethoven, Wagner, etc.)
    # excepto cuando el apellido lo comparten varios compositores del listado
    menciones_compositores = {}
    for comp in compositores:
        n = contar_menciones_nombre(comp, texto_completo, solo_nombre_completo=False,
                                    apellidos_compartidos=apellidos_compartidos)
        if n > 0:
            menciones_compositores[comp] = n

    # Cantantes: solo nombre completo (apellidos como Martínez, García causan ruido)
    menciones_cantantes = {}
    for cant in cantantes:
        n = contar_menciones_nombre(cant, texto_completo, solo_nombre_completo=True)
        if n > 0:
            menciones_cantantes[cant] = n

    # Intérpretes: solo nombre completo por las mismas razones
    menciones_interpretes = {}
    for interp in interpretes:
        n = contar_menciones_nombre(interp, texto_completo, solo_nombre_completo=True)
        if n > 0:
            menciones_interpretes[interp] = n

    # Sexteto de Unión Radio: búsqueda específica con dos variantes
    # ("sexteto de unión radio" + "nuestro sexteto") para evitar
    # mezclar con otros usos genéricos de "sexteto"
    n_sexteto = len(re.findall(r'\bsexteto de unión radio\b', texto_completo))
    n_sexteto += len(re.findall(r'\bnuestro sexteto\b', texto_completo))
    if n_sexteto > 0:
        menciones_interpretes['Sexteto de Unión Radio'] = n_sexteto

    # Evolución temporal de los más mencionados
    top_compositores = sorted(menciones_compositores.items(), key=lambda x: x[1], reverse=True)[:20]
    top_cantantes = sorted(menciones_cantantes.items(), key=lambda x: x[1], reverse=True)[:20]
    top_interpretes = sorted(menciones_interpretes.items(), key=lambda x: x[1], reverse=True)[:20]

    # Evolución por año de los top 10 compositores
    evolucion_compositores = {}
    for nombre, _ in top_compositores[:10]:
        evolucion_compositores[nombre] = {}
        for archivo in archivos:
            year = archivo['year']
            n = contar_menciones_nombre(nombre, archivo['contenido_lower'])
            if year not in evolucion_compositores[nombre]:
                evolucion_compositores[nombre][year] = 0
            evolucion_compositores[nombre][year] += n

    return {
        'compositores': {
            'total_con_menciones': len(menciones_compositores),
            'total_listado': len(compositores),
            'ranking': sorted(menciones_compositores.items(), key=lambda x: x[1], reverse=True),
        },
        'cantantes': {
            'total_con_menciones': len(menciones_cantantes),
            'total_listado': len(cantantes),
            'ranking': sorted(menciones_cantantes.items(), key=lambda x: x[1], reverse=True),
        },
        'interpretes': {
            'total_con_menciones': len(menciones_interpretes),
            'total_listado': len(interpretes),
            'ranking': sorted(menciones_interpretes.items(), key=lambda x: x[1], reverse=True),
        },
        'evolucion_compositores_por_año': evolucion_compositores,
    }


# ============================================================
# 3. LÉXICO DE LA ESCUCHA MUSICAL
# ============================================================

def analizar_lexico_escucha(archivos):
    """
    Analiza vocabulario relacionado con la escucha, la audición,
    las emociones y la percepción musical.
    """
    # Categorías semánticas del léxico de escucha
    # Estructura: {categoría: {lema: [variantes flexivas]}}
    # Se agrupan singular/plural, masculino/femenino y formas verbales bajo un mismo lema
    categorias_escucha = {
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

    # Contar cada lema (sumando todas sus variantes) en todo el corpus
    resultados_por_categoria = {}
    resultados_globales = Counter()
    resultados_por_año = defaultdict(lambda: defaultdict(int))

    for cat_nombre, lemas in categorias_escucha.items():
        conteo_cat = Counter()
        for lema, variantes in lemas.items():
            total = 0
            for archivo in archivos:
                for variante in variantes:
                    pattern = r'\b' + re.escape(variante) + r'\b'
                    n = len(re.findall(pattern, archivo['contenido_lower']))
                    total += n
                    if n > 0:
                        resultados_por_año[archivo['year']][cat_nombre] += n
            if total > 0:
                conteo_cat[lema] = total
                resultados_globales[lema] = total

        resultados_por_categoria[cat_nombre] = {
            'total_menciones': sum(conteo_cat.values()),
            'terminos_encontrados': len(conteo_cat),
            'detalle': conteo_cat.most_common(),
        }

    # Concordancias: extraer contexto de uso para términos clave
    terminos_concordancia = ['escuchar', 'escuchando', 'oyente', 'oyentes',
                             'radioyente', 'radioyentes', 'audición', 'emoción',
                             'sentir', 'oír']
    concordancias = defaultdict(list)
    for archivo in archivos:
        for termino in terminos_concordancia:
            pattern = r'(.{0,80}\b' + re.escape(termino) + r'\b.{0,80})'
            matches = re.findall(pattern, archivo['contenido_lower'])
            for m in matches[:5]:  # Máximo 5 por archivo para no saturar
                concordancias[termino].append({
                    'archivo': archivo['filename'],
                    'contexto': m.strip().replace('\n', ' ')
                })

    return {
        'por_categoria': resultados_por_categoria,
        'total_global': sum(v['total_menciones'] for v in resultados_por_categoria.values()),
        'top_50_terminos': resultados_globales.most_common(50),
        'evolucion_por_año': {str(k): dict(v) for k, v in sorted(resultados_por_año.items())},
        'concordancias': {k: v[:20] for k, v in concordancias.items()},  # 20 ejemplos por término
    }


# ============================================================
# 4. ESTADÍSTICAS GENERALES DEL CORPUS
# ============================================================

def estadisticas_generales(archivos, csv_registros):
    """Genera estadísticas descriptivas completas del corpus."""

    total_palabras = sum(a['palabras'] for a in archivos)
    total_lineas = sum(a['lineas'] for a in archivos)

    # Distribución por año
    por_año = defaultdict(lambda: {'archivos': 0, 'palabras': 0})
    for a in archivos:
        por_año[a['year']]['archivos'] += 1
        por_año[a['year']]['palabras'] += a['palabras']

    # Géneros musicales mencionados
    generos = {
        'ópera': ['ópera', 'opera', 'óperas', 'operas', 'operístico', 'operística'],
        'zarzuela': ['zarzuela', 'zarzuelas', 'género chico', 'género grande'],
        'música sinfónica': ['sinfonía', 'sinfónica', 'sinfónico', 'orquesta sinfónica', 'orquesta filarmónica'],
        'música de cámara': ['cuarteto', 'trío', 'quinteto', 'sexteto', 'música de cámara'],
        'canción/cuplé': ['canción', 'canciones', 'cuplé', 'cuplés', 'cupletista', 'cancionista'],
        'flamenco': ['flamenco', 'flamenca', 'cante', 'cantaor', 'cantaora', 'jondo'],
        'jazz': ['jazz', 'jazz-band', 'jazzband', 'fox-trot', 'foxtrot', 'charleston', 'swing'],
        'música coral': ['coral', 'coro', 'coros', 'orfeón', 'masa coral'],
        'música religiosa': ['misa', 'réquiem', 'requiem', 'sacro', 'sacra', 'liturgia', 'litúrgica'],
        'ballet/danza': ['ballet', 'danza', 'danzas', 'bailarina', 'bailarín', 'baile', 'bailes'],
        'música popular': ['popular', 'populares', 'folklore', 'folclore', 'folklórica'],
        'opereta': ['opereta', 'operetas'],
    }

    menciones_generos = {}
    texto_completo = ' '.join(a['contenido_lower'] for a in archivos)
    for genero, terminos in generos.items():
        total = 0
        for t in terminos:
            pattern = r'\b' + re.escape(t) + r'\b'
            total += len(re.findall(pattern, texto_completo))
        menciones_generos[genero] = total

    # Géneros por año
    generos_por_año = defaultdict(lambda: defaultdict(int))
    for archivo in archivos:
        for genero, terminos in generos.items():
            for t in terminos:
                pattern = r'\b' + re.escape(t) + r'\b'
                n = len(re.findall(pattern, archivo['contenido_lower']))
                if n > 0:
                    generos_por_año[archivo['year']][genero] += n

    # Análisis del CSV de imágenes
    categorias_img = Counter()
    genero_img = Counter()
    origen_img = Counter()
    tipo_musica_img = Counter()
    for reg in csv_registros:
        if reg['categoria']:
            categorias_img[reg['categoria']] += 1
        if reg['genero']:
            genero_img[reg['genero']] += 1
        if reg['origen']:
            origen_img[reg['origen']] += 1
        if reg['tipo_musica']:
            tipo_musica_img[reg['tipo_musica']] += 1

    # Instrumentos mencionados en los textos
    instrumentos = {
        'piano': ['piano', 'pianos', 'pianista', 'pianistas', 'pianola'],
        'violín': ['violín', 'violin', 'violines', 'violinista', 'violinistas'],
        'violonchelo': ['violonchelo', 'violoncello', 'chelo', 'chelista'],
        'guitarra': ['guitarra', 'guitarras', 'guitarrista', 'guitarristas'],
        'órgano': ['órgano', 'organo', 'organista'],
        'arpa': ['arpa', 'arpas', 'arpista'],
        'flauta': ['flauta', 'flautas', 'flautista'],
        'clarinete': ['clarinete', 'clarinetes', 'clarinetista'],
        'oboe': ['oboe', 'oboes', 'oboísta'],
        'trompeta': ['trompeta', 'trompetas', 'trompetista'],
        'saxofón': ['saxofón', 'saxofon', 'saxo', 'saxofonista'],
        'batería': ['batería', 'bateria', 'baterista'],
        'contrabajo': ['contrabajo', 'contrabajos', 'contrabajista'],
        'bandurria': ['bandurria', 'bandurrias'],
        'laúd': ['laúd', 'laud', 'laudista'],
        'acordeón': ['acordeón', 'acordeon', 'acordeonista'],
        'bandoneón': ['bandoneón', 'bandoneon'],
        'gaita': ['gaita', 'gaitas', 'gaitero'],
        'viola': ['viola', 'violas', 'violista'],
        'fagot': ['fagot', 'fagotes'],
        'trompa': ['trompa', 'trompas'],
        'trombón': ['trombón', 'trombon', 'trombones'],
        'tuba': ['tuba', 'tubas'],
        'tímpani': ['tímpani', 'timpani', 'timbal', 'timbales'],
        'castañuelas': ['castañuela', 'castañuelas'],
        'pandereta': ['pandereta', 'panderetas'],
    }

    menciones_instrumentos = {}
    for inst, terminos in instrumentos.items():
        total = 0
        for t in terminos:
            pattern = r'\b' + re.escape(t) + r'\b'
            total += len(re.findall(pattern, texto_completo))
        if total > 0:
            menciones_instrumentos[inst] = total

    # Espacios y lugares musicales
    espacios = {
        'teatro': ['teatro', 'teatros'],
        'conservatorio': ['conservatorio', 'conservatorios'],
        'estudio': ['estudio', 'estudios'],
        'sala': ['sala', 'salas'],
        'salón': ['salón', 'salon', 'salones'],
        'iglesia': ['iglesia', 'iglesias', 'catedral', 'catedrales'],
        'casino': ['casino', 'casinos'],
        'café': ['café', 'cafés'],
        'ateneo': ['ateneo', 'ateneos'],
    }

    menciones_espacios = {}
    for esp, terminos in espacios.items():
        total = 0
        for t in terminos:
            pattern = r'\b' + re.escape(t) + r'\b'
            total += len(re.findall(pattern, texto_completo))
        if total > 0:
            menciones_espacios[esp] = total

    return {
        'corpus': {
            'total_archivos': len(archivos),
            'total_palabras': total_palabras,
            'total_lineas': total_lineas,
            'media_palabras_por_archivo': round(total_palabras / len(archivos), 1) if archivos else 0,
            'rango_temporal': f"{min(a['year'] for a in archivos if a['year'] > 0)}-{max(a['year'] for a in archivos)}",
        },
        'distribucion_por_año': {str(k): v for k, v in sorted(por_año.items())},
        'generos_musicales': sorted(menciones_generos.items(), key=lambda x: x[1], reverse=True),
        'generos_por_año': {str(k): dict(v) for k, v in sorted(generos_por_año.items())},
        'instrumentos': sorted(menciones_instrumentos.items(), key=lambda x: x[1], reverse=True),
        'espacios_musicales': sorted(menciones_espacios.items(), key=lambda x: x[1], reverse=True),
        'imagenes': {
            'total_registros': len(csv_registros),
            'por_categoria': categorias_img.most_common(),
            'por_genero_HM': genero_img.most_common(),
            'por_origen': origen_img.most_common(),
            'por_tipo_musica': tipo_musica_img.most_common(),
        },
    }


# ============================================================
# 5. ANÁLISIS ADICIONAL: NACIONALIDADES Y GEOGRAFÍA
# ============================================================

def analizar_geografia(archivos):
    """Analiza menciones geográficas en el corpus."""
    lugares = {
        'Madrid': ['madrid', 'madrileño', 'madrileña', 'madrileños'],
        'Barcelona': ['barcelona', 'barcelonés', 'barcelonesa'],
        'Bilbao': ['bilbao', 'bilbaíno', 'bilbaína'],
        'Sevilla': ['sevilla', 'sevillano', 'sevillana'],
        'Valencia': ['valencia', 'valenciano', 'valenciana'],
        'San Sebastián': ['san sebastián', 'san sebastian', 'donostiarra'],
        'París': ['parís', 'paris', 'parisino', 'parisina', 'parisiense'],
        'Viena': ['viena', 'vienés', 'vienesa'],
        'Berlín': ['berlín', 'berlin', 'berlinés', 'berlinesa'],
        'Londres': ['londres', 'londinense'],
        'Roma': ['roma', 'romano', 'romana'],
        'Milán': ['milán', 'milan', 'milanés', 'milanesa'],
        'Nueva York': ['nueva york', 'new york', 'neoyorquino'],
        'Buenos Aires': ['buenos aires', 'porteño', 'porteña'],
        'La Habana': ['habana'],
        'Italia': ['italia', 'italiano', 'italiana', 'italianos'],
        'Alemania': ['alemania', 'alemán', 'alemana', 'alemanes', 'germánico', 'germánica'],
        'Francia': ['francia', 'francés', 'francesa', 'franceses'],
        'Rusia': ['rusia', 'ruso', 'rusa', 'rusos'],
        'España': ['españa', 'español', 'española', 'españoles', 'españolas'],
        'Estados Unidos': ['estados unidos', 'norteamericano', 'norteamericana', 'americano'],
        'Austria': ['austria', 'austríaco', 'austriaca'],
        'Hungría': ['hungría', 'hungria', 'húngaro', 'húngara'],
        'Cuba': ['cuba', 'cubano', 'cubana'],
        'México': ['méxico', 'mexico', 'mexicano', 'mexicana'],
        'Argentina': ['argentina', 'argentino'],
    }

    texto_completo = ' '.join(a['contenido_lower'] for a in archivos)
    menciones = {}
    for lugar, terminos in lugares.items():
        total = 0
        for t in terminos:
            pattern = r'\b' + re.escape(t) + r'\b'
            total += len(re.findall(pattern, texto_completo))
        if total > 0:
            menciones[lugar] = total

    return sorted(menciones.items(), key=lambda x: x[1], reverse=True)


# ============================================================
# GENERADOR DE HTML CON GRÁFICOS
# ============================================================

def generar_html_resultados(resultados, output_path):
    """Genera un informe HTML interactivo con Chart.js."""

    opera = resultados['opera']
    personas = resultados['personas']
    escucha = resultados['escucha']
    stats = resultados['estadisticas']
    geo = resultados['geografia']

    # Preparar datos para gráficos
    # Opera por año
    años_opera = sorted([k for k in opera['opera_por_año'].keys() if k > 0])
    pct_opera_año = []
    for y in años_opera:
        d = opera['opera_por_año'][y]
        pct = round(d['opera'] / d['total'] * 100, 1) if d['total'] > 0 else 0
        pct_opera_año.append(pct)

    # Top 20 compositores
    top20_comp = personas['compositores']['ranking'][:20]
    comp_nombres = [c[0] for c in top20_comp]
    comp_valores = [c[1] for c in top20_comp]

    # Top 20 cantantes
    top20_cant = personas['cantantes']['ranking'][:20]
    cant_nombres = [c[0] for c in top20_cant]
    cant_valores = [c[1] for c in top20_cant]

    # Top 20 intérpretes
    top20_interp = personas['interpretes']['ranking'][:20]
    interp_nombres = [c[0] for c in top20_interp]
    interp_valores = [c[1] for c in top20_interp]

    # Óperas más mencionadas
    top_operas = opera['menciones_operas_individuales'][:20]
    opera_nombres = [o[0] for o in top_operas]
    opera_valores = [o[1] for o in top_operas]

    # Categorías de escucha
    cat_escucha = [(k, v['total_menciones']) for k, v in escucha['por_categoria'].items()]
    cat_escucha.sort(key=lambda x: x[1], reverse=True)
    cat_nombres = [c[0] for c in cat_escucha]
    cat_valores = [c[1] for c in cat_escucha]

    # Géneros musicales
    gen_nombres = [g[0] for g in stats['generos_musicales']]
    gen_valores = [g[1] for g in stats['generos_musicales']]

    # Instrumentos
    inst_nombres = [i[0] for i in stats['instrumentos'][:15]]
    inst_valores = [i[1] for i in stats['instrumentos'][:15]]

    # Distribución por año
    años_dist = sorted([k for k in stats['distribucion_por_año'].keys() if k != '0'])
    arch_por_año = [stats['distribucion_por_año'][y]['archivos'] for y in años_dist]
    pal_por_año = [stats['distribucion_por_año'][y]['palabras'] for y in años_dist]

    # Escucha por año
    años_escucha = sorted(escucha['evolucion_por_año'].keys())
    evol_escucha_data = {}
    for cat in cat_nombres:
        evol_escucha_data[cat] = [escucha['evolucion_por_año'].get(y, {}).get(cat, 0) for y in años_escucha]

    # Geografía
    geo_nombres = [g[0] for g in geo[:20]]
    geo_valores = [g[1] for g in geo[:20]]

    # Espacios
    esp_nombres = [e[0] for e in stats['espacios_musicales']]
    esp_valores = [e[1] for e in stats['espacios_musicales']]

    # Evolución géneros por año
    años_gen = sorted([k for k in stats['generos_por_año'].keys() if k != '0'])
    generos_clave = ['ópera', 'zarzuela', 'música sinfónica', 'jazz', 'flamenco', 'canción/cuplé']
    evol_generos = {}
    for g in generos_clave:
        evol_generos[g] = [stats['generos_por_año'].get(y, {}).get(g, 0) for y in años_gen]

    # Top 50 términos de escucha
    top50_esc = escucha['top_50_terminos']
    top50_nombres = [t[0] for t in top50_esc]
    top50_valores = [t[1] for t in top50_esc]

    # Concordancias
    concordancias_html = ""
    for termino, ejemplos in escucha['concordancias'].items():
        concordancias_html += f'<h4 style="color:#800020; margin-top:20px;">«{termino}» ({len(ejemplos)} ejemplos)</h4>\n'
        concordancias_html += '<ul style="font-size:0.9em; font-family: Crimson Text, serif;">\n'
        for ej in ejemplos[:10]:
            ctx = ej['contexto'].replace(termino, f'<strong style="color:#800020">{termino}</strong>')
            concordancias_html += f'  <li><em>{ej["archivo"]}</em>: ...{ctx}...</li>\n'
        concordancias_html += '</ul>\n'

    colors_7 = "['#800020','#1a1a2e','#2d6a4f','#d4a373','#457b9d','#e76f51','#6d6875']"
    colors_12 = "['#800020','#1a1a2e','#2d6a4f','#d4a373','#457b9d','#e76f51','#6d6875','#264653','#e9c46a','#f4a261','#2a9d8f','#023047']"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Discurso - Corpus ONDAS (1925-1935)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;600;700&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Crimson Text', serif; background: #faf9f6; color: #1a1a1a; }}
        .header {{
            background: #1a1a2e; color: white; text-align: center; padding: 50px 20px;
        }}
        .header h1 {{ font-family: 'EB Garamond', serif; font-size: 2.8rem; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2rem; opacity: 0.8; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 30px 20px; }}
        .section {{
            background: white; margin: 30px 0; padding: 35px;
            border-radius: 12px; box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }}
        .section h2 {{
            font-family: 'EB Garamond', serif; font-size: 1.8rem;
            color: #800020; margin-bottom: 20px;
            border-bottom: 2px solid #800020; padding-bottom: 10px;
        }}
        .section h3 {{
            font-family: 'EB Garamond', serif; font-size: 1.4rem;
            color: #1a1a2e; margin: 20px 0 10px;
        }}
        .stat-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f5f0; padding: 20px; border-radius: 8px;
            text-align: center; border-left: 4px solid #800020;
        }}
        .stat-card .number {{
            font-family: 'EB Garamond', serif; font-size: 2.5rem;
            color: #800020; font-weight: 700;
        }}
        .stat-card .label {{ font-size: 0.95rem; color: #666; margin-top: 5px; }}
        .chart-container {{ position: relative; height: 400px; margin: 20px 0; }}
        .chart-container-tall {{ position: relative; height: 600px; margin: 20px 0; }}
        .chart-container-wide {{ position: relative; height: 500px; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.95rem; }}
        th {{ background: #1a1a2e; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #eee; }}
        tr:nth-child(even) {{ background: #f8f5f0; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
        .highlight {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0;
                      border-left: 4px solid #d4a373; font-style: italic; }}
        .nav-toc {{
            position: sticky; top: 0; background: white; z-index: 100;
            padding: 15px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;
        }}
        .nav-toc a {{
            color: #800020; text-decoration: none; padding: 5px 15px;
            border: 1px solid #800020; border-radius: 20px; font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .nav-toc a:hover {{ background: #800020; color: white; }}
        @media (max-width: 768px) {{
            .two-col {{ grid-template-columns: 1fr; }}
            .header h1 {{ font-size: 2rem; }}
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>Análisis de Discurso</h1>
    <p>Corpus ONDAS · Madrid · 1925-1935</p>
    <p style="margin-top:10px; font-size:0.9rem; opacity:0.6;">Proyecto LexiMus · MUSLYME · Universidad de Salamanca · 2026</p>
</div>

<nav class="nav-toc">
    <a href="#corpus">Corpus</a>
    <a href="#opera">Ópera</a>
    <a href="#compositores">Compositores</a>
    <a href="#cantantes">Cantantes</a>
    <a href="#interpretes">Intérpretes</a>
    <a href="#generos">Géneros</a>
    <a href="#instrumentos">Instrumentos</a>
    <a href="#escucha">Léxico de escucha</a>
    <a href="#concordancias">Concordancias</a>
    <a href="#geografia">Geografía</a>
</nav>

<div class="container">

<!-- SECCIÓN: CORPUS -->
<section class="section" id="corpus">
    <h2>1. El corpus textual</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="number">{stats['corpus']['total_archivos']}</div>
            <div class="label">Números analizados</div>
        </div>
        <div class="stat-card">
            <div class="number">{stats['corpus']['total_palabras']:,}</div>
            <div class="label">Palabras totales</div>
        </div>
        <div class="stat-card">
            <div class="number">{stats['corpus']['media_palabras_por_archivo']:,.0f}</div>
            <div class="label">Media de palabras/número</div>
        </div>
        <div class="stat-card">
            <div class="number">{stats['corpus']['rango_temporal']}</div>
            <div class="label">Período</div>
        </div>
    </div>
    <div class="two-col">
        <div class="chart-container">
            <canvas id="chartArchivosAño"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="chartPalabrasAño"></canvas>
        </div>
    </div>
</section>

<!-- SECCIÓN: ÓPERA -->
<section class="section" id="opera">
    <h2>2. Ópera en el corpus</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="number">{opera['porcentaje_secciones_opera']}%</div>
            <div class="label">Secciones con contenido operístico</div>
        </div>
        <div class="stat-card">
            <div class="number">{opera['secciones_opera']}</div>
            <div class="label">Secciones sobre ópera</div>
        </div>
        <div class="stat-card">
            <div class="number">{opera['secciones_no_opera']}</div>
            <div class="label">Secciones sin ópera</div>
        </div>
        <div class="stat-card">
            <div class="number">{opera['porcentaje_archivos_con_opera']}%</div>
            <div class="label">Números con alguna referencia a ópera</div>
        </div>
    </div>

    <div class="two-col">
        <div>
            <div class="chart-container">
                <canvas id="chartOperaPie"></canvas>
            </div>
        </div>
        <div>
            <div class="chart-container">
                <canvas id="chartOperaAño"></canvas>
            </div>
        </div>
    </div>

    <h3>Óperas más mencionadas en los textos</h3>
    <div class="chart-container-tall">
        <canvas id="chartOperasRanking"></canvas>
    </div>

    <table>
        <tr><th>#</th><th>Ópera</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{i+1}</td><td>{o[0]}</td><td>{o[1]}</td></tr>' for i, o in enumerate(opera['menciones_operas_individuales'][:30]))}
    </table>
</section>

<!-- SECCIÓN: COMPOSITORES -->
<section class="section" id="compositores">
    <h2>3. Compositores más citados</h2>
    <p>{personas['compositores']['total_con_menciones']} compositores del listado de {personas['compositores']['total_listado']} aparecen mencionados en los textos.</p>
    <div class="chart-container-tall">
        <canvas id="chartCompositores"></canvas>
    </div>
    <table>
        <tr><th>#</th><th>Compositor</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{i+1}</td><td>{c[0]}</td><td>{c[1]}</td></tr>' for i, c in enumerate(personas['compositores']['ranking'][:40]))}
    </table>
</section>

<!-- SECCIÓN: CANTANTES -->
<section class="section" id="cantantes">
    <h2>4. Cantantes más citados</h2>
    <p>{personas['cantantes']['total_con_menciones']} cantantes del listado de {personas['cantantes']['total_listado']} aparecen mencionados en los textos.</p>
    <div class="chart-container-tall">
        <canvas id="chartCantantes"></canvas>
    </div>
    <table>
        <tr><th>#</th><th>Cantante</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{i+1}</td><td>{c[0]}</td><td>{c[1]}</td></tr>' for i, c in enumerate(personas['cantantes']['ranking'][:40]))}
    </table>
</section>

<!-- SECCIÓN: INTÉRPRETES -->
<section class="section" id="interpretes">
    <h2>5. Otros intérpretes y protagonistas más citados</h2>
    <p>{personas['interpretes']['total_con_menciones']} intérpretes del listado de {personas['interpretes']['total_listado']} aparecen mencionados en los textos.</p>
    <div class="chart-container-tall">
        <canvas id="chartInterpretes"></canvas>
    </div>
    <table>
        <tr><th>#</th><th>Intérprete</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{i+1}</td><td>{c[0]}</td><td>{c[1]}</td></tr>' for i, c in enumerate(personas['interpretes']['ranking'][:40]))}
    </table>
</section>

<!-- SECCIÓN: GÉNEROS -->
<section class="section" id="generos">
    <h2>6. Géneros musicales</h2>
    <div class="two-col">
        <div class="chart-container">
            <canvas id="chartGeneros"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="chartGenerosEvol"></canvas>
        </div>
    </div>
    <table>
        <tr><th>#</th><th>Género</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{i+1}</td><td>{g[0]}</td><td>{g[1]}</td></tr>' for i, g in enumerate(stats['generos_musicales']))}
    </table>
</section>

<!-- SECCIÓN: INSTRUMENTOS -->
<section class="section" id="instrumentos">
    <h2>7. Instrumentos musicales</h2>
    <div class="two-col">
        <div class="chart-container">
            <canvas id="chartInstrumentos"></canvas>
        </div>
        <div>
            <h3>Espacios musicales</h3>
            <div class="chart-container">
                <canvas id="chartEspacios"></canvas>
            </div>
        </div>
    </div>
</section>

<!-- SECCIÓN: ESCUCHA -->
<section class="section" id="escucha">
    <h2>8. Léxico de la escucha musical</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="number">{escucha['total_global']:,}</div>
            <div class="label">Total menciones léxico de escucha</div>
        </div>
    </div>

    <h3>Menciones por categoría semántica</h3>
    <div class="chart-container">
        <canvas id="chartEscuchaCat"></canvas>
    </div>

    <h3>Evolución temporal del léxico de escucha</h3>
    <div class="chart-container-wide">
        <canvas id="chartEscuchaEvol"></canvas>
    </div>

    <h3>50 lemas más frecuentes del léxico de escucha</h3>
    <div class="chart-container-tall">
        <canvas id="chartTop50Escucha"></canvas>
    </div>

    <!-- Detalle por categoría -->
    {"".join(f'''
    <h3>{cat}</h3>
    <p>Total: {datos["total_menciones"]:,} menciones · {datos["terminos_encontrados"]} lemas</p>
    <table>
        <tr><th>Lema</th><th>Frecuencia</th></tr>
        {"".join(f'<tr><td>{t[0]}</td><td>{t[1]:,}</td></tr>' for t in datos["detalle"][:15])}
    </table>
    ''' for cat, datos in escucha['por_categoria'].items())}
</section>

<!-- SECCIÓN: CONCORDANCIAS -->
<section class="section" id="concordancias">
    <h2>9. Concordancias: contextos de uso</h2>
    <p>Ejemplos textuales de cómo se emplean los términos de escucha en el corpus.</p>
    {concordancias_html}
</section>

<!-- SECCIÓN: GEOGRAFÍA -->
<section class="section" id="geografia">
    <h2>10. Geografía musical del corpus</h2>
    <div class="chart-container-tall">
        <canvas id="chartGeo"></canvas>
    </div>
    <table>
        <tr><th>Lugar/País</th><th>Menciones</th></tr>
        {"".join(f'<tr><td>{g[0]}</td><td>{g[1]:,}</td></tr>' for g in geo[:25])}
    </table>
</section>

</div>

<footer style="background:#1a1a2e; color:white; text-align:center; padding:30px; margin-top:40px;">
    <p style="font-family:'EB Garamond',serif; font-size:1.2rem;">Análisis de Discurso · Corpus ONDAS (1925-1935)</p>
    <p style="margin-top:10px; opacity:0.7;">Proyecto LexiMus · GTC MUSLYME · Universidad de Salamanca · 2026</p>
</footer>

<script>
// Colores consistentes
const colPrimario = '#800020';
const colSecundario = '#1a1a2e';
const colTerciario = '#2d6a4f';
const palette = {colors_12};

// CORPUS: archivos por año
new Chart(document.getElementById('chartArchivosAño'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(años_dist)},
        datasets: [{{ label: 'Números por año', data: {json.dumps(arch_por_año)},
            backgroundColor: colPrimario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Números analizados por año' }} }} }}
}});

// CORPUS: palabras por año
new Chart(document.getElementById('chartPalabrasAño'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(años_dist)},
        datasets: [{{ label: 'Palabras por año', data: {json.dumps(pal_por_año)},
            backgroundColor: colSecundario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Palabras por año' }} }} }}
}});

// ÓPERA: pie
new Chart(document.getElementById('chartOperaPie'), {{
    type: 'doughnut',
    data: {{
        labels: ['Secciones con ópera', 'Secciones sin ópera'],
        datasets: [{{ data: [{opera['secciones_opera']}, {opera['secciones_no_opera']}],
            backgroundColor: [colPrimario, '#ddd'] }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Proporción de ópera en el corpus' }} }} }}
}});

// ÓPERA: evolución por año
new Chart(document.getElementById('chartOperaAño'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(años_opera)},
        datasets: [{{ label: '% secciones ópera', data: {json.dumps(pct_opera_año)},
            borderColor: colPrimario, backgroundColor: 'rgba(128,0,32,0.1)', fill: true, tension: 0.3 }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Evolución del contenido operístico (%)' }} }},
        scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: '%' }} }} }} }}
}});

// ÓPERAS ranking
new Chart(document.getElementById('chartOperasRanking'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(opera_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(opera_valores)},
            backgroundColor: colPrimario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Óperas más mencionadas' }} }} }}
}});

// COMPOSITORES
new Chart(document.getElementById('chartCompositores'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(comp_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(comp_valores)},
            backgroundColor: colSecundario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Top 20 compositores más citados' }} }} }}
}});

// CANTANTES
new Chart(document.getElementById('chartCantantes'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(cant_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(cant_valores)},
            backgroundColor: colTerciario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Top 20 cantantes más citados' }} }} }}
}});

// INTÉRPRETES
new Chart(document.getElementById('chartInterpretes'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(interp_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(interp_valores)},
            backgroundColor: '#d4a373' }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Top 20 intérpretes más citados' }} }} }}
}});

// GÉNEROS
new Chart(document.getElementById('chartGeneros'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(gen_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(gen_valores)},
            backgroundColor: palette }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Géneros musicales' }}, legend: {{ display: false }} }} }}
}});

// GÉNEROS evolución
new Chart(document.getElementById('chartGenerosEvol'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(años_gen)},
        datasets: [
            {','.join(f'{{"label":"{g}","data":{json.dumps(evol_generos[g])},"borderColor":palette[{i}],"fill":false,"tension":0.3}}' for i, g in enumerate(generos_clave))}
        ]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Evolución de géneros musicales' }} }} }}
}});

// INSTRUMENTOS
new Chart(document.getElementById('chartInstrumentos'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(inst_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(inst_valores)},
            backgroundColor: colSecundario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Instrumentos más mencionados' }}, legend: {{ display: false }} }} }}
}});

// ESPACIOS
new Chart(document.getElementById('chartEspacios'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(esp_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(esp_valores)},
            backgroundColor: '#457b9d' }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Espacios musicales' }}, legend: {{ display: false }} }} }}
}});

// ESCUCHA: categorías
new Chart(document.getElementById('chartEscuchaCat'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(cat_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(cat_valores)},
            backgroundColor: palette }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Léxico de escucha por categoría semántica' }}, legend: {{ display: false }} }} }}
}});

// ESCUCHA: evolución temporal
new Chart(document.getElementById('chartEscuchaEvol'), {{
    type: 'line',
    data: {{
        labels: {json.dumps(años_escucha)},
        datasets: [
            {','.join(f'{{"label":"{cat}","data":{json.dumps(evol_escucha_data[cat])},"borderColor":palette[{i}],"fill":false,"tension":0.3}}' for i, cat in enumerate(cat_nombres))}
        ]
    }},
    options: {{ responsive: true, maintainAspectRatio: false,
        plugins: {{ title: {{ display: true, text: 'Evolución temporal del léxico de escucha' }} }} }}
}});

// TOP 50 ESCUCHA
new Chart(document.getElementById('chartTop50Escucha'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(top50_nombres)},
        datasets: [{{ label: 'Frecuencia', data: {json.dumps(top50_valores)},
            backgroundColor: colPrimario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: '50 términos de escucha más frecuentes' }}, legend: {{ display: false }} }} }}
}});

// GEOGRAFÍA
new Chart(document.getElementById('chartGeo'), {{
    type: 'bar',
    data: {{
        labels: {json.dumps(geo_nombres)},
        datasets: [{{ label: 'Menciones', data: {json.dumps(geo_valores)},
            backgroundColor: colSecundario }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, indexAxis: 'y',
        plugins: {{ title: {{ display: true, text: 'Geografía musical: lugares más mencionados' }}, legend: {{ display: false }} }} }}
}});
</script>

</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  HTML generado: {output_path}")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("ANÁLISIS DE DISCURSO - CORPUS ONDAS (1925-1935)")
    print("=" * 60)

    # 1. Cargar datos
    print("\n[1/7] Cargando corpus textual...")
    archivos = cargar_corpus(CORPUS_DIR)
    print(f"  {len(archivos)} archivos cargados")
    print(f"  {sum(a['palabras'] for a in archivos):,} palabras totales")

    print("\n[2/7] Cargando listados de referencia...")
    cantantes = cargar_listado(LISTADO_CANTANTES)
    compositores = cargar_listado(LISTADO_COMPOSITORES)
    interpretes = cargar_listado(LISTADO_INTERPRETES)
    operas = cargar_operas(LISTADO_OPERAS)
    print(f"  {len(cantantes)} cantantes, {len(compositores)} compositores, {len(interpretes)} intérpretes, {len(operas)} óperas")

    print("\n[3/7] Cargando CSV de imágenes...")
    csv_registros = cargar_csv_imagenes(CSV_IMAGENES)
    print(f"  {len(csv_registros)} registros de imágenes")

    # 2. Análisis de ópera
    print("\n[4/7] Analizando presencia de ópera...")
    res_opera = analizar_opera_vs_resto(archivos, operas)
    print(f"  {res_opera['secciones_opera']} secciones operísticas de {res_opera['total_secciones']} ({res_opera['porcentaje_secciones_opera']}%)")

    # 3. Análisis de personas
    print("\n[5/7] Contando menciones de compositores, cantantes e intérpretes...")
    res_personas = analizar_autores_interpretes(archivos, cantantes, compositores, interpretes)
    print(f"  Compositores con menciones: {res_personas['compositores']['total_con_menciones']}")
    print(f"  Cantantes con menciones: {res_personas['cantantes']['total_con_menciones']}")
    print(f"  Intérpretes con menciones: {res_personas['interpretes']['total_con_menciones']}")

    # 4. Léxico de escucha
    print("\n[6/7] Analizando léxico de escucha musical...")
    res_escucha = analizar_lexico_escucha(archivos)
    print(f"  {res_escucha['total_global']:,} menciones totales del léxico de escucha")

    # 5. Estadísticas generales
    print("\n[7/7] Generando estadísticas generales...")
    res_stats = estadisticas_generales(archivos, csv_registros)
    res_geo = analizar_geografia(archivos)

    # Compilar resultados
    resultados = {
        'opera': res_opera,
        'personas': res_personas,
        'escucha': res_escucha,
        'estadisticas': res_stats,
        'geografia': res_geo,
    }

    # Guardar JSON
    json_path = os.path.join(OUTPUT_DIR, "analisis_discurso_ondas.json")
    # Convertir Counter y otros objetos no serializables
    def convert(obj):
        if isinstance(obj, Counter):
            return dict(obj)
        if isinstance(obj, defaultdict):
            return dict(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=convert)
    print(f"\n  JSON guardado: {json_path}")

    # Guardar HTML
    html_path = os.path.join(OUTPUT_DIR, "analisis_discurso_ondas.html")
    generar_html_resultados(resultados, html_path)

    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    print(f"\nCorpus: {len(archivos)} números, {sum(a['palabras'] for a in archivos):,} palabras")
    print(f"\nÓPERA:")
    print(f"  Secciones con ópera: {res_opera['secciones_opera']}/{res_opera['total_secciones']} ({res_opera['porcentaje_secciones_opera']}%)")
    print(f"  Números con ópera: {res_opera['archivos_con_opera']}/{res_opera['total_archivos']} ({res_opera['porcentaje_archivos_con_opera']}%)")
    print(f"\nTOP 5 COMPOSITORES:")
    for i, (n, v) in enumerate(res_personas['compositores']['ranking'][:5]):
        print(f"  {i+1}. {n}: {v} menciones")
    print(f"\nTOP 5 CANTANTES:")
    for i, (n, v) in enumerate(res_personas['cantantes']['ranking'][:5]):
        print(f"  {i+1}. {n}: {v} menciones")
    print(f"\nTOP 5 ÓPERAS:")
    for i, (n, v) in enumerate(res_opera['menciones_operas_individuales'][:5]):
        print(f"  {i+1}. {n}: {v} menciones")
    print(f"\nLÉXICO DE ESCUCHA: {res_escucha['total_global']:,} menciones totales")
    for cat, datos in res_escucha['por_categoria'].items():
        print(f"  {cat}: {datos['total_menciones']:,}")

    print(f"\nArchivos generados:")
    print(f"  {json_path}")
    print(f"  {html_path}")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
