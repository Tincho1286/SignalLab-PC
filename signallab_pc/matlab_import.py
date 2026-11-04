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

def expression(text,variables):
    text=text.strip()
    if text.endswith(".'"):return np.asarray(expression(text[:-2],variables)).T
    if text.endswith("'"):return np.asarray(expression(text[:-1],variables)).conj().T
    if text.startswith('[') and text.endswith(']'):
        rows=[]
        for row in split_top(text[1:-1],';\n'):
            cells=split_top(row,',')
            if len(cells)==1:
                # Space-separated literals and variable names; compound cells use commas.
                if re.fullmatch(r'[\w.+\-\s]+',row):cells=row.split()
            values=[np.atleast_2d(expression(c,variables)) for c in cells if c]
            if values:
                if len({a.shape[0] for a in values})!=1:raise ValueError('La concatenación horizontal requiere la misma cantidad de filas.')
                ensure_working_set(sum(a.size for a in values),live_arrays=6)
                rows.append(np.concatenate(values,axis=1))
        if not rows:return np.empty((1,0))
        if len({r.shape[1] for r in rows})!=1:raise ValueError('La concatenación vertical requiere la misma cantidad de columnas.')
        ensure_working_set(sum(a.size for a in rows),live_arrays=6)
        return np.concatenate(rows,axis=0)
    colon=split_top(text,':')
    if len(colon)>1:
        if len(colon) not in (2,3):raise ValueError('Rango no válido.')
        nums=[float(np.asarray(expression(x,variables)).item()) for x in colon]
        start,step,stop=(nums[0],1.,nums[1]) if len(nums)==2 else nums
        if not np.isfinite(nums).all() or step==0:raise ValueError('Rango no finito o paso cero.')
        count=max(0,math.floor((stop-start)/step+1e-10)+1);ensure_working_set(count,live_arrays=6)
        return (start+step*np.arange(count)).reshape(1,-1)
    text=re.sub(r'(?<=[0-9.])([ij])\b',r'*\1',text)
    operators={'.*':'@','./':'//','.^':'**','^':'**'}
    chunks=[];powers={};position=0;cursor=0
    for operator in re.finditer(r'\.\*|\./|\.\^|\^',text):
        prefix=text[cursor:operator.start()];token=operator[0]
        chunks.extend((prefix,operators[token]));position+=len(prefix.encode('utf-8'))
        if token in ('^','.^'):powers[position]=token
        position+=len(operators[token]);cursor=operator.end()
    text=''.join((*chunks,text[cursor:]))
    offsets=[0,*[match.end() for match in re.finditer(rb'\n',text.encode('utf-8'))]]
    tree=ast.parse(text,mode='eval')
    def run(node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float,complex)):return node.value
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
                left=offsets[node.left.end_lineno-1]+node.left.end_col_offset
                right=offsets[node.right.lineno-1]+node.right.col_offset
                operator=next(token for pos,token in powers.items() if left<=pos<right)
                if operator=='^' and (np.size(a)>1 or np.size(b)>1):
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
            unary={'sin':np.sin,'cos':np.cos,'tan':np.tan,'exp':np.exp,'sqrt':np.emath.sqrt,'abs':np.abs,'real':np.real,'imag':np.imag,'conj':np.conj,'log':np.emath.log,'log10':np.emath.log10,'sinc':np.sinc}
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
    with np.errstate(all='raise'):return run(tree.body)

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
