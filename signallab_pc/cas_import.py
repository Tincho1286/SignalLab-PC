"""Build exact CAS objects from mathematical result payloads in the isolated worker."""
import re,unicodedata,copy
import sympy as sp
from .cas_engine import Calculator,empty_state,restore,encode,presentation
from .signal_notation import source as signal_source


def _number(value):
    return sp.Integer(value) if isinstance(value,(int,bool)) else sp.Float(value,17)


def _complex(pair):return _number(pair[0])+sp.I*_number(pair[1])


def _expression(text,variable=None):
    if re.search(r'\b(?:CRootOf|RootOf|RootSum)\s*\(',text):raise ValueError('Este resultado antiguo no conserva la raíz algebraica para CAS. Recalculalo con esta versión para exportarlo exactamente.')
    calculator=Calculator(empty_state())
    calculator.locals={'n':sp.Symbol('n',integer=True),'k':sp.Symbol('k',integer=True),'t':sp.Symbol('t',real=True),'w':sp.Symbol('w',real=True)}
    value=calculator.parse(text)
    if calculator.undefined:raise ValueError('La expresión contiene funciones sin definición: '+', '.join(sorted(calculator.undefined)))
    return value


def _symbol(name):
    name=''.join(c for c in unicodedata.normalize('NFKD',str(name)) if not unicodedata.combining(c))
    name=re.sub('[^A-Za-z0-9_]','_',name)
    return sp.Symbol(name if re.match('[A-Za-z]',name) else 'dato_'+name)


def _value(data,notices):
    kind=data['kind']
    if kind=='encoded':notices.extend(data.get('conditions',[]));return restore(data['encoded'])
    if kind=='expression':
        notices.extend(data.get('conditions',[]))
        if data.get('variable') in ('n','k'):notices.append('La expresión de origen usa un índice entero. Los supuestos y definiciones de la hoja CAS se aplicarán al operar con este resultado.')
        if data.get('encoded'):return restore(data['encoded'])
        if data.get('numeric_source'):
            notices.append('Se importó la expresión numérica disponible; sus decimales son aproximaciones, no coeficientes algebraicos exactos.')
            return _expression(data['numeric_source'],data.get('variable'))
        return _expression(data['source'],data.get('variable'))
    if kind=='number':return _number(data['value'])
    if kind=='complex':return _complex(data['value'])
    if kind=='matrix':return sp.Matrix(data['rows'],data['cols'],[_complex(v) for v in data['values']])
    if kind=='system':
        digital=data['domain']=='digital';v=sp.Symbol('z' if digital else 's')
        def polynomial(coefficients):return sp.Add(*[_complex(c)*v**(-index if digital else len(coefficients)-index-1) for index,c in enumerate(coefficients)])
        notices.append('Transferencia con los coeficientes numéricos almacenados; no se inventa una representación racional exacta de sus decimales.')
        if data.get('roc') is not None:notices.append('ROC registrada del sistema: '+str(data['roc'])+'. Forma parte de su interpretación; la expresión CAS sola no impone el soporte.')
        if data.get('period') is not None:notices.append('Período físico del sistema: T='+str(data['period'])+' s.')
        return (v**data.get('advance',0) if digital else 1)*polynomial(data['b'])/polynomial(data['a'])
    if kind=='samples':
        matrix=sp.Matrix([[_number(x),_complex(y)] for x,y in zip(data['axis'],data['values'])])
        notices.append('Matriz de datos almacenados: primera columna = eje ('+data['units']+'); segunda = valor complejo. Cada fila conserva una muestra. Ejemplo de acceso: rN[0,1].')
        if data.get('dirac'):
            notices.append('Los pesos Dirac se conservan aparte; no son alturas de las muestras.')
            return {_symbol('muestras'):matrix,_symbol('dirac'):sp.Matrix([[_number(t),_complex(w)] for t,w in data['dirac']])}
        return matrix
    if kind=='states':
        notices.append('Tupla de matrices en orden (A, B, C, D). Usá rN[0], rN[1], rN[2] y rN[3].'+(' T='+str(data['period'])+' s.' if data.get('period') is not None else ' Modelo continuo.'))
        return tuple(_value({'kind':'matrix',**matrix},notices) for matrix in data['matrices'])
    if kind=='measures':
        notices.extend(data.get('conditions',[]));return {_symbol(k):_expression(v['expression']) for k,v in data['items'].items()}
    if kind=='mapping':return {_symbol(k):_value(v,notices) for k,v in data['items'].items()}
    if kind=='list':return [_value(v,notices) for v in data['items']]
    raise ValueError('Este tipo de resultado no tiene una representación CAS disponible.')


def import_result(request):
    state=copy.deepcopy(request.get('state') or empty_state());cell=int(request['cell']);notices=[]
    value=_value(request['payload'],notices);encoded=encode(value)
    state['results'][str(cell)]=encoded;state['ans']=cell
    expression=sp.sstr(value) if isinstance(value,sp.Expr) else None
    calculator=Calculator(state)
    from .cas_assumptions import descriptions
    return {'state':state,'encoded_value':encoded,'text':signal_source(value) if isinstance(value,sp.Expr) else str(value),'presentation':presentation(value),
            'expression':expression,'symbols':sorted(str(v) for v in value.free_symbols) if isinstance(value,sp.Basic) else [],
            'provenance':copy.deepcopy(request['payload'].get('provenance')),'notices':list(dict.fromkeys(notices)),'assumptions':descriptions(calculator.assumptions),'variables':[(k,str(v)) for k,v in calculator.variables.items()],
            'functions':[(name+'('+', '.join(params)+')',str(body)) for name,(params,body) in calculator.functions.items()]}
