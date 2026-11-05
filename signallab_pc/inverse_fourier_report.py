"""Reports for the actual inverse calculated on a stored frequency grid."""
from .result_summary import Formula,Section,number


def numeric_model(kind,origin,step,values):
    return {'kind':kind,'origin':float(origin),'step':float(step),'size':int(len(values)),
            'values':[[float(v.real),float(v.imag)] for v in values[:8]]}


def stored_model(signal):
    # Arithmetic and index transforms may carry source metadata for provenance.
    if signal.metadata.get('operation') in ('inverse_dtft','frequency_filter_impulse','ICTFT'):
        return signal.metadata.get('inverse_model')
    return None


def numeric_section(model,symbol):
    length=model['size'];origin=number(model['origin']);step=number(model['step'])
    periodic=model['kind']=='periodic'
    if periodic:
        formula=f'{symbol}[n] = exp(i*({origin})*n)*c[Mod(n,{length})]'
        text=f'{symbol}[n] = exp(j·({origin})·n) · c[n módulo {length}]'
        if length<=8:
            terms=[f'({number(complex(*value))})*KroneckerDelta(Mod(n,{length}),{i})'
                   for i,value in enumerate(model['values']) if complex(*value)]
            if terms:
                formula=f'{symbol}[n] = exp(i*({origin})*n)*('+' + '.join(terms)+')'
                text=formula
            else:formula=text=f'{symbol}[n] = 0'
        rows=[('Origen angular ω₀',origin+' rad/muestra'),('Período de los coeficientes',str(length)+' muestras')]
        paragraphs=['Los c[r] son los coeficientes calculados para la rejilla ingresada, con el peso medio de los extremos si se repiten. El factor exponencial conserva el origen angular.']
        name='c'
    else:
        formula=f'{symbol}(t) = ({step})*Sum(q[k]*H[k]*exp(i*(({origin})+k*({step}))*t),(k,0,{length-1}))/(2*pi)'
        text=f'{symbol}(t) = ΔΩ/(2π) · Σ de k=0 a {length-1} de q[k]·H[k]·exp(j(Ω₀+kΔΩ)t)'
        rows=[('Origen angular Ω₀',origin+' rad/s'),('Paso ΔΩ',step+' rad/s')]
        paragraphs=['La suma usa los valores de la rejilla calculada. q vale 1/2 en ambos extremos y 1 en los puntos interiores.']
        name='H'
    rows.extend((f'{name}[{i}]',number(complex(*value))) for i,value in enumerate(model['values']))
    if length>len(model['values']):paragraphs.append('La tabla muestra los primeros ocho coeficientes. La expresión usa el conjunto completo.')
    return Section('Expresión de la aproximación calculada',paragraphs=paragraphs,rows=rows,formulas=[Formula(formula,text)])


def exact_section(result,symbol):
    left=symbol+'[n]' if result['output_variable']=='n' else symbol+'(t)'
    text=left+' = '+result.get('display_result',result['result'])
    return Section('Expresión algebraica obtenida',formulas=[Formula(text,text)],
                   paragraphs=['Esta fórmula corresponde a la definición de frecuencia. La rejilla finita produce la aproximación numérica indicada aparte.'])


def from_signal(spectrum):
    if not spectrum.expression.strip():return None
    import math
    from .symbolic_process import run_request
    discrete=spectrum.units=='rad/muestra'
    try:return run_request({'operation':'frequency_definition','expression':spectrum.expression,
                            'domain':'discrete' if discrete else 'continuous',
                            'canonical_period':not discrete or math.isclose(spectrum.origin,-math.pi,rel_tol=0,abs_tol=8e-15)})
    except (ValueError,SyntaxError,OSError):return None
