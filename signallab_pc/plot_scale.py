"""Readable automatic y ranges; plotted samples and manual zoom stay intact."""
import math
import unicodedata
import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.container import StemContainer

SMALL_VARIATION=1e-10


def _text(axis):
    return ''.join(c for c in unicodedata.normalize('NFKD',axis.get_ylabel()+' '+axis.get_title()).casefold() if not unicodedata.combining(c))


def _eligible(axis):
    if not axis.get_visible() or not axis.axison or axis.name!='rectilinear':return False
    if axis.get_yscale()!='linear' or axis.get_aspect()!='auto' or getattr(axis,'_colorbar',None) is not None or axis.images:return False
    # An error-measurement tool intentionally studies small differences.
    return not any(word in _text(axis) for word in ('error','residuo','diferencia','snr','ruido','noise'))


def _range(axis):
    low=math.inf;high=-math.inf;count=0
    baselines={id(container.baseline) for container in axis.containers if isinstance(container,StemContainer)}
    def collect(values):
        nonlocal low,high,count
        try:values=np.ma.asarray(values,dtype=float).compressed();values=values[np.isfinite(values)]
        except (TypeError,ValueError):return
        if values.size:low=min(low,float(np.min(values)));high=max(high,float(np.max(values)));count+=values.size
    for line in axis.lines:
        # Reference lines in axis coordinates and invisible stem baselines
        # must not turn a nearly constant data series into a broad range.
        if line.get_visible() and line.get_alpha()!=0 and id(line) not in baselines and line.get_transform()==axis.transData:
            collect(line.get_ydata(orig=False))
    for collection in axis.collections:
        if isinstance(collection,PathCollection) and collection.get_visible() and collection.get_alpha()!=0 and collection.get_offset_transform()==axis.transData:
            offsets=collection.get_offsets()
            if np.ndim(offsets)==2 and np.shape(offsets)[1]==2:collect(offsets[:,1])
    return (low,high) if count else None


def _restore(axis):
    previous=getattr(axis,'_signallab_stable_y',None)
    if previous is not None and axis.get_autoscaley_on() and tuple(axis.get_ylim())==previous:
        axis.autoscale_view(scalex=False,scaley=True)
    axis._signallab_stable_y=None


def apply_stable_scale(figure):
    """Return protected axes; never modify artists or explicit/manual limits."""
    ranges={axis:_range(axis) for axis in figure.axes if _eligible(axis)}
    if getattr(figure,'_signallab_detail_vertical',False):
        for axis in figure.axes:_restore(axis)
        return []
    component_reference=max([1.]+[max(abs(bounds[0]),abs(bounds[1])) for axis,bounds in ranges.items() if bounds and any(label in _text(axis) for label in ('parte real','parte imaginaria'))])
    protected=[];handled=set()
    for axis in figure.axes:
        if axis in handled:continue
        siblings=set(axis.get_shared_y_axes().get_siblings(axis));handled.update(siblings)
        # Shared y limits are a contract: inspect every linked series before
        # changing the limits, and leave groups with a special axis alone.
        if any(sibling not in ranges or not sibling.get_autoscaley_on() for sibling in siblings):
            for sibling in siblings:sibling._signallab_stable_y=None
            continue
        available=[ranges[sibling] for sibling in siblings if ranges[sibling] is not None]
        if not available:
            for sibling in siblings:_restore(sibling)
            continue
        low=min(bounds[0] for bounds in available);high=max(bounds[1] for bounds in available);peak=max(abs(low),abs(high))
        reference=max(1.,peak,component_reference if any(any(label in _text(sibling) for label in ('parte real','parte imaginaria')) for sibling in siblings) else 1.)
        threshold=SMALL_VARIATION*reference
        if peak<=threshold:
            positive=all(any(word in _text(sibling) for word in ('modulo','magnitud','densidad','energia','potencia','|h|','|x|')) and 'db' not in _text(sibling) for sibling in siblings) and low>=0
            bounds=(0.,.05*reference) if positive else (-.05*reference,.05*reference)
        elif high-low<=threshold:
            center=low/2+high/2;padding=.05*reference;bounds=(center-padding,center+padding)
        else:
            for sibling in siblings:_restore(sibling)
            continue
        if not all(math.isfinite(value) for value in bounds) or bounds[0]>=bounds[1] or bounds[0]>low or bounds[1]<high:
            for sibling in siblings:_restore(sibling)
            continue
        current=tuple(axis.get_ylim());was_protected=any(getattr(sibling,'_signallab_stable_y',None)==current for sibling in siblings)
        # Keep an existing broader view, including specification masks.
        if not was_protected and current[0]<=bounds[0] and current[1]>=bounds[1]:continue
        axis.set_ylim(*bounds,auto=None)
        for sibling in siblings:sibling._signallab_stable_y=tuple(sibling.get_ylim());protected.append(sibling)
    return protected


def set_vertical_detail(figure,enabled):
    figure._signallab_detail_vertical=bool(enabled)
    # This explicit action adjusts y only; the user's frequency/time zoom
    # and every underlying sample, coefficient and distribution stay intact.
    for axis in figure.axes:
        if _eligible(axis):
            axis._signallab_stable_y=None;axis.set_autoscaley_on(True);axis.autoscale_view(scalex=False,scaley=True)
