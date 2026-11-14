"""Coordinate changes and equilibria of the stored binary state model."""
import math
import numpy as np
import sympy as sp
from .state_space import StateModel
from .state_frequency import _matrix
from .resources import ensure_working_set
from .jobs import checkpoint


def _rref(value):
    def zero(number):checkpoint();return number==0
    return value.rref(iszerofunc=zero,simplify=False)


def _array(value):
    """Never silently turn a nonzero exact component into floating zero."""
    result=np.empty(value.shape,complex)
    for i in range(value.rows):
        checkpoint()
        for j in range(value.cols):
            parts=value[i,j].as_real_imag();numbers=[]
            for part in parts:
                try:number=float(part)
                except (ValueError,TypeError,OverflowError):raise ValueError('Un componente no se puede representar como float64; se conserva su expresión exacta.')
                if not math.isfinite(number) or number==0 and part!=0:raise ValueError('Un componente excede el rango float64; no se reemplaza por cero.')
                numbers.append(number)
            result[i,j]=complex(*numbers)
    return result


def _stored(value):return dict(shape=list(value.shape),values=[[str(value[i,j]) for j in range(value.cols)] for i in range(value.rows)])


def change_coordinates(model,basis,initial=None):
    P=np.asarray(basis,complex);n=model.states
    if P.shape!=(n,n) or not np.isfinite(P).all():raise ValueError('P debe ser cuadrada, finita y tener una fila y columna por estado. Se define x = P q.')
    initial=np.zeros(n,complex) if initial is None else np.asarray(initial,complex)
    if initial.shape!=(n,) or not np.isfinite(initial).all():raise ValueError('x₀ requiere un valor finito por estado; vacío utiliza ceros.')
    ensure_working_set(max(1,n*n+n*(model.inputs+model.outputs)),bytes_per_sample=1024,live_arrays=24)
    p=_matrix(P);identity=sp.eye(n);reduced,pivots=_rref(p.row_join(identity))
    if sum(i<n for i in pivots)!=n:raise ValueError('P es singular para sus valores almacenados: no define un cambio de coordenadas invertible.')
    inverse=reduced[:,n:];A,B,C,D=(_matrix(getattr(model,key)) for key in ('A','B','C','D'));checkpoint()
    q0=inverse*_matrix(initial[:,None]);numeric_initial=None;initial_notice=''
    try:numeric_initial=_array(q0).reshape(n)
    except ValueError as exc:initial_notice=str(exc)
    exact={'A':inverse*A*p,'B':inverse*B,'C':C*p,'D':D};result=None;notice=''
    try:result=StateModel(**{key:_array(value) for key,value in exact.items()},dt=model.dt,name=model.name+' · coordenadas q')
    except ValueError as exc:notice=str(exc)+' Las matrices transformadas exactas se conservan; no se ofrece un modelo numérico.'
    scale=max(float(np.max(abs(P.real))),float(np.max(abs(P.imag)))) if n else 1.
    try:condition=float(np.linalg.cond(P.real/scale+1j*(P.imag/scale))) if n else 1.
    except np.linalg.LinAlgError:condition=float('inf')
    return dict(model=result,basis=P.copy(),inverse=_stored(inverse),exact_matrices={key:_stored(value) for key,value in exact.items()},original_initial=initial.copy(),transformed_initial=_stored(q0),numeric_initial=numeric_initial,initial_notice=initial_notice,condition=condition if math.isfinite(condition) else None,notice=notice,
        scope='x = P q; Aq = P⁻¹ A P, Bq = P⁻¹ B, Cq = C P, Dq = D. Se opera exactamente sobre los números binarios almacenados y se redondea el modelo reutilizable a float64. No es una sustitución simbólica de los números originales ni una reducción de orden.')


def equilibrium(model,inputs):
    u=np.asarray(inputs,complex)
    if u.shape!=(model.inputs,) or not np.isfinite(u).all():raise ValueError('Indicá una entrada constante finita por canal, incluso en un modelo sin estados.')
    n=model.states;ensure_working_set(max(1,n*n+n*(model.inputs+model.outputs)),bytes_per_sample=1024,live_arrays=24)
    A,B,C,D=(_matrix(getattr(model,key)) for key in ('A','B','C','D'));v=_matrix(u[:,None]);M=-A if model.dt is None else sp.eye(n)-A;rhs=B*v
    reduced,pivots=_rref(M.row_join(rhs));inconsistent=any(all(reduced[i,j]==0 for j in range(n)) and reduced[i,n]!=0 for i in range(n))
    result=dict(kind='inconsistent' if inconsistent else 'unique' if len(pivots)==n else 'family',inputs=u.copy(),equation='-A*x_e = B*u_e' if model.dt is None else '(I-A)*x_e = B*u_e',coefficient_matrix=_stored(M),right_side=_stored(rhs),numeric_state=None,numeric_output=None,
        scope='Equilibrio para entrada constante: dx/dt=0 en continuo o x[n+1]=x[n] en discreto. La compatibilidad y las variables libres se resuelven exactamente sobre los valores binarios almacenados, sin decidirlas por una tolerancia SVD. Un equilibrio no implica estabilidad.')
    if inconsistent:return result
    leading=[j for j in pivots if j<n];free=[j for j in range(n) if j not in leading];particular=sp.zeros(n,1);null=sp.zeros(n,len(free))
    for i,j in enumerate(leading):particular[j]=reduced[i,n]
    for k,j in enumerate(free):
        null[j,k]=1
        for i,pivot in enumerate(leading):null[pivot,k]=-reduced[i,j]
    output=C*particular+D*v;output_null=C*null
    result.update(particular=_stored(particular),nullspace=_stored(null),output=_stored(output),output_nullspace=_stored(output_null),free_states=[j+1 for j in free],parameters=len(free))
    try:result['numeric_state']=_array(particular).reshape(n);result['numeric_output']=_array(output).reshape(model.outputs)
    except ValueError as exc:result.update(numeric_state=None,numeric_output=None,notice=str(exc))
    return result


def diagnostic_matrices(model):
    n=model.states;ensure_working_set(max(1,n*n*(model.inputs+model.outputs)),live_arrays=12)
    ctr=np.empty((n,n*model.inputs),complex);obs=np.empty((n*model.outputs,n),complex);ab=model.B.copy();ca=model.C.copy()
    for k in range(n):
        checkpoint();ctr[:,k*model.inputs:(k+1)*model.inputs]=ab;obs[k*model.outputs:(k+1)*model.outputs,:]=ca
        if k<n-1:
            with np.errstate(all='ignore'):ab=model.A@ab;ca=ca@model.A
    if not np.isfinite(ctr).all() or not np.isfinite(obs).all():raise FloatingPointError('Las matrices de controlabilidad u observabilidad exceden el rango; revisá la escala del modelo.')
    result=dict(controllability=ctr,observability=obs)
    for key,value in [('controllability',ctr),('observability',obs)]:
        scale=max(float(np.max(abs(value.real))),float(np.max(abs(value.imag)))) if value.size else 0.
        normalized=(value.real/scale+1j*(value.imag/scale)) if scale else value
        singular=np.linalg.svd(normalized,compute_uv=False) if n else np.array([],float);threshold=float(max(value.shape)*np.finfo(float).eps*singular[0]) if len(singular) else 0.
        result[key+'_singular']=singular;result[key+'_scale']=scale;result[key+'_threshold']=threshold;result[key+'_rank']=int(np.count_nonzero(singular>threshold))
    return result


def stored_matrix(value):
    return sp.Matrix(value['shape'][0],value['shape'][1],lambda i,j:sp.sympify(value['values'][i][j]))


def coordinates_summary(result):
    from .result_summary import Summary,Section,Formula,number
    sections=[Section('Convención',paragraphs=[result['scope']],formulas=[Formula('x = P*q','x = P q')]),Section('Condicionamiento',rows=[('Condición 2 de P','No representable o no determinada numéricamente' if result['condition'] is None else number(result['condition']))],paragraphs=['Una condición grande puede amplificar el redondeo. Aunque la inversión de los números almacenados sea exacta, el modelo numérico resultante se evalúa con precisión finita.'])]
    for key,matrix in result['exact_matrices'].items():
        value=stored_matrix(matrix);shown=value.evalf(12)
        sections.append(Section(key+' en coordenadas q',formulas=[Formula(key+'_q = '+str(shown),key+'_q = '+str(shown))]))
    if result['notice']:sections.append(Section('Modelo numérico',paragraphs=[result['notice']]))
    q0=stored_matrix(result['transformed_initial']).evalf(12)
    sections.append(Section('Condición inicial transformada',formulas=[Formula('q_0 = '+str(q0),'q₀ = '+str(q0))],paragraphs=['El mismo estado físico se carga como q₀ = P⁻¹ x₀. Copiar el vector x₀ sin transformarlo cambia el problema. Las entradas y salidas conservan sus coordenadas.',result['initial_notice']]))
    return Summary('Cambio de coordenadas de estados',sections)


def equilibrium_summary(result):
    from .result_summary import Summary,Section,Formula
    sections=[Section('Condición de equilibrio',paragraphs=[result['scope']],formulas=[Formula(result['equation'],result['equation'])])]
    if result['kind']=='inconsistent':sections.append(Section('Sin equilibrio',paragraphs=['La ecuación es incompatible para la entrada constante indicada. No se inventa un estado estacionario ni se ofrece cargarlo como condición inicial.']))
    else:
        n=result['particular']['shape'][0];parameters=sp.Matrix([sp.Symbol('c_'+str(k+1)) for k in range(result['parameters'])]) if result['parameters'] else sp.zeros(0,1)
        x=stored_matrix(result['particular'])+stored_matrix(result['nullspace'])*parameters;y=stored_matrix(result['output'])+stored_matrix(result['output_nullspace'])*parameters
        sections.append(Section('Equilibrio único' if result['kind']=='unique' else 'Familia de equilibrios',paragraphs=['Los parámetros c son libres. Cargar en simulación utiliza la solución particular c=0.' if result['parameters'] else 'La ecuación tiene un único estado de equilibrio para esta entrada constante.'],formulas=[Formula('x_e = '+str(x.evalf(12)),'x_e = '+str(x.evalf(12))),Formula('y_e = '+str(y.evalf(12)),'y_e = '+str(y.evalf(12)))]))
        if result.get('notice'):sections.append(Section('Representación numérica',paragraphs=[result['notice']]))
    return Summary('Equilibrio del modelo de estados',sections)
