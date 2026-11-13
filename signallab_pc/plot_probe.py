"""Linked A/B data cursors, with a separate readable measurement table."""
import time
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QHeaderView
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from .probe_data import collect,readings
from .theme_tokens import COLORS as C


def number(value):
    if isinstance(value,(int,np.integer)):return str(value)
    return 'No definido' if not np.isfinite(value) else format(value,'.10g')


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
        self.a=None;self.b=None;self.live={};self.active_axis=None;self.artists=[];self.last_motion=0.;self.enabled=True;self.exporting=False;self._dragging=None;self.inspector=None
        self.widget=QWidget();box=QVBoxLayout(self.widget);box.setContentsMargins(4,2,4,2);box.setSpacing(2)
        row=QHBoxLayout();self.hint=QLabel('Editor de diseño: los clics editan; usá Fijar A/B para medir.' if getattr(canvas,'_signallab_editable',False) else 'Mové el mouse: lectura de puntos. Clic fija A; otro clic fija B.');self.hint.setWordWrap(True);row.addWidget(self.hint,1)
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
        self.inspect_action=QAction('Curvas y medidas…',toolbar);self.inspect_action.setToolTip('Ver la definición almacenada, buscar máximos/mínimos y colocar cursores por coordenada.');self.inspect_action.triggered.connect(self.open_inspector);toolbar.addAction(self.inspect_action)
        self.action.toggled.connect(self.toggle);self.pin_a.clicked.connect(lambda:self.pin('a'));self.pin_b.clicked.connect(lambda:self.pin('b'));self.reset.clicked.connect(self.clear)
        for event,handler in [('draw_event',self.drawn),('resize_event',self.resized),('motion_notify_event',self.motion),('button_press_event',self.press),('button_release_event',self.release),('key_press_event',self.key)]:canvas.mpl_connect(event,handler)
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
        self.release(None);self.a=None;self.b=None;self.pin_b.setEnabled(False);self.update()

    def open_inspector(self):
        if self.inspector is None:
            from .plot_inspector_dialog import PlotInspector
            self.inspector=PlotInspector(self)
        self.inspector.show();self.inspector.raise_();self.inspector.activateWindow()

    def focus(self,trace,coordinate,target='live'):
        from .plot_inspection import nearest
        if trace.key not in {t.key for t in self.traces}:raise ValueError('La figura cambió. Elegí nuevamente la curva.')
        if target not in ('live','a','b'):raise ValueError('Cursor no reconocido.')
        if target=='b' and self.a is None:raise ValueError('Primero colocá el cursor A.')
        index,x,y=nearest(trace,coordinate);base=getattr(trace.axis,'_signallab_index_origin',0);position=x-base
        self.action.setChecked(True);self.active_axis=trace.axis;self.live=readings(self.traces,trace.axis,position,y)
        if target=='live':self.a=None;self.b=None;self.pin_b.setEnabled(False)
        elif target=='a':self.a=dict(self.live);self.pin_b.setEnabled(True)
        else:self.b=dict(self.live)
        low,high=trace.axis.get_xlim()
        if not min(low,high)<=position<=max(low,high):
            middle=low/2+high/2;bounds=(low+position-middle,high+position-middle)
            if np.isfinite(bounds).all():trace.axis.set_xlim(*bounds);self.canvas.draw_idle()
        self.update();self.canvas.draw_idle();return index,x,y

    def resized(self,event):self.background=None

    def pin(self,which):
        if not self.live:return
        if which=='a':self.a=dict(self.live);self.b=None;self.pin_b.setEnabled(True)
        elif self.a is not None:
            if self.a.keys()&self.live.keys():self.b=dict(self.live)
            else:self.a=dict(self.live);self.b=None
        self.update()

    def key(self,event):
        if event.key=='escape':self.clear()
        elif self.enabled and event.key in ('left','right') and not self.toolbar.mode:
            for target,points in (('b',self.b),('a',self.a),('live',self.live)):
                trace=next((t for t in self.traces if t.axis is self.active_axis and not getattr(t,'spatial',True) and points is not None and t.key in points),None)
                if trace is not None:
                    from .plot_inspection import adjacent
                    try:self.focus(trace,adjacent(trace,points[trace.key][0],-1 if event.key=='left' else 1),target)
                    except ValueError:pass
                    break

    def press(self,event):
        if not self.enabled or event.inaxes is None or event.button!=1 or self.toolbar.mode or getattr(self.canvas,'_signallab_editable',False):return
        hits=[]
        for target,points in (('a',self.a),('b',self.b)):
            for trace in self.traces:
                if points is None or trace.axis is not event.inaxes or trace.key not in points:continue
                x,y=points[trace.key][:2];pixel=trace.axis.transData.transform((x-getattr(trace.axis,'_signallab_index_origin',0),y));distance=abs(pixel[0]-event.x)
                if distance<=7:hits.append((distance+min(abs(pixel[1]-event.y),100)/1000,target))
        if hits:
            self._dragging=min(hits)[1];self.canvas.setCursor(Qt.CursorShape.SizeHorCursor);return
        self.motion(event,force=True)
        if self.a is None:self.pin('a')
        elif self.b is None or event.key=='shift':self.pin('b')
        else:self.pin('a')

    def release(self,event):
        if self._dragging is not None:self.canvas.unsetCursor()
        self._dragging=None

    def motion(self,event,force=False):
        if not self.enabled or self.toolbar.mode or event.inaxes is None or event.xdata is None or event.ydata is None:return
        now=time.monotonic()
        if not force and now-self.last_motion<.025:return
        self.last_motion=now;self.active_axis=event.inaxes
        self.live=readings(self.traces,event.inaxes,event.xdata,event.ydata)
        if not self.live:
            self.update();text=event.inaxes.format_coord(event.xdata,event.ydata)
            for image in event.inaxes.images:
                value=image.get_cursor_data(event)
                if value is not None:text+=' · Valor de celda: '+image.format_cursor_data(value)
            self.hint.setText(text);return
        if self._dragging is not None:
            if getattr(event,'button',None)!=1:self.release(event)
            elif self._dragging=='a':self.a=dict(self.live)
            else:self.b=dict(self.live)
            self.update()
        elif self.b is None:self.update()

    def drawn(self,event):
        if self.exporting:return
        traces=collect(self.canvas.figure)
        def revision(trace):
            if getattr(trace,'cell_values',False):return trace.revision
            curve=getattr(trace.artist,'_signallab_probe_curve',None)
            if curve is not None:return tuple(id(v) for v in curve)
            return (id(trace.artist.get_xdata()) if hasattr(trace.artist,'get_xdata') else id(trace.artist.get_offsets()) if hasattr(trace.artist,'get_offsets') else id(trace.axis),id(trace.artist.get_ydata()) if hasattr(trace.artist,'get_ydata') else 0)
        signature=tuple((trace.key,revision(trace)) for trace in traces)
        if signature!=self.signature:
            self.release(None)
            for artist in self.artists:
                try:artist.remove()
                except (ValueError,NotImplementedError):pass
            self.signature=signature;self.traces=traces;self.artists=[];self.guides={};self.markers={};self.a=None;self.b=None;self.live={};self.table.setRowCount(0);self.pin_b.setEnabled(False)
            for trace in traces:
                if trace.axis not in self.guides:
                    self.guides[trace.axis]=[self.artist(trace.axis,[0,0],[0,1],color,transform=trace.axis.get_xaxis_transform(),linestyle='--',linewidth=.85) for color in (C['blue'],C['amber'])]
                self.markers[trace.key]=[self.artist(trace.axis,[],[],color,linestyle='none',marker='o',markersize=6,markerfacecolor=C['panel'],markeredgewidth=1.5) for color in (C['blue'],C['amber'])]
        only_3d=bool(self.canvas.figure.axes) and all(axis.name=='3d' for axis in self.canvas.figure.axes)
        self.inspect_action.setEnabled(bool(traces) and not only_3d)
        self.action.setVisible(not only_3d);self.widget.setVisible(self.enabled and not only_3d);self.table.setVisible(bool(traces))
        try:self.background=self.canvas.copy_from_bbox(self.canvas.figure.bbox)
        except (AttributeError,RuntimeError):self.background=None
        # The backend is already painting this draw event. Draw overlays into
        # its renderer without calling QWidget.repaint recursively via blit.
        self.paint(blit=False)

    def artist(self,axis,x,y,color,**kwargs):
        kwargs.setdefault('transform',axis.transData)
        line=Line2D(x,y,color=color,**kwargs);artist=ProbeArtist(axis,line);self.artists.append(artist);return artist

    def update(self):
        a=self.a if self.a is not None else self.live;b=self.b if self.b is not None else self.live if self.a is not None else {}
        keys=[trace.key for trace in self.traces if trace.key in a or trace.key in b]
        cell_values=any(getattr(trace,'cell_values',False) for trace in self.traces)
        self.table.setColumnCount(4 if cell_values else 7)
        self.table.setHorizontalHeaderLabels(['Traza / medida','A','B','B−A'] if cell_values else ['Panel / traza','x A','y A','x B','y B','Δx (B−A)','Δy (B−A)'])
        header=self.table.horizontalHeader();header.setStretchLastSection(not cell_values)
        header.setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch if cell_values else QHeaderView.ResizeMode.ResizeToContents)
        lookup={t.key:t for t in self.traces};rows=[]
        for key in keys:
            trace=lookup[key];first=a.get(key);second=b.get(key)
            name=(trace.axis.get_ylabel()+' · ' if trace.axis.get_ylabel() and trace.axis.get_ylabel()!=trace.label else '')+trace.label
            if cell_values:
                labels=[trace.axis.get_xlabel() or 'x',trace.axis.get_ylabel() or 'y']
                if getattr(trace,'cell_values',False):labels.append('Valor · '+trace.label)
                for component,label in enumerate(labels):
                    va=first[component] if first else None;vb=second[component] if second else None
                    rows.append([trace.label+' · '+label if component<2 else label,va,vb,vb-va if va is not None and vb is not None else None])
            else:
                rows.append([name,*(list(first[:2]) if first else [None,None]),*(list(second[:2]) if second else [None,None]),second[0]-first[0] if first and second else None,second[1]-first[1] if first and second else None])
        self.table.setRowCount(len(rows))
        for row,values in enumerate(rows):
            for column,value in enumerate(values):
                text=value if column==0 else '—' if value is None else number(value)
                item=QTableWidgetItem(text);item.setToolTip(str(value) if column==0 else 'Sin punto compatible' if value is None else str(value) if isinstance(value,(int,np.integer)) else format(value,'.17g'));self.table.setItem(row,column,item)
        self.hint.setText('A sigue al mouse · clic para fijarlo.' if self.a is None else 'A fijo · B sigue al mouse · clic para fijar B.' if self.b is None else 'A y B fijos · Seguir libera los cursores; clic empieza otro intervalo.')
        if self.a is not None and not getattr(self.canvas,'_signallab_editable',False):self.hint.setText(self.hint.text()+' Arrastrá A/B para moverlos; las flechas recorren puntos.')
        if self.active_axis is not None:
            label=self.active_axis.get_xlabel() or next((axis.get_xlabel() for axis in self.active_axis.get_shared_x_axes().get_siblings(self.active_axis) if axis.get_xlabel()),'')
            if label:self.hint.setText(self.hint.text()+' Eje: '+label+'.')
            if any(getattr(trace,'cell_values',False) and trace.axis is self.active_axis for trace in self.traces):
                self.hint.setText(self.hint.text()+' Y: '+self.active_axis.get_ylabel()+'. Valor de la celda original, sin interpolar.')
        if getattr(self.canvas,'_signallab_editable',False):self.hint.setText('Editor de diseño: los clics cambian polos/ceros. Usá Fijar A/B y Seguir para medir sin editar.')
        self.paint()

    def paint(self,blit=True):
        if self.exporting:return
        for artist in self.artists:artist.set_visible(False)
        if self.enabled:
            groups=(self.a if self.a is not None else self.live,self.b if self.b is not None else self.live if self.a is not None else {})
            for slot,points in enumerate(groups):
                guided=set()
                for trace in self.traces:
                    point=points.get(trace.key)
                    if point is None:continue
                    x,y=point[:2]
                    x-=getattr(trace.axis,'_signallab_index_origin',0)
                    if trace.axis not in guided:
                        guide=self.guides[trace.axis][slot];guide.set_xdata([x,x]);guide.set_visible(True);guided.add(trace.axis)
                    marker=self.markers[trace.key][slot];marker.set_data([x],[y]);is_live=self.a is None if slot==0 else self.b is None
                    marker.set_visible(bool(np.isfinite(y)) and not (is_live and getattr(self.canvas,'_signallab_editable',False)))
        if self.background is None:return
        try:
            self.canvas.restore_region(self.background)
            for artist in self.artists:
                if artist.get_visible():artist.axes.draw_artist(artist)
            if blit:self.canvas.blit(self.canvas.figure.bbox)
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
