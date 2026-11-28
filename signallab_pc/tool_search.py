"""Rank public workflows and their entry points using the same index throughout the desktop."""

import re
from dataclasses import dataclass

from .tool_catalog import DETAILS_BY_KEY, ENTRIES, normalize
from .workflow_choices import variant_title


_TOKEN = re.compile(r'\b[a-z]\s*(?:\(\s*[knstzwω]\s*\)|\[\s*[knstzwω]\s*\])|[^\W_]+')
_GLUE = frozenset('a al con como de del el en la las los para por un una y calcular hago hallar necesito obtener puedo quiero sacar saco ver'.split())
_TERMS = {
    'algebraica': 'algebraico', 'algebraicas': 'algebraico', 'simbolica': 'algebraico', 'simbolico': 'algebraico',
    'analogica': 'analogico', 'analogicas': 'analogico', 'analogicos': 'analogico',
    'continua': 'continuo', 'continuas': 'continuo', 'continuos': 'continuo',
    'discreta': 'discreto', 'discretas': 'discreto', 'discretos': 'discreto',
    'inverso': 'inversa', 'inversas': 'inversa', 'numerica': 'numerico', 'numericas': 'numerico',
    'polos': 'polo', 'ceros': 'cero', 'ventanas': 'ventana', 'senales': 'senal',
    'espectros': 'espectro', 'coeficientes': 'coeficiente', 'muestras': 'muestra',
    'bandas': 'banda', 'tolerancias': 'tolerancia', 'filtros': 'filtro', 'sistemas': 'sistema',
    'transformadas': 'transformada', 'funciones': 'funcion', 'respuestas': 'respuesta',
    'exportacion': 'exportar', 'versus': 'vs', 'solucionar': 'resolver',
}


def tokens(text):
    parts = (part.replace(' ', '') for part in _TOKEN.findall(normalize(text)))
    return tuple(_TERMS.get(word, word) for word in parts if word not in _GLUE)


def match_words(query, words):
    return all(word in words or len(word) >= 3 and any(other.startswith(word) for other in words)
               for word in query)


def rank(query, titles, keywords=()):
    """An exact name beats an alias, which beats a match in descriptive text."""
    if not query:
        return None
    if query == titles[0]:
        return (0, 0, 0)
    if query in titles[1:]:
        return (1, 0, 0)
    # A single letter is a shortcut only when the name or alias explicitly opts in.
    if len(query) == 1 and len(query[0]) == 1:
        return None
    exact = set(query)
    for index, title in enumerate(titles):
        if exact == set(title):
            return (2, index != 0, 0)
    strong = [title for title in titles if match_words(query, title)]
    if strong:
        return min((3, sum(word not in title for word in exact), len(set(title) - exact)) for title in strong)
    names = set().union(*titles)
    words = names | set(keywords)
    if match_words(query, words):
        return (4, sum(word not in names for word in exact), sum(word not in words for word in exact))
    return None


ALIASES = {
    ('basic', 'generate'): ('generar señales', 'crear expresión', 'seno coseno escalón', 'importar señal MATLAB CSV MAT'),
    ('signal_editor', 0): ('editar datos', 'tabla de muestras', 'recortar señal', 'cambiar índice muestras'),
    ('window_signal', 0): ('crear ventana', 'ventana Hann Hanning Hamming Blackman Bartlett Kaiser rectangular'),
    ('basic', 'shift'): ('retardar secuencia', 'adelantar secuencia', 'corrimiento discreto'),
    ('time_transform', 1): ('retardar señal continua', 'adelantar señal continua', 'corrimiento temporal continuo'),
    ('basic', 'reverse'): ('reflejar secuencia', 'invertir tiempo discreto', 'x[-n]'),
    ('basic', 'parity'): ('componente simétrica discreta', 'descomponer par impar discreto'),
    ('time_transform', 4): ('componente simétrica continua', 'descomponer par impar continuo'),
    ('basic', 'measures'): ('energía de muestras', 'potencia de un registro', 'valor eficaz', 'RMS de muestras'),
    ('expression_measures', 'global'): ('energía de expresión', 'energía de un coseno', 'energía infinita', 'energía de todo el eje', 'energía total'),
    ('expression_measures', 'interval'): ('energía entre a y b', 'energía de señal acotada', 'integral de energía en intervalo'),
    ('expression_measures', 'periodic'): ('potencia de un coseno', 'potencia por período', 'potencia media periódica', 'energía por período'),
    ('signal_product', 0): ('enventanar señal', 'multiplicación de señales', 'aplicar ventana a x[n]'),
    ('basic', 'convolve'): ('convolución discreta', 'convolución de secuencias'),
    ('convolution_algebra', 0): ('integral de convolución', 'convolución simbólica'),
    ('dsp_extensions', 'blocks'): ('overlap add', 'overlap save', 'convolución FFT'),
    ('system_analysis', 0): ('Bode', 'función de transferencia', 'polos y ceros', 'diagrama de realización', 'sistema LTI',
                             'analizar H(s)', 'analizar H(z)', 'respuesta en frecuencia', 'retardo de grupo'),
    ('systems', 9): ('simular respuesta temporal', 'respuesta de estado cero', 'respuesta de entrada cero'),
    ('interconnection', 0): ('conectar bloques', 'cascada de sistemas', 'sistemas en paralelo', 'realimentación negativa'),
    ('course_tools', 'fir'): ('FIR Kaiser', 'FIR por bandas', 'FIR con tolerancias', 'diseñar pasabajos por tolerancias',
                              'diseñar pasabanda por tolerancias', 'diseño FIR por especificaciones'),
    ('course_tools', 'iir'): ('diseño digital Butterworth Chebyshev elíptico', 'IIR por bandas'),
    ('course_tools', 'analog'): ('diseño analógico Butterworth Chebyshev elíptico', 'IIR analógico', 'Bessel'),
    ('systems', 0): ('FIR por cortes', 'diseño FIR por longitud'),
    ('fir_window', 0): ('FIR h[n]', 'enventanar h[n]', 'ventana para respuesta al impulso propia', 'FIR respuesta al impulso propia'),
    ('systems', 6): ('diseño por polos y ceros', 'editar polos y ceros', 'dibujar raíces'),
    ('systems', 1): ('notch', 'biquad', 'filtro IIR de segundo orden'),
    ('systems', 2): ('filtro RC', 'pasa bajos RC', 'circuito resistencia capacitor'),
    ('frequency_filter', 0): ('filtro ideal', 'H por tramos', 'respuesta ideal por partes', 'filtro ideal pasabajos', 'filtro ideal pasabanda'),
    ('course_tools', 'phase'): ('fase mínima', 'fase lineal', 'paso todo', 'all pass', 'ajustar fase'),
    ('course_tools', 'convert'): ('bilineal', 'invarianza al impulso', 'de H(s) a H(z)',
                                  'pasar analógico a digital', 'discretizar filtro por ventana'),
    ('basic', 'dft'): ('FFT', 'transformada discreta de Fourier', 'DFT centrada', 'coeficientes FFT'),
    ('basic', 'idft'): ('IFFT', 'IDFT', 'antitransformada DFT', 'FFT inversa'),
    ('course_tools', 'fft'): ('FFT', 'resolución espectral', 'zero padding', 'relleno con ceros', 'FFT enventanada'),
    ('rf', 'spectral'): ('Chirp-Z', 'CZT', 'Zoom FFT'),
    ('fourier', 0): ('DFT vs DTFT', 'comparar DFT y DTFT', 'superponer DFT y DTFT', 'DTFT numérica'),
    ('dtft_symbolic', 0): ('DTFT directa simbólica', 'DTFT de una fórmula'),
    ('inverse_dtft', 0): ('IDTFT numérica', 'antitransformada DTFT numérica'),
    ('dtft_symbolic', 1): ('IDTFT', 'antitransformada DTFT', 'IDTFT simbólica'),
    ('fourier', 1): ('CTFT', 'CTFT numérica', 'espectro tiempo continuo'),
    ('fourier_symbolic', 0): ('CTFT simbólica', 'transformar una fórmula en t'),
    ('fourier_symbolic', 1): ('antitransformada Fourier continua', 'ICTFT simbólica'),
    ('fourier', 3): ('ICTFT', 'antitransformada Fourier numérica'),
    ('fourier', 4): ('coeficientes ak', 'coeficientes an bn', 'serie Fourier continua', 'serie trigonométrica'),
    ('fourier', 5): ('coeficientes Fourier discreta', 'serie Fourier discreta', 'DFS', 'DTFS'),
    ('course_tools', 'lines'): ('Parseval periódico', 'líneas de potencia Fourier', 'PSD de una señal periódica'),
    ('fourier', 6): ('densidad espectral de energía', 'ESD', 'energía en frecuencia'),
    ('fourier', 7): ('PSD', 'densidad espectral de potencia', 'Welch', 'periodograma'),
    ('course_tools', 'band'): ('picos del espectro', 'energía por banda', 'ancho de banda ocupado'),
    ('dsp_extensions', 'stft'): ('espectrograma', 'Fourier de tiempo corto', 'espectro en el tiempo'),
    ('sampling', 1): ('alias', 'frecuencia alias', 'frecuencia de Nyquist', 'submuestreo'),
    ('sampling', 3): ('interpolación sinc', 'reconstrucción sinc', 'reconstrucción D/A', 'retención de orden cero'),
    ('sampling', 2): ('decimar secuencia', 'diezmar secuencia', 'expandir secuencia', 'insertar ceros'),
    ('rational_resampling', 0): ('remuestreo', 'remuestrear con filtro', 'conversión de tasa antialias'),
    ('sampling', 4): ('cuantizar amplitud', 'ruido de cuantización', 'relación señal ruido SNR'),
    ('sampling', 5): ('punto fijo', 'Q15', 'punto flotante', 'desborde saturación redondeo'),
    ('transform_lab', 'z'): ('Z', 'transformada en Z', 'Z algebraica'),
    ('symbolic', 4): ('resolver EDO', 'ecuación diferencial', 'respuesta de una ecuación diferencial'),
    ('difference_equation', 0): ('resolver recurrencia', 'ecuación en diferencias', 'ecuación recursiva'),
}


@dataclass(frozen=True)
class Preset:
    title: str
    summary: str
    aliases: tuple[str, ...]
    trigger: tuple[str, ...]
    fields: tuple[tuple[str, int], ...]


PRESETS = {
    ('transform_lab', 'z'): (
        Preset('Transformada Z inversa', 'Obtener x[n] a partir de X(z) y su región de convergencia.',
               ('Z inversa', 'antitransformada Z', 'IZT', 'inversa de X(z)'), ('inversa', 'antitransformada', 'izt'), (('mode', 1),)),
        Preset('Transformada Z de una secuencia finita', 'Transformar muestras y conservar sus índices.',
               ('Z finita', 'Z de muestras', 'Z registro finito'), ('finita', 'finito', 'muestra'), (('mode', 0), ('direct_input', 1))),
        Preset('Transformada Z directa', 'Transformar una expresión de n con su soporte.',
               ('Z directa', 'Z algebraica directa'), ('directa',), (('mode', 0), ('direct_input', 0))),
    ),
    ('transform_lab', 'laplace'): (
        Preset('Transformada de Laplace inversa', 'Recuperar una expresión en t a partir de X(s).',
               ('Laplace inversa', 'antitransformada de Laplace', 'ILT', 'inversa de X(s)'),
               ('inversa', 'antitransformada', 'ilt'), (('mode', 1),)),
        Preset('Transformada de Laplace directa', 'Transformar x(t) e indicar la interpretación.',
               ('Laplace directa',), ('directa',), (('mode', 0),)),
    ),
    ('systems', 9): (
        Preset('Respuesta al escalón', 'Simular la salida ante un escalón unitario.',
               ('respuesta escalón', 'step response', 'escalón unitario', 'tiempo de subida', 'sobreimpulso',
                'tiempo de establecimiento', 'respuesta escalón H(s)', 'respuesta escalón H(z)'),
               ('escalon', 'step', 'subida', 'sobreimpulso', 'establecimiento'), (('stimulus', 0),)),
        Preset('Respuesta al impulso', 'Calcular h(t) o h[n] para una entrada impulso unitario.',
               ('respuesta impulso', 'impulse response', 'h[n] de un sistema', 'h(t) de un sistema'),
               ('impulso', 'impulse', 'h[n]', 'h(t)'), (('stimulus', 1),)),
    ),
}

_SYSTEM_DOMAINS = ((0, {'analogico', 'continuo', 'h(s)', 'x(t)'}), (1, {'digital', 'discreto', 'h(z)', 'x[n]'}))
_DOMAIN_TERMS = tuple(word for _, names in _SYSTEM_DOMAINS for word in names)
_SYSTEM_KEYS = {('systems', 9), ('system_analysis', 0), ('frequency_filter', 0)}


def option_settings(key, query):
    words = set(query)
    if key == ('transform_lab', 'laplace'):
        if 'bilateral' in words and 'unilateral' not in words:
            return (('interpretation', 1),)
        if 'unilateral' in words and 'bilateral' not in words:
            return (('interpretation', 0),)
    if key in _SYSTEM_KEYS:
        domains = [index for index, names in _SYSTEM_DOMAINS if words & names]
        if len(domains) == 1:
            index = domains[0]
            return (('domain', 1-index if key == ('frequency_filter', 0) else index),)
    return ()


@dataclass(frozen=True)
class ToolHit:
    key: tuple
    title: str
    summary: str
    area: str
    score: tuple
    settings: tuple = ()


_INDEX = []
for _entry in ENTRIES:
    for _key, _values in _entry['variants']:
        _detail = DETAILS_BY_KEY[_key]
        _aliases = tuple(tokens(alias) for alias in ALIASES.get(_key, ()))
        _menu_name = tokens(variant_title(_entry, _key))
        _search_names = (tokens(_detail['title']), *_aliases)
        if _menu_name:
            _search_names += (_menu_name,)
        _terms = tokens(' '.join((
            _entry['title'], _entry['section'], _detail['summary'], _detail['tags'],
            *_values, _entry.get('variant_tags', {}).get(_key, ''),
            _entry.get('model_tags', {}).get(_values[0] if _values else '', ''),
        )))
        if _key in _SYSTEM_KEYS:
            _terms += _DOMAIN_TERMS
        _INDEX.append((_entry, _key, _detail, _search_names, _terms))


def find_tools(text, *, area=None):
    query = tokens(text)
    if not query:
        return []
    hits = []
    for entry, key, detail, names, keywords in _INDEX:
        if area is not None and entry['area'] != area:
            continue
        options = option_settings(key, query)
        score = rank(query, names, keywords)
        best = ToolHit(key, detail['title'], detail['summary'], entry['area'], score, options) if score is not None else None
        for preset in PRESETS.get(key, ()):
            if not any(match_words((word,), preset.trigger) for word in query):
                continue
            titles = (tokens(preset.title), *(tokens(alias) for alias in preset.aliases))
            # A shortcut must match the task as well as its optional domain.
            extra = tokens(preset.summary) + _DOMAIN_TERMS
            if key[0] == 'transform_lab':
                extra = tokens(preset.summary) + ('bilateral', 'unilateral', 'algebraico', 'roc')
                if key[1] == 'z' and preset.fields == (('mode', 1),):
                    extra += ('muestra', 'finito', 'soporte', 'completo', 'racional', 'secuencia')
            score = rank(query, titles, extra)
            if score is not None and (best is None or score <= best.score):
                best = ToolHit(key, preset.title, preset.summary, entry['area'], score, options + preset.fields)
        if best is not None:
            suffix = ''
            if options and options[0][0] == 'interpretation':
                suffix = ' · Bilateral' if options[0][1] else ' · Unilateral'
            elif options and options[0][0] == 'domain':
                digital = options[0][1] == (0 if key == ('frequency_filter', 0) else 1)
                suffix = ' · H(z)' if digital else ' · H(s)'
            hits.append(ToolHit(best.key, best.title + suffix, best.summary, best.area, best.score, best.settings))
    return sorted(hits, key=lambda hit: hit.score)
