"""Herramientas generales de diseño y análisis para Sistemas y Señales."""
import math
import numpy as np
from scipy import signal as sp
from .model import Signal
from .filters import Transfer
from .fourier import dtft
from .resources import ensure_working_set
from .jobs import checkpoint

def bundle(report,signals=(),systems=()):
    return dict(report=report,signals=list(signals),systems=list(systems))

def frequency_response(system,count=2049):
    w=np.linspace(0,np.pi,count) if system.domain=='digital' else np.geomspace(.01,100,count)
    h=system.response(w)
    return w,h

def window_fft(x,length,nfft,window,beta,points):
    if x.domain!='discrete':raise ValueError('Se requiere una secuencia discreta.')
    if not 1<=length<=x.values.size:raise ValueError('La longitud de ventana debe estar entre 1 y la cantidad de muestras de entrada.')
    if nfft<length:raise ValueError('NFFT debe ser al menos la longitud de ventana; no se recorta la señal silenciosamente.')
    if points<2:raise ValueError('Usá al menos dos frecuencias para la DTFT.')
    if beta<0:raise ValueError('β debe ser no negativo.')
    ensure_working_set(int(nfft+points+length),live_arrays=14)
    weights=sp.get_window(('kaiser',beta) if window=='kaiser' else window,length,fftbins=False)
    w=Signal(weights,x.origin,1,'n','Ventana '+window,'discrete')
    clock={key:x.metadata[key] for key in ('sample_rate_hz','time_start_s','time_mapping') if key in x.metadata}
    v=Signal(x.values[:length]*weights,x.origin,1,'n','Señal enventanada','discrete',metadata={**clock,'operation':'windowed_signal'})
    from .spectral_scaling import fft_values,energy_description
    raw=fft_values(v.values,size=nfft)
    from .fourier_phase import bin_frequency, dft_origin_phase
    indices = np.arange(nfft, dtype=np.int64)-nfft//2
    omega = bin_frequency(indices, nfft)
    spectrum = raw[indices % nfft]*dft_origin_phase(indices, nfft, int(x.origin))
    fft=Signal(spectrum,float(omega[0]),2*np.pi/nfft,'rad/muestra','DFT de la señal enventanada','frequency','',{'operation':'DFT','nfft':nfft,'window_length':length,'window':window,'kaiser_beta':beta if window=='kaiser' else None,'input_origin':x.origin})
    dense=dtft(v,-np.pi,np.pi,points)
    window_spectrum=dtft(w,-np.pi,np.pi,points)
    coeff=Signal(raw,0,1,'k','Índices k de la DFT (0 a N−1)','discrete','',{'operation':'DFT','source_origin':x.origin,'nfft':nfft,'input_clock':clock})
    energy=energy_description(v.values);spectral=energy_description(raw,nfft)
    return bundle(f'Ventanas y resolución espectral\n\nLongitud observada: {length}\nNFFT: {nfft}\nCeros agregados: {nfft-length}\nSeparación entre bins: {2*np.pi/nfft:.9g} rad/muestra\nVentana: {window}, simétrica\nGanancia coherente: {np.mean(weights):.9g}\n\nEnergía temporal: {energy}\nSuma |X[k]|²/NFFT: {spectral}\n\nLa FFT no se normaliza hacia adelante. Su fase en rad/muestra respeta el origen de la entrada. La DFT invertible conserva el origen y el reloj de la entrada para la inversa. Se puede elegir un eje local desde cero. La DTFT usa los índices originales.\n\nAgregar ceros densifica la rejilla, pero no mejora la resolución física. Aumentar la duración y cambiar la ventana modifica el ancho del lóbulo y la fuga. Se usan las primeras L muestras; no se supone que aumentar NFFT agrega información.',[fft,dense,v,w,window_spectrum,coeff])

def bands(wp,ws):
    wp=np.asarray(wp,float);ws=np.asarray(ws,float)
    if not np.all(np.isfinite(wp)) or not np.all(np.isfinite(ws)):raise ValueError('Los bordes deben ser finitos.')
    if wp.size!=ws.size or wp.size not in (1,2) or np.any(wp<=0) or np.any(ws<=0) or np.any(wp>=np.pi) or np.any(ws>=np.pi):raise ValueError('Ingresá uno o dos bordes por banda, estrictamente entre 0 y π.')
    if wp.size==1:
        if wp[0]==ws[0]:raise ValueError('La transición debe tener ancho positivo.')
        kind='lowpass' if wp[0]<ws[0] else 'highpass'
    elif ws[0]<wp[0]<wp[1]<ws[1]:kind='bandpass'
    elif wp[0]<ws[0]<ws[1]<wp[1]:kind='bandstop'
    else:raise ValueError('Bordes inválidos. Pasabanda: ws1<wp1<wp2<ws2. Rechazabanda: wp1<ws1<ws2<wp2.')
    return wp,ws,kind

def spec_report(system,wp,ws,kind,dp,ds,pass_upper=None):
    from .band_extrema import evaluate
    count=2 if kind=='bandstop' else 1
    spec={'wp':wp,'ws':ws,'kind':kind,'amplitudes':[1.]*count,'pass_lower':[1-dp]*count,'pass_upper_bands':[1+dp if pass_upper is None else pass_upper]*count,'stop_upper':ds}
    return evaluate(system,spec)[1]

def design_filter(wp,ws,dp,ds,method,period=1,taps=0,window="kaiser",search=0):
    wp,ws,kind=bands(wp,ws)
    if not 0<dp<1 or not 0<ds<1:raise ValueError('Las tolerancias lineales δp y δs deben estar entre 0 y 1.')
    if not np.isfinite(period) or period<=0:raise ValueError('T debe ser positivo y finito.')
    if method not in ('kaiser','butter','cheby1','cheby2','ellip','bilinear','impulse'):raise ValueError('Método de diseño no admitido.')
    extra=[]
    if method=='kaiser':
        attenuation=-20*np.log10(min(dp,ds));width=float(np.min(abs(wp-ws)))
        estimated,beta=sp.kaiserord(attenuation,width/np.pi)
        if window not in {'boxcar','hann','hamming','blackman','kaiser','bartlett'}:raise ValueError('Ventana no admitida.')
        if search<0:raise ValueError('La cota de búsqueda debe ser no negativa.')
        if window!='kaiser' and not taps and not search:
            from .amplitude_design import design
            return design(wp, ws, dp, ds, method, period, window=window)
        chosen_window=('kaiser',beta) if window=='kaiser' else window
        if taps<0:raise ValueError('La longitud debe ser no negativa.')
        count=int(taps) if taps else int(estimated)
        searched=False
        if search:
            if search<2:raise ValueError('La búsqueda necesita al menos dos coeficientes como cota.')
            ensure_working_set(int(search),live_arrays=18)
            found=None;cutoff=(wp+ws)/2
            for candidate in range(2,int(search)+1):
                checkpoint(candidate/search)
                if kind in ('highpass','bandstop') and candidate%2==0:continue
                trial=sp.firwin(candidate,cutoff if cutoff.size==2 else cutoff[0],window=chosen_window,pass_zero=kind,fs=2*np.pi,scale=True)
                trial_system=Transfer(trial,[1])
                if 'dentro de tolerancias.' in spec_report(trial_system,wp,ws,kind,dp,ds):found=candidate;break
            if found is None:raise ValueError('No se encontró una longitud que cumpla en la rejilla hasta la cota indicada. Aumentá la cota o cambiá la ventana/tolerancias.')
            count=found;searched=True
        if count<1:raise ValueError('Usá al menos un coeficiente.')
        if kind in ('highpass','bandstop') and count%2==0:
            if taps:raise ValueError('Con ganancia no nula en π, un FIR simétrico requiere longitud impar.')
            count+=1
        ensure_working_set(count,live_arrays=16)
        cutoff=(wp+ws)/2
        b=sp.firwin(count,cutoff if cutoff.size==2 else cutoff[0],window=chosen_window,pass_zero=kind,fs=2*np.pi,scale=True)
        result=Transfer(b,[1],name='FIR '+window+' por especificaciones')
        ideal=sp.firwin(count,cutoff if cutoff.size==2 else cutoff[0],window='boxcar',pass_zero=kind,fs=2*np.pi,scale=False)
        extra=[Signal(ideal,name='Respuesta ideal truncada'),Signal(sp.get_window(chosen_window,count,fftbins=False),name='Ventana '+window),Signal(b,name='Respuesta FIR h[n]')]
        summary=f'Método: ventana {window}\nLongitud estimada: {estimated}\nLongitud usada: {count}\nOrden: {count-1}\nβ: {beta:.9g}\nRetardo de grupo: {(count-1)/2:g} muestras (salvo ceros de la respuesta)\n\nLa fórmula de Kaiser estima la longitud; no demuestra la mínima. El filtro ideal se trunca y se normaliza al diseñar. Podés fijar otra longitud y examinarla.'
        widths=np.abs(wp-ws)
        width_text='; '.join(('izquierda' if i==0 else 'derecha')+f' = {value:.9g}' for i,value in enumerate(widths)) if len(widths)==2 else f'{widths[0]:.9g}'
        summary+='\n\nTransiciones especificadas (rad/muestra): '+width_text
        summary+=f'\nAncho usado para estimar longitud: {width:.9g} rad/muestra\nTolerancia usada en estimación Kaiser: {min(dp,ds):.9g}'
        summary+='\nCortes del ideal (rad/muestra): '+', '.join(f'{value:.9g}' for value in cutoff)
        summary+='\n\nLas franjas del gráfico son los intervalos permitidos entre los bordes, no una medición del ancho efectivo de la curva. La estimación usa la transición más estrecha y la tolerancia menor. Una sola ventana fija la suavidad de ambos cortes; no obliga a ocupar toda una transición especificada más ancha.'
        if window!='kaiser':summary=summary.replace(f'β: {beta:.9g}', 'β: no corresponde a esta ventana').replace('La fórmula de Kaiser estima la longitud; no demuestra la mínima.', 'La estimación indicada corresponde a Kaiser como referencia, no a la ventana elegida.')
        if searched:summary+='\nBúsqueda exhaustiva de longitudes desde 2 hasta la primera aceptada en la rejilla y familia elegidas. No demuestra el mínimo entre todos los métodos ni el cumplimiento entre frecuencias evaluadas.'
        systems=[result]
    else:
        gp=-20*np.log10(1-dp);gs=-20*np.log10(ds)
        if gs<=gp:raise ValueError('La atenuación de rechazo debe superar la pérdida permitida en paso.')
        if method in ('butter','cheby1','cheby2','ellip'):
            names={'butter':'Butterworth','cheby1':'Chebyshev I','cheby2':'Chebyshev II','ellip':'Elíptico (Cauer)'}
            selectors={'butter':sp.buttord,'cheby1':sp.cheb1ord,'cheby2':sp.cheb2ord,'ellip':sp.ellipord}
            notes={'butter':'Respuesta de módulo máximamente plana en paso, sin ondulación en ambas bandas.',
                   'cheby1':'Ondulación uniforme en paso y rechazo monótono. Revisá también la fase y el transitorio.',
                   'cheby2':'Paso monótono y ondulación uniforme en rechazo, con ceros de transmisión.',
                   'ellip':'Ondulación uniforme en paso y rechazo. Una transición abrupta puede acompañarse de mayor oscilación temporal.'}
            order,cutoff=selectors[method](wp,ws,gp,gs,fs=2*np.pi)
            ensure_working_set(int((2*order+1)**2),live_arrays=16)
            sections=sp.iirfilter(order,cutoff,rp=gp,rs=gs,btype=kind,ftype=method,fs=2*np.pi,output='sos')
            result=Transfer.from_sos(sections,name=names[method]+' digital')
            effective_order=int(order)*(2 if kind in ('bandpass','bandstop') else 1)
            systems=[result];summary=f'Método: {names[method]} digital\nOrden del prototipo: {order}\nOrden del filtro: {effective_order}\nPérdida máxima en paso: {gp:.9g} dB\nAtenuación mínima en rechazo: {gs:.9g} dB\n\n'+notes[method]+'\nEl orden se selecciona para la familia y las especificaciones indicadas; no implica optimalidad entre todas las clases de filtros.'
        else:
            prewarp=method=='bilinear'
            ap=2/period*np.tan(wp/2) if prewarp else wp/period
            astop=2/period*np.tan(ws/2) if prewarp else ws/period
            order,cutoff=sp.buttord(ap,astop,gp,gs,analog=True)
            ensure_working_set(int((2*order+1)**2),live_arrays=18)
            b,a=sp.butter(order,cutoff,btype=kind,analog=True);prototype=Transfer(b,a,'analog','Prototipo Butterworth analógico')
            if prewarp:
                z,p,k=sp.butter(order,cutoff,btype=kind,analog=True,output='zpk')
                z,p,k=sp.bilinear_zpk(z,p,k,fs=1/period)
                result=Transfer.from_sos(sp.zpk2sos(z,p,k),name='Butterworth por bilineal',sample_period_s=period)
            else:result=convert_system(prototype,period,'impulse')['systems'][0]
            systems=[result,prototype]
            summary=f'Método: {method}\nOrden del prototipo: {order}\nT: {period:g} s\nBordes de paso analógicos: {ap}\nBordes de rechazo analógicos: {astop}\n\n'+('La bilineal predeforma los bordes: Ω=(2/T)tan(ω/2).' if prewarp else 'La invarianza al impulso usa h[n]=T·hc(nT). Puede introducir aliasing: las especificaciones del prototipo no garantizan las digitales. Requiere prototipo estrictamente propio; no admite un paso alto con término directo.')
        summary+='\nLa especificación IIR usa ganancia entre 1−δp y 1 en paso, y como máximo δs en rechazo. Las transferencias de orden alto pueden estar mal condicionadas en forma polinómica.'
    if result.sos is not None:
        summary+=f'\n\nRealización: {len(result.sos)} secciones de segundo orden. La respuesta en frecuencia y el filtrado desde reposo usan la cascada. Los coeficientes expandidos se conservan para edición y operaciones algebraicas.'
        summary+='\nCada fila contiene b0, b1, b2; a0, a1, a2:\n'+'\n'.join(f'Sección {i+1}: '+', '.join(f'{v:.12g}' for v in row) for i,row in enumerate(result.sos))
    output=bundle(summary+'\n\n'+spec_report(result,wp,ws,kind,dp,ds,None if method=='kaiser' else 1),extra,systems)
    output['specifications']={'wp':wp.tolist(),'ws':ws.tolist(),'kind':kind,'dp':float(dp),'ds':float(ds),'pass_upper':float(1+dp if method=='kaiser' else 1)}
    if method=='kaiser':
        from .fir_formula import design_summary
        raw=ideal*extra[1].values.real
        gain=float(np.dot(raw,b)/np.dot(raw,raw))
        output['fir_summary']=design_summary(kind,count,cutoff,window,beta,gain,output['report'],result.name)
        output['report']=output['fir_summary'].plain_text()
    if method in ('butter','cheby1','cheby2','ellip'):output['filter_order']=effective_order
    return output

def compare_iir(wp,ws,dp,ds):
    designs=[]
    for index,method in enumerate(('butter','cheby1','cheby2','ellip')):
        checkpoint(index/4)
        designs.append(design_filter(wp,ws,dp,ds,method))
    checkpoint(1)
    systems=[item['systems'][0] for item in designs]
    rows=[f"{system.name}: orden {item['filter_order']}; {len(system.sos)} secciones" for system,item in zip(systems,designs)]
    report='Comparación de familias IIR\n\nMismos bordes y tolerancias para las cuatro familias. Frecuencias en rad/muestra.\n\n'+'\n'.join(rows)+'\n\nEl menor orden no determina por sí solo la elección: compará ondulación, fase, retardo y respuesta temporal. El selector identifica el filtro que se exporta o reutiliza.\n\n'+'\n\n'.join(item['report'] for item in designs)
    output=bundle(report,systems=systems);output['specifications']=designs[0]['specifications'];output['comparison']=True
    return output

def impulse_roc(system, period, *, inverse=False):
    """Map the contour as well as the poles under z = exp(s*T)."""
    if system.roc is None:
        return {'mode': 'right'}
    from .transfer_plane import convergence
    convergence(system)  # Reject a contour on a pole before mapping it.
    mode = system.roc['mode']
    if mode in ('left', 'right'):
        return {'mode': mode}
    if inverse:
        sigma = float(np.log(system.roc['radius'])/period)
        if not np.isfinite(sigma):
            raise ValueError('La línea σ de la ROC convertida excede el rango numérico.')
        return {'mode': 'line', 'sigma': sigma}
    with np.errstate(over='ignore', under='ignore'):
        radius = float(np.exp(system.roc['sigma']*period))
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError('El radio de la ROC convertida excede el rango numérico.')
    return {'mode': 'radius', 'radius': radius}


def convert_system(system,period,method):
    if not np.isfinite(period) or period<=0:raise ValueError('T debe ser positivo y finito.')
    ensure_working_set(int((max(len(system.a),len(system.b))+1)**2),live_arrays=18)
    if method in ('impulse','bilinear'):
        if system.domain!='analog':raise ValueError('Se requiere H(s) continua.')
        b=np.trim_zeros(system.b,'f');b=b if b.size else np.array([0j])
        if np.any(b.imag) or np.any(system.a.imag):raise ValueError('La conversión requiere coeficientes reales.')
        if method=='impulse':
            from .transfer_plane import effective_plane_system
            system = effective_plane_system(system)
            b = np.trim_zeros(system.b, 'f')
            b = b if b.size else np.array([0j])
            if np.any(b) and len(b)>=len(system.a):raise ValueError('Invarianza al impulso requiere H(s) estrictamente propia, sin término de Dirac directo.')
            roc = impulse_roc(system, period)
            if np.any(b):
                num,den,_=sp.cont2discrete((b.real,system.a.real),period,method='impulse');num=num.reshape(-1)
            else:
                num, den = [0], [1]
            note='h[n] = T · hc(nT), con el límite derecho en n=0. Los polos y la ROC se mapean mediante z=exp(sT). La respuesta puede sufrir aliasing y la transformación inversa no es única.'
            if system.roc is None:
                note += ' Como la entrada no especifica una ROC, se adopta la interpretación causal.'
        else:
            from .bilinear_mapping import convert
            result,procedure,exact_transfer=convert(system,period)
            note='s = (2/T) · (z−1)/(z+1). Ω = (2/T)tan(ω/2). No hay aliasing por el mapeo, pero sí deformación de frecuencia.'
        if method=='impulse':result=Transfer(num,den,'digital','Conversión '+method,sample_period_s=period,roc=roc)
        if method == 'impulse':
            from .transfer_plane import convergence
            note += '\nROC discreta: ' + convergence(result)['text']
    elif method=='impulse_inverse':
        if system.domain!='digital':raise ValueError('La reconstrucción por invarianza requiere H(z).')
        if system.advance:raise ValueError('La inversa por invarianza de polos simples no admite avances. Para esta transferencia usá Bilineal inversa.')
        roc = impulse_roc(system, period, inverse=True)
        residues,poles,direct=sp.residuez(system.b,system.a,tol=1e-10)
        if np.any(direct!=0):raise ValueError('Esta reconstrucción requiere fracciones simples sin parte polinómica directa; los términos de impulso necesitan un tratamiento distributivo.')
        if np.any(abs(poles)<1e-12):raise ValueError('Un polo nulo no tiene logaritmo finito en el mapeo exponencial.')
        if any(abs(poles[i]-poles[j])<1e-9*max(1,abs(poles[i])) for i in range(len(poles)) for j in range(i)):
            raise ValueError('La reconstrucción actual admite polos simples separados; no polos múltiples o numéricamente coincidentes.')
        candidates=[]
        real_system=not np.any(system.b.imag) and not np.any(system.a.imag)
        for branch in (0,1):
            analog_poles=[];analog_residues=[]
            for r,pole in zip(residues,poles):
                if real_system and abs(pole.imag)<1e-10 and abs(r.imag)<1e-10:
                    decay=np.log(abs(pole))/period;frequency=(0 if pole.real>0 else np.pi)+2*np.pi*branch
                    if frequency==0:analog_poles.append(decay);analog_residues.append(r.real/period)
                    else:
                        analog_poles.extend([decay+1j*frequency/period,decay-1j*frequency/period]);analog_residues.extend([r.real/(2*period)]*2)
                else:
                    shift=branch*(1 if np.angle(pole)>=0 else -1)
                    analog_poles.append((np.log(complex(pole))+2j*np.pi*shift)/period);analog_residues.append(r/period)
            num,den=sp.invres(np.asarray(analog_residues),np.asarray(analog_poles),[])
            if real_system:num=np.real_if_close(num,tol=1000);den=np.real_if_close(den,tol=1000)
            candidate = Transfer(num,den,'analog','Candidato analógico · rama '+str(branch),roc=roc)
            from .transfer_plane import convergence
            convergence(candidate)
            candidates.append(candidate)
        return bundle('Inversa de invarianza al impulso: candidatos\n\nh[n]=T·hc(nT). Para r/(1−p z⁻¹), un término continuo compatible tiene residuo r/T y polo (log(p)+j2πk)/T.\n\nSe muestran dos elecciones de ramas. Para polos y residuos reales se construyen pares conjugados cuando hace falta: tienen las mismas muestras, pero distinta evolución entre ellas. La respuesta no es única.\n\nAlcance: polos simples separados y sin parte polinómica directa. La descomposición usa tolerancia numérica 1e−10; no es una equivalencia algebraica exacta. En n=0 se interpreta el valor por la derecha de hc.',systems=candidates)
    else:
        if system.domain!='digital':raise ValueError('La bilineal inversa requiere H(z) discreta.')
        from .bilinear_mapping import convert
        result,procedure,exact_transfer=convert(system,period,inverse=True)
        note='z = (1+sT/2)/(1−sT/2). Para un T fijado la sustitución racional es única. El resultado puede ser impropio y no tener una respuesta temporal ordinaria.'
    output=bundle('Conversión de sistemas\n\n'+note+'\nT: '+str(period)+' s',systems=[result])
    if method!='impulse':
        output.update(procedure=procedure,exact_transfer=exact_transfer)
        output['report']+='\n\nTransferencia obtenida por sustitución exacta del modelo almacenado: H = '+exact_transfer
        if result.advance:output['report']+='\nLa expresión contiene '+str(result.advance)+' muestras de avance. No se reemplazan por un polo grande ni se simulan como retardos causales.'
    return output

def normalize_gain(system,omega,target):
    target=float(target)
    if not math.isfinite(target) or target<=0:raise ValueError('El módulo objetivo debe ser positivo y finito.')
    value=system.response(np.array([omega]))[0];magnitude=abs(value)
    if not np.isfinite(magnitude) or magnitude==0:raise ValueError('No se puede normalizar sobre un cero o un punto singular.')
    target_mantissa,target_exponent=math.frexp(target)
    source_mantissa,source_exponent=math.frexp(magnitude)
    mantissa=target_mantissa/source_mantissa
    exponent=target_exponent-source_exponent

    def rescale(values):
        base,power=np.frexp(values)
        with np.errstate(over='ignore',under='ignore'):
            output=np.ldexp(base*mantissa,power+exponent)
        if not np.isfinite(output).all() or np.any((values!=0)&(output==0)):
            raise ValueError('Los coeficientes normalizados exceden el rango representable.')
        return output

    if system.sos is not None:
        sections=system.sos.copy();sections[0,:3]=rescale(sections[0,:3])
        result=Transfer.from_sos(sections,'Sistema normalizado',sample_period_s=system.sample_period_s)
    else:
        numerator=rescale(system.b.real)+1j*rescale(system.b.imag)
        result=Transfer(numerator,system.a,system.domain,'Sistema normalizado',advance=system.advance,sample_period_s=system.sample_period_s)
    result.advance=system.advance
    from copy import deepcopy
    result.roc=deepcopy(system.roc)
    try:factor=f'{math.ldexp(mantissa,exponent):.12g}'
    except OverflowError:factor=f'{mantissa:.12g} × 2^{exponent}'
    if factor=='0':factor=f'{mantissa:.12g} × 2^{exponent}'
    return bundle(f'Normalización de ganancia\n\nFrecuencia angular: {omega:g}\nMódulo previo: {magnitude:.12g}\nMódulo objetivo: {target:g}\nFactor aplicado: {factor}\n\nSe modifica sólo la ganancia; la fase y las posiciones de polos y ceros se conservan.',systems=[result])

def phase_structure(system):
    from .phase_adjustment import factor_phase
    return factor_phase(system)


def inverse_z_contour(system,mode,radius,start,count,points):
    if system.domain!='digital':raise ValueError('Se requiere una transferencia discreta.')
    if count<1 or points<2*count:raise ValueError('Usá N≥1 y al menos 2N puntos de contorno.')
    ensure_working_set(int(points+count),live_arrays=14)
    from .transfer_plane import effective_plane_system,evaluate_plane,plane_poles
    system=effective_plane_system(system)
    radii=abs(plane_poles(system))
    if mode=='causal':radius=max(1.,float(np.max(radii)) if radii.size else 0)*1.2
    elif mode=='anticausal':
        if not radii.size or np.any(radii==0):raise ValueError('No hay un disco interior no nulo compatible; revisá polos en cero y términos de avance/retardo.')
        radius=float(np.min(radii))*.8
    elif mode=='stable':radius=1.
    if radius<=0 or not np.isfinite(radius):raise ValueError('El radio debe ser positivo y finito.')
    if np.any(np.isclose(radii,radius,rtol=1e-9,atol=0)):raise ValueError('El contorno coincide con un polo; elegí un radio dentro de una ROC abierta.')
    if 2*max(abs(start),abs(start+count-1))>=points:raise ValueError('Aumentá los puntos de contorno para que |n| sea menor que la mitad de ellos.')
    theta=2*np.pi*np.arange(points)/points
    h=evaluate_plane(system,radius*np.exp(1j*theta))
    if not np.isfinite(h).all():
        raise ValueError('La respuesta sobre el contorno excede el rango numérico o contiene un polo.')
    coeff=np.fft.ifft(h);indices=np.arange(start,start+count)
    with np.errstate(over='ignore',invalid='ignore'):values=coeff[indices%points]*np.power(radius,indices.astype(float))
    if not np.all(np.isfinite(values)):raise ValueError('La aproximación excede el rango numérico; acercá el radio a 1 o acortá el intervalo.')
    lower=max([0.]+[float(r) for r in radii if r<radius]);upper=min([float('inf')]+[float(r) for r in radii if r>radius])
    signal=Signal(values,start,1,'n','Z inversa por contorno','discrete','',{'operation':'inverse_z_contour','radius':radius,'contour_points':points,'roc_inner':lower,'roc_outer':None if np.isinf(upper) else upper})
    return bundle(f'Z inversa bilateral numérica\n\nROC elegida entre radios: {lower:g} < |z| < {upper:g}\nRadio de integración: {radius:g}\nPuntos del contorno: {points}\n\nh[n] ≈ rⁿ · IFFT(H(r·exp(jθ)))[n]\n\nEl radio selecciona una expansión de Laurent. El contorno exterior corresponde a la expansión causal de una representación causal; el interior puede incluir términos finitos en índices no negativos. El círculo unidad selecciona la interpretación estable si no hay polos sobre él.\n\nEs una aproximación con aliasing circular de coeficientes, especialmente cerca de polos. Aumentá puntos y compará radios dentro de la misma ROC para estudiar convergencia. No es una inversión algebraica exacta; valores muy pequeños pueden ser error de redondeo.',[signal])

def band_energy(spectrum,low,high):
    from .spectral_measurements import analyze
    data=analyze(spectrum,[('Banda',low,high)])
    return dict(bundle(data['report'],[data['cumulative']] if data['cumulative'] is not None else []),bands=data['bands'],moments=data['moments'],peaks=data['peaks'])


def periodic_lines(coefficients,period):
    if coefficients.domain!='discrete':raise ValueError('Ingresá los coeficientes c[k] de la serie, con k entero.')
    if coefficients.metadata.get('operation')=='discrete_fourier_series':raise ValueError('Esta herramienta interpreta una serie de tiempo continuo. Usá coeficientes de serie continua o ingresalos manualmente.')
    period=float(coefficients.metadata.get('period_s',period))
    if not np.isfinite(period) or period<=0:raise ValueError('El período debe ser positivo y finito.')
    powers=abs(coefficients.values)**2;omega0=2*np.pi/period
    weights=Signal(2*np.pi*powers,coefficients.origin*omega0,omega0,'rad/s','Pesos de líneas de potencia','frequency','',{'operation':'continuous_fourier_series','distribution':'Dirac weights, not finite density heights','power_line_weights':True,'period_s':period})
    power=float(np.sum(powers))
    return bundle(f'Potencia de una señal periódica\n\nSx(ω) = 2π Σ |c[k]|² δ(ω−kω₀)\nω₀: {omega0:.12g} rad/s\nPeríodo: {period:g} s\nPotencia de los armónicos disponibles: {power:.12g}\n\nCada tallo representa el peso de una delta, no su altura ni una densidad finita. Parseval da P=Σ|c[k]|². Si faltan armónicos o los coeficientes se estimaron por cuadratura, el resultado sólo aproxima la potencia total. No se deben integrar los tallos con trapecios.',[weights])

def map_analog_frequency(analog,period,method):
    raw=float(analog)*float(period)
    if not math.isfinite(raw):raise ValueError('Ω·T excede el rango numérico.')
    if method in ('bilinear','inverse'):return 2*math.atan(raw/2)
    value=math.remainder(raw,math.tau)
    return -math.pi if value==math.pi else value


def frequency_mapping(omega,analog,period,method,direction,branch):
    if not np.isfinite(period) or period<=0:raise ValueError('T debe ser positivo y finito.')
    if method not in ('kaiser','butter','cheby1','cheby2','ellip','bilinear','impulse'):raise ValueError('Método de diseño no admitido.')
    if method=='bilinear':
        if direction!='to_digital' and not -np.pi<omega<np.pi:raise ValueError('La bilineal requiere −π<ω<π para frecuencia analógica finita.')
        if direction=='to_digital':result=map_analog_frequency(analog,period,method);unit='rad/muestra'
        elif direction=='to_analog':result=2/period*np.tan(omega/2);unit='rad/s'
        else:
            if analog==0:raise ValueError('Ω debe ser distinta de cero para determinar T.')
            result=2*np.tan(omega/2)/analog;unit='s'
        explanation='Ω=(2/T)tan(ω/2); ω=2 atan(ΩT/2). Para T fijado es un mapeo uno a uno entre Ω real y −π<ω<π.'
    else:
        if direction=='to_digital':result=map_analog_frequency(analog,period,method);unit='rad/muestra'
        elif direction=='to_analog':result=(omega+2*np.pi*branch)/period;unit='rad/s'
        else:
            if analog==0:raise ValueError('Ω debe ser distinta de cero para determinar T.')
            result=(omega+2*np.pi*branch)/analog;unit='s'
        explanation='ω≡ΩT (módulo 2π). La inversa tiene ramas Ω=(ω+2πk)/T: no es única. Para señales reales también deben considerarse las frecuencias conjugadas. Este mapeo no elimina el aliasing de espectros superpuestos.'
    if not np.isfinite(result) or (direction=='period' and result<=0):raise ValueError('La combinación no produce un valor finito válido; T debe ser positivo.')
    return bundle(f'Mapeo de frecuencia\n\nResultado: {result:.12g} {unit}\nRama k: {branch}\n\n'+explanation)
