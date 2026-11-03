"""Input/output conditions of a rational transfer, without assuming a ROC."""
import numpy as np


def record(system):
    from .transfer_plane import convergence, effective_plane_system
    effective = effective_plane_system(system);digital = system.domain=='digital'
    information = convergence(effective)
    b = np.trim_zeros(effective.b, 'f');a = np.trim_zeros(effective.a, 'f')
    if digital:
        # B(q)/A(q) with a0!=0: at infinity q=0; advance can introduce a pole.
        first = int(np.flatnonzero(effective.b)[0]) if np.any(effective.b) else effective.advance
        proper = effective.advance<=first
    else:proper = len(b)<=len(a)
    if not information['known']:
        causal = 'No determinada: falta la ROC.'
        stable = 'No determinada: falta la ROC.' if digital or proper else 'No BIBO estable: contiene derivadas ideales de la entrada.'
        frequency = 'Evaluación formal; no se afirma que sea la transformada de Fourier de h.'
    else:
        exterior = np.isinf(information['outer'])
        causal = 'Sí: ROC exterior y sin avances.' if digital and exterior and proper else 'Sí: ROC derecha y transferencia propia.' if not digital and exterior and proper else 'No causal: el soporte incluye tiempos negativos.' if not exterior or digital and not proper else 'Causal como distribución; incluye derivadas de impulsos.'
        stable = 'Sí: el círculo unitario pertenece a la ROC.' if digital and information['unit'] else 'Sí: el eje imaginario pertenece a la ROC y H(s) es propia.' if not digital and information['unit'] and proper else 'No: la ROC excluye la frontera de Fourier.' if not information['unit'] else 'No BIBO estable: H(s) es impropia.'
        frequency = 'Transformada de Fourier compatible con la ROC.' if information['unit'] else 'La evaluación sobre la frontera no representa una respuesta de Fourier convergente.'
    if information.get('boundary'):
        stable='No se declara estabilidad: hay un polo sobre la frontera de Fourier o numéricamente indistinguible de ella.'
    if not len(b):
        causal='Sí: el sistema nulo tiene h=0.';stable='Sí: la salida es nula para toda entrada acotada.';frequency='Respuesta de Fourier nula en todo el eje de frecuencia.'
    return {'domain':'Discreto · H(z)' if digital else 'Continuo · H(s)', 'roc':information['text'], 'causality':causal, 'bibo_stability':stable, 'frequency_interpretation':frequency,
            'scope':'Clasificación entrada–salida del modelo racional almacenado, con cancelación de factores exactamente comunes. No demuestra estabilidad interna de una realización. Los polos y las fronteras se evalúan numéricamente.'}


def section(system):
    from .result_summary import Section
    data = record(system)
    return Section('Condiciones de validez', rows=[('Dominio', data['domain']), ('Región de convergencia', data['roc']), ('Causalidad', data['causality']), ('Estabilidad BIBO', data['bibo_stability'])], paragraphs=[data['frequency_interpretation'], data['scope']])
