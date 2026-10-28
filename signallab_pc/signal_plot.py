"""Convención común de muestras, curvas y discontinuidades de fase."""
import numpy as np

def plot_samples(axis,x,y,*,discrete=False,label=None,color=None,phase=False):
    x=np.asarray(x);y=np.asarray(y)
    if not discrete or len(x)==0:
        if phase and len(x)>1:
            # Separar el salto de rama sin borrar ninguna muestra válida.
            cuts=np.flatnonzero(np.isfinite(y[:-1]) & np.isfinite(y[1:]) & (abs(np.diff(y))>np.pi))+1
            x=np.insert(x.astype(float),cuts,np.nan);y=np.insert(y.astype(float),cuts,np.nan)
        return axis.plot(x,y,label=label,color=color)
    color=color or axis._get_lines.get_next_color()
    result=axis.stem(x,y,linefmt=color,markerfmt='o',basefmt=' ',label=label)
    result.markerline.set_color(color);result.markerline.set_markersize(3)
    result.stemlines.set_color(color);result.stemlines.set_linewidth(.9)
    axis.axhline(0,color='#617187',linewidth=.6,zorder=0)
    return result


from fractions import Fraction
from matplotlib.ticker import MaxNLocator, ScalarFormatter, FuncFormatter, Locator

class IndexLocator(MaxNLocator):
    """Keep integer sample coordinates even when zooming below one sample."""
    def __init__(self):
        super().__init__(nbins=9,integer=True,min_n_ticks=1)
    def tick_values(self,vmin,vmax):
        return np.unique(np.rint(super().tick_values(vmin,vmax)))

class SampleMarkLocator(Locator):
    """One mark per integer while individual marks are visually distinguishable."""
    def __call__(self):
        return self.tick_values(*self.axis.get_view_interval())
    def tick_values(self,vmin,vmax):
        low,high=sorted((vmin,vmax));first=int(np.ceil(low));last=int(np.floor(high))
        # Drawing millions of coincident ticks is neither readable nor useful.
        # This affects display only; zoom restores every individual index.
        capacity=max(32,int(self.axis.axes.bbox.width*2)) if self.axis is not None else 1000
        step=max(1,int(np.ceil((last-first+1)/capacity)))
        first=((first+step-1)//step)*step
        return np.arange(first,last+1,step,dtype=float)


def _sample_coordinate(axis,symbol):
    from matplotlib.container import StemContainer
    def describe(x,y):
        if x is None or not np.isfinite(x):return ''
        index=int(np.floor(x+.5));parts=[]
        for container in axis.containers:
            if not isinstance(container,StemContainer):continue
            coordinates=np.asarray(container.markerline.get_xdata())
            values=np.asarray(container.markerline.get_ydata())
            hit=np.flatnonzero(coordinates==index)
            if hit.size:
                label=container.get_label()
                if not label or label.startswith('_'):label=axis.get_ylabel() or 'valor'
                value=values[hit[0]]
                parts.append(f'{label} = {value:.7g}' if np.isfinite(value) else f'{label}: no definido')
        return f'{symbol} = {index}'+(' · '+'; '.join(parts) if parts else ' · sin muestra dibujada en este índice')
    return describe


class AngularLocator(MaxNLocator):
    """Adaptive angular ticks in radians, expressed as multiples of pi."""
    def __init__(self):
        super().__init__(nbins=7, steps=[1, 2, 2.5, 5, 10])
    def tick_values(self, vmin, vmax):
        return super().tick_values(vmin/np.pi, vmax/np.pi)*np.pi

def _pi_label(value, position=None):
    ratio=value/np.pi
    if abs(ratio)<1e-12:return '0'
    fraction=Fraction(float(ratio)).limit_denominator(64)
    if abs(float(fraction)-ratio)>1e-9:return f'{ratio:.5g}π'
    n,d=fraction.numerator,fraction.denominator
    prefix='−' if n<0 else ''
    numerator=('' if abs(n)==1 else str(abs(n)))+'π'
    return prefix+numerator+('' if d==1 else '/'+str(d))

def configure_axis(axis, *, discrete_index=False, units='', label=None, index_symbol='n'):
    """Choose ticks by coordinate meaning, never by whether a curve uses stems."""
    if axis.get_xscale()=='linear':
        if discrete_index:
            axis.xaxis.set_major_locator(IndexLocator())
            axis.xaxis.set_minor_locator(SampleMarkLocator())
            axis.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
        elif units=='rad/muestra':
            axis.xaxis.set_major_locator(AngularLocator())
            axis.xaxis.set_major_formatter(FuncFormatter(_pi_label))
        else:
            axis.xaxis.set_major_locator(MaxNLocator(nbins=8))
            axis.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    if discrete_index:
        for sibling in axis.get_shared_x_axes().get_siblings(axis):
            sibling.tick_params(axis='x',which='minor',bottom=True,length=3,width=.7)
            sibling.tick_params(axis='x',which='major',bottom=True,length=5)
            sibling.format_coord=_sample_coordinate(sibling,index_symbol)
    axis.tick_params(axis='both',labelsize=9)
    if label is not None:axis.set_xlabel(label)

def configure_signal_axis(axis, source):
    units=source.units;discrete=source.domain=='discrete'
    operation=source.metadata.get('operation','')
    if discrete:
        label='Coeficiente k (entero)' if units in ('k','bin k') or operation=='DFT' else 'Índice n (muestras)'
        if 'correlation' in operation:label='Retardo k (muestras)'
    elif source.domain=='continuous':
        label='Retardo τ (s)' if 'correlation' in operation else 'Tiempo t (s)'
    elif units=='rad/muestra':label='Frecuencia angular ω (rad/muestra)'
    elif units=='rad/s':label='Frecuencia angular Ω (rad/s)'
    else:label=units
    configure_axis(axis,discrete_index=discrete,units=units,label=label,
                   index_symbol='k' if units in ('k','bin k') or 'correlation' in operation else 'n')


def is_discrete_plot(source):
    return (source.domain=='discrete' or bool(source.metadata.get('discrete_spectrum'))
            or source.metadata.get('operation') in {'DFT','discrete_fourier_series','continuous_fourier_series','stft'})


def validate_overlay(signals):
    """Overlay coordinates only when their domains and units have the same meaning."""
    if not signals:return
    reference=signals[0]
    if any(source.domain!=reference.domain or source.units!=reference.units for source in signals[1:]):
        raise ValueError('Para superponer señales, sus ejes deben tener el mismo dominio y unidades. Convertí primero los datos: no se mezclan índices, segundos, Hz o radianes en un mismo eje.')


def configure_frequency_overlay(axes,signals):
    validate_overlay(signals)
    if not signals or any(source.domain!='frequency' for source in signals):
        raise ValueError('La comparación requiere espectros sobre un eje de frecuencia común.')
    # Use complete source axes, not a decimated display or the phase's valid subset.
    edges=[edge for source in signals for edge in (source.origin,source.origin+source.step*(source.values.size-1))]
    low,high=min(edges),max(edges)
    if low==high:
        width=abs(signals[0].step);low-=width/2;high+=width/2
    for axis in axes:
        configure_signal_axis(axis,signals[0]);axis.set_xlim(low,high)
