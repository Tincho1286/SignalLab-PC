"""Paged explanations of existing sum/product results, without a second solver."""
import math
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
from .continuous import interpolate_record
from .resources import ensure_working_set


class Alignment:
    def __init__(self,first,second,result):
        ensure_working_set(sum(len(s.values) for s in (first,second,result)),live_arrays=5)
        self.first,self.second,self.result=(s.copy_with(metadata=deepcopy(s.metadata)) for s in (first,second,result))
        self.sources=[SimpleNamespace(axis=s.axis,values=s.values,step=s.step) for s in (self.first,self.second)] if result.domain=='continuous' else []

    def page(self,start=0,count=250):
        y=self.result;stop=min(len(y.values),start+count)
        if start<0 or start>stop:raise ValueError('La fila no pertenece al resultado.')
        axis=[int(y.origin)+i for i in range(start,stop)] if y.domain=='discrete' else y.origin+y.step*np.arange(start,stop)
        columns=[];coverage=[]
        for index,s in enumerate((self.first,self.second)):
            if y.domain=='discrete':
                offsets=[n-int(s.origin) for n in axis];valid=np.array([0<=i<len(s.values) for i in offsets]);values=np.zeros(len(axis),complex)
                for j,i in enumerate(offsets):
                    if valid[j]:values[j]=s.values[i]
            else:
                cached=self.sources[index];values=interpolate_record(cached,np.asarray(axis));points=cached.axis
                tolerance=min(s.step/4,max(4*math.ulp(float(points[0])),4*math.ulp(float(points[-1]))));valid=(np.asarray(axis)>=points[0]-tolerance)&(np.asarray(axis)<=points[-1]+tolerance)
            columns.append(values);coverage.append(valid)
        return [(n,columns[0][j],columns[1][j],y.values[start+j],('x y segunda' if coverage[0][j] and coverage[1][j] else 'Solo x · segunda = 0' if coverage[0][j] else 'Solo segunda · x = 0' if coverage[1][j] else 'Ambas fuera del registro · 0')) for j,n in enumerate(axis)]

    def offset_for(self,text):
        from .scalar_expression import integer_value,real_value
        y=self.result;coordinate=integer_value(text) if y.domain=='discrete' else real_value(text)
        offset=coordinate-int(y.origin) if y.domain=='discrete' else round((coordinate-y.origin)/y.step)
        if not 0<=offset<len(y.values):raise ValueError('La coordenada no pertenece al intervalo del resultado.')
        return offset
