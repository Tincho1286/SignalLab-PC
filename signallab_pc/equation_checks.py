"""Residuals with an explicit domain and a separate initial-condition check."""
import numpy as np
import sympy as sp
from .symbolic import parse,T,N


def right_of_zero(value):
    replacements={}
    for gate in value.atoms(sp.Heaviside):
        if gate.args[0]==T:replacements[gate]=sp.S.One
        elif gate.args[0]==-T:replacements[gate]=sp.S.Zero
    for impulse in value.atoms(sp.DiracDelta):
        if impulse.args[0] in (T,-T):replacements[impulse]=sp.S.Zero
    return value.xreplace(replacements)


def ode(request,result):
    if not result.get('evaluated'):return {'status':'No evaluada: la solución contiene transformadas pendientes.'}
    y=right_of_zero(parse(result['result']));f=right_of_zero(parse(request['expression']));coefficients=[parse(v) for v in request['coefficients']]
    if sp.count_ops(y)+sp.count_ops(f)>400:return {'status':'Residuo simbólico no reducido por el tamaño de la expresión. La solución se conserva.'}
    terms=[a*sp.diff(y,T,j) for j,a in enumerate(coefficients)]
    residual=sp.simplify(sum(terms)-f)
    initial=[]
    for j,text in enumerate(request['initial']):
        value=sp.limit(sp.diff(y,T,j),T,0,dir='+');error=sp.simplify(value-parse(text))
        initial.append({'derivative':j,'obtained':str(value),'requested':text,'residual':str(error),'satisfied':error==0})
    return {'status':'Identidad verificada para t>0.' if residual==0 else 'Residuo no nulo o no reducido; revisá las condiciones de la solución.','symbolic_residual':str(residual),'initial':initial,
            'scope':'Se sustituye la fórmula en la EDO para t>0. Los valores iniciales se comprueban por límite derecho en 0+. Los impulsos en t=0 pertenecen al arranque causal y se excluyen sólo de la ecuación interior; los impulsos desplazados no se eliminan. Un residuo simbólico sin reducir no demuestra por sí solo que la solución sea incorrecta.'}


def difference(request,result,arrays=None):
    values=result.get('numeric_samples');start=result['origin']
    data={'status':'Sin muestras numéricas: no se calcula un residuo de registro.','scope':'Se verifica la recurrencia de las muestras generadas y se incorpora el historial indicado. Esta comprobación numérica no certifica por sí sola la fórmula cerrada.'}
    if values:
        from scipy.signal import lfilter
        from .resources import ensure_working_set
        ensure_working_set(len(values)+(len(arrays[1]) if arrays is not None else len(result['initial'])),live_arrays=16)
        if arrays is not None:a,history,y,f=arrays
        else:
            a=np.array([complex(parse(v).evalf(18)) for v in result['coefficients']]);history=np.array([complex(parse(v).evalf(18)) for v in result['initial']]);y=np.array([complex(*v) for v in values])
            fexpr=parse(request['expression']);f=np.array([complex(fexpr.subs(N,start+i).evalf(18)) for i in range(len(y))])
        # Scale coefficients and amplitudes before evaluating the residual.
        cs=float(max(abs(a.real).max(),abs(a.imag).max()));ys=float(max(np.max(abs(y.real)),np.max(abs(y.imag)),np.max(abs(history.real),initial=0),np.max(abs(history.imag),initial=0),np.max(abs(f.real)),np.max(abs(f.imag))))
        if ys==0:normalized=np.zeros(len(y));absolute=np.zeros(len(y))
        else:
            aa=a/cs;ext=np.r_[history[::-1]/ys,y/ys];ff=(f/ys)/cs
            lhs=lfilter(aa,[1],ext)[len(history):];residual=lhs-ff
            denominator=lfilter(abs(aa),[1],abs(ext))[len(history):]+abs(ff)
            normalized=np.divide(abs(residual),denominator,out=np.where(abs(residual)==0,0.,np.nan),where=denominator>0)
            with np.errstate(over='ignore',invalid='ignore'):absolute=(abs(residual)*cs)*ys
        finite=np.isfinite(normalized)
        if finite.all():
            worst=int(np.argmax(normalized));maximum=float(np.max(absolute))
            data.update(status='Residuo numérico evaluado sobre el registro.',normalized_max=float(normalized[worst]),worst_index=start+worst,absolute_max=maximum if np.isfinite(maximum) else None,interval=[start,start+len(y)-1],count=len(y))
        else:data['status']='El residuo excede el rango numérico; no se declara una comprobación satisfactoria.'
    return data


def section(data,discrete=False):
    from .result_summary import Section,Formula,number
    rows=[('Estado',data['status'])]
    if 'normalized_max' in data:rows.extend([('Máximo residuo normalizado',number(data['normalized_max'])),('Índice del máximo',str(data['worst_index'])),('Intervalo comprobado',str(data['interval'][0])+' a '+str(data['interval'][1])),('Máximo absoluto',number(data['absolute_max']) if data['absolute_max'] is not None else 'Fuera del rango de doble precisión')])
    rows.extend(('Condición inicial · derivada '+str(v['derivative']),'Cumple por límite derecho' if v['satisfied'] else 'Residuo: '+v['residual']) for v in data.get('initial',[]))
    formulas=[]
    if data.get('symbolic_residual') is not None:formulas.append(Formula('r(t) = '+data['symbolic_residual'],'r(t) = '+data['symbolic_residual']))
    if discrete:formulas.append(Formula('r[n] = Sum(a[k]*y[n-k],(k,0,M))-f[n]','r[n] = Σ a[k]·y[n−k] − f[n]'))
    paragraphs=[data.get('scope','')]
    if discrete:paragraphs.append('Se normaliza |r[n]| por Σ|a[k]·y[n−k]|+|f[n]|. Si todos los términos son cero, el residuo normalizado es cero. Un valor cercano al redondeo mide coherencia numérica; no se convierte en una prueba de exactitud simbólica.')
    return Section('Comprobación de la solución',rows=rows,formulas=formulas,paragraphs=paragraphs)


def ode_summary(request,result):
    from .result_summary import Summary,Section,Formula
    equation=' + '.join('('+v+')*'+('y(t)' if j==0 else 'Derivative(y(t),(t,'+str(j)+'))') for j,v in enumerate(request['coefficients']))+' == '+request['expression']
    sections=[Section('Ecuación',formulas=[Formula(equation,equation)]),Section('Solución para t≥0',formulas=[Formula('y(t) = '+result['result'],'y(t) = '+result['result'])]),Section('Condiciones iniciales',rows=[('Derivada '+str(j)+' en 0+',v) for j,v in enumerate(request['initial'])]),Section('Transformada obtenida',formulas=[Formula('Y(s) = '+result['Y(s)'],'Y(s) = '+result['Y(s)'])])]
    if result.get('residual_check'):sections.append(section(result['residual_check']))
    return Summary('Ecuación diferencial',sections)
