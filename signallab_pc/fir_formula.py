"""Impulse-response formulas for the two window-method FIR designers."""
from fractions import Fraction
import numpy as np
from .result_summary import Formula, Section, Summary, number


def angular(value):
    """Keep simple multiples of pi legible; other cuts remain numerical."""
    ratio = Fraction(float(value / np.pi)).limit_denominator(1000)
    if abs(float(ratio) * np.pi - value) <= 2e-14 * max(1, abs(value)):
        top = 'pi' if ratio.numerator == 1 else str(ratio.numerator) + '*pi'
        return top if ratio.denominator == 1 else top + '/' + str(ratio.denominator)
    return number(value)


def kernel(kind, cutoffs, variable='x'):
    def low(cut):
        ratio = Fraction(float(cut / np.pi)).limit_denominator(1000)
        c = str(ratio) if abs(float(ratio) * np.pi - cut) <= 2e-14 * max(1, abs(cut)) else number(cut / np.pi)
        return '(' + c + ')*sinc((' + c + ')*(' + variable + '))'
    first = low(cutoffs[0])
    if kind == 'lowpass': return first
    if kind == 'highpass': return 'sinc(' + variable + ')-(' + first + ')'
    band = low(cutoffs[1]) + '-(' + first + ')'
    return band if kind == 'bandpass' else 'sinc(' + variable + ')-(' + band + ')'


def window_expression(window, length, beta):
    phase = '2*pi*n/' + str(length - 1)
    if window == 'boxcar': return '1'
    if window == 'hann': return '0.5-0.5*cos(' + phase + ')'
    if window == 'hamming': return '0.54-0.46*cos(' + phase + ')'
    if window == 'blackman': return '0.42-0.5*cos(' + phase + ')+0.08*cos(2*(' + phase + '))'
    if window == 'bartlett': return '1-abs((2*n-' + str(length - 1) + ')/' + str(length - 1) + ')'
    if window == 'kaiser':
        b = number(beta)
        return 'I_0((' + b + ')*sqrt(1-(2*n/' + str(length - 1) + '-1)^2))/I_0(' + b + ')'
    raise ValueError('Ventana FIR desconocida.')


def design_summary(kind, length, cutoffs, window, beta, gain=1, details='', title='FIR por enventanado'):
    """Describe the actual centered kernel, symmetric window and gain used."""
    delay = number((length - 1) / 2)
    core = kernel(kind, cutoffs)
    shifted = kernel(kind, cutoffs, 'n-' + delay)
    multiplier = '' if gain == 1 else '(' + number(gain) + ')*'
    product = multiplier + 'g(n-' + delay + ')*w[n]'
    expanded = multiplier + '(' + shifted + ')*w[n]'
    condition = '0 <= n <= ' + str(length - 1)
    final = 'Piecewise((' + product + ', ' + condition + '), (0, True))'
    ideal = kernel(kind, cutoffs, 'n')
    sections = [
        Section('Respuesta al impulso ideal', paragraphs=[
            'El ideal no está truncado: se define para todos los índices enteros n. Las frecuencias de corte están en rad/muestra.',
            'Se usa sinc(x)=sin(πx)/(πx), con sinc(0)=1. En índices enteros, sinc(n)=δ[n].'
        ], rows=[('Cortes del ideal', ', '.join(angular(c) for c in cutoffs) + ' rad/muestra')], formulas=[
            Formula('h_ideal[n] = ' + ideal, 'h_ideal[n] = ' + ideal),
            Formula('g(x) = ' + core, 'g(x) = ' + core)
        ]),
        Section('Ventana y desplazamiento', paragraphs=[
            'g(x) es el núcleo anterior evaluado también entre índices. El FIR se centra en D=(L−1)/2 y queda limitado a 0≤n≤L−1. Si L es par, D es semientero; los índices n del filtro siguen siendo enteros.',
            'I₀ es la función de Bessel modificada de primera especie y orden cero.' if window == 'kaiser' else 'La ventana es simétrica y vale cero fuera del intervalo indicado.'
        ], rows=[('Longitud L', str(length)), ('Orden M=L−1', str(length-1)), ('Desplazamiento D (muestras)', delay)], formulas=[
            Formula('w[n] = Piecewise((' + window_expression(window, length, beta) + ', ' + condition + '), (0, True))', 'w[n] = ' + window_expression(window, length, beta) + ' para ' + condition + '; 0 fuera')
        ]),
        Section('Respuesta al impulso del filtro', rows=[('Factor de ganancia C', number(gain))], paragraphs=[
            'Se multiplica el ideal desplazado por la ventana. El factor C es el aplicado a los coeficientes; no se supone ganancia unitaria si el diseño no la normaliza. El texto copiable conserva hasta 12 cifras significativas; la vista redondea los decimales para facilitar la lectura. Los coeficientes conservan su precisión numérica.'
        ], formulas=[Formula('h[n] = ' + final, 'h[n] = ' + product + ' para ' + condition + '; 0 fuera'),
                     Formula('h[n] = ' + expanded, 'Dentro del intervalo: h[n] = ' + expanded)])
    ]
    for section in sections:
        for formula in section.formulas:formula.numeric=True
    if details:
        rows = []; paragraphs = []
        for line in details.splitlines():
            if ': ' in line:
                label, value = line.split(': ', 1); rows.append((label, value))
            elif line.strip(): paragraphs.append(line)
        sections.append(Section('Datos del diseño y comprobación', rows=rows, paragraphs=paragraphs))
    return Summary(title, sections)
