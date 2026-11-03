"""Edición directa del plano de polos y ceros sobre el lienzo existente."""
import numpy as np
from .pole_zero_marks import draw_root_markers
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QComboBox,QCheckBox,QLabel,QPushButton
from .systems_panel import parse_list,list_text

class PoleZeroEditor(QWidget):
    def __init__(self,panel,context):
        super().__init__();self.panel=panel;self.context=context;self.drag=None;self._cursor_cache={};self._inside=False
        panel.canvas._signallab_editable=True;panel.canvas._signallab_root_editor=self
        from matplotlib.backend_tools import Cursors
        original_cursor=panel.canvas.set_cursor
        def backend_cursor(shape):
            original_cursor(shape)
            if shape==Cursors.POINTER and self._inside:self.refresh_cursor()
        panel.canvas.set_cursor=backend_cursor
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);row=QHBoxLayout()
        self.mode=QComboBox();self.mode.addItems(['Agregar polo ×','Agregar cero ○','Mover punto','Quitar punto']);row.addWidget(self.mode)
        self.coordinates=QComboBox();self.coordinates.addItems(['Binómica · real / imaginaria','Polar · módulo / ángulo (rad)']);box.addWidget(self.coordinates);self.coordinates.currentIndexChanged.connect(lambda *_:self.redraw(preserve=False))
        self.pairs=QCheckBox('Pares conjugados');self.pairs.setChecked(True);row.addWidget(self.pairs);box.addLayout(row)
        self.note=QLabel('Hacé clic en el plano para agregar un polo. El diseño se actualiza al terminar cada edición.');self.note.setWordWrap(True);box.addWidget(self.note)
        self.connections=[panel.canvas.mpl_connect('button_press_event',self.press),panel.canvas.mpl_connect('motion_notify_event',self.move),panel.canvas.mpl_connect('button_release_event',self.release),panel.canvas.mpl_connect('scroll_event',self.scroll)]
        for key in ('zeros','poles','gain'):
            panel.fields[key].textChanged.connect(self.dirty)
            panel.fields[key].editingFinished.connect(self.manual)
        panel.domain.currentIndexChanged.connect(self.manual)
        self.mode.currentIndexChanged.connect(self.choose_mode);self.mode.activated.connect(self.choose_mode)
        self.connections.extend([panel.canvas.mpl_connect(name,self.cursor_event) for name in ('axes_enter_event','axes_leave_event','figure_leave_event')])
        self.redraw()
        window=getattr(panel.canvas,'_signallab_window',None)
        if window is not None:self.install_plot_controls(window,window.layout())
    def install_plot_controls(self,window,layout):
        if hasattr(self,'plot_controls'):return
        self.plot_controls=QWidget(window);box=QVBoxLayout(self.plot_controls);box.setContentsMargins(4,0,4,2);box.setSpacing(3)
        row=QHBoxLayout();mode=QComboBox();mode.addItems([self.mode.itemText(i) for i in range(self.mode.count())]);mode.setCurrentIndex(self.mode.currentIndex());mode.setAccessibleName('Acción del mouse en el plano');row.addWidget(mode,1)
        mode.currentIndexChanged.connect(self.mode.setCurrentIndex);self.mode.currentIndexChanged.connect(mode.setCurrentIndex);mode.activated.connect(self.choose_mode)
        pairs=QCheckBox('Conjugados');pairs.setChecked(self.pairs.isChecked());pairs.toggled.connect(self.pairs.setChecked);self.pairs.toggled.connect(pairs.setChecked);row.addWidget(pairs);box.addLayout(row)
        row=QHBoxLayout();coordinates=QComboBox();coordinates.addItems(['Plano binómico','Plano polar']);coordinates.setCurrentIndex(self.coordinates.currentIndex());row.addWidget(coordinates)
        coordinates.currentIndexChanged.connect(self.coordinates.setCurrentIndex);self.coordinates.currentIndexChanged.connect(coordinates.setCurrentIndex)
        for text,factor in [('Acercar +',.8),('Alejar −',1.25)]:
            button=QPushButton(text);button.setProperty('calculationInput',False);button.clicked.connect(lambda checked=False,scale=factor:self.zoom(scale));row.addWidget(button)
        fit=QPushButton('Ajustar a raíces');fit.clicked.connect(lambda:self.redraw(preserve=False));row.addWidget(fit);row.addStretch();box.addLayout(row)
        hint=QLabel('Rueda: zoom en la posición del mouse. Alejar amplía el plano para insertar raíces fuera de la vista actual.');hint.setWordWrap(True);hint.setObjectName('muted');box.addWidget(hint)
        layout.insertWidget(1,self.plot_controls)
    def choose_mode(self,*_):
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        if toolbar and toolbar.mode:
            if str(toolbar.mode)=='pan/zoom':toolbar.pan()
            else:toolbar.zoom()
        self.refresh_cursor()
    def scroll(self,event):
        if self.busy() or event.inaxes is None or event.xdata is None or event.ydata is None:return
        step=getattr(event,'step',0)
        if step:self.zoom(.8 if step>0 else 1.25,event)
    def zoom(self,factor,event=None):
        if not self.panel.figure.axes:return
        axis=self.panel.figure.axes[0];toolbar=getattr(self.panel.canvas,'toolbar',None)
        if toolbar:toolbar.push_current()
        if axis.name=='polar':
            high=axis.get_ylim()[1]*factor
            if not np.isfinite(high) or high<=0:return
            axis.set_ylim(0,high)
        else:
            x,y=axis.get_xlim(),axis.get_ylim();cx=event.xdata if event else (x[0]+x[1])/2;cy=event.ydata if event else (y[0]+y[1])/2
            limits=[cx+(x[0]-cx)*factor,cx+(x[1]-cx)*factor,cy+(y[0]-cy)*factor,cy+(y[1]-cy)*factor]
            if not np.isfinite(limits).all() or limits[0]>=limits[1] or limits[2]>=limits[3]:return
            axis.set_xlim(limits[:2]);axis.set_ylim(limits[2:])
        if toolbar:toolbar.push_current()
        self.panel.canvas.draw_idle()
    def refresh_cursor(self,*_):
        from .editor_pointer import insertion_cursor
        from PySide6.QtCore import Qt
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        if toolbar and toolbar.mode:return
        if self.busy():self.panel.canvas.setCursor(Qt.CursorShape.BusyCursor);return
        mode=self.mode.currentIndex()
        if not self._inside:self.panel.canvas.unsetCursor()
        elif mode<2:
            from .theme_tokens import COLORS as C
            key=(mode,float(self.panel.canvas.devicePixelRatioF()),C['red'],C['blue'],C['window'])
            if key not in self._cursor_cache:self._cursor_cache[key]=insertion_cursor(self.panel.canvas,'pole' if mode==0 else 'zero')
            self.panel.canvas.setCursor(self._cursor_cache[key])
        else:self.panel.canvas.setCursor(Qt.CursorShape.OpenHandCursor if mode==2 else Qt.CursorShape.CrossCursor)
        messages=['Hacé clic para agregar un polo en la posición del cursor ×.','Hacé clic para agregar un cero en la posición del cursor ○.','Arrastrá un polo o cero existente para moverlo.','Hacé clic cerca de un polo o cero para quitarlo.']
        self.note.setText(messages[mode])
    def cursor_event(self,event):
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        if toolbar and toolbar.mode:return
        if event.name in ('axes_leave_event','figure_leave_event') or event.inaxes is None:
            self._inside=False;self.panel.canvas.unsetCursor();return
        self._inside=True;self.refresh_cursor()
    def dirty(self,*_):
        callback=getattr(self.context,'on_design_dirty',None)
        if callback:callback()
    def data(self):return [list(parse_list(self.panel.fields[key].text(),True)) for key in ('zeros','poles')]
    def write(self,data):
        from .coefficient_editor import split_coefficients
        for key,values in zip(('zeros','poles'),data):
            # Keep exact source text for every root the mouse did not change.
            old=split_coefficients(self.panel.fields[key].text());used=set();output=[]
            try:numbers=list(parse_list(self.panel.fields[key].text(),True))
            except ValueError:numbers=[]
            for value in values:
                index=next((i for i,previous in enumerate(numbers) if i not in used and previous==value),None)
                if index is None:output.append(list_text([value]))
                else:used.add(index);output.append(old[index])
            self.panel.fields[key].setText(', '.join(output))
    def busy(self):return bool(self.context.window._workers)
    def active(self,event):
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        return event.inaxes is not None and event.xdata is not None and event.ydata is not None and not (toolbar and toolbar.mode) and not self.busy()
    def point(self,event):
        value=event.ydata*np.exp(1j*event.xdata) if self.coordinates.currentIndex()==1 else complex(event.xdata,event.ydata)
        if self.coordinates.currentIndex()==1 and event.xdata%np.pi==0:value=complex(value.real,0)
        return value
    def nearest(self,event,data):
        choices=[]
        for kind,values in enumerate(data):
            for index,value in enumerate(values):
                pixel=event.inaxes.transData.transform((np.angle(value)%(2*np.pi),abs(value)) if self.coordinates.currentIndex()==1 else (value.real,value.imag));distance=np.hypot(pixel[0]-event.x,pixel[1]-event.y)
                if distance<14:choices.append((distance,kind,index))
        return min(choices)[1:] if choices else None
    def partner(self,values,index):
        value=values[index]
        if not self.pairs.isChecked() or not value.imag:return None
        return next((i for i,z in enumerate(values) if i!=index and abs(z-value.conjugate())<1e-7*max(1,abs(value))),None)
    def press(self,event):
        if event.button!=1 or not self.active(event):return
        try:data=self.data()
        except ValueError:self.note.setText('Corregí las listas de polos y ceros antes de editar el plano.');return
        mode=self.mode.currentIndex()
        if mode<2:
            kind=1 if mode==0 else 0;value=self.point(event);data[kind].append(value)
            if self.pairs.isChecked() and value.imag:data[kind].append(value.conjugate())
            self.write(data);self.redraw();self.submit();return
        selected=self.nearest(event,data)
        if selected is None:self.note.setText('Seleccioná un punto existente; podés acercar el gráfico con la barra de zoom.');return
        kind,index=selected;pair=self.partner(data[kind],index)
        if mode==3:
            for i in sorted([index]+([pair] if pair is not None else []),reverse=True):data[kind].pop(i)
            self.write(data);self.redraw();self.submit()
        else:self.drag=(data,kind,index,pair)
    def move(self,event):
        self.cursor_event(event)
        if self.drag is None or not self.active(event):return
        data,kind,index,pair=self.drag;value=self.point(event);data[kind][index]=value
        if pair is None and self.pairs.isChecked() and value.imag:
            pair=len(data[kind]);data[kind].append(value.conjugate());self.drag=(data,kind,index,pair)
        if pair is not None:data[kind][pair]=value.conjugate()
        self.write(data);self.redraw(preserve=True)
    def release(self,event):
        if self.drag is None:return
        self.drag=None;self.submit()
    def manual(self,*_):
        if self.busy():return
        self.dirty();self.redraw(preserve=False)
        self.note.setText('Definición editada. Presioná Diseñar desde polos y ceros para actualizar el sistema, o editá el plano con el mouse.')
    def redraw(self,preserve=True):
        try:data=self.data()
        except ValueError:return
        limits=None
        if preserve and self.panel.figure.axes and (self.panel.figure.axes[0].name=='polar')==(self.coordinates.currentIndex()==1):limits=(self.panel.figure.axes[0].get_xlim(),self.panel.figure.axes[0].get_ylim())
        self.panel.figure.clear();polar=self.coordinates.currentIndex()==1;axis=self.panel.figure.add_subplot(111,projection='polar' if polar else None)
        if polar:
            from matplotlib.ticker import FuncFormatter
            from .signal_plot import _pi_label
            draw_root_markers(axis,*data,polar=True)
            angle=np.linspace(0,2*np.pi,361)
            if self.panel.domain.currentIndex()==0:axis.plot(angle,np.ones_like(angle),'--',color='#667b97',label='Círculo unidad')
            axis.xaxis.set_major_formatter(FuncFormatter(_pi_label));axis.set_title('Plano polar · radio = módulo · ángulo en radianes',pad=24)
            axis.set_ylim(0,max([1.5]+[abs(z)*1.25 for values in data for z in values]));axis.grid(alpha=.3)
            if axis.get_legend_handles_labels()[0]:axis.legend()
            axis.format_coord=lambda theta,r:f'r = {r:.6g} · θ = {_pi_label(theta)} rad · {r*np.exp(1j*theta):.6g}'
            if limits:axis.set_xlim(limits[0]);axis.set_ylim(limits[1])
            self.finish_redraw();return
        draw_root_markers(axis,*data)
        if self.panel.domain.currentIndex()==0:
            angle=np.linspace(0,2*np.pi,361);axis.plot(np.cos(angle),np.sin(angle),'--',color='#667b97')
        axis.axvline(0,color='#667b97',linewidth=.7);axis.axhline(0,color='#667b97',linewidth=.7)
        axis.set_xlabel('Parte real');axis.set_ylabel('Parte imaginaria');axis.set_aspect('equal',adjustable='box');axis.grid(alpha=.2)
        if axis.get_legend_handles_labels()[0]:axis.legend()
        if limits:axis.set_xlim(limits[0]);axis.set_ylim(limits[1])
        else:
            extent=max([1.5]+[max(abs(z.real),abs(z.imag))*1.25 for values in data for z in values]);axis.set_xlim(-extent,extent);axis.set_ylim(-extent,extent)
        self.finish_redraw()
    def finish_redraw(self):
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        if toolbar:toolbar.update();toolbar.push_current()
        self.panel.figure.tight_layout();self.panel.canvas.draw_idle()
    def submit(self):
        zeros,poles=self.data()
        self.note.setText('Actualizando el sistema, su plano y la respuesta en frecuencia.')
        self.panel.guard(self.panel.design_roots)
