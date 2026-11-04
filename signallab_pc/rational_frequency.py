"""Exceptional-point evaluation of the exact stored binary rational model."""
from fractions import Fraction as F
from math import hypot,nextafter,inf,isfinite
import numpy as np
from .jobs import checkpoint
from .resources import ensure_working_set

ZERO=(F(0),F(0));ONE=(F(1),F(0))
def add(a,b):return a[0]+b[0],a[1]+b[1]
def sub(a,b):return a[0]-b[0],a[1]-b[1]
def mul(a,b):return a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]
def scale(a,n):return a[0]*n,a[1]*n
def div(a,b):
    norm=b[0]*b[0]+b[1]*b[1]
    return (a[0]*b[0]+a[1]*b[1])/norm,(a[1]*b[0]-a[0]*b[1])/norm
def exact(value):return F(float(complex(value).real)),F(float(complex(value).imag))
def trim(coeff):
    start=0
    while start<len(coeff)-1 and coeff[start]==ZERO:start+=1
    return tuple(coeff[start:])
def derivative(coeff):return tuple(scale(value,len(coeff)-i-1) for i,value in enumerate(coeff[:-1])) or (ZERO,)
def polyval(coeff,point):
    result=ZERO
    for n,value in enumerate(coeff):
        if n%64==0:checkpoint()
        result=add(mul(result,point),value)
    return result
def convolution(one,two):
    result=[ZERO]*(len(one)+len(two)-1)
    for n,a in enumerate(one):
        checkpoint()
        for k,b in enumerate(two):result[n+k]=add(result[n+k],mul(a,b))
    return trim(result)
def jet(coeff,point):
    for order in range(len(coeff)):
        value=polyval(coeff,point)
        if value!=ZERO:return order,value,polyval(derivative(coeff),point),coeff
        coeff=derivative(coeff)
    return None
def real_float(value):
    try:result=float(value)
    except OverflowError:return float('nan')
    return result if isfinite(result) and (result!=0 or value==0) else float('nan')
def complex_float(value):
    try:result=complex(float(value[0]),float(value[1]))
    except OverflowError:return complex(np.nan,np.nan)
    return result if np.isfinite(result) and (result!=0 or value==ZERO) else complex(np.nan,np.nan)


class RationalModel:
    def __init__(self,b,a,*,digital=False,advance=0):
        self.b=trim(tuple(b));self.a=trim(tuple(a));self.digital=digital;self.advance=advance;self.reduced=False
        self.constant=None
        if len(self.b)==len(self.a):
            ratio=div(self.b[0],self.a[0])
            if all(v==mul(ratio,w) for v,w in zip(self.b,self.a)):self.constant=ratio
        degree=max(len(self.b),len(self.a))
        ensure_working_set(degree*degree,bytes_per_sample=256,live_arrays=8)
    @classmethod
    def system(cls,system):
        digital=system.domain=='digital'
        if system.sos is not None:
            degree=2*len(system.sos)+1;ensure_working_set(degree*degree,bytes_per_sample=256,live_arrays=8)
            b=a=(ONE,)
            for row in system.sos:
                b=convolution(b,trim(tuple(exact(v) for v in row[:3][::-1])))
                a=convolution(a,trim(tuple(exact(v) for v in row[3:][::-1])))
        else:
            b=tuple(exact(v) for v in (system.b[::-1] if digital else system.b))
            a=tuple(exact(v) for v in (system.a[::-1] if digital else system.a))
        return cls(b,a,digital=digital,advance=system.advance)
    def reduce(self):
        """Remove polynomial factors exactly, never match nearby numerical roots."""
        import sympy as sp
        checkpoint();x=sp.Dummy('coordinate')
        def number(v):return sp.Rational(v[0].numerator,v[0].denominator)+sp.I*sp.Rational(v[1].numerator,v[1].denominator)
        b=sp.Poly.from_list([number(v) for v in self.b],x);a=sp.Poly.from_list([number(v) for v in self.a],x)
        common=sp.gcd(b,a);checkpoint()
        if common.degree()>0:
            def coefficients(polynomial):
                result=[]
                for v in polynomial.exquo(common).all_coeffs():
                    re,im=v.as_real_imag();result.append((F(int(sp.numer(re)),int(sp.denom(re))),F(int(sp.numer(im)),int(sp.denom(im)))))
                return tuple(result)
            self.b,self.a=coefficients(b),coefficients(a)
        self.reduced=True
    def uncertain(self,coeff,value,point):
        re,im=complex_float(point).real,complex_float(point).imag
        maximum=max(abs(re),abs(im))
        if not isfinite(maximum):return True
        radius=F(0) if maximum==0 else F(maximum)*F(nextafter(hypot(re/maximum,im/maximum),inf))
        bound=F(0)
        for v in coeff:bound=bound*radius+abs(v[0])+abs(v[1])
        return max(abs(value[0]),abs(value[1]))<=F(32+8*len(coeff),2**52)*bound
    def pair(self,point,*,exact_coordinate=False):
        checkpoint()
        if self.constant is not None:return complex_float(self.constant),(-float(self.advance) if self.digital else 0.) if self.constant!=ZERO else float('nan')
        point=exact(point)
        if all(v==ZERO for v in self.b):return 0j,float('nan')
        numerator,denominator=jet(self.b,point),jet(self.a,point)
        if denominator is None:return complex(np.nan,np.nan),float('nan')
        if numerator is None:return 0j,float('nan')
        if numerator[0]>denominator[0]:return 0j,float('nan')
        if numerator[0]<denominator[0]:return complex(np.nan,np.nan),float('nan')
        bad_denominator=not exact_coordinate and self.uncertain(denominator[3],denominator[1],point)
        bad_numerator=not exact_coordinate and self.uncertain(numerator[3],numerator[1],point)
        if (bad_denominator or bad_numerator) and not self.reduced:
            self.reduce();return self.pair(complex(float(point[0]),float(point[1])),exact_coordinate=exact_coordinate)
        if bad_denominator:return complex(np.nan,np.nan),float('nan')
        response=complex_float(div(numerator[1],denominator[1]))
        if bad_numerator:return response,float('nan')
        slope=sub(div(numerator[2],scale(numerator[1],numerator[0]+1)),div(denominator[2],scale(denominator[1],denominator[0]+1)))
        delay=mul(point,slope)[0]-self.advance if self.digital else -slope[0]
        return response,real_float(delay)


def repair(system,points,values,mask,*,delay=False):
    indices=np.flatnonzero(mask)
    if not len(indices):return values
    model=RationalModel.system(system);result=np.array(values,copy=True)
    if model.constant is not None:
        response,group_delay=model.pair(0j);result[mask]=group_delay if delay else response;return result
    for index in indices:
        point=points.flat[index]
        coordinate_known=system.domain=='analog' or (point.imag==0 and point.real in (-1,1))
        response,group_delay=model.pair(point,exact_coordinate=coordinate_known);result.flat[index]=group_delay if delay else response
    return result


def repair_plane(system,points,values,mask):
    indices=np.flatnonzero(mask&np.isfinite(points))
    if not len(indices):return values
    if system.sos is not None:
        degree=2*len(system.sos)+system.advance+1;ensure_working_set(degree*degree,bytes_per_sample=256,live_arrays=8)
        b=a=(ONE,)
        for row in system.sos:
            b=convolution(b,trim(tuple(exact(v) for v in row[:3])));a=convolution(a,trim(tuple(exact(v) for v in row[3:])))
        b=tuple(b)+(ZERO,)*system.advance
    else:
        if system.domain=='analog':bb,aa=system.b,system.a
        else:
            degree=max(len(system.b),len(system.a))
            bb=np.r_[system.b,np.zeros(degree-len(system.b)+system.advance)];aa=np.r_[system.a,np.zeros(degree-len(system.a))]
        b,a=tuple(exact(v) for v in bb),tuple(exact(v) for v in aa)
    model=RationalModel(b,a);result=np.array(values,copy=True)
    for index in indices:result.flat[index]=model.pair(points.flat[index],exact_coordinate=True)[0]
    return result
