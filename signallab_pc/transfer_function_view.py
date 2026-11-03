"""Wireframe views of a rational H(s) or H(z), independent of frequency plots."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox,QComboBox,QFormLayout
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from mpl_toolkits.mplot3d import Axes3D  # Register and package the 3D projection.
from .report_view import ReportView
from .numeric_input import real_field
from .transfer_plane import convergence,evaluate_plane,plane_roots


class TransferFunctionView(QWidget):
    def __init__(self):
        super().__init__();self.system=None;self._grid=None;layout=QVBoxLayout(self)
        self.formula=ReportView();self.formula.setMaximumHeight(155);layout.addWidget(self.formula)
        controls=QFormLayout();layout.addLayout(controls);self.ranges={};self.axis_labels={}
        for coordinate in ('real','imag'):
            container=QWidget();row=QHBoxLayout(container);row.setContentsMargins(0,0,0,0)
            for suffix,label,value in [('low','Desde','-1.5'),('high','Hasta','1.5')]:
                row.addWidget(QLabel(label));field=QLineEdit(value);row.addWidget(field,1);self.ranges[coordinate+'_'+suffix]=field
            axis_label=QLabel();self.axis_labels[coordinate]=axis_label;controls.addRow(axis_label,container)
        draw=QPushButton('Actualizar gráficas');draw.clicked.connect(self.draw);layout.addWidget(draw)
        self.note=QLabel('La figura permite elegir módulo/ángulo o parte real/imaginaria. Cada altura corresponde a una componente de H sobre el plano complejo.');self.note.setWordWrap(True);layout.addWidget(self.note)
        self.figure=Figure(figsize=(11,5.5));self.canvas=FigureCanvasQTAgg(self.figure);self.toolbar=NavigationToolbar2QT(self.canvas,self)
        self.components=QComboBox();self.components.addItems(['Módulo y ángulo','Parte real e imaginaria']);self.components.setAccessibleName('Componentes de la transferencia');self.components.setToolTip('Cambia la representación del resultado; no modifica el sistema ni su región de convergencia.')
        self.toolbar.addSeparator();self.toolbar.addWidget(self.components);self.components.currentIndexChanged.connect(self.draw)
        layout.addWidget(self.toolbar);layout.addWidget(self.canvas,1)

    def set_system(self,system):
        if self.system is system:return
        self.system=system;self._grid=None;digital=system.domain=='digital';symbol='z' if digital else 's'
        from .phase_summary import transfer_formula
        from .result_summary import Summary,Section
        information=convergence(system) if digital else {'text':'ROC de Laplace no especificada. La fracción racional por sí sola no determina el soporte temporal.'}
        self.formula.set_readable(Summary('Función de transferencia H('+symbol+')',[Section('Definición',formulas=[transfer_formula(system,digits=12)[0]]),Section('Región de convergencia',paragraphs=[information['text']])]))
        zeros,poles=plane_roots(system);radius=float(max(np.max(abs(zeros),initial=0),np.max(abs(poles),initial=0)))
        extent=max(1.5,1.25*radius) if digital else 1.25*radius if radius>0 else 1.5
        for coordinate in ('real','imag'):
            self.ranges[coordinate+'_low'].setText(format(-extent,'.12g'));self.ranges[coordinate+'_high'].setText(format(extent,'.12g'))
        self.axis_labels['real'].setText('Re('+symbol+')');self.axis_labels['imag'].setText('Im('+symbol+')');self.draw()

    def _samples(self):
        bounds=tuple(real_field(self.ranges[key]) for key in ('real_low','real_high','imag_low','imag_high'))
        x0,x1,y0,y1=bounds
        if not np.isfinite(bounds).all() or x1<=x0 or y1<=y0:raise ValueError('Indicá intervalos finitos crecientes para las partes real e imaginaria.')
        key=(id(self.system),bounds)
        if self._grid is not None and self._grid[0]==key:return self._grid[1:]
        x=np.linspace(x0,x1,121);y=np.linspace(y0,y1,121)
        if np.any(np.diff(x)<=0) or np.any(np.diff(y)<=0):raise ValueError('La precisión disponible no permite distinguir la malla de ese intervalo.')
        xx,yy=np.meshgrid(x,y);values=evaluate_plane(self.system,xx+1j*yy)
        # Leave a hole at every cell containing a pole; do not bridge a pole
        # merely because its exact position is between mesh vertices.
        _,poles=plane_roots(self.system)
        for pole in poles:
            if x0<=pole.real<=x1 and y0<=pole.imag<=y1:
                column=int(np.searchsorted(x,pole.real));row=int(np.searchsorted(y,pole.imag))
                values[max(0,row-1):min(len(y),row+1),max(0,column-1):min(len(x),column+1)]=complex(np.nan,np.nan)
        self._grid=(key,xx,yy,values,bounds)
        return xx,yy,values,bounds

    def draw(self,*_):
        if self.system is None:return
        try:
            xx,yy,h,bounds=self._samples();x0,x1,y0,y1=bounds;digital=self.system.domain=='digital';symbol='z' if digital else 's'
            polar=self.components.currentIndex()==0
            if polar:
                angle=np.full(h.shape,np.nan);valid=np.isfinite(h)&(abs(h)>0);angle[valid]=np.angle(h[valid])
                cut=np.zeros(h.shape,dtype=bool)
                horizontal=np.abs(np.diff(angle,axis=1))>np.pi;vertical=np.abs(np.diff(angle,axis=0))>np.pi
                cut[:,:-1]|=horizontal;cut[:,1:]|=horizontal;cut[:-1,:]|=vertical;cut[1:,:]|=vertical;angle[cut]=np.nan
                components=(abs(h),angle);titles=('Módulo de H('+symbol+')','Ángulo principal de H('+symbol+')');zlabels=('|H('+symbol+')|','Arg(H) (rad)')
            else:components=(h.real,h.imag);titles=('Parte real de H('+symbol+')','Parte imaginaria de H('+symbol+')');zlabels=('Re(H)','Im(H)')
            with np.errstate(all='ignore'):finite=abs(h)
            finite=finite[np.isfinite(finite)];peak=float(finite.max(initial=0));amplitude=.05 if peak<=1e-10 else min(np.finfo(float).max,peak*1.05)
            self.figure.clear()
            for index,(values,title,zlabel) in enumerate(zip(components,titles,zlabels)):
                axis=self.figure.add_subplot(1,2,index+1,projection='3d');axis.view_init(elev=27,azim=-125)
                if np.isfinite(values).any():axis.plot_wireframe(xx,yy,values,rstride=4,cstride=4,color='#79c4ad' if index==0 else '#8ab6df',linewidth=.55)
                else:axis.text2D(.5,.5,'Componente no definida en la malla',ha='center',transform=axis.transAxes)
                axis.set(xlim=(x0,x1),ylim=(y0,y1),xlabel='Re('+symbol+')'+(' (s⁻¹)' if not digital else ''),ylabel='Im('+symbol+')'+(' (rad/s)' if not digital else ''),zlabel=zlabel,title=title)
                axis.set_box_aspect((1,1,.8));axis.set_zlim((-np.pi,np.pi) if polar and index==1 else (0,amplitude) if polar else (-amplitude,amplitude))
                if polar and index==1:axis.set_zticks([-np.pi,-np.pi/2,0,np.pi/2,np.pi],['−π','−π/2','0','π/2','π'])
                if digital:
                    theta=np.linspace(0,2*np.pi,361);real=np.cos(theta);imag=np.sin(theta);inside=(real>=x0)&(real<=x1)&(imag>=y0)&(imag<=y1)
                    axis.plot(np.where(inside,real,np.nan),np.where(inside,imag,np.nan),np.zeros(theta.shape),linestyle='--',color='#8194ae',linewidth=.7)
                elif x0<=0<=x1:axis.plot([0,0],[y0,y1],[0,0],linestyle='--',color='#8194ae',linewidth=.7)
            description=convergence(self.system)['text'] if digital else 'ROC de Laplace no especificada.'
            self.note.setText(description+' Dos gráficas de malla muestran '+('módulo lineal y ángulo principal en radianes.' if polar else 'las partes real e imaginaria, con igual escala vertical.')+' Se interrumpe el trazado en polos y en saltos del ángulo. La línea discontinua indica '+('el círculo unitario.' if digital else 'el eje imaginario s=jΩ.')+' La fracción puede evaluarse fuera de su ROC; la respuesta en frecuencia se consulta por separado.')
            self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
        except Exception as exc:QMessageBox.warning(self,'No se pudo representar la transferencia',str(exc))
