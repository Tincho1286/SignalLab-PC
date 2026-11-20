"""Real causal FIR equalization of a complex response over a specified band."""
import numpy as np
from scipy.linalg import lstsq
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint


def design_compensator(system,low,high,taps,delay,gain=1.,regularization=1e-4):
    if system.domain!='digital' or np.any(system.b.imag) or np.any(system.a.imag):raise ValueError('El compensador FIR de esta opción requiere un sistema digital con coeficientes reales.')
    from .system_conditions import require_causal_roc
    require_causal_roc(system,operation='La compensación FIR requiere un sistema causal.')
    if not np.isfinite([low,high,gain,regularization]).all() or not 0<=low<high<=np.pi:raise ValueError('La banda debe cumplir 0 ≤ Desde < Hasta ≤ pi rad/muestra, con datos finitos.')
    if gain<=0 or regularization<0:raise ValueError('La ganancia objetivo debe ser positiva y la regularización no negativa.')
    if isinstance(taps,bool) or int(taps)!=taps or taps<1 or isinstance(delay,bool) or int(delay)!=delay or delay<0:raise ValueError('Usá una cantidad positiva de coeficientes y un retardo entero no negativo.')
    taps,delay=int(taps),int(delay)
    # Resolve FIR and target oscillations independently of a display grid.
    points=max(1025,8*taps+1,8*delay+1)
    ensure_working_set(int(4*points*taps+taps*taps),live_arrays=8)
    if not np.any(system.b):raise ValueError('Un sistema nulo no permite recuperar una salida de ganancia positiva mediante compensación.')
    # The model retains its poles; a frequency fit cannot stabilize hidden dynamics.
    if system.sos is not None:
        poles=np.concatenate([np.roots(row[3:]) for row in system.sos])
    else:
        ensure_working_set(len(system.a)**2,live_arrays=4);poles=np.roots(system.a)
    if np.any(abs(poles)>=1):raise ValueError('Esta compensación requiere polos causales estrictamente dentro del círculo unidad. Ajustar la respuesta en frecuencia no estabiliza un sistema inestable.')
    omega=np.linspace(low,high,points);h=system.response(omega)
    if not np.isfinite(h).all():raise ValueError('La respuesta de entrada no es finita en la banda elegida.')
    checkpoint(.1)
    basis=np.exp(-1j*np.outer(omega,np.arange(taps)));matrix=(h/gain)[:,None]*basis
    if not np.isfinite(matrix).all():raise ValueError('La escala de H respecto de la ganancia objetivo excede la precisión disponible.')
    target=np.exp(-1j*omega*delay);norm=np.sqrt(points)
    design=np.vstack((matrix.real/norm,matrix.imag/norm));rhs=np.r_[target.real/norm,target.imag/norm]
    del basis,matrix
    if regularization:
        design=np.vstack((design,np.sqrt(regularization)*np.eye(taps)));rhs=np.r_[rhs,np.zeros(taps)]
    scale=max(1.,float(np.max(abs(design))),float(np.max(abs(rhs))))
    design/=scale;rhs/=scale
    coefficients,_,rank,singular=lstsq(design,rhs,lapack_driver='gelsd');del design,rhs
    checkpoint(.6)
    if not np.isfinite(coefficients).all():raise ValueError('No se obtuvo un compensador finito; revisá la banda o aumentá la regularización.')
    compensator=Transfer(coefficients,[1],name='Compensador FIR C(z)',sample_period_s=system.sample_period_s)
    # Independent denser grid, including points not used in the fit.
    check_w=np.linspace(low,high,2*points+1);check_h=system.response(check_w);check_c=compensator.response(check_w);wanted=gain*np.exp(-1j*check_w*delay)
    actual=check_h*check_c;relative=actual/gain-np.exp(-1j*check_w*delay)
    if not np.isfinite(relative).all():raise ValueError('La evaluación independiente del compensador excedió el rango numérico.')
    before=check_h/gain-np.exp(-1j*check_w*delay)
    def rms(values):
        maximum=float(np.max(abs(values)))
        return maximum*(float(np.linalg.norm(values/maximum))/np.sqrt(len(values))) if maximum else 0.
    metrics={'relative_rms':rms(relative),
        'relative_max':float(np.max(abs(relative))),
        'original_relative_rms':rms(before),
        'rank':int(rank),'variables':taps,'points':points,'validation_points':len(check_w),
        'condition':float(singular[0]/singular[-1]) if len(singular) and singular[-1]>0 else None}
    if metrics['condition'] is not None and not np.isfinite(metrics['condition']):metrics['condition']=None
    combined=None;combined_note=''
    try:
        from .control import interconnect
        combined=interconnect(system,compensator,'cascade');probe=combined.response(check_w)
        if not np.isfinite(probe).all() or np.max(abs(probe-actual)/np.maximum(1,abs(actual)))>1e-8:raise ValueError('La forma polinómica conjunta pierde precisión frente al producto de las respuestas.')
        combined.name='Sistema compensado H(z) C(z)'
    except ValueError as exc:
        combined=None;combined_note='El compensador C está disponible. La figura calcula la cascada multiplicando las respuestas. La transferencia conjunta no se pudo guardar con suficiente precisión. '+str(exc)
    plot_w=np.linspace(0,np.pi,max(2049,2*points+1));plot_h=system.response(plot_w);plot_c=compensator.response(plot_w)
    plot_joint=plot_h*plot_c
    if not np.isfinite(plot_joint).all():raise ValueError('La comparación de banda completa no es finita en doble precisión.')
    metrics['max_compensator_gain']=float(np.max(abs(plot_c)))
    checkpoint(1)
    result={'systems':[compensator]+([combined] if combined is not None else []),'signals':[],
        'report':'Compensación FIR de módulo y fase · mínimos cuadrados regularizados',
        'compensation':{'input':system,'compensator':compensator,'low':float(low),'high':float(high),'taps':taps,'delay':delay,'gain':float(gain),'regularization':float(regularization),'metrics':metrics,'combined_note':combined_note,'omega':plot_w,'original':plot_h,'joint':plot_joint}}
    result['report']=compensation_summary(result['compensation'],compensator).plain_text()
    return result


def compensation_summary(data,selected):
    from .result_summary import Summary,Section,Formula,number
    from .phase_summary import transfer_formula
    symbol='C' if selected is data['compensator'] else 'G';formula,compact=transfer_formula(selected,symbol)
    metrics=data['metrics'];sections=[Section('Sistema seleccionado · '+selected.name,formulas=[formula])]
    if compact:sections.append(Section('Coeficientes de la fórmula',rows=[('b[k]',', '.join(number(v) for v in selected.b)),('a[k]',', '.join(number(v) for v in selected.a))]))
    gain=number(data['gain']);delay=data['delay']
    sections.extend([
        Section('Ajuste dentro de la banda',rows=[
            ('Error RMS antes de compensar',number(metrics['original_relative_rms'])),
            ('Error RMS después de compensar',number(metrics['relative_rms'])),
            ('Error máximo medido después de compensar',number(metrics['relative_max'])),
            ('Puntos de comprobación',metrics['validation_points']),
            ('Máximo |C| medido entre 0 y π',number(metrics['max_compensator_gain'])),
        ],paragraphs=['Los errores se expresan como fracción de la ganancia objetivo y corresponden a los puntos evaluados.']),
        Section('Objetivo de la cascada',rows=[
            ('Banda (rad/muestra)',number(data['low'])+' a '+number(data['high'])),
            ('Ganancia objetivo',gain),('Retardo objetivo',f'{delay} muestras'),
            ('Coeficientes de C',data['taps']),('Puntos de diseño',metrics['points']),
            ('Regularización λ',number(data['regularization'])),
        ],formulas=[
            Formula('G(z) = H(z)*C(z)','G(z) = H(z)·C(z)'),
            Formula(f'F(w) = {gain}*exp(-i*w*{delay})',f'F(ω) = {gain}·exp(−iω·{delay})'),
        ]),
    ])
    if metrics['rank']<metrics['variables'] or metrics['condition'] is None:
        sections.append(Section('Diagnóstico del ajuste',rows=[
            ('Rango / incógnitas',f"{metrics['rank']} / {metrics['variables']}"),
            ('Condición numérica',number(metrics['condition']) if metrics['condition'] is not None else 'No disponible'),
        ]))
    if data['combined_note']:
        sections.append(Section('Transferencia de la cascada',paragraphs=[data['combined_note']]))
    original,original_compact=transfer_formula(data['input'],'H');source=data['input']
    sections.append(Section('Sistema de entrada',formulas=[original],rows=[('b[k]',', '.join(number(v) for v in source.b)),('a[k]',', '.join(number(v) for v in source.a))] if original_compact else []))
    return Summary('Compensación de respuesta',sections)


def export_comparison(data,path):
    import csv
    from .atomic_file import atomic_text_file
    w=data['omega'];h=data['original'];g=data['joint'];c=data['compensator'].response(w);inside=(w>=data['low'])&(w<=data['high'])
    target=data['gain']*np.exp(-1j*w*data['delay'])
    with atomic_text_file(path,newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['omega_rad_muestra','en_banda','H_real','H_imag','C_real','C_imag','HC_real','HC_imag','objetivo_real','objetivo_imag','error_relativo_modulo'])
        for i,omega in enumerate(w):writer.writerow([omega,int(inside[i]),h[i].real,h[i].imag,c[i].real,c[i].imag,g[i].real,g[i].imag,target[i].real if inside[i] else '',target[i].imag if inside[i] else '',abs(g[i]-target[i])/data['gain'] if inside[i] else ''])
