"""Shared hyperbolic vocabulary and CAS-compatible numerical principal branches."""
import numpy as np

NAMES=('sinh','cosh','tanh','sech','csch','coth','asinh','acosh','atanh','asech','acsch','acoth')
ALIASES={**{'arc'+name[1:]:name for name in NAMES if name.startswith('a')},'senh':'sinh','arcsenh':'asinh'}


def symbolic_functions():
    import sympy as sp
    functions={name:getattr(sp,name) for name in NAMES}
    functions.update({alias:functions[name] for alias,name in ALIASES.items()})
    return functions


def _inverse(value,kind):
    z=np.asarray(value,dtype=np.complex128)
    # Signed zeros from arithmetic must not select a different sheet from the
    # exact CAS value on a cut. Away from cuts NumPy uses the same branches.
    z=np.where(z.real==0,0.,z.real)+1j*np.where(z.imag==0,0.,z.imag)
    if kind=='asinh':
        result=np.arcsinh(z)
        return np.where((z.real==0)&(z.imag<-1),-np.conj(result),result)
    if kind=='acosh':return np.arccosh(z)
    if kind=='atanh':
        result=np.arctanh(z)
        return np.where((z.imag==0)&(z.real>1),np.conj(result),result)
    if kind=='acoth':
        # acoth(0)=i*pi/2 on the CAS principal branch, not atanh(infinity).
        return np.where(z==0,1j*np.pi/2,_inverse(np.divide(1.,z),'atanh'))
    inverse=np.divide(1.,z)
    return _inverse(inverse,'acosh' if kind=='asech' else 'asinh')


NUMERIC={'sinh':np.sinh,'cosh':np.cosh,'tanh':np.tanh,
    'sech':lambda z:np.divide(1.,np.cosh(z)),
    'csch':lambda z:np.divide(1.,np.sinh(z)),
    'coth':lambda z:np.divide(1.,np.tanh(z)),
    **{name:(lambda z,kind=name:_inverse(z,kind)) for name in NAMES if name.startswith('a')}}
NUMERIC.update({alias:NUMERIC[name] for alias,name in ALIASES.items()})
