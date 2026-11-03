"""Optional explanation assembled from stored calculation data, never re-solved."""


def build(request, result):
    op = request.get('operation');z = op.startswith('z_');inverse = op in ('z_inverse_expression', 'inverse_laplace')
    steps = []
    definition = 'X(z) = Sum(x[n]*z^(-n),(n,a,b))' if z else 'X(s) = Integral(x(t)*exp(-s*t),(t,-oo,oo))' if request.get('interpretation')=='bilateral' else 'X(s) = Integral(x(t)*exp(-s*t),(t,0,oo))'
    if not inverse:
        text = 'Se aplica la definición sobre el soporte indicado; fuera de él la señal se considera cero.' if z else 'Se aplica la definición integral con la interpretación temporal elegida.'
        steps.append({'title':'1. Definición y soporte', 'text':text, 'formula':definition})
        if z:steps[0]['text'] += ' a='+str(request.get('origin', request.get('lower', '0')))+'; b='+str(request.get('upper', request.get('origin', 0)+len(request.get('samples', []))-1 if op=='z_finite' else 'oo'))+'.'
        steps.append({'title':'2. Convergencia', 'text':'La expresión y su región de convergencia forman un único resultado. Las ramas condicionadas conservan sus restricciones.'})
    else:
        if result.get('decomposition'):
            steps.append({'title':'1. Descomposición calculada', 'text':'Se separó la parte polinómica de los términos asociados a cada polo. Los coeficientes que aparecen aquí son los usados para reconstruir la señal.', 'formula':('X(z)' if z else 'X(s)')+' = '+result['decomposition']})
        elif result.get('method')=='geometric_pairs':
            steps.append({'title':'1. Pares geométricos y linealidad', 'text':'Cada sumando de la entrada se reconoció como un par geométrico. Se conservan sus coeficientes, potencias y desplazamientos.'})
        else:
            steps.append({'title':'1. Inversión simbólica', 'text':'Se utilizó el motor simbólico. Este caso no registra una descomposición intermedia; no se atribuyen pasos que no fueron calculados.'})
        for index,pair in enumerate(result.get('geometric_terms',[])):
            c,d,p,m=pair['coefficient'],pair['delay'],pair['pole'],pair['order'];q='(n-('+d+'))'
            term='('+c+')*delta[n-('+d+')]' if p is None else '('+c+')*binomial('+q+'+'+str(m-1)+','+str(m-1)+')*('+p+')^'+q+'*u[n-('+d+')]' if pair['right'] else '('+c+')*(-1)^'+str(m)+'*binomial(-'+q+'-1,'+str(m-1)+')*('+p+')^'+q+'*u[('+d+')-'+str(m)+'-n]'
            steps.append({'title':'Par geométrico '+str(index+1),'text':'Coeficiente '+c+'; desplazamiento '+d+(' muestras; término derecho.' if pair['right'] else ' muestras; término izquierdo.'),'formula':'x_'+str(index+1)+'[n] = '+term})
        steps.append({'title':'Soporte elegido por la ROC', 'text':('Los polos interiores al radio de la ROC generan términos derechos; los exteriores, términos izquierdos. Las potencias de z generan impulsos desplazados.' if z else 'Los polos a la izquierda de la ROC generan términos derechos; los situados a la derecha, términos izquierdos. Los términos polinómicos generan impulsos y sus derivadas.')+' ROC: '+str(result.get('roc', 'Interpretación unilateral / causal.'))})
        if result.get('time_shift'):steps.append({'title':'3. Desplazamiento temporal', 'text':result['time_shift']})
    if result.get('evaluated', True) and not result.get('branches'):
        lhs = 'x[n]' if inverse and z else 'x(t)' if inverse else 'X(z)' if z else 'X(s)'
        steps.append({'title':str(len(steps)+1)+'. Resultado', 'text':'Se reúnen los términos, manteniendo el soporte y las condiciones del informe principal.', 'formula':lhs+' = '+result.get('display_result', result.get('result', ''))})
    return steps


def summary(steps):
    from .result_summary import Summary, Section, Formula
    sections = [Section(item['title'], paragraphs=[item['text']], formulas=[Formula(item['formula'], item['formula'])] if item.get('formula') else []) for item in steps]
    if not sections:sections = [Section('Sin desarrollo registrado', paragraphs=['Calculá la transformada para consultar los pasos disponibles. Los resultados anteriores conservan su fórmula y sus condiciones.'])]
    return Summary('Desarrollo de la transformada', sections)
