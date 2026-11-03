"""Optional teaching views derived from the actual inputs and stored outputs."""


def fourier(request,result):
    op=request['operation'];discrete='dtft' in op;inverse=op.startswith('inverse')
    if discrete:
        definition='x[n] = Integral(X(w)*exp(i*w*n),(w,-pi,pi))/(2*pi)' if inverse else 'X(w) = Sum(x[n]*exp(-i*w*n),(n,a,b))'
        text='La DTFT es 2π-periódica. La inversa integra un período y usa 1/(2π).' if inverse else 'Se suman los índices del soporte indicado; no se aplica el factor 1/N de una DFT inversa.'
    else:
        definition='x(t) = Integral(X(w)*exp(i*w*t),(w,-oo,oo))/(2*pi)' if inverse else 'X(w) = Integral(x(t)*exp(-i*w*t),(t,-oo,oo))'
        text='Se usa frecuencia angular en rad/s. La inversa incluye el factor 1/(2π).'
    lhs='x[n]' if discrete and inverse else 'x(t)' if inverse else 'X(w)'
    return [{'title':'Definición y normalización','text':text,'formula':definition},{'title':'Evaluación registrada','text':'El motor evalúa esta suma o integral. Se conserva la entrada; no se reconstruye una secuencia de manipulaciones internas que el motor no registre.','formula':request['expression']},{'title':'Condiciones y alcance','text':str(result.get('condition',''))+' '+result.get('scope','')},{'title':'Resultado' if result.get('evaluated') else 'Expresión pendiente','text':'Se conserva la interpretación del informe principal.','formula':lhs+' = '+result.get('display_result',result.get('result',''))}]


def ode(request,result):
    return [{'title':'1. Transformar las derivadas','text':'Se aplica Laplace unilateral. Y_d(s) representa la transformada de y′(t). Cada derivada aporta términos con los valores iniciales: éstos se conservan en la ecuación transformada.','formula':'Y_d(s) = s*Y(s)-y(0)'},{'title':'2. Despejar la salida','text':'Se agrupan los términos que multiplican Y(s), incluyendo la entrada y las condiciones iniciales.','formula':'Y(s) = '+result['Y(s)']},{'title':'3. Invertir y comprobar','text':'La inversa es causal. La comprobación del informe distingue la ecuación para t>0 de los límites iniciales en 0+.','formula':'y(t) = '+result['result']}]


def difference(request,result):
    steps=[{'title':'1. Recurrencia y prehistoria','text':'La ecuación se impone desde n₀='+str(result['origin'])+'. Los valores anteriores de y se incorporan como condiciones iniciales.'},{'title':'2. Separar los efectos','text':'La respuesta de entrada cero conserva el historial; la de estado cero conserva f[n].','formula':'y[n] = ('+result['zero_input']+')+('+result['zero_state']+')'}]
    if result.get('unilateral_output'):steps.append({'title':'3. Transformada unilateral calculada','text':'Se conserva la expresión transformada utilizada para obtener la solución.','formula':'Y(z) = '+result['unilateral_output']})
    steps.append({'title':'Resultado y dominio','text':result['condition']+' · '+result['method'],'formula':'y[n] = '+result['display_result']})
    return steps


def convolution(x,h,y,continuous=False):
    return [{'title':'1. Definición','text':'La segunda entrada se invierte y se desplaza; se integra el producto.' if continuous else 'Para cada n se multiplican las muestras que coinciden al invertir y desplazar la segunda entrada. Fuera de ambos registros se toma cero.','formula':'y(t) = Integral(x(tau)*h(t-tau),(tau,-oo,oo))' if continuous else 'y[n] = Sum(x[k]*h[n-k],(k,-oo,oo))'},
            {'title':'2. Soporte y normalización','text':('La integral numérica usa el modelo interpolado de los registros. El paso temporal participa en la integración; los pesos de impulsos ideales se conservan por separado.' if continuous else 'Longitud Nx+Nh−1 = '+str(x.values.size)+'+'+str(h.values.size)+'−1 = '+str(y.values.size)+'. Primer índice: '+str(x.origin)+'+'+str(h.origin)+' = '+str(y.origin)+'. No se divide por N.')},
            {'title':'3. Resultado almacenado','text':str(y.values.size)+' valores. La tabla y la figura contienen el resultado numérico; estos pasos explican su definición y soporte, sin afirmar una derivación simbólica.'}]


def numeric_fourier(x,y):
    op=y.metadata['operation']
    if op=='DTFT':
        definition='X(w) = Sum(x[n]*exp(-i*w*n),(n,'+str(x.origin)+','+str(x.origin+x.values.size-1)+'))'
        method='Se suman todas las muestras con sus índices originales. Fuera del registro se considera cero. El eje angular usa rad/muestra y no se divide por N.'
    elif op=='CTFT_rectangle':
        definition='X_reg(w) = Delta_t*Sum(x[k]*exp(-i*w*t[k]),(k,0,N-1))'
        method='La parte ordinaria usa cuadratura rectangular, con Δt='+str(x.step)+' s. Los impulsos ideales aportan términos de Fourier exactos por posición y peso; no se reemplazan por picos de una muestra.'
    else:
        definition='x(t) = Integral(X(w)*exp(i*w*t),(w,w0,w1))/(2*pi)'
        method='Se integra la ventana de frecuencia almacenada mediante trapecios: los extremos tienen peso 1/2 y se incluye Δω/(2π). No se reconstruye información fuera del intervalo disponible.'
    return [{'title':'1. Definición utilizada','text':method,'formula':definition},{'title':'2. Registro y resultado','text':str(x.values.size)+' valores de entrada; '+str(y.values.size)+' valores de salida. El origen y el paso de cada registro se conservan en sus datos.'},{'title':'3. Alcance','text':'El resultado numérico describe el registro y el intervalo elegido. Aumentar los puntos de dibujo no recupera información ausente ni garantiza convergencia de una señal infinita.'}]
