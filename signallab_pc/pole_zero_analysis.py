"""Read-only root inspection, independent of the pole/zero design editor."""
import numpy as np
from .pole_zero_marks import draw_root_markers,origin_description
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QLabel
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from .report_view import ReportView,report_panel

def analyze_roots(system,advance=0):
    zeros,poles=system.poles_zeros()
    # The numeric causal proxy of a formula with a net advance includes extra
    # poles at zero. Multiplication by z**advance cancels those poles first.
    if advance:
        origin=np.flatnonzero(poles==0);cancel=min(advance,len(origin))
        poles=np.delete(poles,origin[:cancel]);zeros=np.r_[zeros,np.zeros(advance-cancel)]
    return zeros,poles

class PoleZeroAnalysis(QWidget):
    def __init__(self):
        super().__init__();self.result=None;root=QVBoxLayout(self)
        row=QHBoxLayout();row.addWidget(QLabel('Coordenadas del plano'));self.coordinates=QComboBox();self.coordinates.addItems(['Binómicas: real e imaginaria','Polares: ángulo y módulo']);row.addWidget(self.coordinates,1);root.addLayout(row)
        self.figure=Figure(figsize=(6,5));self.canvas=FigureCanvasQTAgg(self.figure);root.addWidget(NavigationToolbar2QT(self.canvas,self));root.addWidget(self.canvas,1)
        self.report=ReportView();root.addWidget(report_panel(self.report),1);self.report.setPlainText('Analizá H y seleccioná la pestaña Polos y ceros. Esta vista sólo consulta el sistema calculado.')
        self.coordinates.currentIndexChanged.connect(self.redraw)
    def set_result(self,system,zeros,poles,advance=0):
        self.result=(system,np.asarray(zeros),np.asarray(poles),advance)
        advance+=system.advance
        def number(z):return f'{z.real:.9g} {"+" if z.imag>=0 else "−"} {abs(z.imag):.9g}j'
        lines=['POLOS Y CEROS · '+('Plano z' if system.domain=='digital' else 'Plano s')]
        lines+=['Ceros ('+str(len(zeros))+'): '+(', '.join(number(v) for v in zeros) or 'ninguno finito')]
        lines+=['Polos ('+str(len(poles))+'): '+(', '.join(number(v) for v in poles) or 'ninguno finito')]
        origin=origin_description(zeros,poles)
        if origin:lines.append(origin)
        if not np.any(system.b):lines+=['H es nula: no se definen ceros aislados. Se muestran los polos del denominador cargado.']
        else:
            lines+=['Criterio causal por ubicación de polos: '+system.stability(poles), 'Región estable: |z| < 1.' if system.domain=='digital' else 'Región estable: Re(s) < 0.']
        if system.domain=='digital' and system.roc is not None:
            from .transfer_plane import convergence
            information=convergence(system)
            lines+=['ROC seleccionada: '+information['text'],'Estabilidad BIBO de la transferencia bilateral: '+('compatible con el círculo unitario dentro de la ROC.' if information['unit'] else 'el círculo unitario no pertenece a la ROC.')+' Esto no prueba estabilidad interna de una realización con cancelaciones.']
        if system.domain=='analog' and len(np.trim_zeros(system.b,'f'))>len(np.trim_zeros(system.a,'f')):
            lines+=['Transferencia analógica impropia: la ubicación de sus polos finitos no basta para afirmar estabilidad BIBO.']
        if advance:lines+=['La expresión tiene un avance de '+str(advance)+' muestras; no representa un filtro causal. El plano corresponde a la fórmula completa, incluido ese avance.']
        lines+=['Las raíces se calculan numéricamente. El redondeo puede afectar raíces múltiples y órdenes altos. No se cancelan polos y ceros por proximidad. El criterio usual de estabilidad BIBO por polos presupone una realización causal y propia. La fórmula racional sola no fija una ROC ni demuestra estabilidad interna tras cancelaciones.']
        self.report.setPlainText('\n\n'.join(lines));self.redraw()
    def redraw(self,*_):
        if self.result is None:return
        system,zeros,poles,_=self.result;polar=self.coordinates.currentIndex()==1
        self.figure.clear();ax=self.figure.add_subplot(111,projection='polar' if polar else None)
        if polar:
            theta=np.linspace(0,2*np.pi,361)
            if system.domain=='digital':ax.plot(theta,np.ones_like(theta),'--',color='#8192a6',label='Círculo unidad')
            from matplotlib.ticker import FuncFormatter
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v,pos:f'{v/np.pi:g}π' if v else '0'))
            ax.set_ylim(0,max(1.15,float(max(np.max(abs(zeros),initial=0),np.max(abs(poles),initial=0)))*1.15))
            coords=lambda values:(np.mod(np.angle(values),2*np.pi),abs(values))
            ax.set_title('Plano z · ángulo (rad), módulo' if system.domain=='digital' else 'Plano s · ángulo (rad), módulo')
        else:
            if system.domain=='digital':
                theta=np.linspace(0,2*np.pi,361);ax.plot(np.cos(theta),np.sin(theta),'--',color='#8192a6',label='Círculo unidad')
            ax.axhline(0,color='#8192a6',linewidth=.7);ax.axvline(0,color='#8192a6',linewidth=.7)
            coords=lambda values:(values.real,values.imag)
            ax.set_xlabel('Parte real');ax.set_ylabel('Parte imaginaria');ax.set_aspect('equal',adjustable='box');ax.margins(.15);ax.set_title('Plano z' if system.domain=='digital' else 'Plano s')
        draw_root_markers(ax,zeros,poles,polar=polar)
        if not polar:
            from .pole_zero_marks import frame_root_plane
            frame_root_plane(ax,zeros,poles,digital=system.domain=='digital')
        ax.grid(alpha=.25)
        if ax.get_legend_handles_labels()[0]:ax.legend()
        self.figure.tight_layout();self.canvas.draw_idle()
