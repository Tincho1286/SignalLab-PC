"""Inspect stored curve definitions and extrema of actual evaluated points."""
import ast
import numpy as np
from scipy.signal import find_peaks
from .resources import ensure_working_set


def system_curve(artist,system,component,*,advance=0,phase_kind='continuous'):
    artist._signallab_curve_definition=dict(system=system,component=component,advance=int(advance),phase_kind=phase_kind)


def stored_curve(artists,x,y,source,component):
    from matplotlib.container import StemContainer
    targets=[artists.markerline] if isinstance(artists,StemContainer) else artists if isinstance(artists,(tuple,list)) else [artists]
    for artist in targets:artist._signallab_probe_curve=(x,y);artist._signallab_curve_input=(source,component)


def coordinate_expression(expression,variable):
    """Numeric editors alias x/t/n/k/w to one coordinate; do not edit callees."""
    from .math_source import normalize
    tree=ast.parse(normalize(expression),mode='eval')
    class Coordinate(ast.NodeTransformer):
        def visit_Name(self,node):return ast.copy_location(ast.Name(id=variable,ctx=node.ctx),node) if node.id.lower() in ('x','t','n','k','w') else node
        def visit_Call(self,node):
            node.args=[self.visit(a) for a in node.args]
            for keyword in node.keywords:keyword.value=self.visit(keyword.value)
            return node
    return ast.unparse(Coordinate().visit(tree))


def values(trace):
    if getattr(trace,'cell_values',False) or getattr(trace,'spatial',True):raise ValueError('Esta operación requiere una curva de una variable. Un plano de polos/ceros o un mapa tiene otra interpretación.')
    source=getattr(trace.artist,'_signallab_probe_source',None)
    if source is not None:
        signal,component=source;x=signal.axis;z=signal.values
        with np.errstate(all='ignore'):
            y=z.real if component=='real' else z.imag if component=='imag' else np.abs(z) if component=='magnitude' else np.where(z.real>0,10*np.log10(z.real),np.nan) if component=='density_db' else np.where(z!=0,np.angle(z),np.nan)
        return x,np.asarray(y),True
    full=getattr(trace.artist,'_signallab_probe_curve',None)
    if full is not None:return np.asarray(full[0]),np.asarray(full[1]),True
    full=getattr(trace.artist,'_signallab_probe_values',None)
    if full is not None:
        origin,step,y=full;return origin+step*np.arange(len(y)),np.asarray(y),True
    return trace.x,trace.y,False


def extrema(trace,low=None,high=None,local=False):
    x,y,complete=values(trace);ensure_working_set(int(len(x)),live_arrays=8)
    if low is not None and high is not None and low>high:raise ValueError('El intervalo debe estar ordenado.')
    valid=np.isfinite(x)&np.isfinite(y)
    if low is not None:valid&=x>=low
    if high is not None:valid&=x<=high
    ids=np.flatnonzero(valid)
    if not len(ids):raise ValueError('No hay valores finitos de esta curva en el intervalo elegido.')
    minimum=int(ids[np.argmin(y[ids])]);maximum=int(ids[np.argmax(y[ids])]);records=[]
    def add(index,kind,plateau=1):
        records.append(dict(kind=kind,index=int(index),x=int(x[index]) if x.dtype.kind in 'iu' else float(x[index]),y=float(y[index]),plateau=int(plateau)))
    if minimum==maximum or y[minimum]==y[maximum]:add(minimum,'Máximo y mínimo (constante)')
    else:add(maximum,'Máximo de los puntos');add(minimum,'Mínimo de los puntos')
    if local:
        selected={minimum,maximum}
        source=getattr(trace.artist,'_signallab_probe_source',None);context=getattr(trace.artist,'_signallab_curve_definition',{})
        principal=(source is not None and source[1]=='phase') or context.get('component')=='phase' and context.get('phase_kind')!='continuous'
        breaks=np.diff(ids)>1
        if principal:breaks|=abs(np.diff(y[ids]))>np.pi
        for segment in np.split(ids,np.flatnonzero(breaks)+1):
            if len(segment)<3:continue
            for sign,kind in ((1,'Máximo local'),(-1,'Mínimo local')):
                found,props=find_peaks(sign*y[segment],plateau_size=(1,None));ensure_working_set(int(len(records)+len(found)),bytes_per_sample=320,live_arrays=3)
                for index,size in zip(segment[found],props['plateau_sizes']):
                    if index not in selected:add(int(index),kind,size);selected.add(int(index))
    return dict(rows=records,points=int(len(ids)),complete=complete,low=low,high=high,local=bool(local),scope='Extremos de los puntos finitos evaluados, no una optimización algebraica entre muestras. Los máximos locales son interiores a cada tramo sin huecos; no se cruza un NaN ni se extrapola.')


def nearest(trace,coordinate):
    x,y,_=values(trace);valid=np.flatnonzero(np.isfinite(x)&np.isfinite(y))
    if not len(valid):raise ValueError('Esta curva no tiene puntos finitos para leer.')
    ordered=x[valid];descending=len(ordered)>1 and ordered[-1]<ordered[0]
    if descending:ordered=ordered[::-1];valid=valid[::-1]
    where=int(np.searchsorted(ordered,coordinate));candidates=[i for i in (where-1,where) if 0<=i<len(valid)];index=int(valid[min(candidates,key=lambda i:abs((int(ordered[i]) if ordered.dtype.kind in 'iu' else float(ordered[i]))-coordinate))])
    return index,int(x[index]) if x.dtype.kind in 'iu' else float(x[index]),float(y[index])


def adjacent(trace,coordinate,direction):
    x,y,_=values(trace);index,_,_=nearest(trace,coordinate);valid=np.flatnonzero(np.isfinite(x)&np.isfinite(y));position=int(np.searchsorted(valid,index));index=int(valid[min(max(position+direction,0),len(valid)-1)])
    return int(x[index]) if x.dtype.kind in 'iu' else float(x[index])


def definition(trace):
    from .result_summary import Summary,Section,Formula,number
    sections=[];context=getattr(trace.artist,'_signallab_curve_definition',None)
    if context is not None:
        system=context['system'];digital=system.domain=='digital';variable='z' if digital else 's';name='H('+variable+')'
        from .filters import Transfer
        if isinstance(system,Transfer):
            from .phase_summary import transfer_formula
            formula,compact=transfer_formula(system);sections.append(Section('Sistema que define la curva',formulas=[formula]))
            if compact:sections.append(Section('Coeficientes numéricos de las sumas',rows=[('b[k]',', '.join(number(v) for v in system.b)),('a[k]',', '.join(number(v) for v in system.a))]))
        else:
            name='F(w)';sections.append(Section('Definición de frecuencia almacenada',formulas=[Formula('F(w) = '+system.frequency_expression,'F(w) = '+system.frequency_expression)],paragraphs=[system.interpretation,'Condición: '+system.condition]))
        extra=context.get('advance',0)
        if isinstance(system,Transfer):
            frequency='H(exp(i*w))' if digital else 'H(i*w)'
            if extra:frequency='exp(i*w*('+str(extra)+'))*('+frequency+')'
            sections.append(Section('Evaluación sobre frecuencia',formulas=[Formula('F(w) = '+frequency,'F(w) = '+frequency)]))
        role=context['component'];rules={'magnitude':'y(w) = abs(F(w))','db':'y(w) = 20*log(abs(F(w)))/log(10)','real':'y(w) = re(F(w))','imag':'y(w) = im(F(w))','phase':'y(w) = arg(F(w))','delay':'y(w) = -im(diff(F(w),w)/F(w))'}
        rule=rules[role]
        if role=='phase' and context.get('phase_kind')=='continuous':rule='y(w) = arg(F(w)) + 2*pi*m(w)'
        sections.append(Section('Representación dibujada',formulas=[Formula(rule,rule)],paragraphs=['ω se expresa en rad/muestra.' if digital else 'Ω se expresa en rad/s.','En fase continua, m(w) es el entero que mantiene la rama en cada tramo evaluado. La fase y el retardo no están definidos en ceros o puntos excluidos.'] if role in ('phase','delay') else []))
    else:
        stored=getattr(trace.artist,'_signallab_probe_source',getattr(trace.artist,'_signallab_curve_input',None))
        if stored is not None:
            source,component=stored;expression=str(source.expression or '').strip();variable='n' if source.domain=='discrete' else 't' if source.domain=='continuous' else 'w'
            from .temporal_formula import exact_section
            from .distributions import dirac_terms
            if dirac_terms(source):sections.append(Section('Parte ordinaria e impulsos',paragraphs=['La curva seleccionada muestra la parte ordinaria. Las fórmulas del modelo completo pueden incluir Dirac; sus pesos se dibujan en un panel separado y no son alturas finitas de esta curva.']))
            if expression and source.metadata.get('operation')=='continuous_expression' and 'regular_expression' in source.metadata:
                sections.append(Section('Definición completa de entrada',formulas=[Formula('F(t) = '+expression,'F(t) = '+expression)]));expression=source.metadata['regular_expression']
            exact=exact_section(source)
            if exact is not None:
                sections.append(exact);sections.append(Section('Componente de la curva',rows=[('Representación',{'real':'Parte real','imag':'Parte imaginaria','magnitude':'Módulo','phase':'Fase principal'}.get(component,component))]))
            elif expression and expression!='lista ingresada':
                sampling=source.metadata.get('operation')=='sampling'
                if source.metadata.get('operation') in (None,'generate','sampling','continuous_expression'):
                    try:expression=coordinate_expression(expression,'t' if sampling else variable)
                    except (ValueError,SyntaxError,RecursionError):pass
                if sampling:
                    sections.append(Section('Señal continua muestreada',formulas=[Formula('g(t) = '+expression,'g(t) = '+expression)]))
                    clock=source.metadata;rate=clock.get('sample_rate_hz');start=clock.get('time_start_s')
                    try:rate=float(rate);start=float(start);valid_clock=bool(np.isfinite([rate,start]).all() and rate>0)
                    except (ValueError,TypeError,OverflowError):valid_clock=False
                    if not valid_clock:
                        expression=None;sections.append(Section('Reloj no registrado',paragraphs=['Se conserva la fórmula continua de entrada, pero falta el reloj para expresar esta secuencia mediante sus índices. Se pueden consultar los datos numéricos.']))
                    else:expression='g(('+repr(start)+')+(n-('+str(source.origin)+'))/('+repr(rate)+'))'
                base='f['+variable+']' if source.domain=='discrete' else 'f('+variable+')'
                if expression:sections.append(Section('Definición almacenada',formulas=[Formula(base+' = '+expression,base+' = '+expression)]))
                represented={'real':'re('+base+')','imag':'im('+base+')','magnitude':'abs('+base+')','phase':'arg('+base+')','phase_unwrapped':'arg('+base+')+2*pi*m('+variable+')','density_db':'10*log('+base+')/log(10)','magnitude_db':'20*log(abs('+base+'))/log(10)'}.get(component)
                output='y['+variable+']' if source.domain=='discrete' else 'y('+variable+')'
                if represented and expression:sections.append(Section('Componente de la curva',formulas=[Formula(output+' = '+represented,output+' = '+represented)]))
                if component=='phase_unwrapped':sections.append(Section('Rama de fase',paragraphs=['m es el entero que mantiene la continuidad dentro de cada tramo evaluado. No se unen regiones separadas por ceros o exclusiones.']))
                if component=='delay_numeric':sections.append(Section('Retardo representado',paragraphs=['Se aproxima la derivada negativa de la fase desenrollada mediante diferencias en la rejilla. No es una derivada algebraica exacta; los ceros y cortes se omiten.']))
            else:sections.append(Section('Datos numéricos',paragraphs=['Esta curva conserva valores numéricos, pero no una fórmula algebraica que los defina. No se inventa una expresión mediante interpolación. Podés consultar sus puntos y buscar extremos.']))
            sections.append(Section('Intervalo almacenado',rows=[('Primera coordenada',str(source.axis[0])),('Última coordenada',str(source.axis[-1])),('Puntos',str(len(source.values))),('Unidad del eje',source.units)],paragraphs=['Una fórmula se presenta con el intervalo observado. El dibujo no certifica su comportamiento fuera de ese intervalo.']))
            if source.data_kind=='spectral_lines':sections.append(Section('Pesos espectrales',paragraphs=['Los puntos representan pesos de líneas ideales, no alturas de una densidad ordinaria. Los extremos comparan esos pesos.']))
            condition=source.metadata.get('source_frequency_condition',source.metadata.get('frequency_condition',source.metadata.get('source_condition','True')))
            if condition not in ('True',True,None):sections.append(Section('Condición registrada',paragraphs=[str(condition)]))
            if source.metadata.get('calculation_notes'):
                from .calculation_notes import plain_text
                sections.append(Section('Valores por continuidad',paragraphs=[plain_text(source.metadata['calculation_notes'])]))
        else:sections.append(Section('Definición no registrada',paragraphs=['Esta figura no conserva una fórmula algebraica para la traza seleccionada. Se puede consultar la representación numérica disponible; no se deduce una fórmula exacta a partir del dibujo.']))
    sections.append(Section('Qué se puede medir',paragraphs=['Los extremos corresponden a puntos evaluados de la representación dibujada. Un máximo entre muestras, un polo o una discontinuidad requieren un análisis distinto. No se interpola al colocar un cursor.']))
    return Summary(trace.label,sections)
