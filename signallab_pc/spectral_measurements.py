"""Band measures and moments with explicit density/bin semantics and logarithmic sums."""
import math
import numpy as np
from scipy.special import logsumexp
from scipy.signal import find_peaks
from .model import Signal
from .resources import ensure_working_set
from .jobs import checkpoint
from .stft_tools import logarithmic_magnitude


def power_lines(source):
    m=source.metadata
    return source.domain=='frequency' and source.units=='rad/s' and m.get('operation')=='continuous_fourier_series' and (m.get('power_line_weights') is True or m.get('distribution')=='Dirac weights, not finite density heights')


def series_coefficients(source):
    return source.data_kind=='harmonics' and source.metadata.get('operation') in ('continuous_fourier_series','discrete_fourier_series')


def supported(source):
    return (source.domain=='frequency' and source.units in ('rad/s','rad/muestra','Hz') and (source.data_kind!='spectral_lines' or power_lines(source)) and source.data_kind!='spectral_measurement') or source.data_kind=='dft_bins' or series_coefficients(source)


def quantity(logvalue):
    """JSON-safe finite values; keep nonzero values outside float64 as scientific text."""
    if logvalue==-np.inf:return dict(value=0.,text='0',log_value=None)
    if not math.isfinite(logvalue):raise ValueError('La medida no tiene una escala numérica finita.')
    exponent=math.floor(logvalue/math.log(10));mantissa=math.exp(logvalue-exponent*math.log(10))
    try:value=math.exp(logvalue)
    except OverflowError:value=None
    if value==0 or value is not None and not math.isfinite(value):value=None
    return dict(value=value,text=format(value,'.12g') if value is not None else f'{mantissa:.12g}e{exponent} (fuera de float64)',log_value=float(logvalue))


def prepare(source,interpretation='auto'):
    if not supported(source):raise ValueError('Cargá un espectro, una densidad o una DFT. Las distribuciones generales y las medidas acumuladas requieren otra interpretación.')
    from .inverse_frequency_domain import require_defined_samples
    require_defined_samples(source)
    if interpretation not in ('auto','spectrum','energy_density','power_density','density_per_unit','area'):raise ValueError('Interpretación espectral no reconocida.')
    m=source.metadata;op=m.get('operation');n=len(source.values);x=source.axis.astype(float)
    ensure_working_set(n,live_arrays=32)
    if source.step<=0 or not np.all(np.isfinite(x)) or n>1 and np.any(np.diff(x)<=0):raise ValueError('Se requiere un eje creciente con frecuencias distinguibles.')
    if m.get('estimator')=='legacy':raise ValueError('El periodograma sin calibración no es una densidad. Recalculá con Welch calibrado o Un segmento calibrado.')
    is_lines=power_lines(source);is_coeff=series_coefficients(source);units='k' if is_coeff or source.data_kind=='dft_bins' else source.units;bins=False;periodic=False;label='Energía';rule='Integración de una densidad lineal por tramos; sólo el intervalo observado.'
    if is_coeff:
        interpretation='coefficient_power';label='Potencia';bins=True;rule='Parseval para coeficientes de serie normalizados: suma |c[k]|². Sólo los armónicos disponibles.'
    elif is_lines:
        interpretation='power_density';label='Potencia';bins=True
        rule='Suma de pesos de líneas de potencia divididos por 2π. No se interpretan como alturas ni se elevan al cuadrado.'
    elif interpretation=='auto':
        interpretation='area' if source.data_kind=='frequency_response' else 'power_density' if op in ('spectral_density','welch','periodogram') else 'energy_density' if op=='energy_density' else 'spectrum'
        if interpretation=='power_density' and (m.get('density_convention')=='per_coordinate' or ('frame' in m and m.get('nfft')==n and '2*pi*Fs' in m.get('normalization',''))):interpretation='density_per_unit'
    if not is_lines:
        from .distributions import regular_only
        regular_only(source,'Las medidas de espectros ordinarios; usá pesos de líneas de potencia para distribuciones periódicas')
    if interpretation=='coefficient_power':logs=2*logarithmic_magnitude(source.values)
    elif interpretation in ('energy_density','power_density','density_per_unit'):
        if np.any(source.values.imag) or np.any(source.values.real<0):raise ValueError('Una densidad o peso de potencia requiere valores reales no negativos. No se descarta parte imaginaria ni se recortan negativos.')
        with np.errstate(divide='ignore'):logs=np.log(source.values.real)
        label='Energía' if interpretation=='energy_density' else 'Potencia'
        if is_lines:logs-=math.log(math.tau)
        else:
            angular_factor=interpretation in ('energy_density','power_density') and source.units!='Hz'
            if angular_factor:logs-=math.log(math.tau)
            rule=('Integral con dω/(2π).' if angular_factor else 'Integral directa en la unidad del eje.')+' Se interpola linealmente la densidad dentro del intervalo disponible.'
            # Known FFT density samples represent bins; include the final bin once.
            fft_count=m.get('segment',m.get('nfft',0))
            known=op in ('spectral_density','welch','periodogram') and isinstance(fft_count,(int,np.integer)) and fft_count>=n
            periodic_energy=op=='energy_density' and m.get('discrete_spectrum') and math.isclose(source.step*n,math.tau,rel_tol=1e-10,abs_tol=0)
            if known or periodic_energy:bins=True;periodic=periodic_energy or fft_count==n;logs+=math.log(source.step)
    else:
        if source.data_kind=='density':raise ValueError('La entrada ya es una densidad. Cargá X o H para medir un módulo al cuadrado.')
        logs=2*logarithmic_magnitude(source.values)
        if interpretation=='area':label='Área de |H|²';rule='Integral de |H|² en la unidad del eje, sin factor de Parseval; no es energía de una señal.'
        elif op=='DFT':
            count=m.get('N',n)
            if isinstance(count,bool) or int(count)!=count or count<n:raise ValueError('La DFT no conserva una longitud N válida.')
            count=int(count);bins=True;periodic=count==n;logs-=math.log(count)
            if source.units=='rad/muestra':
                if not math.isclose(source.step*count,math.tau,rel_tol=1e-10,abs_tol=0):raise ValueError('La separación de la DFT no coincide con N.')
                if periodic and not (math.isclose(float(x[0]),0,abs_tol=1e-12) or math.isclose(float(x[0]),-(count//2)*source.step,rel_tol=1e-10,abs_tol=1e-12)):raise ValueError('El origen de la DFT no coincide con su orden. Conservá su rejilla original.')
            rule='Parseval: suma |X[k]|²/N por bins [inicio, fin), sin interpolar coeficientes.'
        elif op=='stft':
            if m.get('nfft')!=n or not m.get('window_gain',0)>0:raise ValueError('La STFT no conserva su normalización. Usá la densidad de la ventana o el tramo enventanado.')
            bins=True;periodic=True;logs+=2*math.log(m['window_gain'])-math.log(n)
            if m['input_domain']=='continuous':logs+=math.log(m['input_step'])
            label='Energía del tramo enventanado';rule='Se deshace la normalización por Σw y se aplica Parseval a la FFT de la ventana.'
        else:
            if source.units=='rad/s' and op=='DTFT':raise ValueError('Esta DTFT no registra la conversión de frecuencia física. Cargá su eje original en rad/muestra.')
            if source.units!='Hz':logs-=math.log(math.tau)
            rule=('Integral de |X|² con dω/(2π).' if source.units!='Hz' else 'Integral de |X(f)|² df.')+' La densidad se interpola linealmente entre las muestras.'
    if bins:
        if is_lines or is_coeff:low,high=float(x[0]),float(x[-1]+source.step)
        elif units in ('bin k','k'):low,high=float(x[0]),float(x[0]+n)
        elif periodic:
            width=source.step*n;physical_rate=None
            if source.units=='rad/muestra' and math.isclose(width,math.tau,rel_tol=1e-10,abs_tol=0):width=math.tau
            elif source.units=='Hz' and m.get('sample_rate_hz') is not None:
                expected=float(m['sample_rate_hz'])
                if math.isfinite(expected) and expected>0 and math.isclose(width,expected,rel_tol=1e-10,abs_tol=0):width=expected
            elif source.units=='rad/s' and m.get('input_domain') in ('continuous','discrete'):
                physical_rate=1/float(m['input_step']) if m['input_domain']=='continuous' else float(m.get('input_clock',{}).get('sample_rate_hz',width/math.tau))
                expected=math.tau*physical_rate
                if math.isfinite(expected) and expected>0 and math.isclose(width,expected,rel_tol=1e-10,abs_tol=0):width=expected
                else:physical_rate=None
            centered=m.get('dft_order')=='centered' or x[0]<0 or n==1
            low,high=(-width/2,width/2) if centered else (float(x[0]),float(x[0]+width))
            if source.units=='rad/muestra':
                from .fourier_phase import bin_frequency
                x=bin_frequency(np.arange(n)-(n//2 if centered else 0),n)
            elif physical_rate is not None:
                from .fourier_phase import bin_frequency
                x=bin_frequency(np.arange(n)-(n//2 if centered else 0),n)*physical_rate
        else:low,high=float(x[0]),float(x[-1]+source.step)
        if interpretation in ('energy_density','power_density','density_per_unit') and not is_lines:rule='Suma de densidad × ancho de bin'+(' / (2π)' if interpretation in ('energy_density','power_density') and source.units!='Hz' else '')+'. El extremo derecho no se incluye, para no contar un bin dos veces.'
    else:
        if n<2:raise ValueError('Una curva necesita al menos dos frecuencias. Un único valor sólo permite una medida si está identificado como bin.')
        low,high=float(x[0]),float(x[-1])
    if not math.isfinite(low) or not math.isfinite(high) or not low<high:raise ValueError('El intervalo disponible excede el rango numérico.')
    return dict(x=x,logs=logs,input_logs=logarithmic_magnitude(source.values),bins=bins,periodic=periodic,lines=is_lines or is_coeff,low=low,high=high,units=units,label=label,rule=rule,interpretation=interpretation)


def interpolate_log(x,logs,points):
    index=np.clip(np.searchsorted(x,points,side='right')-1,0,len(x)-2)
    ratio=(points-x[index])/(x[index+1]-x[index])
    with np.errstate(divide='ignore'):
        return np.logaddexp(logs[index]+np.log1p(-ratio),logs[index+1]+np.log(ratio))


def band_log(profile,low,high):
    if not math.isfinite(low) or not math.isfinite(high) or not profile['low']<=low<high<=profile['high']:raise ValueError('La banda debe estar ordenada y contenida en el intervalo disponible.')
    x=profile['x'];logs=profile['logs']
    if profile['bins']:return float(logsumexp(logs[(x>=low)&(x<high)]))
    inside=(x>low)&(x<high);coords=np.r_[low,x[inside],high]
    sampled=np.r_[interpolate_log(x,logs,np.array([low]))[0],logs[inside],interpolate_log(x,logs,np.array([high]))[0]]
    return float(logsumexp(np.log(np.diff(coords))+np.logaddexp(sampled[:-1],sampled[1:])-math.log(2)))


def moments(profile,total):
    x=profile['x'];logs=profile['logs']
    if total==-np.inf:return dict(centroid=None,rms_width=None,reason='No hay peso positivo; el centro y el ancho no están definidos.')
    if profile['bins']:nodes=x;mass=logs
    else:
        u=np.array([(1-math.sqrt(3/5))/2,.5,(1+math.sqrt(3/5))/2]);weights=np.array([5/18,4/9,5/18])
        nodes=(x[:-1,None]*(1-u)+x[1:,None]*u).ravel()
        a=logs[:-1,None]+np.log1p(-u);b=logs[1:,None]+np.log(u)
        mass=(np.logaddexp(a,b)+np.log(np.diff(x))[:,None]+np.log(weights)).ravel()
    with np.errstate(divide='ignore'):first,sign=logsumexp(mass+np.log(abs(nodes)),b=np.sign(nodes),return_sign=True)
    center=0. if sign==0 else quantity(float(first-total))['value']
    if center is None:return dict(centroid=None,rms_width=None,reason='El centro no se puede representar en float64.')
    center=float(sign*center);scale=np.maximum(abs(nodes),abs(center))
    with np.errstate(divide='ignore',invalid='ignore'):
        logdistance=np.where(scale>0,np.log(scale)+np.log(abs(nodes/scale-center/scale)),-np.inf)
    variance=float(logsumexp(mass+2*logdistance)-total);width=quantity(variance/2)
    return dict(centroid=center,rms_width=width['value'],width_text=width['text'],reason='Son momentos lineales de la medida disponible, no una banda ocupada. En un eje periódico dependen del corte elegido para el período; no certifican el espectro fuera del intervalo.')


def peak_rows(profile,level_db=-40.,prominence_percent=1.,interpolate=False):
    if not math.isfinite(level_db) or level_db>0 or not math.isfinite(prominence_percent) or not 0<=prominence_percent<=100:raise ValueError('El nivel debe ser ≤0 dB y la prominencia debe estar entre 0 y 100 %.')
    logs=profile['logs'];finite=np.isfinite(logs)
    if not np.any(finite):return []
    peak=float(np.max(logs[finite]));n=len(logs);threshold=peak+level_db*math.log(10)/10;prominences=None
    if profile['lines'] or n==1:indices=np.flatnonzero(finite&(logs>=threshold));props=None
    else:
        values=np.tile(logs,3) if profile['periodic'] else logs
        found,props=find_peaks(values,height=threshold,plateau_size=(1,None))
        keep=(found>=n)&(found<2*n) if profile['periodic'] else np.ones(len(found),bool)
        found=found[keep];props={k:v[keep] for k,v in props.items()};prominences=log_prominences(values,found)-peak
        keep=prominences>=math.log(prominence_percent/100) if prominence_percent else np.ones(len(found),bool)
        indices=found[keep]-(n if profile['periodic'] else 0);prominences=prominences[keep];props={k:v[keep] for k,v in props.items()}
    rows=[]
    for pos,index in enumerate(indices):
        estimate=None;plateau=int(props['plateau_sizes'][pos]) if props is not None else 1
        if interpolate and plateau==1 and n>=3 and (profile['periodic'] or 0<index<n-1):
            left,mid,right=logs[(index-1)%n],logs[index],logs[(index+1)%n];curve=left-2*mid+right
            if np.all(np.isfinite([left,mid,right])) and curve<0:
                offset=.5*(left-right)/curve
                if abs(offset)<=.5:
                    estimate=float(profile['x'][index]+offset*(profile['x'][1]-profile['x'][0]))
                    if profile['periodic']:estimate=profile['low']+(estimate-profile['low'])%(profile['high']-profile['low'])
        rows.append(dict(index=int(index),frequency=float(profile['x'][index]),estimated_frequency=estimate,relative_db=float(10/math.log(10)*(logs[index]-peak)),level=quantity(float(logs[index]))['text'],prominence_percent=math.exp(float(prominences[pos]))*100 if prominences is not None else None,plateau=plateau,kind='línea' if profile['lines'] else 'bin único' if n==1 else 'máximo local'))
    if not profile['periodic'] and not profile['lines'] and n>1:
        for i,j in ((0,1),(n-1,n-2)):
            if logs[i]>=threshold and logs[i]>logs[j]:rows.append(dict(index=i,frequency=float(profile['x'][i]),estimated_frequency=None,relative_db=float(10/math.log(10)*(logs[i]-peak)),level=quantity(float(logs[i]))['text'],prominence_percent=None,plateau=1,kind='extremo del intervalo; sin prominencia'))
    for row in rows:row['input_level']=quantity(float(profile['input_logs'][row['index']]))['text']
    return sorted(rows,key=lambda row:(-row['relative_db'],row['frequency']))


def log_prominences(values,indices):
    """Strictly higher neighbours + vector range minima avoid quadratic scans."""
    n=len(values);left=np.empty(n,dtype=np.int64);right=np.empty(n,dtype=np.int64);stack=[]
    for i,value in enumerate(values):
        while stack and values[stack[-1]]<=value:stack.pop()
        left[i]=stack[-1] if stack else 0;stack.append(i)
    stack=[]
    for i in range(n-1,-1,-1):
        while stack and values[stack[-1]]<=values[i]:stack.pop()
        right[i]=stack[-1] if stack else n-1;stack.append(i)
    size=1<<(n-1).bit_length();tree=np.full(2*size,np.inf);tree[size:size+n]=values
    width=size
    while width>1:tree[width//2:width]=np.minimum(tree[width:2*width:2],tree[width+1:2*width:2]);width//=2
    def minimum(a,b):
        a=a+size;b=b+size+1;result=np.full(len(a),np.inf)
        while np.any(a<b):
            take=(a<b)&((a&1)==1);result[take]=np.minimum(result[take],tree[a[take]]);a[take]+=1
            take=(a<b)&((b&1)==1);b[take]-=1;result[take]=np.minimum(result[take],tree[b[take]])
            a//=2;b//=2
        return result
    base=np.maximum(minimum(left[indices],indices),minimum(indices,right[indices]))
    with np.errstate(divide='ignore',invalid='ignore'):return values[indices]+np.log(-np.expm1(base-values[indices]))


def analyze(source,bands,*,interpretation='auto',level_db=-40.,prominence_percent=1.,interpolate=False):
    profile=prepare(source,interpretation);total=band_log(profile,profile['low'],profile['high']);rows=[]
    for index,(name,low,high) in enumerate(bands):
        checkpoint(index/max(1,len(bands)));low=profile['low'] if low is None else float(low);high=profile['high'] if high is None else float(high)
        logvalue=band_log(profile,low,high);fraction=None if total==-np.inf else min(1.,math.exp(min(0.,logvalue-total)))
        rows.append(dict(name=name or 'Banda '+str(index+1),low=low,high=high,measure=quantity(logvalue),fraction=fraction))
    if not rows:raise ValueError('Agregá al menos una banda.')
    ordered=sorted(rows,key=lambda row:row['low']);end=-np.inf;overlap=False
    for row in ordered:overlap=overlap or row['low']<end;end=max(end,row['high'])
    m=moments(profile,total);peaks=peak_rows(profile,level_db,prominence_percent,interpolate)
    if profile['bins']:mass=profile['logs']
    else:mass=np.r_[-np.inf,np.log(np.diff(profile['x']))+np.logaddexp(profile['logs'][:-1],profile['logs'][1:])-math.log(2)]
    if total==-np.inf:cumulative=None
    else:
        values=np.minimum(1.,np.cumsum(np.exp(mass-total)));values[-1]=1.
        cumulative=Signal(values,source.origin,source.step,profile['units'],'Fracción espectral acumulada','frequency',metadata=dict(operation='spectral_fraction',quantity=profile['label'],rule=profile['rule'],bins=profile['bins'],bounds=[profile['low'],profile['high']]))
    report=profile['label']+' por bandas\n\n'+profile['rule']+'\nUnidad del eje: '+profile['units']+'\nIntervalo disponible: ['+format(profile['low'],'.12g')+', '+format(profile['high'],'.12g')+']\nTotal disponible: '+quantity(total)['text']
    for row in rows:report+='\n\n'+row['name']+': ['+format(row['low'],'.12g')+', '+format(row['high'],'.12g')+(')' if profile['bins'] else ']')+'\n'+profile['label']+': '+row['measure']['text']+'\nFracción del total disponible: '+('no definida' if row['fraction'] is None else format(100*row['fraction'],'.9g')+' %')
    report+='\n\nLas bandas se solapan; no sumes sus porcentajes como una partición.' if overlap else '\n\nLas bandas no se solapan. Los porcentajes se refieren sólo al intervalo disponible.'
    report+='\n\nCentro espectral: '+('no definido' if m['centroid'] is None else format(m['centroid'],'.12g')+' '+profile['units'])+'\nAncho RMS respecto del centro: '+m.get('width_text','no definido')+'\n'+m['reason']
    report+='\n\nLos picos se buscan sobre las muestras disponibles. La frecuencia interpolada, si se solicita, es una aproximación parabólica y no aumenta la resolución del registro. Los extremos no tienen prominencia definida. Una fracción acumulada no conserva la fase ni puede usarse como espectro para una inversa.'
    if source.metadata.get('dc_line_weight',0):report+='\n\nEsta PSD corresponde a las fluctuaciones y excluye la línea de media en cero. Su peso registrado no se sumó automáticamente a estas medidas.'
    return dict(report=report,bands=rows,total=quantity(total),moments=m,peaks=peaks,cumulative=cumulative,limits=[profile['low'],profile['high']],units=profile['units'],quantity=profile['label'],rule=profile['rule'],interpretation=profile['interpretation'],overlap=overlap,bins=profile['bins'])


def stft_band_series(data,bands,physical=False):
    from .stft_tools import axes,density_spectrum
    _,centers,_,time_unit,rate=axes(data,physical);m=data['metadata'];outputs=[]
    ensure_working_set(m['frames']*max(1,len(bands)),live_arrays=12)
    collected=[[] for _ in bands]
    for frame in range(m['frames']):
        checkpoint(frame/m['frames']);profile=prepare(density_spectrum(data,frame,physical));
        for index,(_,low,high) in enumerate(bands):
            value=quantity(band_log(profile,profile['low'] if low is None else low,profile['high'] if high is None else high))
            if value['value'] is None:raise ValueError('La potencia de una banda excede float64; no se publica una curva con ceros ficticios.')
            collected[index].append(value['value'])
    for (name,low,high),values in zip(bands,collected):
        metadata=dict(operation='stft_band_power',window_length=m['window_length'],hop=m['hop'],nfft=m['nfft'],band=[low,high],frequency_units='rad/s' if physical or m['input_domain']=='continuous' else 'rad/muestra',scope='Window-square-weighted finite-frame power; no detrending')
        if m['input_domain']=='continuous' or physical:
            step=m['hop']*(m['input_step'] if m['input_domain']=='continuous' else 1/rate)
            outputs.append(Signal(values,float(centers[0]),step,time_unit,'Potencia · '+(name or 'banda'),'continuous',metadata=metadata))
        else:
            metadata.update(frame_center_start=float(centers[0]),frame_center_step=m['hop'],frame_center_units=m['time_units'])
            clock=m['input_clock']
            if 'sample_rate_hz' in clock:
                fs=float(clock['sample_rate_hz']);new_rate=fs/m['hop']
                if not math.isfinite(new_rate) or new_rate<=0:raise ValueError('El reloj de las ventanas excede el rango numérico.')
                metadata.update(sample_rate_hz=new_rate,time_start_s=float(clock.get('time_start_s',m['input_origin']/fs))+(float(centers[0])-m['input_origin'])/fs)
            outputs.append(Signal(values,0,1,'n','Potencia por ventana · '+(name or 'banda'),'discrete',metadata=metadata))
    return outputs
