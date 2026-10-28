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
            values=[np.atleast_1d(expression(c,variables)).reshape(-1) for c in cells if c]
            if values:rows.append(np.concatenate(values))
        if not rows:return np.empty((1,0))
        if len({len(r) for r in rows})!=1:raise ValueError('Las filas de una matriz deben tener igual longitud.')
        return np.vstack(rows)
    colon=split_top(text,':')
    if len(colon)>1:
        if len(colon) not in (2,3):raise ValueError('Rango no válido.')
        nums=[float(np.asarray(expression(x,variables)).item()) for x in colon]
        start,step,stop=(nums[0],1.,nums[1]) if len(nums)==2 else nums
        if not np.isfinite(nums).all() or step==0:raise ValueError('Rango no finito o paso cero.')
        count=max(0,math.floor((stop-start)/step+1e-10)+1);ensure_working_set(count,live_arrays=6)
        return (start+step*np.arange(count)).reshape(1,-1)
    text=re.sub(r'(?<=[0-9.])([ij])\b',r'*\1',text)
    scalar_power=bool(re.search(r'(?<!\.)\^',text))
    text=text.replace('.*','@').replace('./','//').replace('.^','**').replace('^','**')
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
            if isinstance(node.op,(ast.Pow,ast.BitXor)):
                if scalar_power and np.size(a)>1:raise ValueError('La potencia matricial ^ no se importa; separá las potencias escalares y usá .^ para vectores.')
                return np.power(np.asarray(a,dtype=complex if np.iscomplexobj(a) else float),b)
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
    if array.ndim==0 or array.ndim==1 or 1 in array.shape:return array.reshape(-1)
    return array[:,column]

def make_signal(data,name,column,domain,axis_name=None,origin=0,step=1,units=None):
    values=vector(data.load(name),column);origin=float(origin);step=float(step)
    if axis_name:
        axis=np.asarray(data.load(axis_name))
        if axis.ndim>2 or (axis.ndim==2 and min(axis.shape)>1):raise ValueError('Seleccioná un vector para el eje, no una matriz de canales.')
        axis=axis.reshape(-1)
        if axis.ndim!=1 or axis.size!=values.size or np.any(np.imag(axis)) or not np.isfinite(axis).all():raise ValueError('El eje debe ser un vector real finito con tantas coordenadas como muestras.')
        axis=axis.real;origin=float(axis[0])
        if len(axis)>1:
            step=float((axis[-1]-axis[0])/(len(axis)-1))
            if step<=0 or not np.allclose(axis,origin+step*np.arange(len(axis)),rtol=0,atol=max(abs(step)*1e-7,np.finfo(float).eps*np.max(abs(axis))*8)):
                raise ValueError('El eje no es uniforme y creciente. No se remuestrea ni se descartan coordenadas.')
    if domain=='discrete' and (origin!=int(origin) or not np.isclose(step,1,rtol=0,atol=1e-9)):raise ValueError('Una secuencia requiere índices enteros con paso 1. Para tiempos en segundos elegí señal continua muestreada.')
    if step<=0:raise ValueError('El paso debe ser positivo.')
    return Signal(values,origin,1 if domain=='discrete' else step,units or {'discrete':'n','continuous':'s','frequency':'rad/s'}[domain],name,domain,metadata={'source_format':'MATLAB','source_file':data.path.name,'source_variable':name,'column':column+1,'axis_variable':axis_name})

