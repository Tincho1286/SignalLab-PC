"""Linked A/B data cursors, with a separate readable measurement table."""
import time
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QToolButton,QTableWidget,QTableWidgetItem,QHeaderView,QSizePolicy
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from .probe_data import collect,readings
from .signal_plot import vertical_axis_name
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
        self.a=None;self.b=None;self.live={};self.active_axis=None;self.artists=[];self.last_motion=0.;self.enabled=True;self.exporting=False;self._dragging=None;self.inspector=None;self.readings_dock=None
        self.widget=QWidget();self.widget.setObjectName('cursorPanel');box=QVBoxLayout(self.widget);box.setContentsMargins(8,4,8,6);box.setSpacing(4)
        from .figure_controls import WrappedControls
        strip=QWidget();policy=QSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Minimum);policy.setHeightForWidth(True);strip.setSizePolicy(policy);row=WrappedControls(strip);row.setContentsMargins(0,0,0,0)
        self.hint=QLabel();self.hint.setObjectName('cursorReadout');self.hint.setAccessibleName('Coordenadas del cursor');self.hint.setTextFormat(Qt.TextFormat.PlainText)
        self.hint.setToolTip('Mové el mouse para leer un punto. En un gráfico de análisis, un clic fija A y otro fija B. En un editor, usá los botones Fijar A/B.')
        self.hint.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        box.addWidget(self.hint)
        self.pin_a=QPushButton('Fijar A');self.pin_b=QPushButton('Fijar B');self.reset=QPushButton('Seguir');self.pin_b.setEnabled(False)
        self.table_toggle=QToolButton();self.table_toggle.setText('Tabla A/B');self.table_toggle.setCheckable(True);self.table_toggle.setToolTip('Mostrar las lecturas de todos los paneles. Se abre al fijar el primer cursor.')
        self.copy=QPushButton('Copiar');self.copy.setToolTip('Copiar las lecturas con toda la precisión disponible, como tabla.');self.copy.clicked.connect(self.copy_values)
        for button in (self.pin_a,self.pin_b,self.reset,self.table_toggle,self.copy):row.addWidget(button)
        box.addWidget(strip)
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['Panel / traza','x A','y A','x B','y B','Δx (B−A)','Δy (B−A)'])
        self.table.setObjectName('cursorTable');self.table.setAccessibleName('Mediciones de los cursores A y B');self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers);self.table.verticalHeader().hide();self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents);self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setToolTip('A y B leen puntos de las trazas, sin interpolar. Los valores completos están en la descripción de cada celda. Δy usa la representación dibujada; una fase principal puede saltar 2π. Seguir libera ambos cursores.');box.addWidget(self.table);layout.addWidget(self.widget)
        from PySide6.QtGui import QAction
        self.action=QAction('Cursores',toolbar);self.action.setCheckable(True);self.action.setChecked(True);self.action.setToolTip('Leer puntos y medir diferencias con cursores A/B. Clic fija A; otro clic o Mayús+clic fija B. Esc libera los cursores.');toolbar.addAction(self.action)
        self.inspect_action=QAction('Curvas y medidas',toolbar);self.inspect_action.setCheckable(True);self.inspect_action.setToolTip('Ver la definición de una curva, medir sus extremos y ubicar un punto.');self.inspect_action.toggled.connect(self.set_inspector_visible);toolbar.addAction(self.inspect_action)
        from .design import icon
        self.action.setIcon(icon('cursor'));self.inspect_action.setIcon(icon('measure'))
        self.action.toggled.connect(self.toggle);self.pin_a.clicked.connect(lambda:self.pin('a'));self.pin_b.clicked.connect(lambda:self.pin('b'));self.reset.clicked.connect(self.clear)
        self.table_toggle.toggled.connect(self.refresh_reading_panel);self.table_toggle.clicked.connect(self.open_readings_tab);self.refresh_reading_panel()
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

    def refresh_reading_panel(self):
        rows = self.table.rowCount()
        dock = self.readings_dock
        self.table.setVisible(bool(rows) and (dock is not None or self.table_toggle.isChecked()))
        if dock is not None:
            dock.readings_hint.setVisible(not rows)
        elif rows and self.table_toggle.isChecked():
            height = self.table.horizontalHeader().sizeHint().height()
            height += sum(self.table.rowHeight(row) for row in range(min(rows, 3)))
            # Keep a complete row visible if the numbers need a horizontal scrollbar.
            height += self.table.horizontalScrollBar().sizeHint().height() + 4
            self.table.setFixedHeight(height)
        self.pin_a.setEnabled(bool(self.live))
        self.pin_b.setEnabled(self.a is not None and bool(self.live))
        self.reset.setEnabled(self.a is not None)
        self.copy.setEnabled(bool(rows))
        if self.a is not None and self.b is not None:
            status = 'A y B fijos'
        elif self.a is not None:
            status = 'A fijo · B libre'
        else:
            status = 'Lectura libre'
        trace = next((item for item in self.traces if item.axis is self.active_axis and item.key in self.live), None)
        if trace is None:
            empty = 'Usá Fijar A/B para medir en el editor' if getattr(self.canvas,'_signallab_editable',False) else 'Mové el puntero sobre la figura'
            self.hint.setText(empty if self.a is None else status)
            return
        axis = trace.axis
        point = self.live[trace.key]
        label = axis.get_xlabel() or next((sibling.get_xlabel() for sibling in axis.get_shared_x_axes().get_siblings(axis) if sibling.get_xlabel()), 'x')
        reading = f'{status}  ·  {label} = {number(point[0])}  ·  {vertical_axis_name(axis) or "y"} = {number(point[1])}'
        if getattr(trace,'cell_values',False):
            reading += '  ·  Valor = '+number(point[2])
        self.hint.setText(reading)

    def dock_readings(self, inspector):
        if inspector is self.readings_dock:
            return
        self.readings_dock = inspector
        if inspector is None:
            self.widget.layout().addWidget(self.table)
            self.table_toggle.setToolTip('Mostrar las lecturas debajo del gráfico.')
        else:
            self.table.setMinimumHeight(0)
            self.table.setMaximumHeight(inspector.maximumHeight())
            inspector.readings_layout.addWidget(self.table, 1)
            self.table_toggle.setToolTip('Abrir las lecturas A/B en Curvas y medidas.')
        self.refresh_reading_panel()

    def open_readings_tab(self):
        if self.readings_dock is not None:
            self.readings_dock.tabs.setCurrentWidget(self.readings_dock.readings_page)
            self.table_toggle.setChecked(True)

    def open_inspector(self):
        if self.inspect_action.isChecked():
            self.set_inspector_visible(True)
        else:
            self.inspect_action.setChecked(True)

    def set_inspector_visible(self, visible):
        window = self.canvas._signallab_window
        embedded = hasattr(window, 'attach_inspector')
        if visible and self.inspector is None:
            from .plot_inspector_dialog import PlotInspector
            self.inspector = PlotInspector(self, window, embedded=embedded)
            self.inspector.dismissed.connect(lambda: self.inspect_action.setChecked(False))
            if embedded:
                window.attach_inspector(self.inspector)
        if self.inspector is None:
            return
        if embedded:
            if visible:
                window.focus_action.setChecked(False)
                if not window.isVisible():
                    from .plot_view import enlarge_plot
                    enlarge_plot(self.canvas, window)
            window.show_inspector(visible)
        else:
            self.inspector.setVisible(visible)
            if visible:
                self.inspector.raise_()
                self.inspector.activateWindow()

    def focus(self,trace,coordinate,target='live'):
        from .plot_inspection import nearest
        if trace.key not in {t.key for t in self.traces}:raise ValueError('La figura cambió. Elegí nuevamente la curva.')
        if target not in ('live','a','b'):raise ValueError('Cursor no reconocido.')
        if target=='b' and self.a is None:raise ValueError('Primero colocá el cursor A.')
        index,x,y=nearest(trace,coordinate);base=getattr(trace.axis,'_signallab_index_origin',0);position=x-base
        self.action.setChecked(True);self.active_axis=trace.axis;self.live=readings(self.traces,trace.axis,position,y)
        if target=='live':self.a=None;self.b=None;self.pin_b.setEnabled(False)
        elif target=='a':
            first_pin=self.a is None
            self.a=dict(self.live)
            if first_pin:self.table_toggle.setChecked(True)
        else:self.b=dict(self.live)
        low,high=trace.axis.get_xlim()
        if not min(low,high)<=position<=max(low,high):
            middle=low/2+high/2;bounds=(low+position-middle,high+position-middle)
            if np.isfinite(bounds).all():trace.axis.set_xlim(*bounds);self.canvas.draw_idle()
        self.update();self.canvas.draw_idle();return index,x,y

    def resized(self,event):self.background=None

    def pin(self,which):
        if not self.live:return
        if which=='a':
            first_pin=self.a is None
            self.a=dict(self.live);self.b=None
            if first_pin:self.table_toggle.setChecked(True)
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
        self.action.setVisible(not only_3d);self.widget.setVisible(self.enabled and not only_3d)
        self.table_toggle.setEnabled(bool(traces));self.refresh_reading_panel()
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
            axis_name = vertical_axis_name(trace.axis)
            name = (axis_name + ' · ' if axis_name and axis_name != trace.label else '') + trace.label
            if cell_values:
                labels=[trace.axis.get_xlabel() or 'x',axis_name or 'y']
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
        self.refresh_reading_panel()
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
