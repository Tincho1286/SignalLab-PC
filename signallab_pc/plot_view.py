"""Ampliación temporal del lienzo, conservando figura, zoom y datos."""
from PySide6.QtWidgets import QDialog,QVBoxLayout
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


def hide_plot(canvas):
    window = getattr(canvas, '_signallab_window', None)
    if window is not None:
        window.hide()


def open_result_plot(view, owner):
    canvas = view.canvas
    if getattr(canvas, '_signallab_window', None) is None:
        for toolbar in view.findChildren(NavigationToolbar2QT):
            if toolbar.canvas is canvas:
                install_enlarge(toolbar)
                break
    view.views.setCurrentIndex(0)
    canvas.draw()
    enlarge_plot(canvas, owner)


def install_enlarge(toolbar):
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QWidget,QLabel,QSizePolicy
    if getattr(toolbar,'_signallab_enlarge',False):return
    toolbar._signallab_enlarge=True
    canvas=toolbar.canvas;parent=canvas.parentWidget();layout=parent.layout()
    if layout is None:return
    launcher=QWidget(parent);box=QVBoxLayout(launcher);box.setContentsMargins(0,4,0,4)
    note=QLabel('Usá «Abrir gráfico» en la cabecera de resultados. La figura se abre en una ventana independiente.');note.setWordWrap(True);box.addWidget(note);box.addStretch()
    launcher.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
    item=layout.replaceWidget(canvas,launcher);del item
    toolbar_parent=toolbar.parentWidget()
    if toolbar_parent.layout() is not None:toolbar_parent.layout().removeWidget(toolbar)
    title='Gráfico · SignalLab'
    ancestor=parent
    while ancestor is not None:
        if ancestor.__class__.__module__.endswith('pole_zero_editor'):canvas._signallab_editable=True
        route=getattr(ancestor,'tool_item',None)
        if route:title=route[0]+' · SignalLab';break
        ancestor=ancestor.parentWidget()
    window=FigureWindow(parent,Qt.WindowType.Window)
    window.setModal(False);window.setWindowTitle(title);window.setWindowIcon(parent.window().windowIcon())
    content=QVBoxLayout(window);content.setContentsMargins(6,6,6,6);content.addWidget(toolbar)
    controls=getattr(canvas,'_signallab_plot_controls',None)
    if controls is not None:content.addWidget(controls)
    content.addWidget(canvas,1)
    editor=getattr(canvas,'_signallab_root_editor',None)
    if editor is not None:editor.install_plot_controls(window,content)
    from PySide6.QtGui import QAction
    detail=QAction('Detalle vertical',toolbar);detail.setCheckable(True);detail.setChecked(bool(getattr(canvas.figure,'_signallab_detail_vertical',False)))
    detail.setToolTip('Ajustar la escala a los valores originales, incluso variaciones muy pequeñas. Desactivado evita amplificar variaciones menores que 10⁻¹⁰ de la referencia visual (al menos 1). No se redondean ni se borran datos. El zoom manual sigue disponible.')
    toolbar.addSeparator();toolbar.addAction(detail);canvas._signallab_detail_action=detail
    vertical_range = QAction('Escala vertical…',toolbar)
    vertical_range.setToolTip('Elegí un panel y ajustá su rango vertical automático, completo o manual.')
    def choose_vertical_range():
        from .plot_limits_dialog import VerticalRangeDialog
        VerticalRangeDialog(canvas,window).exec()
    vertical_range.triggered.connect(choose_vertical_range)
    toolbar.addAction(vertical_range)
    scale_note=QLabel();scale_note.setWordWrap(True);scale_note.setStyleSheet('color:'+C['muted']+';font-size:9pt;');scale_note.hide();content.addWidget(scale_note);canvas._signallab_scale_note=scale_note
    def vertical_detail(enabled):
        from .plot_scale import set_vertical_detail
        set_vertical_detail(canvas.figure,enabled);canvas.draw_idle()
    detail.toggled.connect(vertical_detail)
    canvas.setMinimumSize(0,0);canvas.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
    available=parent.screen().availableGeometry();window.resize(min(1000,available.width()-32),min(700,available.height()-48));window.setMinimumSize(360,280)
    canvas._signallab_window=window;canvas._signallab_launcher=launcher
    from .plot_actions import bind_canvas
    bind_canvas(canvas,parent)
    from .plot_probe import PlotProbe
    PlotProbe(canvas,toolbar,content)
    from .figure_controls import install as install_controls
    install_controls(toolbar,content,canvas)
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
                 if artist is not axis.patch and not getattr(artist,'_signallab_probe',False)]
        canvas._signallab_has_plot_result=bool(artists)
        refresh=getattr(canvas,'_signallab_plot_action_refresh',None)
        if refresh is not None:refresh()
        signature=tuple(id(artist) for artist in artists)
        if artists and signature!=last[0] and not getattr(canvas, '_signallab_explicit_plot', False):
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
        if axis.name=='3d':
            axis.zaxis.set_tick_params(colors=C['muted'],labelsize=9);axis.zaxis.label.set_color(C['text'])
            for coordinate in (axis.xaxis,axis.yaxis,axis.zaxis):
                coordinate.pane.set_facecolor(C['panel']);coordinate.pane.set_edgecolor(C['disabled'])
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
            # Data-mapped colors belong to the color scale, not to the UI palette.
            if collection.get_array() is not None:continue
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
            if any(getattr(axis,'_signallab_db_focused',False) for axis in protected):
                note.setText('Vista en dB enfocada en el paso y los lóbulos. Para ver los nulos profundos, elegí «Escala vertical» y «Rango completo».')
            else:
                note.setText('Escala estable en '+str(len(protected))+' panel(es). Activá «Detalle vertical» para ver pequeñas variaciones.' if protected else '')
            note.setVisible(bool(protected))
        return original_draw(*args,**kwargs)
    def print_figure(*args,**kwargs):
        probe=getattr(canvas,'_signallab_probe',None);state=probe.before_export() if probe is not None else None
        try:
            prepare_figure(canvas.figure)
            return original_print(*args,**kwargs)
        finally:
            if probe is not None:probe.after_export(state)
    canvas.draw=draw;canvas.print_figure=print_figure
