"""Ampliación temporal del lienzo, conservando figura, zoom y datos."""
from PySide6.QtWidgets import QDialog,QVBoxLayout,QPushButton
from .theme_tokens import COLORS as C
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

class FigureWindow(QDialog):
    """Persistent non-modal figure; closing hides it without discarding the data."""
    def closeEvent(self,event):
        self.hide();event.ignore()


def enlarge_plot(canvas,owner):
    window=getattr(canvas,'_signallab_window',None)
    if window is not None:
        window.show();window.raise_();window.activateWindow();canvas.draw_idle()


def install_enlarge(toolbar):
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QWidget,QLabel,QSizePolicy
    if getattr(toolbar,'_signallab_enlarge',False):return
    toolbar._signallab_enlarge=True
    canvas=toolbar.canvas;parent=canvas.parentWidget();layout=parent.layout()
    if layout is None:return
    launcher=QWidget(parent);box=QVBoxLayout(launcher);box.setContentsMargins(0,4,0,4)
    note=QLabel('Los gráficos se abren en una ventana independiente.');note.setWordWrap(True);box.addWidget(note)
    button=QPushButton('Abrir gráfico');box.addWidget(button);box.addStretch()
    launcher.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
    item=layout.replaceWidget(canvas,launcher);del item
    toolbar_parent=toolbar.parentWidget()
    if toolbar_parent.layout() is not None:toolbar_parent.layout().removeWidget(toolbar)
    title='Gráfico · SignalLab'
    ancestor=parent
    while ancestor is not None:
        route=getattr(ancestor,'tool_item',None)
        if route:title=route[0]+' · SignalLab';break
        ancestor=ancestor.parentWidget()
    window=FigureWindow(parent,Qt.WindowType.Window)
    window.setModal(False);window.setWindowTitle(title);window.setWindowIcon(parent.window().windowIcon())
    content=QVBoxLayout(window);content.setContentsMargins(6,6,6,6);content.addWidget(toolbar);content.addWidget(canvas,1)
    from PySide6.QtGui import QAction
    detail=QAction('Detalle vertical',toolbar);detail.setCheckable(True);detail.setChecked(bool(getattr(canvas.figure,'_signallab_detail_vertical',False)))
    detail.setToolTip('Ajustar la escala a los valores originales, incluso variaciones muy pequeñas. Desactivado evita amplificar variaciones menores que 10⁻¹⁰ de la referencia visual (al menos 1). No se redondean ni se borran datos. El zoom manual sigue disponible.')
    toolbar.addSeparator();toolbar.addAction(detail);canvas._signallab_detail_action=detail
    scale_note=QLabel();scale_note.setWordWrap(True);scale_note.setStyleSheet('color:'+C['muted']+';font-size:9pt;');scale_note.hide();content.addWidget(scale_note);canvas._signallab_scale_note=scale_note
    def vertical_detail(enabled):
        from .plot_scale import set_vertical_detail
        set_vertical_detail(canvas.figure,enabled);canvas.draw_idle()
    detail.toggled.connect(vertical_detail)
    canvas.setMinimumSize(0,0);canvas.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
    available=parent.screen().availableGeometry();window.resize(min(1000,available.width()-32),min(700,available.height()-48));window.setMinimumSize(360,280)
    canvas._signallab_window=window;canvas._signallab_launcher=launcher
    button.clicked.connect(lambda:enlarge_plot(canvas,toolbar))
    install_figure_layout(canvas)
    original_draw=canvas.draw;last=[None];pending=[False]
    def open_result():
        pending[0]=False
        if not window.isVisible():window.show()
    def draw(*args,**kwargs):
        result=original_draw(*args,**kwargs)
        # New plot objects identify a new result; repainting/zooming a closed
        # figure must not reopen it. An empty placeholder is not a result.
        artists=[artist for axis in canvas.figure.axes for artist in [*axis.lines,*axis.collections,*axis.images,*axis.patches]
                 if artist is not axis.patch]
        signature=tuple(id(artist) for artist in artists)
        if artists and signature!=last[0]:
            last[0]=signature
            if not pending[0]:pending[0]=True;QTimer.singleShot(0,window,open_result)
        return result
    canvas.draw=draw
    # draw_idle works even while the canvas belongs to a hidden window.
    canvas.draw_idle()



def prepare_figure(figure):
    """Reservar una columna de leyenda fuera de los ejes, también al exportar."""
    import textwrap
    from matplotlib.colors import to_hex
    palette={'#68c7b4': '#79c4ad', '#55d6c2': '#79c4ad', '#087e8b': '#79c4ad', '#178775': '#79c4ad', '#8b9cfa': '#b4a1d5', '#6457aa': '#b4a1d5', '#91a5f6': '#8ab6df', '#6e80bb': '#8ab6df', '#efb56c': '#dfb374', '#e8b56b': '#dfb374', '#b36a12': '#dfb374', '#c15c14': '#dfb374', '#ec819c': '#db96a6', '#b64f72': '#db96a6', '#dd8baf': '#db96a6', '#8194ae': '#a6b2c1', '#91a0b5': '#a6b2c1', '#5c6775': '#a6b2c1', '#4b5666': '#a6b2c1', '#0072bd': '#8ab6df', '#1264a0': '#8ab6df', '#087c68': '#79c4ad', '#a96815': '#dfb374'}
    current={'#79c4ad':C['green'],'#b4a1d5':C['purple'],'#8ab6df':C['blue'],'#dfb374':C['amber'],'#db96a6':C['red'],'#a6b2c1':C['muted']}
    palette={old:current.get(color,color) for old,color in palette.items()}
    figure.set_facecolor(C['report'])
    handles=[];labels=[];seen=set()
    previous=getattr(figure,'_signallab_legend',None)
    needs_legend=(previous is not None and previous in figure.legends)
    for axis in figure.axes:
        legend=axis.get_legend()
        if legend is not None:needs_legend=True;legend.remove()
        axis.set_facecolor(C['panel']);axis.tick_params(colors=C['muted'],labelsize=9)
        for spine in axis.spines.values():spine.set_color(C['disabled'])
        for text in [axis.title,axis.xaxis.label,axis.yaxis.label,*axis.texts]:
            text.set_color(C['text'])
        for line in axis.lines:
            try:
                color=to_hex(line.get_color())
                if color in palette:line.set_color(palette[color])
            except (ValueError,TypeError):pass
        # Match explicitly colored stems/scatter to their line/legend colors.
        from matplotlib.colors import to_rgba
        for collection in axis.collections:
            for channel in ('facecolor','edgecolor'):
                getter=getattr(collection,'get_'+channel+'s',None);setter=getattr(collection,'set_'+channel+'s',None)
                if getter is None or setter is None:continue
                colors=getter().copy();changed=False
                for index,rgba in enumerate(colors):
                    old=to_hex(rgba)
                    if old in palette:
                        colors[index]=to_rgba(palette[old],rgba[3]);changed=True
                if changed:setter(colors)
        for handle,label in zip(*axis.get_legend_handles_labels()):
            if label not in seen:handles.append(handle);labels.append(textwrap.fill(label,30,break_long_words=False));seen.add(label)
    if previous is not None and previous in figure.legends:previous.remove()
    if handles and needs_legend:
        figure._signallab_legend=figure.legend(handles,labels,loc='outside right upper',fontsize=8,frameon=False,title='Referencias',title_fontsize=9,labelcolor=C['text'],borderaxespad=.8)
        figure._signallab_legend.get_title().set_color(C['text'])
    else:figure._signallab_legend=None
    # Constrained layout calcula márgenes con títulos, unidades y leyenda al tamaño real.
    figure.set_layout_engine('constrained',w_pad=.09,h_pad=.09,hspace=.12,wspace=.08)
    from .plot_scale import apply_stable_scale
    return apply_stable_scale(figure)


def install_figure_layout(canvas):
    if getattr(canvas,'_signallab_layout',False):return
    canvas._signallab_layout=True
    original_draw=canvas.draw;original_print=canvas.print_figure
    def draw(*args,**kwargs):
        protected=prepare_figure(canvas.figure)
        note=getattr(canvas,'_signallab_scale_note',None)
        if note is not None:
            note.setText('Escala estable en '+str(len(protected))+' panel(es). Los valores se conservan. Activá «Detalle vertical» para ver sus pequeñas variaciones.' if protected else '')
            note.setVisible(bool(protected))
        return original_draw(*args,**kwargs)
    def print_figure(*args,**kwargs):
        prepare_figure(canvas.figure)
        return original_print(*args,**kwargs)
    canvas.draw=draw;canvas.print_figure=print_figure
