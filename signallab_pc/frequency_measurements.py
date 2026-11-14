"""Definition-based frequency readings, finite bands and local level searches."""
import math
import numpy as np
from scipy.optimize import brentq,minimize_scalar
from .filters import Transfer
from .frequency_analysis import response_magnitudes
from .jobs import checkpoint
from .resources import ensure_working_set


def evaluate(data,omega,*,with_delay=True):
    """Keep the analyzed definition and its conditions, never interpolate H."""
    w=np.atleast_1d(np.asarray(omega,float))
    if not np.isfinite(w).all():raise ValueError('Las frecuencias deben ser reales y finitas.')
    ensure_working_set(w.size,live_arrays=24)
    model=data.system
    if isinstance(model,Transfer):
        extra=data.advance-model.advance
        with np.errstate(all='ignore'):h=model.response(w)*np.exp(1j*w*extra);delay=model.group_delay(w)-extra if with_delay else np.full(w.shape,np.nan)
    else:
        from .symbolic import parse
        from .analytic_frequency import _sample,_condition_mask,smooth_frequency_derivative
        frequency=parse(model.frequency_expression);eligible=_condition_mask(parse(model.condition),w)
        h=_sample(frequency,w,repair=True,eligible=eligible);h[~eligible]=complex(np.nan,np.nan)
        delay=np.full(w.shape,np.nan)
        if with_delay:
            derivative,jumps=smooth_frequency_derivative(frequency,w)
            slope=_sample(derivative,w,repair=True,eligible=eligible)
            with np.errstate(all='ignore'):
                scale=np.maximum(abs(h.real),abs(h.imag));normalized=h.real/scale+1j*(h.imag/scale)
                delay=-((slope.real/scale+1j*(slope.imag/scale))/normalized).imag
            delay=np.where(eligible&~jumps,delay,np.nan)
    magnitude,db=response_magnitudes(h);valid=np.isfinite(h)&(h!=0)
    return dict(omega=w,response=h,magnitude=magnitude,db=db,phase=np.where(valid,np.angle(h),np.nan),delay=np.where(valid&np.isfinite(delay),delay,np.nan))


def _number(value):return float(value) if np.isfinite(value) else None


def readings(data,frequencies):
    values=evaluate(data,frequencies);rows=[]
    for w,h,m,d,p,tau in zip(values['omega'],values['response'],values['magnitude'],values['db'],values['phase'],values['delay']):
        rows.append(dict(frequency=float(w),real=_number(h.real),imag=_number(h.imag),magnitude=_number(m),db=float(d) if not np.isnan(d) else None,phase=_number(p),delay=_number(tau)))
    return rows,values


def interval(data,low=None,high=None):
    low=float(data.omega[0]) if low is None else float(low);high=float(data.omega[-1]) if high is None else float(high)
    if not np.isfinite([low,high]).all() or not data.omega[0]<=low<high<=data.omega[-1]:
        raise ValueError('La banda debe ser creciente y quedar dentro del intervalo del último análisis. Ampliá ese análisis para observar otras frecuencias.')
    return low,high


def grid(data,low,high,count=2049):
    if isinstance(count,bool) or int(count)!=count or count<3:raise ValueError('Usá al menos tres puntos para medir una banda.')
    ensure_working_set(int(count)+len(data.omega),live_arrays=32)
    seeds=list(data.omega[(data.omega>=low)&(data.omega<=high)])
    model=data.system
    if isinstance(model,Transfer) and len(model.a)>1:
        from .transfer_plane import plane_poles,effective_plane_system
        for pole in plane_poles(effective_plane_system(model)):
            checkpoint()
            center=float(pole.imag) if model.domain=='analog' else float(np.angle(pole))
            width=abs(float(pole.real)) if model.domain=='analog' else abs(1-float(abs(pole)))
            centers=[center]
            if model.domain=='digital':
                first=math.ceil((low-center)/(2*np.pi));last=math.floor((high-center)/(2*np.pi))
                ensure_working_set(last-first+1,live_arrays=32)
                centers=[center+2*np.pi*k for k in range(first,last+1)]
            for c in centers:
                for offset in (-8.,-1.,0.,1.,8.):
                    value=c+offset*width
                    if low<=value<=high:seeds.append(value)
    return np.unique(np.r_[np.linspace(low,high,int(count)),seeds])


def _local_extrema(data,values):
    w=values['omega'];m=values['magnitude'];valid=np.isfinite(m);bad=int(np.count_nonzero(~valid));failed=0
    if not np.any(valid):return None,None,bad,failed
    ids=np.flatnonzero(valid);candidates=[(float(m[i]),float(w[i])) for i in (ids[np.argmin(m[ids])],ids[np.argmax(m[ids])])]
    for sign in (1.,-1.):
        q=sign*m
        noise=64*np.finfo(float).eps*np.maximum(np.maximum(abs(q[:-2]),abs(q[2:])),np.finfo(float).tiny)
        local=np.flatnonzero(valid[1:-1]&valid[:-2]&valid[2:]&(q[1:-1]<=q[:-2])&(q[1:-1]<=q[2:])&((q[:-2]-q[1:-1]>noise)|(q[2:]-q[1:-1]>noise)))+1
        for i in local:
            checkpoint();left,right=float(w[i-1]),float(w[i+1])
            def f(t):return sign*float(evaluate(data,[left+t*(right-left)],with_delay=False)['magnitude'][0])
            fit=minimize_scalar(f,bounds=(0.,1.),method='bounded',options={'xatol':1e-11,'maxiter':100})
            if fit.success and np.isfinite(fit.fun):candidates.append((sign*float(fit.fun),left+float(fit.x)*(right-left)))
            else:failed+=1
    return min(candidates),max(candidates),bad,failed


def band_measures(data,bands,*,count=2049,delay=False):
    rows=[];plots=[]
    if not bands:raise ValueError('Agregá al menos una banda.')
    ensure_working_set((int(count)+len(data.omega))*len(bands),live_arrays=32)
    for name,low,high,minimum,maximum in bands:
        checkpoint();low,high=interval(data,low,high)
        if minimum is not None and (not math.isfinite(minimum) or minimum<0):raise ValueError('El límite inferior de módulo debe ser no negativo y finito.')
        if maximum is not None and (not math.isfinite(maximum) or maximum<0):raise ValueError('El límite superior de módulo debe ser no negativo y finito.')
        if minimum is not None and maximum is not None and minimum>maximum:raise ValueError('El límite inferior de módulo no puede superar al superior.')
        values=evaluate(data,grid(data,low,high,count));small,large,bad,failed=_local_extrema(data,values)
        row=dict(name=name,low=low,high=high,minimum=None if small is None else small[0],minimum_at=None if small is None else small[1],maximum=None if large is None else large[0],maximum_at=None if large is None else large[1],lower_limit=minimum,upper_limit=maximum,undefined=bad,failed_refinements=failed)
        margins=([small[0]-minimum] if small is not None and minimum is not None else [])+([maximum-large[0]] if large is not None and maximum is not None else [])
        row['margin']=min(margins) if margins else None
        row['status']='Medición incompleta' if bad or failed or small is None else 'Sin límite solicitado' if not margins else 'Dentro en la comprobación numérica' if min(margins)>=0 else 'Fuera de los límites'
        if delay:
            tau=values['delay'];valid=np.isfinite(tau);ids=np.flatnonzero(valid)
            row.update(delay_points=int(len(ids)),delay_undefined=int(len(tau)-len(ids)))
            if len(ids):
                i,j=ids[np.argmin(tau[ids])],ids[np.argmax(tau[ids])]
                row.update(delay_min=float(tau[i]),delay_min_at=float(values['omega'][i]),delay_max=float(tau[j]),delay_max_at=float(values['omega'][j]),delay_median=float(np.median(tau[ids])),delay_spread=float(tau[j]-tau[i]))
        rows.append(row);plots.append(values)
    return rows,plots


def level_crossings(data,*,low=None,high=None,count=2049,level=-3.010299956639812,relative=True,reference=0.):
    low,high=interval(data,low,high);level=float(level)
    if not math.isfinite(level):raise ValueError('El nivel debe ser finito.')
    reference_db=0.
    if relative:
        reference_db=float(evaluate(data,[reference],with_delay=False)['db'][0])
        if not math.isfinite(reference_db):raise ValueError('La frecuencia de referencia debe tener un módulo finito no nulo, representable en dB.')
        target=reference_db+level
    else:
        if level<=0:raise ValueError('El nivel absoluto de módulo debe ser positivo.')
        target=20*math.log10(level)
    if not math.isfinite(target):raise ValueError('El nivel de comparación excede el rango numérico.')
    w=grid(data,low,high,count);values=evaluate(data,w)
    def normalized(db):
        with np.errstate(all='ignore'):return np.tanh((db-target)*(math.log(10)/20))
    def function(x):return float(normalized(evaluate(data,[x],with_delay=False)['db'][0]))
    y=normalized(values['db']);finite=np.isfinite(y);near=finite&(abs(y)<=1e-10);flat=np.zeros(len(w),bool);flat[:-1]|=near[:-1]&near[1:];flat[1:]|=near[:-1]&near[1:]
    roots=[];rejected=0
    def add(x):
        nonlocal rejected
        residual=function(x)
        if not np.isfinite(residual) or abs(residual)>1e-9:rejected+=1;return
        if not any(abs(x-old)<=32*max(math.ulp(float(x)),math.ulp(old)) for old in roots):roots.append(float(x))
    for i in np.flatnonzero(near&~flat):add(w[i])
    pairs=np.flatnonzero(finite[:-1]&finite[1:]&~flat[:-1]&~flat[1:]&(np.signbit(y[:-1])!=np.signbit(y[1:])))
    for i in pairs:
        checkpoint();left,right=float(w[i]),float(w[i+1])
        try:
            t=brentq(lambda t:function(left+t*(right-left)),0.,1.,xtol=8*np.finfo(float).eps,rtol=8*np.finfo(float).eps)
            add(left+t*(right-left))
        except (ValueError,RuntimeError,OverflowError):rejected+=1
    local=np.flatnonzero(finite[1:-1]&finite[:-2]&finite[2:]&~flat[1:-1]&(abs(y[1:-1])<abs(y[:-2]))&(abs(y[1:-1])<abs(y[2:])))+1
    for i in local:
        if np.signbit(y[i-1])!=np.signbit(y[i+1]):continue
        checkpoint();left,right=float(w[i-1]),float(w[i+1])
        if any(left<=root<=right for root in roots):continue
        try:
            fit=minimize_scalar(lambda t:abs(function(left+t*(right-left))),bounds=(0.,1.),method='bounded',options={'xatol':1e-13,'maxiter':100})
            if not fit.success:rejected+=1
            elif fit.fun<=1e-10:add(left+float(fit.x)*(right-left))
        except (ValueError,RuntimeError,OverflowError):rejected+=1
    roots.sort();rows,_=readings(data,roots);nonisolated=bool(flat.any());bad=int(np.count_nonzero(~finite));complete=not (rejected or bad or nonisolated);bands=[]
    if complete:
        edges=np.unique([low,*roots,high])
        for left,right in zip(edges[:-1],edges[1:]):
            middle=function(left+(right-left)/2)
            if not math.isfinite(middle):complete=False;bad+=1
            elif right>left and middle>0:bands.append(dict(low=float(left),high=float(right),width=float(right-left),window_limited=bool(left==low or right==high)))
        if not complete:bands=[]
    return dict(rows=rows,plot=[values],target_db=target,relative=relative,level=level,reference=reference if relative else None,reference_db=reference_db if relative else None,above=bands,partition_complete=complete,nonisolated=nonisolated,undefined=bad,rejected=rejected,low=low,high=high)


def analyze(data,mode,**options):
    base=dict(mode=mode,units=data.units,delay_units='muestras' if data.system.domain=='digital' else 's',system=data.system.to_document(),extra_advance=int(data.advance-data.system.advance),point_phase='principal',source_interval=[float(data.omega[0]),float(data.omega[-1])])
    if mode=='points':rows,values=readings(data,options['frequencies']);result=dict(rows=rows,plot=[values])
    elif mode=='level':result=level_crossings(data,**options)
    elif mode in ('bands','delay'):
        rows,values=band_measures(data,delay=mode=='delay',**options);result=dict(rows=rows,plot=values)
    else:raise ValueError('Medición de frecuencia no admitida.')
    base.update(result)
    base['scope']='Se evalúa la definición del último resultado, con sus condiciones. Los extremos y cruces son estimaciones numéricas dentro de los intervalos indicados; no certifican todos los puntos ni lo que ocurre fuera. La fase puntual es el ángulo principal; el retardo no se define en ceros, polos o saltos.'
    return base


def summary(result):
    from .result_summary import Summary,Section,number
    titles={'points':'Lecturas de la definición','level':'Cruces de nivel','bands':'Bandas y tolerancias','delay':'Retardo de grupo por banda'}
    sections=[Section('Definición y alcance',paragraphs=[result['scope']],rows=[('Frecuencias',result['units']),('Retardo de grupo',result['delay_units'])])]
    show=lambda x:'No definido' if x is None else '−∞' if np.isneginf(x) else number(x)
    if result['mode']=='level':
        sections.append(Section('Nivel buscado',rows=[('Módulo absoluto (dB)',show(result['target_db'])),('Cruces aislados encontrados',str(len(result['rows']))),('Intervalos rechazados',str(result['rejected'])),('Puntos no definidos',str(result['undefined']))],paragraphs=['Nivel relativo a |H| en la frecuencia de referencia.' if result['relative'] else 'Nivel absoluto en amplitud lineal.','Hay tramos indistinguibles del nivel; no se asigna una frecuencia única.' if result['nonisolated'] else 'Un salto entre dos valores no se acepta como cruce si la definición no alcanza el nivel.']))
        if result['partition_complete']:
            for band in result['above']:sections.append(Section('Tramo observado por encima del nivel',rows=[('Desde',show(band['low'])),('Hasta',show(band['high'])),('Ancho observado',show(band['width']))],paragraphs=['El tramo toca el borde de la ventana: no se presenta como ancho de banda completo.' if band['window_limited'] else 'Ambos extremos son cruces encontrados dentro de la ventana.']))
        else:sections.append(Section('Tramos pendientes',paragraphs=['No se asignan anchos de banda: hay valores no definidos, tramos sobre el nivel o candidatos sin resolver. Los cruces que sí se resolvieron se conservan en la tabla.']))
    if result['mode'] in ('bands','delay'):
        for row in result['rows']:
            fields=[('Desde',row['low']),('Hasta',row['high']),('Mínimo |H|',row['minimum']),('En frecuencia',row['minimum_at']),('Máximo |H|',row['maximum']),('En frecuencia',row['maximum_at']),('Margen de amplitud',row['margin'])]
            if result['mode']=='delay':fields.extend([('Menor retardo observado',row.get('delay_min')),('En frecuencia',row.get('delay_min_at')),('Mayor retardo observado',row.get('delay_max')),('En frecuencia',row.get('delay_max_at')),('Mediana de retardos',row.get('delay_median')),('Variación observada',row.get('delay_spread')),('Puntos sin retardo definido',row['delay_undefined'])])
            sections.append(Section(row['name'],rows=[(key,show(v)) for key,v in fields],paragraphs=[row['status'],'Los extremos de módulo se refinan localmente. Las estadísticas de retardo utilizan los puntos evaluados, sin promediar a través de valores no definidos.']))
    else:
        for row in result['rows'][:20]:sections.append(Section('Frecuencia '+show(row['frequency'])+' '+result['units'],rows=[('Parte real',show(row['real'])),('Parte imaginaria',show(row['imag'])),('Módulo',show(row['magnitude'])),('Módulo (dB)',show(row['db'])),('Ángulo principal (rad)',show(row['phase'])),('Retardo de grupo',show(row['delay']))]))
        if len(result['rows'])>20:sections.append(Section('Tabla completa',paragraphs=['El informe resume las primeras 20 lecturas. La tabla y el CSV conservan todas.']))
    return Summary(titles[result['mode']],sections)
