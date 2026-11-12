"""A separate ROC window; selecting a region updates the existing inverse form."""
import math
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPushButton
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT


def region_at(data,coordinate):
    if not math.isfinite(coordinate):return -1
    for i,region in enumerate(data['regions']):
        low=region['lower_numeric'];high=region['upper_numeric']
        low=None if low is None else float(low);high=None if high is None else float(high)
        if (low is None or coordinate>low) and (high is None or coordinate<high):return i
    return -1


class RocPicker(QDialog):
    def __init__(self,panel,data):
        super().__init__(panel);self.panel=panel;self.data=data
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.finished.connect(self.release)
        self.setWindowTitle('Región de convergencia · '+('Z' if data['kind']=='z' else 'Laplace'));self.resize(780,660)
        root=QVBoxLayout(self);intro=QLabel('Hacé clic dentro de una región o elegila en la lista. Aplicar cambia la ROC de la inversa; la expresión se conserva.'+(' En Laplace se utiliza interpretación bilateral.' if data['kind']=='laplace' else ''))
        intro.setWordWrap(True);root.addWidget(intro)
        self.figure=Figure(figsize=(7,4),layout='constrained');self.canvas=FigureCanvasQTAgg(self.figure);self.canvas.setMinimumHeight(260)
        from .plot_view import install_figure_layout
        install_figure_layout(self.canvas)
        self.toolbar=NavigationToolbar2QT(self.canvas,self);self.toolbar._signallab_enlarge=True;root.addWidget(self.toolbar);root.addWidget(self.canvas,1)
        self.choice=QComboBox();self.choice.setAccessibleName('Región abierta para la inversa')
        for region in data['regions']:self.choice.addItem(region['label'])
        self.choice.setCurrentIndex(-1);root.addWidget(self.choice)
        self.note=QLabel(data['report']+' '+data['scope']);self.note.setWordWrap(True);root.addWidget(self.note)
        self.status=QLabel('Seleccioná una región.');self.status.setWordWrap(True);root.addWidget(self.status)
        buttons=QHBoxLayout();root.addLayout(buttons)
        self.apply_button=QPushButton('Aplicar ROC');self.calculate_button=QPushButton('Aplicar y calcular inversa');self.calculate_button.setObjectName('primary')
        buttons.addWidget(self.apply_button);buttons.addWidget(self.calculate_button);close=QPushButton('Cerrar');buttons.addWidget(close);close.clicked.connect(self.close)
        self.apply_button.clicked.connect(lambda:self.apply(False));self.calculate_button.clicked.connect(lambda:self.apply(True))
        self.choice.currentIndexChanged.connect(self.draw);self.canvas.mpl_connect('button_press_event',self.clicked);self.draw()

    def release(self,*_):
        if getattr(self.panel,'roc_picker',None) is self:self.panel.roc_picker=None

    def clicked(self,event):
        if event.inaxes is None or event.xdata is None or event.ydata is None or event.button!=1 or self.toolbar.mode:return
        coordinate=math.hypot(event.xdata,event.ydata) if self.data['kind']=='z' else event.xdata
        index=region_at(self.data,coordinate)
        if index<0:self.status.setText('El borde no pertenece a una ROC abierta. Elegí un punto dentro de una región.');return
        self.choice.setCurrentIndex(index)

    def draw(self,*_):
        selected=self.choice.currentIndex();self.apply_button.setEnabled(selected>=0);self.calculate_button.setEnabled(selected>=0)
        self.figure.clear();axis=self.figure.subplots();data=self.data
        if selected>=0:
            region=data['regions'][selected];self.status.setText(region['label']+' · '+('radio interior = ' if data['kind']=='z' else 'σ interior = ')+region['display_value']);self.status.setToolTip(region['value'])
        poles=[complex(*p) for p in data['poles'] if p is not None]
        extent=max([1.]+[max(abs(p.real),abs(p.imag)) for p in poles])*1.45
        if not data.get('plot_available',True) or not math.isfinite(extent) or extent>1e150:
            axis.text(.5,.5,'La escala excede la representación del gráfico.\nUsá la lista de regiones.',ha='center',va='center',transform=axis.transAxes);self.canvas.draw_idle();return
        if data['kind']=='z':extent=max(extent,1.45)
        axis.set_xlim(-extent,extent);axis.set_ylim(-extent,extent);axis.set_aspect('equal',adjustable='box')
        axis.axhline(0,color='gray',lw=.7);axis.axvline(0,color='gray',lw=.7)
        if selected>=0:
            region=data['regions'][selected];low=region['lower_numeric'];high=region['upper_numeric']
            low=None if low is None else float(low);high=None if high is None else float(high)
            if data['kind']=='z':
                from matplotlib.patches import Wedge
                outer=min(high if high is not None else extent*2,extent*2);inner=min(low or 0.,outer)
                axis.add_patch(Wedge((0,0),outer,0,360,width=outer-inner,color='#68c7b4',alpha=.2,label='ROC elegida'))
            else:axis.axvspan(max(low if low is not None else -extent,-extent),min(high if high is not None else extent,extent),alpha=.2,color='#68c7b4',label='ROC elegida')
        if data['kind']=='z':
            from matplotlib.patches import Circle
            axis.add_patch(Circle((0,0),1,fill=False,linestyle=':',color='gray',label='Círculo unitario'))
            for radius in map(float,data['boundaries']):
                if radius<=extent*2:axis.add_patch(Circle((0,0),radius,fill=False,linestyle='--',color='#e8b56b'))
        else:
            for boundary in map(float,data['boundaries']):axis.axvline(boundary,linestyle='--',color='#e8b56b')
        if poles:axis.scatter([p.real for p in poles],[p.imag for p in poles],marker='x',s=65,linewidths=1.8,color='#ef986c',label='Polos')
        axis.set_xlabel('Parte real');axis.set_ylabel('Parte imaginaria');axis.set_title('Polos y regiones abiertas · plano '+('z' if data['kind']=='z' else 's'));axis.grid(alpha=.2)
        if selected>=0 or poles or data['kind']=='z':axis.legend(loc='upper left',fontsize=8)
        self.canvas.draw_idle()

    def apply(self,calculate):
        index=self.choice.currentIndex()
        if index<0:return
        if self.panel.mode.currentIndex()!=1 or self.panel.expression.text()!=self.data['expression']:
            self.status.setText('La expresión cambió. Volvé a abrir el selector para usar los polos actuales.');return
        region=self.data['regions'][index]
        if self.data['kind']=='z':
            self.panel.roc.setCurrentIndex({'right':0,'left':1,'radius':2}[region['mode']]);self.panel.radius.setText(region['value'])
        else:
            self.panel.interpretation.setCurrentIndex(1);self.panel.laplace_roc.setCurrentIndex({'right':0,'left':1,'line':2}[region['mode']]);self.panel.sigma.setText(region['value'])
        self.panel.result_state.refresh();self.accept()
        if calculate:self.panel.calculate()
