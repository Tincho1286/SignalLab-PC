"""Render the visible interval of a dense curve, retaining extrema and true samples."""
import numpy as np


def visible_indices(x,y,low,high,budget=4000):
    if len(x)!=len(y) or budget<4:raise ValueError('La curva requiere coordenadas y valores del mismo tamaño.')
    low,high=sorted((low,high));first=max(0,int(np.searchsorted(x,low))-1);last=min(len(x),int(np.searchsorted(x,high,side='right'))+1)
    count=last-first
    if count<=budget:return np.arange(first,last,dtype=np.int64)
    block=int(np.ceil(count/max(1,budget//4)));selected=[first,last-1]
    for start in range(first,last,block):
        stop=min(start+block,last);part=np.asarray(y[start:stop]);finite=np.flatnonzero(np.isfinite(part))
        selected.extend((start,stop-1))
        if finite.size:selected.extend((start+int(finite[np.argmin(part[finite])]),start+int(finite[np.argmax(part[finite])])))
        # Keep a nonfinite break rather than connecting across a missing value.
        invalid=np.flatnonzero(~np.isfinite(part))
        if invalid.size:selected.extend((start+int(invalid[0]),start+int(invalid[-1])))
    return np.unique(np.asarray(selected,dtype=np.int64))


class VisibleCurve:
    def __init__(self,axis,x,y,*,label=None,color=None):
        self.axis=axis;self.x=np.asarray(x);self.y=np.asarray(y);self.busy=False
        if self.x.ndim!=1 or self.y.shape!=self.x.shape or not len(self.x) or not np.isfinite(self.x).all() or not np.all(self.x[1:]>self.x[:-1]):
            raise ValueError('La curva debe tener coordenadas finitas y crecientes.')
        self.line=axis.plot([],[],label=label,color=color)[0]
        self.line._signallab_probe_curve=(self.x,self.y)
        self.connection=axis.callbacks.connect('xlim_changed',self.update)
        axis.figure.canvas.mpl_connect('resize_event',self.update)
        self.update()

    def update(self,*_):
        if self.busy:return
        self.busy=True
        try:
            budget=max(400,int(self.axis.bbox.width*4))
            ids=visible_indices(self.x,self.y,*self.axis.get_xlim(),budget=budget)
            self.line.set_data(self.x[ids],self.y[ids])
            self.axis.figure.canvas.draw_idle()
        finally:self.busy=False


class VisibleStem(VisibleCurve):
    """Adaptive unconnected frequency samples, with full data retained for probes."""
    def __init__(self,axis,x,y,*,bottom=0.,label=None):
        from matplotlib.collections import LineCollection
        self.bottom=bottom;self.stems=LineCollection([]);self.stems._signallab_reference=True;axis.add_collection(self.stems)
        super().__init__(axis,x,y,label=label)
        self.line.set_linestyle('none');self.line.set_marker('.');self.stems.set_color(self.line.get_color());self.update()
    def update(self,*_):
        super().update()
        x,y=self.line.get_data();segments=np.empty((len(x),2,2));segments[:,0,0]=x;segments[:,1,0]=x;segments[:,0,1]=self.bottom;segments[:,1,1]=y
        self.stems.set_segments(segments)
