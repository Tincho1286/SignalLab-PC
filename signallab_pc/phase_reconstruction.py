"""Periodic log-spectrum reconstruction with an explicitly causal cepstrum.

Convention: H(w)=sum h[n] exp(-j*w*n). Magnitude alone omits delay,
constant phase and all-pass factors; phase alone also omits a gain scale.
"""
import csv,math
import numpy as np
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint


def _causal(values):
    count=len(values);cepstrum=np.fft.ifft(values);output=np.zeros(count,dtype=complex)
    output[0]=cepstrum[0];output[1:(count+1)//2]=2*cepstrum[1:(count+1)//2]
    if count%2==0:output[count//2]=cepstrum[count//2]
    return output


def _canonical(values,origin):
    """Interpolate a real periodic record onto -pi + 2*pi*k/N."""
    count=len(values);harmonics=np.rint(np.fft.fftfreq(count)*count).astype(int)
    shift=(-np.pi-origin)%(2*np.pi);factors=np.exp(1j*harmonics*shift)
    # A real Nyquist cosine is the interpolation convention for an even grid.
    if count%2==0:factors[count//2]=np.cos(harmonics[count//2]*shift)
    return np.fft.ifft(np.fft.fft(values)*factors).real


def reconstruct(source,kind='magnitude',*,delay=0,constant_phase=0.,reference_gain=1.,floor=0.,real_half_period=False):
    if kind not in ('magnitude','db','phase'):raise ValueError('Elegí módulo lineal, módulo en dB o fase en radianes.')
    if source.domain!='frequency' or source.units!='rad/muestra':raise ValueError('Se requiere un período de frecuencias en rad/muestra.')
    if source.step<=0 or len(source.values)<3:raise ValueError('Usá frecuencias crecientes, con al menos tres puntos incluyendo los extremos del período.')
    original_origin=float(source.origin);original_span=source.step*(len(source.values)-1);completed=False
    if real_half_period and np.isclose(original_span,np.pi,rtol=1e-9,atol=1e-10) and np.isclose(source.origin,0,rtol=0,atol=1e-10):
        if np.any(source.values.imag):raise ValueError('La columna de módulo o fase debe ser real.')
        data=source.values.real;half_w=source.axis
        if kind=='phase':
            corrected=data+delay*half_w;offset=corrected[0];base=corrected-offset
            if abs(np.sin(offset))>1e-8 or abs(base[-1])>1e-8*max(1.,float(np.max(abs(base)))):raise ValueError('La fase no es compatible con el modelo real de fase mínima y el desplazamiento indicado: revisá los valores en 0 y pi, el desenrollado y d.')
            full_w=np.linspace(-np.pi,np.pi,2*len(data)-1);full=np.r_[-base[:0:-1],base]+offset-delay*full_w
        else:full=np.r_[data[:0:-1],data]
        source=Signal(full,-np.pi,source.step,'rad/muestra',source.name,'frequency',source.expression,source.metadata);completed=True
    span=source.step*(len(source.values)-1)
    if not np.isclose(span,2*np.pi,rtol=1e-9,atol=1e-10):raise ValueError('Los datos deben cubrir un período completo de 2*pi rad/muestra, con ambos extremos. Para −pi a pi usá paso 2*pi/(cantidad−1). Si el archivo cubre 0…pi y el sistema es real, habilitá completar por simetría. Otra banda parcial no basta sin hipótesis adicionales.')
    if np.any(source.values.imag):raise ValueError('Ingresá valores reales de módulo, dB o fase; una respuesta compleja H no es una de esas columnas.')
    if isinstance(delay,bool) or int(delay)!=delay:raise ValueError('El desplazamiento d debe ser un entero: positivo retrasa y negativo adelanta.')
    delay=int(delay)
    if not np.isfinite([constant_phase,reference_gain,floor]).all() or reference_gain<=0 or floor<0:raise ValueError('La fase constante debe ser finita, la ganancia de referencia positiva y el piso no negativo.')
    count=len(source.values)-1;ensure_working_set(count,live_arrays=30)
    limit=np.iinfo(np.int64)
    if delay-count//2<limit.min or delay-count//2+count-1>limit.max:raise ValueError('La ventana temporal excede los índices enteros de 64 bits.')
    raw=source.values.real;input_w=source.axis;omega=np.linspace(-np.pi,np.pi,count+1);periodic_w=omega[:-1]
    floor_count=0
    if kind=='phase':
        corrected=raw+delay*input_w
        tolerance=1e-8*max(1.,float(np.max(abs(corrected))))
        if abs(corrected[-1]-corrected[0])>tolerance:raise ValueError('La fase, después de quitar d, no cierra un período. Ingresá fase desenrollada y su retardo/avance conocido; no se deduce automáticamente desde una banda incompleta.')
        if np.max(abs(np.diff(corrected)))>=np.pi:raise ValueError('Hay saltos de fase de pi o más entre muestras. Desenrollá la fase o aumentá la resolución antes de reconstruir.')
        target=_canonical(corrected[:-1],source.origin)
        cepstrum=_causal(1j*target)
        # Fix the missing real constant by evaluating the interpolated log H at DC.
        indices=np.arange(count);parity=np.where(indices%2, -1.,1.)
        log_dc=float(np.sum(cepstrum*parity).real)
        cepstrum[0]+=math.log(reference_gain)-log_dc
    else:
        if kind=='magnitude':
            if np.any(raw<0):raise ValueError('El módulo lineal no puede ser negativo.')
            work=raw.copy()
            if floor:
                selected=work<floor;floor_count=int(np.count_nonzero(selected[:-1]));work=np.maximum(work,floor)
            if np.any(work<=0):raise ValueError('log|H| requiere módulo positivo. Para un cero ideal, indicá explícitamente un piso positivo: cambiará el modelo y se informará cuántos puntos modifica.')
            log_input=np.log(work)
        else:
            log_input=raw*(math.log(10)/20)
            if floor:
                selected=log_input<math.log(floor);floor_count=int(np.count_nonzero(selected[:-1]));log_input=np.maximum(log_input,math.log(floor))
        if abs(log_input[-1]-log_input[0])>1e-8*max(1.,float(np.max(abs(log_input)))):raise ValueError('Los extremos del módulo no coinciden. Usá un período completo con el mismo valor inicial y final.')
        target=_canonical(log_input[:-1],source.origin)
        cepstrum=_causal(target);cepstrum[0]+=1j*constant_phase
    checkpoint(.35)
    log_response=np.fft.fft(cepstrum);log_magnitude=log_response.real
    with np.errstate(all='ignore'):magnitude=np.exp(log_magnitude)
    if not np.isfinite(magnitude).all() or np.any(magnitude==0):raise ValueError('El módulo reconstruido excede el rango numérico positivo. Cambiá la escala de ganancia o revisá las variaciones de fase.')
    # Modulation uses d modulo N, keeping large integer delays out of sin/cos.
    k=np.arange(count);shift=(1 if delay%2==0 else -1)*np.exp(-2j*np.pi*k*(delay%count)/count)
    response=magnitude*np.exp(1j*log_response.imag)*shift
    phase=log_response.imag-delay*periodic_w
    delay_values=np.fft.fft(np.arange(count)*cepstrum).real+delay
    full_response=np.r_[response,response[0]];full_magnitude=np.r_[magnitude,magnitude[0]]
    full_phase=np.r_[phase,log_response.imag[0]-delay*np.pi];full_delay=np.r_[delay_values,delay_values[0]]
    # A second resolution estimates sensitivity of the finite-data reconstruction.
    decimated=None
    if count>=8:
        coarse_count=count//2;coarse_indices=np.arange(coarse_count)*2
        if count%2==0:
            coarse=_causal(target[coarse_indices] if kind!='phase' else 1j*target[coarse_indices]);coarse_log=np.fft.fft(coarse)
            reference=log_response[coarse_indices].imag if kind!='phase' else log_response[coarse_indices].real
            compared=coarse_log.imag if kind!='phase' else coarse_log.real
            difference=reference-compared
            difference-=float(np.mean(difference)) # phase/gain constants are separate conventions.
            decimated=float(np.max(abs(difference)))
    error=float(np.max(abs(log_response.imag-target))) if kind=='phase' else float(np.max(abs(log_response.real-target)))
    nyquist=float(abs(cepstrum[count//2])) if count%2==0 else 0.
    kept=cepstrum[:count//2+1];true_coeff=kept*np.where(np.arange(len(kept))%2,-1.,1.)
    metadata={'operation':'minimum_phase_reconstruction','input_kind':kind,'delay_samples':delay,'constant_phase_rad':float(cepstrum[0].imag),'reference_gain_dc':float(reference_gain) if kind=='phase' else None,'magnitude_floor':float(floor),'modified_points':floor_count,'period_intervals':count,'input_origin':original_origin,'input_period_span':float(original_span),'completed_by_real_symmetry':completed,'log_model_coefficients':[[float(v.real),float(v.imag)] for v in true_coeff],
        'grid_input_error':error,'coarse_grid_sensitivity':decimated,'nyquist_log_component':nyquist,
        'scope':'Reconstrucción de fase mínima bajo un modelo cepstral causal de período completo. d y la fase constante son convenciones o datos conocidos, no propiedades deducidas del módulo. Las muestras no determinan la respuesta entre frecuencias sin el modelo interpolado. No se recuperan factores paso todo desconocidos.'}
    h=Signal(full_response,-np.pi,2*np.pi/count,'rad/muestra','H reconstruida · modelo de fase mínima'+(' y desplazamiento' if delay else ''),'frequency','',metadata)
    cyclic=np.fft.ifft(response);start=delay-count//2;indices=np.arange(count,dtype=np.int64)+start
    taps=cyclic[indices%count]*np.where(indices%2,-1.,1.)
    impulse=Signal(taps,start,1,'n','h[n] · aproximación del período muestreado','discrete','',{k:v for k,v in metadata.items() if k!='log_model_coefficients'})
    impulse.metadata.update(approximation='finite-period inverse Fourier; aliased time record',not_a_fir_definition=True,scope='Registro temporal obtenido de una rejilla finita. Incluye aliasing temporal y no define un FIR exacto ni demuestra el soporte completo de la respuesta.')
    checkpoint(1)
    data={'response':h,'impulse':impulse,'omega':omega,'magnitude':full_magnitude,'phase':full_phase,'delay':full_delay,'log_magnitude':np.r_[log_magnitude,log_magnitude[0]],'metadata':metadata}
    return {'systems':[],'signals':[h,impulse],'reconstruction':data,'report':reconstruction_summary(data).plain_text()}


def reconstruction_summary(data):
    from .result_summary import Summary,Section,Formula,number
    m=data['metadata'];phase=m['input_kind']=='phase'
    rows=[('Entrada','Fase desenrollada (rad)' if phase else 'Módulo (dB)' if m['input_kind']=='db' else 'Módulo lineal'),('Intervalos del período',m['period_intervals']),('Desplazamiento d',str(m['delay_samples'])+' muestras'),('Fase constante del modelo',number(m['constant_phase_rad'])+' rad'),('Puntos modificados por el piso',m['modified_points']),('Error del dato sobre la rejilla',number(m['grid_input_error']))]
    if phase:rows.append(('Módulo fijado en ω=0',number(m['reference_gain_dc'])))
    if m['completed_by_real_symmetry']:rows.append(('Semiperíodo completado','Simetría de un modelo real; hipótesis indicada por el usuario'))
    if m['coarse_grid_sensitivity'] is not None:rows.append(('Cambio máximo al usar la mitad de puntos',number(m['coarse_grid_sensitivity'])+(' en log-módulo' if phase else ' rad')))
    return Summary('Reconstrucción de módulo y fase',[
        Section('Resultado y convenciones',rows=rows,formulas=[Formula('H(w) = exp(L(w))*exp(-i*w*'+str(m['delay_samples'])+')','H(ω)=exp(L(ω))·exp(−jωd)'),Formula('L(w) = Sum(c[k]*exp(-i*w*k),(k,0,'+str(len(m['log_model_coefficients'])-1)+'))','L(ω) es una suma de exponenciales con los coeficientes c[k] guardados en el JSON.')],paragraphs=['Se construye un logaritmo de respuesta con cepstrum causal: sus coeficientes son la transformada inversa del logaritmo del espectro y sólo se conservan índices no negativos. El módulo y la fase forman un par bajo esa hipótesis; los factores paso todo desconocidos no quedan determinados. d>0 agrega retardo y d<0 agrega avance.']),
        Section('Qué fija la información faltante',paragraphs=['La fase sola no fija la escala del módulo: se impone el valor indicado en frecuencia cero.' if phase else 'El módulo no fija el retardo, la fase constante ni factores paso todo. Se usa un modelo base de fase mínima y después se aplica el desplazamiento y la fase constante indicados.',
            'La relación usa logaritmo del módulo, no el módulo directamente. Un piso positivo modifica los ceros y los niveles pequeños antes del cálculo; el informe cuenta esos cambios.']),
        Section('Cómo interpretar la resolución',paragraphs=['Se usa un período completo de 2π rad/muestra con el extremo final repetido, o datos 0…π completados por simetría real cuando se indicó esa hipótesis. El cálculo no duplica el extremo final; la salida se centra entre −π y π para reutilizarla como respuesta en frecuencia.',
            'La sensibilidad compara la rejilla con una versión de la mitad de puntos cuando es posible; no es una cota de error frente al sistema real. Aumentá resolución y compará resultados cerca de cambios rápidos. En una rejilla par, el armónico Nyquist no tiene un compañero independiente: se usa una convención cepstral y su componente puede perderse en un viaje módulo→fase→módulo. Componente logarítmica en Nyquist: '+number(m['nyquist_log_component'])+'.']),
        Section('Resultados disponibles',paragraphs=['H reconstruida es una respuesta compleja en rad/muestra, exportable y reutilizable en filtros definidos en frecuencia. No se presenta como un numerador/denominador racional exacto.',
            'h[n] es un registro aproximado de la inversa numérica, centrado alrededor del desplazamiento elegido. La rejilla finita produce réplicas temporales; la presencia de pequeñas muestras negativas no prueba que el modelo base sea no causal. El registro no se convierte automáticamente en un FIR exacto.',
            'La figura de H muestra módulo, fase y retardo del modelo cepstral interpolado; no deriva la fase principal con saltos. El CSV conserva esas curvas y el JSON de H conserva el modelo y sus convenciones.'])])


def export_reconstruction(data,path):
    from .atomic_file import atomic_text_file
    response=data['response'].values
    with atomic_text_file(path,newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['omega_rad_muestra','H_real','H_imag','modulo','modulo_dB','fase_rad','retardo_muestras'])
        for row in zip(data['omega'],response.real,response.imag,data['magnitude'],20*data['log_magnitude']/math.log(10),data['phase'],data['delay']):writer.writerow([float(v) for v in row])


def draw_reconstruction(data,figure,mode=0):
    from .signal_plot import configure_axis
    figure.clear();axes=np.atleast_1d(figure.subplots(3 if mode==0 else 1,1,sharex=True))
    db=20*data['log_magnitude']/math.log(10)
    curves=[(db,'Módulo (dB)'),(data['phase'],'Fase desenrollada (rad)'),(data['delay'],'Retardo (muestras)')] if mode==0 else [(data['magnitude'],'|H|')] if mode==3 else [(data['delay'],'Retardo (muestras)')] if mode==2 else [(db,'Módulo (dB)')]
    for axis,(values,label) in zip(axes,curves):axis.plot(data['omega'],values);axis.set_ylabel(label);axis.grid(alpha=.2)
    configure_axis(axes[-1],units='rad/muestra',label='ω (rad/muestra)');axes[-1].set_xlim(-np.pi,np.pi);figure.set_layout_engine('constrained')
