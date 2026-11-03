"""Read plotted points without interpolation or changes to scientific data."""
from dataclasses import dataclass
import numpy as np
from matplotlib.container import StemContainer
from matplotlib.collections import PathCollection


def attach_signal(artists, source, component):
    targets=[artists.markerline] if isinstance(artists,StemContainer) else artists if isinstance(artists,(tuple,list)) else [artists]
    for artist in targets:artist._signallab_probe_source=(source,component)


@dataclass
class Trace:
    axis:object
    artist:object
    label:str
    x:np.ndarray
    y:np.ndarray
    spatial:bool=False

    def __post_init__(self):
        self.valid=np.flatnonzero(np.isfinite(self.x))
        self.sorted_x=self.x[self.valid]
        difference=np.diff(self.sorted_x)
        if difference.size and np.all(difference<=0):self.valid=self.valid[::-1];self.sorted_x=self.sorted_x[::-1]
        elif difference.size and not np.all(difference>=0):self.spatial=True

    @property
    def key(self):return id(self.artist)

    def point(self,x,y=None):
        complete=getattr(self.artist,'_signallab_probe_values',None)
        if complete is not None:
            origin,step,values=complete;index=min(max(int(np.floor((x-origin)/step+.5)),0),len(values)-1)
            return float(origin+index*step),float(values[index])
        full=getattr(self.artist,'_signallab_probe_source',None)
        if full is not None:
            source,component=full
            index=min(max(int(np.floor((x-source.origin)/source.step+.5)),0),source.values.size-1)
            coordinate=source.origin+index*source.step;value=source.values[index]
            value=value.real if component=='real' else value.imag if component=='imag' else abs(value) if component=='magnitude' else 10*np.log10(value.real) if component=='density_db' and value.real>0 else np.nan if component=='density_db' else np.angle(value) if value else np.nan
            return float(coordinate),float(value)
        if not self.valid.size:return None
        if self.spatial:
            # Scatter and complex-plane loops require a 2-D screen distance.
            if y is None:return None
            ids=self.valid[np.isfinite(self.y[self.valid])]
            if not ids.size:return None
            points=self.axis.transData.transform(np.column_stack((self.x[ids],self.y[ids])))
            target=self.axis.transData.transform((x,y));distance=np.sum((points-target)**2,axis=1)
            good=np.isfinite(distance)
            if not good.any():return None
            index=ids[np.flatnonzero(good)[np.argmin(distance[good])]]
        else:
            where=int(np.searchsorted(self.sorted_x,x));candidates=[i for i in (where-1,where) if 0<=i<len(self.valid)]
            index=self.valid[min(candidates,key=lambda i:abs(self.sorted_x[i]-x))]
        return float(self.x[index]),float(self.y[index])


def collect(figure):
    traces=[]
    for axis in figure.axes:
        if axis.name=='3d' or not axis.axison or getattr(axis,'_colorbar',None) is not None:continue
        stems={id(c.markerline):c for c in axis.containers if isinstance(c,StemContainer)}
        baselines={id(c.baseline) for c in axis.containers if isinstance(c,StemContainer)}
        for artist in [*axis.lines,*axis.collections]:
            if getattr(artist,'_signallab_probe',False) or not artist.get_visible() or artist.get_alpha()==0 or id(artist) in baselines:continue
            try:
                if artist in axis.lines:
                    if artist.get_transform()!=axis.transData:continue
                    x=np.ma.filled(np.ma.asarray(artist.get_xdata(orig=False),dtype=float),np.nan)
                    y=np.ma.filled(np.ma.asarray(artist.get_ydata(orig=False),dtype=float),np.nan);spatial=False
                elif isinstance(artist,PathCollection) and artist.get_offset_transform()==axis.transData:
                    offsets=np.ma.filled(artist.get_offsets(),np.nan);x=offsets[:,0];y=offsets[:,1];spatial=True
                else:continue
                if np.ndim(x)!=1 or len(x)!=len(y) or not len(x):continue
                label=(stems[id(artist)].get_label() if id(artist) in stems else artist.get_label()) or ''
                if label.startswith('_'):label=axis.get_ylabel() or 'Traza '+str(len(traces)+1)
                traces.append(Trace(axis,artist,label,x,y,spatial))
            except (ValueError,TypeError,IndexError):continue
    return traces


def compatible(axis,other):
    if axis is other:return True
    if axis.name!=other.name:return False
    if other in axis.get_shared_x_axes().get_siblings(axis):return True
    tag=getattr(axis,'_signallab_coordinate',None)
    return tag is not None and tag==getattr(other,'_signallab_coordinate',None)


def readings(traces,axis,x,y):
    result={}
    for trace in traces:
        if compatible(axis,trace.axis):
            point=trace.point(x,y if trace.axis is axis else None)
            if point is not None:result[trace.key]=point
    return result
