"""Uniform sampling of a real signal with one positive-frequency band."""
import math
import numpy as np
from .resources import ensure_working_set
from .jobs import checkpoint

def analyze(low,high,candidate=None):
    if not np.isfinite([low,high]).all() or not 0<low<high:
        raise ValueError('Los bordes deben cumplir 0 < ΩL < ΩH, en rad/s.')
    if candidate is not None and (not np.isfinite(candidate) or candidate<=0):
        raise ValueError('La frecuencia angular de muestreo debe ser positiva, o dejá el campo vacío.')
    width=high-low;ratio=high/width
    if not np.isfinite(ratio) or ratio>=2**53:
        raise ValueError('La banda es demasiado estrecha respecto de su frecuencia para distinguir los intervalos con precisión.')
    count=math.floor(ratio)
    ensure_working_set(count,live_arrays=12)
    checkpoint(0)
    m=np.arange(1,count+1,dtype=np.float64)
    lower=2*(high/m);upper=np.full(count,np.inf)
    upper[1:]=2*(low/(m[1:]-1))
    if not np.isfinite(lower).all() or not np.isfinite(upper[1:]).all() or np.any(lower<=0):
        raise ValueError('La escala de frecuencias excede la precisión disponible.')
    tolerance=64*np.finfo(float).eps*np.maximum(lower,np.where(np.isfinite(upper),upper,lower))
    nonempty=upper>=lower-tolerance
    m=m[nonempty];lower=lower[nonempty];upper=upper[nonempty];tolerance=tolerance[nonempty]
    zero_margin=(upper-lower)<=tolerance
    status='Sin tasa candidata';index=None
    if candidate is not None:
        interior=(candidate>lower+tolerance)&(candidate<upper-tolerance)&~zero_margin
        touching=(candidate>=lower-tolerance)&(candidate<=upper+tolerance)
        if np.any(interior):index=int(np.flatnonzero(interior)[0]);status='Admisible con margen espectral'
        elif np.any(touching):index=int(np.flatnonzero(touching)[0]);status='En un borde teórico: sin margen garantizado'
        else:status='No admisible para toda la banda: hay solapamiento'
    lines=['Muestreo pasabanda',f'Banda positiva: {low:.12g} a {high:.12g} rad/s.',f'Ancho B = {width:.12g} rad/s.',
           'Se supone una señal real con espectro nulo fuera de esta banda y su reflejo negativo.',
           '', 'Intervalos teóricos', '2 ΩH / m ≤ Ωs ≤ 2 ΩL / (m−1). Para m = 1 no hay límite superior.',
           'Ωs = 2π Fs. Los extremos son contactos entre bandas; para dejar margen elegí el interior.',
           'La cota 2B no implica que cualquier tasa superior sea válida.', '', 'm | Ωs inferior (rad/s) | Ωs superior (rad/s) | Margen']
    for i in range(min(len(m),100)):
        lines.append(f'{int(m[i])} | {lower[i]:.12g} | '+('∞' if np.isinf(upper[i]) else f'{upper[i]:.12g}')+' | '+('Sólo contacto' if zero_margin[i] else 'Interior disponible'))
    if len(m)>100:lines.append(f'Se muestran 100 de {len(m)} intervalos. Exportar intervalos conserva todos.')
    lines+=['','Tasa consultada',status]
    if candidate is not None:
        lines += [f'Ωs = {candidate:.12g} rad/s; Fs = {candidate/(2*np.pi):.12g} muestras/s; T = {2*np.pi/candidate:.12g} s.']
        if index is not None:
            zone=int(m[index]);lines += [f'Zona m = {zone}. Orientación en la banda positiva plegada: '+('invertida.' if zone%2==0 else 'conservada.')]
    lines+=['','Alcance','Los bordes no garantizan reconstrucción de componentes impulsivas situadas exactamente en ellos. La clasificación de contacto incluye la tolerancia de redondeo numérico.',
            'El teorema supone soporte estrictamente limitado y muestreo uniforme ideal. Un filtro real necesita bandas de guarda; el conversor debe admitir la banda analógica original.',
            'No se simulan aquí una forma de señal ni el filtro de reconstrucción. El gráfico representa tasas admisibles, no amplitudes del espectro.']
    checkpoint(1)
    return dict(report='\n'.join(lines),signals=[],systems=[],bandpass=dict(low=low,high=high,candidate=candidate,m=m,lower=lower,upper=upper,zero_margin=zero_margin,status=status))

def export_intervals(path,result):
    import csv
    from .atomic_file import atomic_text_file
    with atomic_text_file(path,newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['omega_low_rad_s',result['low'],'omega_high_rad_s',result['high']])
        writer.writerow(['m','omega_s_min_rad_s','omega_s_max_rad_s','Fs_min_samples_s','Fs_max_samples_s','interior_available'])
        for m,lo,hi,zero in zip(result['m'],result['lower'],result['upper'],result['zero_margin']):
            writer.writerow([int(m),lo,'infinity' if np.isinf(hi) else hi,lo/(2*np.pi),'infinity' if np.isinf(hi) else hi/(2*np.pi),not bool(zero)])
