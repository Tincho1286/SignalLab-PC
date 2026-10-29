"""Edición directa del plano de polos y ceros sobre el lienzo existente."""
import numpy as np
from .pole_zero_marks import draw_root_markers
from PySide6.QtWidgets import QWidget,QHBoxLayout,QVBoxLayout,QComboBox,QCheckBox,QLabel
from .systems_panel import parse_list,list_text

class PoleZeroEditor(QWidget):
    def __init__(self,panel,context):
        super().__init__();self.panel=panel;self.context=context;self.drag=None
        box=QVBoxLayout(self);box.setContentsMargins(0,0,0,0);row=QHBoxLayout()
        self.mode=QComboBox();self.mode.addItems(['Agregar polo ×','Agregar cero ○','Mover punto','Quitar punto']);row.addWidget(self.mode)
        self.coordinates=QComboBox();self.coordinates.addItems(['Binómica · real / imaginaria','Polar · módulo / ángulo (rad)']);box.addWidget(self.coordinates);self.coordinates.currentIndexChanged.connect(lambda *_:self.redraw())
        self.pairs=QCheckBox('Pares conjugados');self.pairs.setChecked(True);row.addWidget(self.pairs);box.addLayout(row)
        self.note=QLabel('Hacé clic en el plano para agregar un polo. El diseño se actualiza al terminar cada edición.');self.note.setWordWrap(True);box.addWidget(self.note)
        self.connections=[panel.canvas.mpl_connect('button_press_event',self.press),panel.canvas.mpl_connect('motion_notify_event',self.move),panel.canvas.mpl_connect('button_release_event',self.release)]
        for key in ('zeros','poles','gain'):
            panel.fields[key].textChanged.connect(self.dirty)
            panel.fields[key].editingFinished.connect(self.manual)
        panel.domain.currentIndexChanged.connect(self.manual)
        self.redraw()
    def dirty(self,*_):
        callback=getattr(self.context,'on_design_dirty',None)
        if callback:callback()
    def data(self):return [list(parse_list(self.panel.fields[key].text(),True)) for key in ('zeros','poles')]
    def write(self,data):
        for key,values in zip(('zeros','poles'),data):self.panel.fields[key].setText(list_text(values))
    def busy(self):return bool(self.context.window._workers)
    def active(self,event):
        toolbar=getattr(self.panel.canvas,'toolbar',None)
        return event.inaxes is not None and event.xdata is not None and event.ydata is not None and not (toolbar and toolbar.mode) and not self.busy()
    def point(self,event):
        value=event.ydata*np.exp(1j*event.xdata) if self.coordinates.currentIndex()==1 else complex(event.xdata,event.ydata)
        if self.pairs.isChecked() and abs(value.imag)<.02*abs(event.inaxes.get_ylim()[1]-event.inaxes.get_ylim()[0]):value=complex(value.real,0)
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
        self.dirty();self.redraw()
        self.note.setText('Definición editada. Presioná Diseñar desde polos y ceros para actualizar el sistema, o editá el plano con el mouse.')
    def redraw(self,preserve=False):
        try:data=self.data()
        except ValueError:return
        limits=None
        if preserve and self.panel.figure.axes:limits=(self.panel.figure.axes[0].get_xlim(),self.panel.figure.axes[0].get_ylim())
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
            self.panel.figure.tight_layout();self.panel.canvas.draw_idle();return
        draw_root_markers(axis,*data)
        if self.panel.domain.currentIndex()==0:
            angle=np.linspace(0,2*np.pi,361);axis.plot(np.cos(angle),np.sin(angle),'--',color='#667b97')
        axis.axvline(0,color='#667b97',linewidth=.7);axis.axhline(0,color='#667b97',linewidth=.7)
        axis.set_xlabel('Parte real');axis.set_ylabel('Parte imaginaria');axis.set_aspect('equal',adjustable='box');axis.grid(alpha=.2)
        if axis.get_legend_handles_labels()[0]:axis.legend()
        if limits:axis.set_xlim(limits[0]);axis.set_ylim(limits[1])
        else:
            extent=max([1.5]+[max(abs(z.real),abs(z.imag))*1.25 for values in data for z in values]);axis.set_xlim(-extent,extent);axis.set_ylim(-extent,extent)
        self.panel.figure.tight_layout();self.panel.canvas.draw_idle()
    def submit(self):
        zeros,poles=self.data()
        self.note.setText('Actualizando el sistema, su plano y la respuesta en frecuencia.')
        self.panel.guard(self.panel.design_roots)
