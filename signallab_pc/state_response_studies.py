"""Saved state trajectories, linear decomposition and per-step contributions."""
from copy import deepcopy
import math
import numpy as np
from .jobs import checkpoint
from .resources import ensure_working_set


def simulate(model,grid,initial,separate=False):
    initial=np.asarray(initial,complex)
    if initial.shape!=(model.states,) or not np.isfinite(initial).all():raise ValueError('Indicá un estado inicial finito por estado; vacío utiliza ceros.')
    count=len(grid.axis);ensure_working_set(max(1,count*(model.states+model.inputs+model.outputs)),live_arrays=22 if separate else 10)
    transition=model.discretize(grid.step,'zoh') if model.dt is None else model
    _,output,states=transition.simulate(grid.values,initial=initial)
    components=[dict(name='Total',output=output,states=states)]
    if separate:
        _,forced,xf=transition.simulate(grid.values)
        _,natural,xn=transition.simulate(np.zeros_like(grid.values),initial=initial)
        components.extend([dict(name='Estado cero',output=forced,states=xf),dict(name='Entrada cero',output=natural,states=xn)])
    return dict(model=model,transition=transition,grid=grid,initial=np.asarray(initial,complex).copy(),components=components)


def capture(run,component_index=0):
    grid=run['grid'];component=run['components'][component_index]
    m=run['model'];ensure_working_set(max(1,len(grid.axis)*(m.inputs+m.outputs+m.states)+2*(m.states*m.states+m.states*m.inputs+m.outputs*m.states)),live_arrays=8)
    return dict(model=deepcopy(run['model']),transition=deepcopy(run['transition']),component=component['name'],axis=grid.axis.copy(),discrete=grid.discrete,inputs=np.zeros_like(grid.values) if component_index==2 else grid.values.copy(),output=component['output'].copy(),states=component['states'].copy())


def _show(value):
    result=[]
    for part in value:
        try:number=float(part)
        except OverflowError:return None
        if not math.isfinite(number) or number==0 and part!=0:return None
        result.append(number)
    return complex(*result)


def inspect(trace,index,*,family='output',channel=0):
    from .scalar_expression import integer_value
    from .rational_frequency import exact,mul,add,ZERO
    index=integer_value(index);channel=integer_value(channel);count=len(trace['axis'])
    if not 0<=index<count:raise ValueError('Elegí la posición de una muestra guardada, contando desde cero.')
    model=trace['model'];transition=trace['transition'];target=index
    ensure_working_set(model.states+model.inputs,bytes_per_sample=1024,live_arrays=6)
    if family=='output':
        if not 0<=channel<model.outputs:raise ValueError('Canal de salida fuera de rango.')
        factors=((model.C[channel],trace['states'][index],'Estado actual'),(model.D[channel],trace['inputs'][index],'Entrada actual'));computed=trace['output'][index,channel];name='y'+str(channel+1)
    elif family=='state':
        if index>=count-1:raise ValueError('La transición posterior a la última muestra no se simuló. Elegí un punto anterior.')
        if not 0<=channel<model.states:raise ValueError('Estado fuera de rango.')
        target=index+1;factors=((transition.A[channel],trace['states'][index],'Estado actual'),(transition.B[channel],trace['inputs'][index],'Entrada retenida' if not trace['discrete'] else 'Entrada actual'));computed=trace['states'][target,channel];name='x'+str(channel+1)
    else:raise ValueError('Elegí una salida o un estado siguiente.')
    rows=[];total=ZERO
    for coefficients,values,kind in factors:
        for k,(coefficient,value) in enumerate(zip(coefficients,values)):
            if k%64==0:checkpoint()
            term=mul(exact(coefficient),exact(value));total=add(total,term);rows.append(dict(source=kind,channel=k+1,coefficient=complex(coefficient),value=complex(value),contribution=_show(term)))
    residual=add(exact(computed),tuple(-part for part in total));coordinate=lambda k:int(trace['axis'][k]) if trace['discrete'] else float(trace['axis'][k])
    return dict(index=index,coordinate=coordinate(index),target_coordinate=coordinate(target),family=family,channel=channel,name=name,component=trace.get('component','Total'),rows=rows,computed=complex(computed),reconstructed=_show(total),residual=_show(residual),unrepresentable=sum(row['contribution'] is None for row in rows))


def summary(trace,data):
    from .result_summary import Summary,Section,number
    show=lambda x:number(x) if x is not None else 'Fuera del rango float64; no se reemplaza por cero.'
    equation='y[k] = C*x[k] + D*u[k]' if data['family']=='output' else 'x[k+1] = A*x[k] + B*u[k]' if trace['discrete'] else 'x(t+Δt) = Ad*x(t) + Bd*u(t)'
    return Summary('Aportes a '+data['name']+' · '+data['component'],[Section('Muestra guardada',rows=[('Componente',data['component']),('Coordenada de los datos',str(data['coordinate'])),('Coordenada del resultado',str(data['target_coordinate']))],paragraphs=[equation,'El índice de posición recorre el registro desde cero. Las coordenadas conservan el primer índice o instante original. En continuo, Ad y Bd corresponden a la propagación ZOH de ese cálculo; la ecuación siguiente no es una aproximación de Euler.']),Section('Reconstrucción',rows=[('Suma de aportes',show(data['reconstructed'])),('Valor almacenado',show(data['computed'])),('Almacenado menos suma',show(data['residual'])),('Aportes fuera de rango',str(data['unrepresentable']))],paragraphs=['Se reconstruyen productos y sumas como racionales de los números binarios guardados. La diferencia puede mostrar redondeo de la realización; no altera su salida ni demuestra una identidad simbólica sobre el modelo original.'])])
