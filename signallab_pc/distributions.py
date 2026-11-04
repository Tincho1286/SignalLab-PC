"""Finite sums of Dirac terms stored separately from the sampled regular part."""
import numpy as np

def dirac_terms(source):
    raw=list(source.metadata.get('dirac_terms',[]))
    if 'dirac_at_zero' in source.metadata:raw.append([0.,source.metadata['dirac_at_zero']])
    result={}
    for entry in raw:
        try:position=float(entry[0]);weight=complex(*entry[1])
        except (TypeError,ValueError,IndexError) as exc:raise ValueError('Cada impulso requiere posición real y peso complejo.') from exc
        if not np.isfinite(position) or not np.isfinite(weight):raise ValueError('La posición y el peso de cada impulso deben ser finitos.')
        result[position]=result.get(position,0j)+weight
    if any(not np.isfinite(w) for w in result.values()):raise ValueError('La suma de pesos de los impulsos excede el rango numérico.')
    return [(t,w) for t,w in sorted(result.items()) if w]

def regular_only(source,operation):
    if source.domain=='frequency' and source.metadata.get('distribution'):
        raise ValueError(operation+' requiere valores ordinarios. Las líneas espectrales contienen pesos de Dirac.')
    if dirac_terms(source):raise ValueError(operation+' requiere una señal ordinaria. Esta entrada incluye impulsos Dirac, que no son muestras de altura finita. Usá una operación que los trate explícitamente.')

def attach_terms(metadata,terms):
    merged={}
    for t,w in terms:merged[t]=merged.get(t,0j)+w
    metadata.pop('dirac_at_zero',None);metadata.pop('dirac_terms',None)
    entries=[]
    for t,w in sorted(merged.items()):
        if not np.isfinite(t) or not np.isfinite(w):raise ValueError('La distribución resultante excede el rango numérico.')
        if not w:continue
        pair=[float(w.real),float(w.imag)]
        if t==0:metadata['dirac_at_zero']=pair
        else:entries.append([float(t),pair])
    if entries:metadata['dirac_terms']=entries
    return metadata
