"""Observed sensitivity of one coefficient conversion, not a universal bound."""
import numpy as np


def diagnose(original,stored,poles,quantized,sections):
    from scipy.optimize import linear_sum_assignment
    from .resources import ensure_working_set
    if sections:
        one=original.sos[:,4:].reshape(-1);two=stored.sos[:,4:].reshape(-1)
    else:
        n=max(len(original.a),len(stored.a));one=np.pad(original.a,(0,n-len(original.a)));two=np.pad(stored.a,(0,n-len(stored.a)))
    scale=float(max(np.max(abs(one.real),initial=0),np.max(abs(one.imag),initial=0)))
    change=float(np.max(abs(two/scale-one/scale),initial=0)) if scale else 0.
    displacement=None
    if len(poles)==len(quantized):
        if len(poles):
            ensure_working_set(len(poles)**2,live_arrays=4)
            scale_p=float(max(np.max(abs(poles.real)),np.max(abs(poles.imag)),np.max(abs(quantized.real)),np.max(abs(quantized.imag))))
            cost=abs(poles[:,None]/scale_p-quantized[None,:]/scale_p) if scale_p else np.zeros((len(poles),len(poles)))
            if np.isfinite(cost).all():
                i,j=linear_sum_assignment(cost)
                with np.errstate(over='ignore'):shift=float(cost[i,j].max())*scale_p
                displacement=shift if np.isfinite(shift) else None
        else:displacement=0.
    amplification=displacement/change if displacement is not None and change>0 else None
    if amplification is not None and not np.isfinite(amplification):amplification=None
    distance=float(np.min(abs(abs(poles)-1))) if len(poles) else None
    after=float(np.min(abs(abs(quantized)-1))) if len(quantized) else None
    warnings=[]
    if len(poles) and np.max(abs(poles))<1 and np.max(abs(quantized))>=1:warnings.append('La cuantización llevó al menos un polo a la frontera o fuera del círculo unidad. El criterio de ubicación de polos para una realización causal deja de cumplirse. La estabilidad entrada–salida requiere considerar la ROC y las cancelaciones.')
    if amplification is not None and amplification>10:warnings.append('En esta conversión los polos variaron mucho respecto del cambio relativo del denominador. Compará más bits y una cascada de secciones de segundo orden.')
    if len(original.a)>5 and not sections:warnings.append('Los polinomios de orden alto pueden ser sensibles. Si el filtro dispone de SOS, compará la opción de conservarlas antes de aumentar el orden o reducir bits.')
    return {'denominator_relative_change':change,'matched_pole_shift':displacement,'observed_amplification':amplification,'distance_to_unit_circle_before':distance,'distance_to_unit_circle_after':after,'warnings':warnings,
            'scope':'Se emparejan los polos minimizando la suma de desplazamientos, conservando multiplicidades. La amplificación es el máximo desplazamiento dividido por el cambio relativo máximo de coeficientes del denominador en esta conversión. No es una derivada, una cota general ni una prueba de robustez ante todas las perturbaciones. La estructura estudiada —SOS o polinomios— forma parte del resultado.'}


def section(data):
    from .result_summary import Section,number
    rows=[]
    for key,label in [('denominator_relative_change','Cambio relativo máximo del denominador'),('matched_pole_shift','Máximo desplazamiento de polos emparejados'),('observed_amplification','Amplificación observada'),('distance_to_unit_circle_before','Distancia mínima al círculo unidad · original'),('distance_to_unit_circle_after','Distancia mínima al círculo unidad · cuantizado')]:rows.append((label,number(data[key]) if data[key] is not None else 'No corresponde o no se pudo determinar'))
    return Section('Sensibilidad numérica observada',rows=rows,paragraphs=[*data['warnings'],data['scope']])
