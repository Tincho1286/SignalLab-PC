"""Inspect finite linear convolution using captured inputs, without recomputing it."""
from dataclasses import dataclass
import numpy as np
from .scalar_expression import integer_value
from .resources import ensure_working_set


@dataclass(frozen=True)
class ConvolutionTrace:
    x: np.ndarray
    h: np.ndarray
    y: np.ndarray
    x0: int
    h0: int
    y0: int


def capture(x, h, y):
    from .operations import _discrete
    for value in (x,h,y):_discrete(value)
    if y.origin!=int(x.origin)+int(h.origin) or len(y.values)!=len(x.values)+len(h.values)-1:
        raise ValueError('La salida no corresponde al soporte de la convolución lineal completa.')
    ensure_working_set(len(x.values)+len(h.values)+len(y.values),live_arrays=3)
    arrays=[value.values.copy() for value in (x,h,y)]
    for array in arrays:array.flags.writeable=False
    return ConvolutionTrace(*arrays,int(x.origin),int(h.origin),int(y.origin))


def calculate(x,h):
    from .operations import linear_convolution
    y=linear_convolution(x,h)
    try:return y,capture(x,h,y),None
    except (ValueError,MemoryError) as exc:return y,None,str(exc)


def inspect(trace,index,offset=0,count=100):
    n=integer_value(index);offset=integer_value(offset);count=integer_value(count)
    if not trace.y0<=n<trace.y0+len(trace.y):raise ValueError('Elegí n dentro del intervalo calculado.')
    if offset<0 or count<1:raise ValueError('La página de productos debe tener inicio no negativo y tamaño positivo.')
    first=max(trace.x0,n-trace.h0-len(trace.h)+1)
    last=min(trace.x0+len(trace.x)-1,n-trace.h0);total=max(0,last-first+1)
    if offset>=total and offset!=0:raise ValueError('Esa página queda fuera de los productos de esta muestra.')
    begin=first+offset;shown=max(0,min(count,total-offset));xi=begin-trace.x0;hi=n-begin-trace.h0
    xv=trace.x[xi:xi+shown];hv=trace.h[hi-shown+1:hi+1][::-1] if shown else trace.h[:0]
    # Products are ordinary multiplication: convolution does not conjugate h.
    with np.errstate(over='ignore',under='ignore',invalid='ignore'):
        products=xv*hv
        all_products=trace.x[first-trace.x0:last-trace.x0+1]*trace.h[n-last-trace.h0:n-first-trace.h0+1][::-1]
        reconstructed=np.sum(all_products,dtype=np.complex128)
    # A rounded-to-zero product of two nonzero complex values is underflow,
    # not a mathematical zero. Do not present it as an exact contribution.
    invalid=(~np.isfinite(all_products))|((all_products==0)&(trace.x[first-trace.x0:last-trace.x0+1]!=0)&(trace.h[n-last-trace.h0:n-first-trace.h0+1][::-1]!=0))
    finite=bool(not invalid.any() and np.isfinite(reconstructed))
    rows=[dict(k=begin+i,h_index=n-begin-i,x=complex(a),h=complex(b),product=complex(p) if np.isfinite(p) and (p!=0 or a==0 or b==0) else None) for i,(a,b,p) in enumerate(zip(xv,hv,products))]
    computed=complex(trace.y[n-trace.y0])
    return dict(index=n,first=first,last=last,total=total,offset=offset,rows=rows,
                computed=computed,reconstructed=complex(reconstructed) if finite else None,
                residual=computed-complex(reconstructed) if finite else None,unrepresentable_products=int(invalid.sum()))


def summary(data):
    from .result_summary import Summary,Section,Formula,number
    n=data['index'];rows=[('Índice n',str(n)),('Productos de la suma completa',str(data['total'])),('y['+str(n)+'] almacenada',number(data['computed']))]
    if data['reconstructed'] is not None:
        rows.extend([('Suma directa de todos los productos',number(data['reconstructed'])),('Diferencia numérica',number(data['residual']))])
    notes=['Se invierte h[k] y se desplaza hasta h[n−k]. Sólo se suman los productos donde coinciden ambos soportes. Fuera de los registros, las señales valen cero; no se conjuga h.',
           'La tabla y la alineación muestran una página de productos; la suma incluye todos. Se usan las muestras del último cálculo, aunque después edites las entradas.']
    if data['reconstructed'] is None:notes.append('Un producto o su suma queda fuera del rango numérico del inspector, por exceso o por subdesbordamiento. La tabla lo indica en lugar de inventar un cero. La salida calculada se conserva; no se reemplaza por esta comprobación.')
    else:notes.append('La diferencia compara una suma directa con la salida guardada, que puede haberse calculado por FFT. Puede existir redondeo; no es una prueba simbólica.')
    return Summary('Convolución · paso n='+str(n),[Section('Suma de productos',rows=rows,paragraphs=notes,formulas=[Formula('y[n] = Sum(x[k]*h[n-k], (k, -oo, oo))','y[n] = Σ x[k]·h[n−k]')])])
