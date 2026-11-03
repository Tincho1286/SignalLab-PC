"""Linked A/B data cursors, with a separate readable measurement table."""
import time
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QHeaderView
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from .probe_data import collect,readings
from .theme_tokens import COLORS as C


def number(value):return 'No definido' if not np.isfinite(value) else format(value,'.10g')


class ProbeArtist(Artist):
    """An overlay, deliberately excluded from Axes.relim and trace discovery."""
    _signallab_probe=True
    def __init__(self,axis,line):
        super().__init__();self.line=line;self.set_animated(True);self.set_visible(False);self.set_in_layout(False);self.set_zorder(100)
        axis.add_artist(self);line.axes=axis;line.set_figure(axis.figure);line.set_clip_path(axis.patch)
    def draw(self,renderer):
        if self.get_visible():self.line.draw(renderer)
    def set_data(self,x,y):self.line.set_data(x,y)
    def set_xdata(self,x):self.line.set_xdata(x)


class PlotProbe:
    def __init__(self,canvas,toolbar,layout):
        self.canvas=canvas;self.toolbar=toolbar;self.traces=[];self.signature=None;self.background=None
        self.a=None;self.b=None;self.live={};self.active_axis=None;self.artists=[];self.last_motion=0.;self.enabled=True;self.exporting=False
        self.widget=QWidget();box=QVBoxLayout(self.widget);box.setContentsMargins(4,2,4,2);box.setSpacing(2)
        row=QHBoxLayout();self.hint=QLabel('Mové el mouse: lectura de puntos. Clic fija A; otro clic fija B.');self.hint.setWordWrap(True);row.addWidget(self.hint,1)
        self.pin_a=QPushButton('Fijar A');self.pin_b=QPushButton('Fijar B');self.reset=QPushButton('Seguir');self.pin_b.setEnabled(False)
        self.copy=QPushButton('Copiar');self.copy.setToolTip('Copiar las lecturas con toda la precisión disponible, como tabla.');self.copy.clicked.connect(self.copy_values)
        for button in (self.pin_a,self.pin_b,self.reset,self.copy):row.addWidget(button)
        box.addLayout(row)
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['Panel / traza','x A','y A','x B','y B','Δx (B−A)','Δy (B−A)'])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.verticalHeader().hide();self.table.setMaximumHeight(146);self.table.setMinimumHeight(58)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setToolTip('A y B leen puntos de las trazas, sin interpolar. Los valores completos están en la descripción de cada celda. Δy usa la representación dibujada; una fase principal puede saltar 2π. Seguir libera ambos cursores.');box.addWidget(self.table);layout.addWidget(self.widget)
        from PySide6.QtGui import QAction
        self.action=QAction('Cursores',toolbar);self.action.setCheckable(True);self.action.setChecked(True);self.action.setToolTip('Leer puntos y medir diferencias con cursores A/B. Clic fija A; otro clic o Mayús+clic fija B. Esc libera los cursores.');toolbar.addAction(self.action)
        self.action.toggled.connect(self.toggle);self.pin_a.clicked.connect(lambda:self.pin('a'));self.pin_b.clicked.connect(lambda:self.pin('b'));self.reset.clicked.connect(self.clear)
        for event,handler in [('draw_event',self.drawn),('motion_notify_event',self.motion),('button_press_event',self.press),('key_press_event',self.key)]:canvas.mpl_connect(event,handler)
        canvas._signallab_probe=self

    def copy_values(self):
        from PySide6.QtWidgets import QApplication
        headers=[self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
        rows=['\t'.join(headers)]
        for r in range(self.table.rowCount()):rows.append('\t'.join(self.table.item(r,c).toolTip() if self.table.item(r,c).text()!='—' else '' for c in range(self.table.columnCount())))
        QApplication.clipboard().setText('\n'.join(rows))

    def toggle(self,enabled):
        self.enabled=enabled;self.widget.setVisible(enabled)
        if not enabled:
            for artist in self.artists:artist.set_visible(False)
        self.paint()

    def clear(self):
        self.a=None;self.b=None;self.pin_b.setEnabled(False);self.update()

    def pin(self,which):
        if not self.live:return
        if which=='a':self.a=dict(self.live);self.b=None;self.pin_b.setEnabled(True)
        elif self.a is not None:
            if self.a.keys()&self.live.keys():self.b=dict(self.live)
            else:self.a=dict(self.live);self.b=None
        self.update()

    def key(self,event):
        if event.key=='escape':self.clear()

    def press(self,event):
        if not self.enabled or event.inaxes is None or event.button!=1 or self.toolbar.mode or getattr(self.canvas,'_signallab_editable',False):return
        self.motion(event,force=True)
        if self.a is None:self.pin('a')
        elif self.b is None or event.key=='shift':self.pin('b')
        else:self.pin('a')

    def motion(self,event,force=False):
        if not self.enabled or self.toolbar.mode or event.inaxes is None or event.xdata is None or event.ydata is None:return
        now=time.monotonic()
        if not force and now-self.last_motion<.025:return
        self.last_motion=now;self.active_axis=event.inaxes
        self.live=readings(self.traces,event.inaxes,event.xdata,event.ydata)
        if not self.live:
            self.table.setRowCount(0);text=event.inaxes.format_coord(event.xdata,event.ydata)
            for image in event.inaxes.images:
                value=image.get_cursor_data(event)
                if value is not None:text+=' · Valor de celda: '+image.format_cursor_data(value)
            self.hint.setText(text);return
        if self.b is None:self.update()

    def drawn(self,event):
        if self.exporting:return
        traces=collect(self.canvas.figure)
        signature=tuple((t.key,id(t.artist.get_xdata()) if hasattr(t.artist,'get_xdata') else id(t.artist.get_offsets()),id(t.artist.get_ydata()) if hasattr(t.artist,'get_ydata') else 0) for t in traces)
        if signature!=self.signature:
            for artist in self.artists:
                try:artist.remove()
                except (ValueError,NotImplementedError):pass
            self.signature=signature;self.traces=traces;self.artists=[];self.guides={};self.markers={};self.a=None;self.b=None;self.live={};self.table.setRowCount(0);self.pin_b.setEnabled(False)
            for trace in traces:
                if trace.axis not in self.guides:
                    self.guides[trace.axis]=[self.artist(trace.axis,[0,0],[0,1],color,transform=trace.axis.get_xaxis_transform(),linestyle='--',linewidth=.85) for color in (C['blue'],C['amber'])]
                self.markers[trace.key]=[self.artist(trace.axis,[],[],color,linestyle='none',marker='o',markersize=6,markerfacecolor=C['panel'],markeredgewidth=1.5) for color in (C['blue'],C['amber'])]
        only_3d=bool(self.canvas.figure.axes) and all(axis.name=='3d' for axis in self.canvas.figure.axes)
        self.action.setVisible(not only_3d);self.widget.setVisible(self.enabled and not only_3d);self.table.setVisible(bool(traces))
        try:self.background=self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        except (AttributeError,RuntimeError):self.background=None
        self.paint()

    def artist(self,axis,x,y,color,**kwargs):
        kwargs.setdefault('transform',axis.transData)
        line=Line2D(x,y,color=color,**kwargs);artist=ProbeArtist(axis,line);self.artists.append(artist);return artist

    def update(self):
        a=self.a if self.a is not None else self.live;b=self.b if self.b is not None else self.live if self.a is not None else {}
        keys=[trace.key for trace in self.traces if trace.key in a or trace.key in b]
        self.table.setRowCount(len(keys));lookup={t.key:t for t in self.traces}
        for row,key in enumerate(keys):
            trace=lookup[key];first=a.get(key);second=b.get(key)
            name=(trace.axis.get_ylabel()+' · ' if trace.axis.get_ylabel() and trace.axis.get_ylabel()!=trace.label else '')+trace.label
            values=[name,*(list(first) if first else [None,None]),*(list(second) if second else [None,None]),second[0]-first[0] if first and second else None,second[1]-first[1] if first and second else None]
            for column,value in enumerate(values):
                text=value if column==0 else '—' if value is None else number(value)
                item=QTableWidgetItem(text);item.setToolTip(str(value) if column==0 else 'Sin punto compatible' if value is None else format(value,'.17g'));self.table.setItem(row,column,item)
        self.hint.setText('A sigue al mouse · clic para fijarlo.' if self.a is None else 'A fijo · B sigue al mouse · clic para fijar B.' if self.b is None else 'A y B fijos · Seguir libera los cursores; clic empieza otro intervalo.')
        if self.active_axis is not None:
            label=self.active_axis.get_xlabel() or next((axis.get_xlabel() for axis in self.active_axis.get_shared_x_axes().get_siblings(self.active_axis) if axis.get_xlabel()),'')
            if label:self.hint.setText(self.hint.text()+' Eje: '+label+'.')
        self.paint()

    def paint(self):
        if self.exporting:return
        for artist in self.artists:artist.set_visible(False)
        if self.enabled:
            groups=(self.a if self.a is not None else self.live,self.b if self.b is not None else self.live if self.a is not None else {})
            for slot,points in enumerate(groups):
                guided=set()
                for trace in self.traces:
                    point=points.get(trace.key)
                    if point is None:continue
                    x,y=point
                    if trace.axis not in guided:
                        guide=self.guides[trace.axis][slot];guide.set_xdata([x,x]);guide.set_visible(True);guided.add(trace.axis)
                    marker=self.markers[trace.key][slot];marker.set_data([x],[y]);marker.set_visible(bool(np.isfinite(y)))
        if self.background is None:return
        try:
            self.canvas.restore_region(self.background)
            for artist in self.artists:
                if artist.get_visible():artist.axes.draw_artist(artist)
            self.canvas.blit(self.canvas.figure.bbox)
        except (RuntimeError,AttributeError):self.background=None

    def before_export(self):
        self.exporting=True
        state=[artist.get_visible() for artist in self.artists]
        for artist in self.artists:artist.set_visible(False)
        return state

    def after_export(self,state):
        self.exporting=False
        for artist,visible in zip(self.artists,state):artist.set_visible(visible)
        self.background=None;self.canvas.draw_idle()
