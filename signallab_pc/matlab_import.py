"""Numeric MATLAB data import. Never executes MATLAB or Python scripts."""
import ast, math, re
from pathlib import Path
import numpy as np
from .resources import ensure_working_set
from .model import Signal

def split_top(text,separators):
    parts=[];start=0;depth=0
    for i,c in enumerate(text):
        if c in '([':depth+=1
        elif c in ')]':depth-=1
        elif depth==0 and c in separators:parts.append(text[start:i].strip());start=i+1
    parts.append(text[start:].strip());return parts

_TOKEN=re.compile(
    r"\s+|(?:\d+\.(?![*/^'])\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?|"
    r"[^\W\d]\w*|\.'|\.\*|\./|\.\^|<=|>=|==|~=|[+\-*/^':(),<>\[\];]"
)
_PRECEDENCE={'<':5,'<=':5,'>':5,'>=':5,'==':5,'~=':5,':':10,
             '+':20,'-':20,'*':30,'.*':30,'/':30,'./':30,
             '^':40,'.^':40,"'":40,".'":40}
_BINOPS={'+':ast.Add,'-':ast.Sub,'*':ast.Mult,'.*':ast.MatMult,'/':ast.Div,'./':ast.FloorDiv,
         '^':ast.Pow,'.^':ast.Pow}
_COMPARISONS={'<':ast.Lt,'<=':ast.LtE,'>':ast.Gt,'>=':ast.GtE,'==':ast.Eq,'~=':ast.NotEq}


def _lex(text):
    tokens=[];cursor=0
    while cursor<len(text):
        token=_TOKEN.match(text,cursor)
        if token is None:raise ValueError('Símbolo no admitido en la expresión MATLAB: '+text[cursor:cursor+12])
        if not token[0].isspace():tokens.append((token[0],cursor,token.end()))
        cursor=token.end()
    return tokens


class _MatlabExpression:
    def __init__(self,text):
        self.text=text;self.tokens=_lex(text);self.position=0

    def peek(self):
        return self.tokens[self.position][0] if self.position<len(self.tokens) else ''

    def take(self,expected=None):
        token=self.peek()
        if not token or expected is not None and token!=expected:raise ValueError('Expresión MATLAB incompleta.')
        self.position+=1
        return token

    def prefix(self):
        start=self.position;token=self.take()
        if token in ('+','-'):
            return ast.UnaryOp(ast.UAdd() if token=='+' else ast.USub(),self.read(35))
        if token=='(':
            value=self.read();self.take(')');return value
        if token=='[':
            depth=1
            while depth:
                next_token=self.take()
                if next_token=='[':depth+=1
                if next_token==']':depth-=1
            return ast.Constant(self.text[self.tokens[start][1]:self.tokens[self.position-1][2]])
        if token[0].isdigit() or token.startswith('.') and len(token)>1 and token[1].isdigit():
            number=ast.Constant(float(token) if any(c in token for c in '.eE') else int(token))
            if self.peek() in ('i','j') and self.tokens[start][2]==self.tokens[self.position][1]:
                return ast.BinOp(number,ast.Mult(),ast.Name(self.take()))
            return number
        if token.isidentifier():
            name=ast.Name(token)
            if self.peek()!='(':return name
            self.take('(');args=[]
            if self.peek()!=')':
                args.append(self.read())
                while self.peek()==',':
                    self.take(',');args.append(self.read())
            self.take(')')
            return ast.Call(name,args,[])
        raise ValueError('Se esperaba un valor o una expresión entre paréntesis.')

    def read(self,minimum=0):
        left=self.prefix()
        while _PRECEDENCE.get(self.peek(),-1)>=minimum:
            operator=self.take();precedence=_PRECEDENCE[operator]
            if operator in ("'",".'"):
                call=ast.Call(ast.Name('transpose'),[left],[])
                call.matlab_transpose=operator
                left=call
                continue
            right=self.read(precedence+1)
            if operator==':':
                args=[left,right]
                if self.peek()==':':
                    self.take(':');args.append(self.read(precedence+1))
                call=ast.Call(ast.Name('colon'),args,[])
                call.matlab_colon=True
                left=call
            elif operator in _COMPARISONS:
                left=ast.Compare(left,[_COMPARISONS[operator]()],[right])
            else:
                left=ast.BinOp(left,_BINOPS[operator](),right)
                if operator in ('^','.^'):left.matlab_power=operator
        return left


def _array_cells(row):
    cells=[];start=0;depth=0
    for match in re.finditer(r'[\s,]+|[\[(\])]',row):
        token=match[0]
        if token in ('[','('):depth+=1
        elif token in (']',')'):depth-=1
        elif depth==0:
            before=row[start:match.start()].rstrip();after=row[match.end():]
            if not before or not after:continue
            complete=before[-1].isalnum() or before[-1] in ".)]'"
            next_cell=after[0].isalnum() or after[0] in '[(' or after[0]=='.' and len(after)>1 and after[1].isdigit()
            signed=after[0] in '+-' and len(after)>1 and not after[1].isspace()
            call=after.startswith('(') and before[-1].isalpha()
            if ',' in token or complete and (signed or next_cell and not call):
                cells.append(before);start=match.end()
    cells.append(row[start:].strip())
    return cells


def _colon(args):
    nums=[float(np.asarray(arg).item()) for arg in args]
    start,step,stop=(nums[0],1.,nums[1]) if len(nums)==2 else nums
    if not np.isfinite(nums).all() or step==0:raise ValueError('Rango no finito o paso cero.')
    if start!=stop and (stop>start)!=(step>0):return np.empty((1,0))
    ratio=(stop-start)/step
    if not math.isfinite(ratio):raise ValueError('La longitud del rango excede el rango numérico.')
    nearest=round(ratio)
    at_endpoint=abs(ratio-nearest)<=4*math.ulp(ratio)
    count=(nearest if at_endpoint else math.floor(ratio))+1
    ensure_working_set(count,live_arrays=6)
    values=start+step*np.arange(count)
    if at_endpoint and count>1:values[-1]=stop
    return values.reshape(1,-1)


def expression(text,variables):
    text=text.strip()
    if text.startswith('['):
        depth=0
        for index,char in enumerate(text):
            if char=='[':depth+=1
            if char==']':depth-=1
            if depth==0:break
        if depth==0 and index==len(text)-1:
            rows=[]
            for row in split_top(text[1:-1],';\n'):
                cells=_array_cells(row)
                values=[np.atleast_2d(expression(c,variables)) for c in cells if c]
                if values:
                    if len({a.shape[0] for a in values})!=1:raise ValueError('La concatenación horizontal requiere la misma cantidad de filas.')
                    ensure_working_set(sum(a.size for a in values),live_arrays=6)
                    rows.append(np.concatenate(values,axis=1))
            if not rows:return np.empty((1,0))
            if len({r.shape[1] for r in rows})!=1:raise ValueError('La concatenación vertical requiere la misma cantidad de columnas.')
            ensure_working_set(sum(a.size for a in rows),live_arrays=6)
            return np.concatenate(rows,axis=0)
    parser=_MatlabExpression(text)
    tree=parser.read()
    if parser.peek():raise ValueError('Operador o separador inesperado: '+parser.peek())
    def run(node):
        if isinstance(node,ast.Constant):
            if isinstance(node.value,str):return expression(node.value,variables)
            return node.value
        if isinstance(node,ast.Name):
            if node.id in variables:return variables[node.id]
            if node.id in ('pi','i','j'):return np.pi if node.id=='pi' else 1j
            raise ValueError('Variable no definida: '+node.id)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):return -run(node.operand) if isinstance(node.op,ast.USub) else run(node.operand)
        if isinstance(node,ast.BinOp):
            a,b=run(node.left),run(node.right)
            shape=np.broadcast_shapes(np.shape(a),np.shape(b));ensure_working_set(math.prod(shape),live_arrays=8)
            if isinstance(node.op,ast.Add):return a+b
            if isinstance(node.op,ast.Sub):return a-b
            if isinstance(node.op,ast.MatMult):return a*b
            if isinstance(node.op,ast.Mult):
                if np.size(a)>1 and np.size(b)>1:raise ValueError('Para multiplicación elemento a elemento usá .*; el producto matricial no se importa desde .m.')
                return a*b
            if isinstance(node.op,ast.Div):
                if np.size(b)>1:raise ValueError('Para división elemento a elemento usá ./ .')
                return a/b
            if isinstance(node.op,ast.FloorDiv):return a/b
            if isinstance(node.op,ast.Pow):
                if node.matlab_power=='^' and (np.size(a)>1 or np.size(b)>1):
                    raise ValueError('La potencia matricial ^ no se importa. Usá .^ para potencias elemento a elemento.')
                base=np.asarray(a,dtype=complex if np.iscomplexobj(a) else float)
                if not np.iscomplexobj(base) and np.any(base<0) and (np.iscomplexobj(b) or np.any(np.asarray(b)!=np.trunc(b))):
                    base=base.astype(complex)
                return np.power(base,b)
        if isinstance(node,ast.Compare) and len(node.ops)==1:
            a,b=run(node.left),run(node.comparators[0]);op=node.ops[0]
            for cls,fn in [(ast.Lt,np.less),(ast.LtE,np.less_equal),(ast.Gt,np.greater),(ast.GtE,np.greater_equal),(ast.Eq,np.equal),(ast.NotEq,np.not_equal)]:
                if isinstance(op,cls):return fn(a,b)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
            args=[run(a) for a in node.args];name=node.func.id
            if getattr(node,'matlab_colon',False):return _colon(args)
            transpose=getattr(node,'matlab_transpose',None)
            if transpose:
                value=np.asarray(args[0])
                return value.conj().T if transpose=="'" else value.T
            unary={'sin':np.sin,'cos':np.cos,'tan':np.tan,'exp':np.exp,'sqrt':np.emath.sqrt,'abs':np.abs,'real':np.real,'imag':np.imag,'conj':np.conj,'log':np.emath.log,'log10':np.emath.log10,'sinc':np.sinc}
            from .hyperbolic import NUMERIC
            unary.update(NUMERIC)
            if name in unary and len(args)==1:return unary[name](*args)
            if name=='complex' and len(args)==2:return np.asarray(args[0])+1j*np.asarray(args[1])
            if name=='linspace' and len(args) in (2,3):
                n=100 if len(args)==2 else int(args[2]);ensure_working_set(n,live_arrays=6)
                if n<0 or (len(args)==3 and n!=args[2]):raise ValueError('Cantidad de linspace no válida.')
                return np.linspace(float(args[0]),float(args[1]),n).reshape(1,-1)
            if name in ('zeros','ones') and len(args) in (1,2):
                shape=tuple(int(a) for a in args)
                if any(s<0 or s!=a for s,a in zip(shape,args)):raise ValueError('Tamaño de matriz no válido.')
                if len(shape)==1:shape*=2
                ensure_working_set(math.prod(shape),live_arrays=6)
                return (np.zeros if name=='zeros' else np.ones)(shape)
        raise ValueError('Expresión no admitida. Exportá las variables a .mat desde MATLAB para importar este cálculo.')
    with np.errstate(all='raise'):return run(tree)

def read_script(path):
    text=Path(path).read_text(encoding='utf-8-sig');text=re.sub(r'%[^\n]*','',text);text=re.sub(r'\.\.\.\s*\n',' ',text)
    variables={}
    for statement in split_top(text,';\n'):
        if not statement:continue
        if statement.strip() in ('clear','clear all'):variables.clear();continue
        if statement.strip() in ('clc','close all'):continue
        match=re.fullmatch(r'([A-Za-z]\w*)\s*=\s*(.+)',statement,re.S)
        if not match:raise ValueError('Instrucción .m no admitida: '+statement[:90]+'. Importá un .mat para scripts con funciones, gráficos o bucles.')
        name,value=match.groups()
        try:array=np.asarray(expression(value,variables))
        except Exception as exc:raise ValueError(f'Variable {name}: {exc}') from exc
        if array.dtype.kind not in 'biufc' or not np.isfinite(array).all():raise ValueError(f'{name}: se requieren datos numéricos finitos.')
        ensure_working_set(sum(v.size for k,v in variables.items() if k!=name)+array.size,live_arrays=4)
        variables[name]=array
    return variables

class MatlabFile:
    def __init__(self,path):
        self.path=Path(path);self.script=None;self.hdf=False;self.entries={}
        if self.path.suffix.lower()=='.m':
            self.script=read_script(path);self.entries={k:v.shape for k,v in self.script.items() if v.size and v.ndim<=2}
            if not self.entries:raise ValueError('El archivo .m no define variables numéricas importables.')
            return
        import h5py
        self.hdf=h5py.is_hdf5(path)
        if self.hdf:
            with h5py.File(path,'r') as f:
                def visit(name,node):
                    if name.startswith('#') or not isinstance(node,h5py.Dataset) or node.ndim>2 or not node.size:return
                    cls=node.attrs.get('MATLAB_class',b'')
                    if cls in (b'char',b'cell',b'struct',b'opaque'):return
                    if node.dtype.kind in 'biufc' or node.dtype.names==('real','imag'):self.entries[name]=tuple(reversed(node.shape))
                f.visititems(visit)
        else:
            from scipy.io import whosmat
            for name,shape,kind in whosmat(path):
                if kind in ('double','single','int8','uint8','int16','uint16','int32','uint32','int64','uint64','logical') and len(shape)<=2 and math.prod(shape):self.entries[name]=shape
        if not self.entries:raise ValueError('No hay vectores ni matrices numéricas compatibles. Exportá la señal y su eje como variables numéricas.')
    def load(self,name):
        ensure_working_set(math.prod(self.entries[name]),live_arrays=6)
        if self.script is not None:return self.script[name]
        if self.hdf:
            import h5py
            with h5py.File(self.path,'r') as f:result=f[name][()]
            if result.dtype.names:result=result['real']+1j*result['imag']
            return result.T
        from scipy.io import loadmat
        return loadmat(self.path,variable_names=[name])[name]

def vector(array,column=0):
    array=np.asarray(array)
    if array.ndim>2:raise ValueError('Seleccioná un vector o una matriz de canales de dos dimensiones.')
    if array.size==0:raise ValueError('La variable seleccionada no contiene muestras.')
    if array.ndim==0 or array.ndim==1 or 1 in array.shape:return array.reshape(-1)
    if not 0<=column<array.shape[1]:raise ValueError('La columna seleccionada no existe.')
    return array[:,column]


def make_signal(data,name,column,domain,axis_name=None,origin=0,step=1,units=None):
    from .scalar_expression import integer_value
    values=vector(data.load(name),column);step=float(step)
    if domain not in ('discrete','continuous','frequency'):raise ValueError('Dominio de señal no admitido.')
    origin=integer_value(str(origin)) if domain=='discrete' and not axis_name else float(origin)
    if axis_name:
        axis=np.asarray(data.load(axis_name))
        if axis.ndim>2 or (axis.ndim==2 and min(axis.shape)>1):raise ValueError('Seleccioná un vector para el eje, no una matriz de canales.')
        axis=axis.reshape(-1)
        if axis.size!=values.size or np.any(np.imag(axis)) or not np.isfinite(axis).all():raise ValueError('El eje debe ser un vector real finito con tantas coordenadas como muestras.')
        axis=axis.real
        if domain=='discrete':
            # Never project an integer axis to float: adjacent indices beyond
            # 2**53 would silently move or collapse.
            origin=int(axis[0]);last=origin+len(axis)-1;limit=np.iinfo(np.int64)
            if origin<limit.min or last>limit.max:raise ValueError('El eje excede los índices enteros de 64 bits.')
            if axis.dtype.kind in 'iu':valid=np.array_equal(axis,np.arange(len(axis),dtype=np.int64)+origin)
            else:
                from .jobs import checkpoint
                valid=True
                for index,value in enumerate(axis):
                    if index%4096==0:checkpoint()
                    if value!=int(value) or int(value)!=origin+index:valid=False;break
            if not valid:raise ValueError('Una secuencia requiere índices enteros consecutivos y exactos. No se redondea ni se remuestrea el eje.')
            step=1
        else:
            origin=float(axis[0])
            if len(axis)>1:
                from .uniform_axis import uniform_step
                step=uniform_step(axis)
    if domain=='discrete' and step!=1:raise ValueError('Una secuencia requiere paso exactamente 1. Para tiempos en segundos elegí señal continua muestreada.')
    if not np.isfinite(step) or step<=0:raise ValueError('El paso debe ser positivo y finito.')
    return Signal(values,origin,step,units or {'discrete':'n','continuous':'s','frequency':'rad/s'}[domain],name,domain,metadata={'source_format':'MATLAB','source_file':data.path.name,'source_variable':name,'column':column+1,'axis_variable':axis_name})
