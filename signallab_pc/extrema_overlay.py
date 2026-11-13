"""Measurement markers excluded from trace discovery and data limits."""
import numpy as np
from matplotlib.lines import Line2D
from .theme_tokens import COLORS as C


class ExtremaOverlay:
    def __init__(self,canvas):self.canvas=canvas;self.artists=[]
    def clear(self,redraw=True):
        for artist in self.artists:
            try:artist.remove()
            except (ValueError,NotImplementedError):pass
        self.artists=[]
        if redraw:self.canvas.draw_idle()
    def show(self,trace,rows,selected=None):
        self.clear(False);axis=trace.axis;base=getattr(axis,'_signallab_index_origin',0)
        for kind,marker,color in (('Máximo','v',C['green']),('Mínimo','^',C['blue'])):
            subset=[row for row in rows if row['kind'].startswith(kind) or 'constante' in row['kind']]
            if not subset:continue
            # Large tables remain inspectable without thousands of overlay
            # objects. One line per marker kind contains all representative points.
            self.add(axis,[row['x']-base for row in subset],[row['y'] for row in subset],marker=marker,color=color,markersize=7)
        if selected is not None:
            self.add(axis,[selected['x']-base],[selected['y']],marker='o',markerfacecolor='none',markeredgecolor=C['amber'],markeredgewidth=2,markersize=12)
        self.canvas.draw_idle()
    def add(self,axis,x,y,**style):
        from .plot_probe import ProbeArtist
        line=Line2D(x,y,linestyle='none',transform=axis.transData,**style);artist=ProbeArtist(axis,line)
        artist.set_animated(False);artist.set_visible(True);self.artists.append(artist)
