"""Read plotted points without interpolation or changes to scientific data."""
from dataclasses import dataclass
import numpy as np
from matplotlib.container import StemContainer
from matplotlib.collections import PathCollection
from .signal_plot import vertical_axis_name
from .uniform_axis import sample_coordinate, sample_index


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

    @property
    def sample_source(self):
        return getattr(self.artist, '_signallab_table_source', None) or getattr(self.artist, '_signallab_probe_source', None)

    def sample_point(self, index):
        source, component = self.sample_source
        coordinate = sample_coordinate(source, index)
        complete = getattr(self.artist, '_signallab_probe_values', None)
        if complete is not None:
            return coordinate, float(complete[2][index])
        value = source.values[index]
        if component == 'real':
            value = value.real
        elif component == 'imag':
            value = value.imag
        elif component == 'magnitude':
            value = abs(value)
        elif component == 'density_db':
            value = 10 * np.log10(value.real) if value.real > 0 else np.nan
        else:
            value = np.angle(value) if value else np.nan
        return coordinate, float(value)

    def point(self,x,y=None):
        curve=getattr(self.artist,'_signallab_probe_curve',None)
        if curve is not None:
            coordinates,values=curve
            descending=coordinates[-1]<coordinates[0];ordered=coordinates[::-1] if descending else coordinates
            base=getattr(self.axis,'_signallab_index_origin',0)
            lookup=ordered-base if base else ordered
            if x<lookup[0] or x>lookup[-1]:return None
            where=int(np.searchsorted(lookup,x));ids=[i for i in (where-1,where) if 0<=i<len(lookup)]
            index=min(ids,key=lambda i:abs((int(lookup[i]) if lookup.dtype.kind in 'iu' else float(lookup[i]))-x));index=len(coordinates)-1-index if descending else index
            return int(coordinates[index]) if coordinates.dtype.kind in 'iu' else float(coordinates[index]),float(values[index])
        if self.sample_source is not None:
            source, _ = self.sample_source
            base = getattr(self.axis,'_signallab_index_origin',0)
            index = sample_index(source, x, base=base)
            return self.sample_point(index) if index is not None else None
        complete=getattr(self.artist,'_signallab_probe_values',None)
        if complete is not None:
            origin,step,values=complete
            end=origin+step*(len(values)-1)
            if len(values)>1 and not min(origin,end)<=x<=max(origin,end):return None
            index=min(max(int(np.floor((x-origin)/step+.5)),0),len(values)-1)
            return float(origin+index*step),float(values[index])
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
            if self.valid.size>1 and not self.sorted_x[0]<=x<=self.sorted_x[-1]:return None
            where=int(np.searchsorted(self.sorted_x,x));candidates=[i for i in (where-1,where) if 0<=i<len(self.valid)]
            index=self.valid[min(candidates,key=lambda i:abs(self.sorted_x[i]-x))]
        base=getattr(self.axis,'_signallab_index_origin',None)
        coordinate=float(self.x[index]) if base is None else base+int(round(self.x[index]))
        return coordinate,float(self.y[index])


class PlanePointer:
    def __init__(self,axis):
        self.axis=axis;self.artist=axis.patch;self.label=getattr(axis,'_signallab_plane_label','Posición en el plano')
    @property
    def key(self):return id(self.axis.patch)
    def point(self,x,y=None):
        return (float(x),float(y)) if y is not None and np.isfinite([x,y]).all() else None


def collect(figure):
    traces=[]
    for axis in figure.axes:
        if axis.name=='3d' or not axis.axison or getattr(axis,'_colorbar',None) is not None:continue
        if getattr(axis,'_signallab_plane',False):traces.append(PlanePointer(axis));continue
        stems={id(c.markerline):c for c in axis.containers if isinstance(c,StemContainer)}
        baselines={id(c.baseline) for c in axis.containers if isinstance(c,StemContainer)}
        for artist in [*axis.lines,*axis.collections,*axis.images]:
            if getattr(artist,'_signallab_probe',False) or getattr(artist,'_signallab_reference',False) or not artist.get_visible() or artist.get_alpha()==0 or id(artist) in baselines:continue
            try:
                from .grid_probe import grid_trace
                grid=grid_trace(axis,artist)
                if grid is not None:traces.append(grid);continue
                if artist in axis.lines:
                    if artist.get_transform()!=axis.transData:continue
                    x=np.ma.filled(np.ma.asarray(artist.get_xdata(orig=False),dtype=float),np.nan)
                    y=np.ma.filled(np.ma.asarray(artist.get_ydata(orig=False),dtype=float),np.nan);spatial=False
                elif isinstance(artist,PathCollection) and artist.get_offset_transform()==axis.transData:
                    offsets=np.ma.filled(artist.get_offsets(),np.nan);x=offsets[:,0];y=offsets[:,1];spatial=True
                else:continue
                if np.ndim(x)!=1 or len(x)!=len(y) or not len(x):continue
                label=(stems[id(artist)].get_label() if id(artist) in stems else artist.get_label()) or ''
                if label.startswith('_'):label=vertical_axis_name(axis) or 'Traza '+str(len(traces)+1)
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
    base=getattr(axis,'_signallab_index_origin',0)
    for trace in traces:
        linked=trace.axis is axis if getattr(trace,'cell_values',False) else compatible(axis,trace.axis)
        if linked:
            origin=getattr(trace.axis,'_signallab_index_origin',0)
            point=trace.point(x+(base-origin),y if trace.axis is axis else None)
            if point is not None:result[trace.key]=point
    return result


def nearest_reading(traces, points, axis, x, y):
    """Pick the nearest readable point in screen space on the hovered panel."""
    local = [trace.key for trace in traces if trace.axis is axis and trace.key in points]
    if len(local) < 2:
        return next(iter(local), next(iter(points), None))
    base = getattr(axis, '_signallab_index_origin', 0)
    target = axis.transData.transform((x, y))
    coordinates = np.array([(points[key][0] - base, points[key][1]) for key in local])
    offsets = axis.transData.transform(coordinates) - target
    distances = np.hypot(offsets[:, 0], offsets[:, 1])
    finite = np.flatnonzero(np.isfinite(distances))
    return local[finite[distances[finite].argmin()]] if finite.size else local[0]


def trace_name(trace):
    panel = vertical_axis_name(trace.axis) or trace.axis.get_title()
    return f'{panel} · {trace.label}' if panel and panel != trace.label else trace.label
