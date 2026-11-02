"""Rational H(z) in the complex plane and explicit annular convergence."""
import numpy as np
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .report_view import ReportView
from .numeric_input import real_field


from .transfer_plane import convergence,evaluate_plane,effective_system,plane_roots


class ZPlaneView(QWidget):
    def __init__(self):
        super().__init__();self.system=None;layout=QVBoxLayout(self)
        self.formula=ReportView();self.formula.setMaximumHeight(150);layout.addWidget(self.formula)
        row=QHBoxLayout();row.addWidget(QLabel('Semiancho del plano'));self.extent=QLineEdit('2');self.extent.setMaximumWidth(120);row.addWidget(self.extent)
        draw=QPushButton('Actualizar plano');draw.clicked.connect(self.draw);row.addWidget(draw);row.addStretch();layout.addLayout(row)
        self.note=QLabel('El color representa |H(z)| en el plano; la respuesta en frecuencia se estudia por separado.');self.note.setWordWrap(True);layout.addWidget(self.note)
        self.figure=Figure(figsize=(6,5));self.canvas=FigureCanvasQTAgg(self.figure);layout.addWidget(NavigationToolbar2QT(self.canvas,self));layout.addWidget(self.canvas,1)
    def set_system(self,system):
        if self.system is system:return
        self.system=system
        from .phase_summary import transfer_formula
        from .result_summary import Summary,Section
        information=convergence(system)
        self.formula.set_readable(Summary('H(z) en el plano complejo',[Section('Definición',formulas=[transfer_formula(system,digits=12)[0]]),Section('Región de convergencia',paragraphs=[information['text']])]))
        _,poles=plane_roots(system);self.extent.setText(format(max(1.5,float(np.max(abs(poles),initial=0))*1.2),'.8g'));self.draw()
    def draw(self):
        if self.system is None:return
        try:
            extent=real_field(self.extent)
            if extent<=0 or not np.isfinite(extent):raise ValueError('El semiancho debe ser positivo y finito.')
            system=self.system;info=convergence(system);zeros,poles=plane_roots(system)
            coordinate=np.linspace(-extent,extent,401);x,y=np.meshgrid(coordinate,coordinate);z=x+1j*y
            magnitude=abs(evaluate_plane(system,z))
            with np.errstate(all='ignore'):db=20*np.log10(magnitude)
            self.figure.clear();axis=self.figure.add_subplot(111)
            color=axis.pcolormesh(x,y,np.ma.masked_invalid(db),shading='auto',cmap='viridis')
            self.figure.colorbar(color,ax=axis,label='20 log₁₀ |H(z)| (dB)')
            if info['known']:
                radius=abs(z);outside=((radius<info['inner']) if info.get('zero_included') else (radius<=info['inner']))|(radius>=info['outer'])
                if outside.any():axis.contourf(x,y,outside.astype(float),levels=[.5,1.5],colors=['#101620'],alpha=.6)
                for value in (info['inner'],info['outer']):
                    if 0<value<extent*1.5:axis.add_patch(Circle((0,0),value,fill=False,color='#dfb374',linestyle=':'))
            theta=np.linspace(0,2*np.pi,501);axis.plot(np.cos(theta),np.sin(theta),'--',color='#e1e7ee',label='Círculo unitario')
            if zeros.size:axis.scatter(zeros.real,zeros.imag,marker='o',s=72,facecolors='none',edgecolors='#68c7b4',label='Ceros',zorder=5)
            if poles.size:axis.scatter(poles.real,poles.imag,marker='x',s=68,c='#efb56c',label='Polos',zorder=6)
            for points in (zeros,poles):
                unique,counts=np.unique(points,return_counts=True)
                for point,count in zip(unique,counts):
                    if count>1:axis.annotate(str(count),(point.real,point.imag),xytext=(7,7),textcoords='offset points')
            axis.axhline(0,color='#8194ae',alpha=.35);axis.axvline(0,color='#8194ae',alpha=.35)
            axis.set(xlim=(-extent,extent),ylim=(-extent,extent),xlabel='Re(z)',ylabel='Im(z)',title='Plano complejo · H(z)');axis.set_aspect('equal');axis.legend()
            self.note.setText(info['text']+' '+('El círculo unitario pertenece a la ROC.' if info['unit'] else 'La respuesta DTFT no está definida sobre todo el círculo unitario.' if info['known'] else '')+' El mapa cancela factores comunes exactos y evalúa la expresión racional; las zonas atenuadas quedan fuera de la ROC. Ceros exactos (−∞ dB) y polos no reciben un color finito.')
            self.figure.set_layout_engine('constrained');self.canvas.draw_idle()
        except Exception as exc:QMessageBox.warning(self,'No se pudo dibujar H(z)',str(exc))
