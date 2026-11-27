"""The shared detached workspace for scientific figures."""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLayout, QMenu, QSizePolicy, QSplitter, QToolButton, QVBoxLayout, QWidget
from .design import icon
from .theme_tokens import COLORS as C
from .window_fit import WatchWorkArea, fit_window
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

class FigureWindow(QDialog):
    """Persistent non-modal figure; closing hides it without discarding the data."""
    def __init__(self, parent, canvas, title):
        super().__init__(parent, Qt.WindowType.Window)
        self.setObjectName('scientificFigure')
        self.canvas = canvas
        self._figure_label = ''
        self._siblings = ()
        self.inspector = None
        self.inspector_requested = False
        self.inspector_sizes = {}
        self._short_screen = False
        self.setModal(False)
        self.setWindowTitle(title)
        self.setWindowIcon(parent.window().windowIcon())

        root = QVBoxLayout(self)
        root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        root.setContentsMargins(11, 9, 11, 9)
        root.setSpacing(7)
        header = QWidget()
        row = QHBoxLayout(header)
        row.setContentsMargins(3, 0, 0, 0)
        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(1)
        self.heading = QLabel()
        self.heading.setObjectName('figureHeading')
        self.heading.setWordWrap(True)
        titles.addWidget(self.heading)
        self.origin = QLabel()
        self.origin.setObjectName('figureOrigin')
        self.origin.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        titles.addWidget(self.origin)
        row.addLayout(titles, 1)

        self.alternatives = QToolButton()
        self.alternatives.setObjectName('figureAlternatives')
        self.alternatives.setText('Cambiar figura')
        self.alternatives.setIcon(icon('chart'))
        self.alternatives.setIconSize(QSize(17, 17))
        self.alternatives.setAccessibleName('Cambiar a otra figura del resultado')
        self.alternatives.setToolTip('Cambiar a otra figura del mismo resultado')
        self.alternatives.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.alternatives.setMenu(QMenu(self.alternatives))
        self.alternatives.hide()
        row.addWidget(self.alternatives)

        self.controls_action = QToolButton()
        self.controls_action.setObjectName('figureCompactControls')
        self.controls_action.setText('Controles')
        self.controls_action.setIcon(icon('filter'))
        self.controls_action.setIconSize(QSize(17, 17))
        self.controls_action.setCheckable(True)
        self.controls_action.setAccessibleName('Mostrar u ocultar los controles del gráfico')
        self.controls_action.setToolTip('Mostrar u ocultar la barra y las opciones de la figura')
        self.controls_action.toggled.connect(self.update_inspector)
        self.controls_action.hide()
        row.addWidget(self.controls_action)

        self.focus_action = QToolButton()
        self.focus_action.setObjectName('figureFocus')
        self.focus_action.setIconSize(QSize(17, 17))
        self.focus_action.setCheckable(True)
        self.focus_action.toggled.connect(self.set_focus_mode)
        row.addWidget(self.focus_action)
        root.addWidget(header)

        self.tools, self.tools_layout = self.section('figureTools')
        root.addWidget(self.tools)
        self.options, self.options_layout = self.section('figureOptions')
        root.addWidget(self.options)
        self.body = QSplitter()
        self.body.setObjectName('figureSplit')
        self.body.setChildrenCollapsible(False)
        self.body.setHandleWidth(10)
        root.addWidget(self.body, 1)
        chart, chart_layout = self.section('figureChart')
        chart.setMinimumSize(0, 0)
        self.body.addWidget(chart)
        canvas_frame = QFrame()
        canvas_frame.setObjectName('figureCanvasFrame')
        canvas_layout = QVBoxLayout(canvas_frame)
        canvas_layout.setContentsMargins(1, 1, 1, 1)
        canvas_layout.addWidget(canvas)
        chart_layout.addWidget(canvas_frame, 1)
        self.readouts, self.readout_layout = self.section('figureReadouts')
        chart_layout.addWidget(self.readouts)

        shortcut = QAction(self)
        shortcut.setShortcut(QKeySequence('F11'))
        shortcut.triggered.connect(lambda: self.focus_action.toggle())
        self.addAction(shortcut)
        self.windowTitleChanged.connect(self.update_heading)
        self.update_heading()
        self.set_focus_mode(False)
        self._work_area_watch = WatchWorkArea(self, self._fit_to_screen)

    @staticmethod
    def section(name):
        panel = QWidget()
        panel.setObjectName(name)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        return panel, layout

    def update_heading(self, *_):
        source = self.windowTitle().removesuffix(' · SignalLab')
        figure = self._figure_label if self._figure_label not in ('', 'Resultado') else source
        self.heading.setText(figure)
        self.origin.setText(source)
        self.origin.setToolTip(source)
        self.origin.setVisible(source != figure)

    def set_figure_choices(self, choices, select):
        options = tuple((entry[0], label, current) for entry, label, current in choices)
        if options == self._siblings:
            return
        self._siblings = options
        menu = self.alternatives.menu()
        menu.clear()
        for entry, label, current in choices:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(current)
            action.setEnabled(not current)
            if current:
                self._figure_label = label
            action.triggered.connect(lambda checked=False, item=entry: select(item))
        if not any(current for _, _, current in choices):
            self._figure_label = ''
        self.update_heading()
        self.alternatives.setVisible(len(choices) > 1)

    def set_focus_mode(self, enabled):
        self.update_inspector()
        title = 'Mostrar controles' if enabled else 'Solo figura'
        self.focus_action.setText(title)
        self.focus_action.setIcon(icon('restore' if enabled else 'expand'))
        self.focus_action.setAccessibleName(title)
        self.focus_action.setToolTip(title + ' · F11')
        self.canvas.draw_idle()

    def attach_inspector(self, panel):
        panel.hide()
        self.inspector = panel
        self.body.addWidget(panel)

    def show_inspector(self, visible):
        self.inspector_requested = visible
        self.update_inspector()

    def remember_inspector_size(self):
        sizes = self.body.sizes()
        if len(sizes) == 2 and all(sizes):
            self.inspector_sizes[self.body.orientation()] = sizes

    def update_inspector(self):
        focused = self.focus_action.isChecked()
        visible = self.inspector is not None and self.inspector_requested and not focused
        orientation = Qt.Orientation.Horizontal if self.width() >= 955 else Qt.Orientation.Vertical
        compact = visible and orientation == Qt.Orientation.Vertical
        self.canvas.figure._signallab_compact_labels = compact
        hide_controls = compact or self._short_screen
        self.controls_action.setVisible(not focused and hide_controls)
        show_controls = not focused and (not hide_controls or self.controls_action.isChecked())
        self.tools.setVisible(show_controls)
        self.options.setVisible(show_controls)
        self.readouts.setVisible(not focused and (not self._short_screen or show_controls))
        if self.inspector is None:
            return
        orientation_changed = self.body.orientation() != orientation
        if not self.inspector.isHidden() and (orientation_changed or not visible):
            self.remember_inspector_size()
        self.body.setOrientation(orientation)
        if visible and (self.inspector.isHidden() or orientation_changed):
            self.inspector.show()
            sizes = self.inspector_sizes.get(orientation)
            if sizes is None:
                span = self.body.width() if orientation == Qt.Orientation.Horizontal else self.body.height()
                chart = round(span * (.62 if orientation == Qt.Orientation.Horizontal else .60))
                sizes = [chart, span - chart]
            self.body.setSizes(sizes)
        elif not visible:
            self.inspector.hide()
        self.canvas._signallab_probe.dock_readings(self.inspector if visible else None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        style = (Qt.ToolButtonStyle.ToolButtonIconOnly if self.width() < 550
                 else Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.alternatives.setToolButtonStyle(style)
        self.focus_action.setToolButtonStyle(style)
        self.controls_action.setToolButtonStyle(style)
        self.update_inspector()

    def _fit_to_screen(self):
        self._short_screen = self.screen().availableGeometry().height() < 440
        self.update_inspector()
        fit_window(self, QSize(360, 280))

    def closeEvent(self,event):
        self.hide();event.ignore()


def enlarge_plot(canvas,owner):
    window=getattr(canvas,'_signallab_window',None)
    if window is not None:
        launcher=getattr(canvas,'_signallab_plot_action_scope',None)
        from .plot_actions import PlotLauncher
        if isinstance(launcher, PlotLauncher):
            launcher.sync_window(canvas)
        window._fit_to_screen()
        window.show()
        window._fit_to_screen()
        window.raise_();window.activateWindow();canvas.draw_idle()
    return window


def hide_plot(canvas):
    window = getattr(canvas, '_signallab_window', None)
    if window is not None:
        window.hide()


def ensure_figure_window(canvas):
    if getattr(canvas, '_signallab_window', None) is None:
        for toolbar in canvas.parentWidget().findChildren(NavigationToolbar2QT):
            if toolbar.canvas is canvas:
                install_enlarge(toolbar)
                break


def open_result_plot(view, owner):
    canvas = view.canvas
    ensure_figure_window(canvas)
    view.views.setCurrentIndex(0)
    canvas.draw()
    enlarge_plot(canvas, owner)


def install_enlarge(toolbar, *, standalone=False):
    from PySide6.QtCore import Qt,QTimer
    from PySide6.QtWidgets import QWidget,QLabel,QMenu,QSizePolicy,QToolButton
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
    window=FigureWindow(parent,canvas,title)
    window.tools_layout.addWidget(toolbar)
    controls=getattr(canvas,'_signallab_plot_controls',None)
    if controls is not None:window.options_layout.addWidget(controls)
    editor=getattr(canvas,'_signallab_root_editor',None)
    if editor is not None:editor.install_plot_controls(window,window.options_layout)
    detail=QAction('Detalle vertical',toolbar);detail.setCheckable(True);detail.setChecked(bool(getattr(canvas.figure,'_signallab_detail_vertical',False)))
    detail.setToolTip('Mostrar variaciones pequeñas en la escala automática.')
    canvas._signallab_detail_action=detail
    scale = QToolButton()
    scale.setObjectName('figureScale')
    scale.setProperty('figureControl', True)
    scale.setText('Escala vertical')
    scale.setToolTip('Detalle de redondeo y rango vertical de los paneles')
    scale.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    menu = QMenu(scale)
    scale.setMenu(menu)
    menu.addAction(detail)
    vertical_range = menu.addAction('Ajustar rango…')
    vertical_range.setToolTip('Elegí un panel y ajustá su rango vertical automático, completo o manual.')
    def choose_vertical_range():
        from .plot_limits_dialog import VerticalRangeDialog
        VerticalRangeDialog(canvas,window).exec()
    vertical_range.triggered.connect(choose_vertical_range)
    toolbar.addWidget(scale)
    scale_note=QLabel();scale_note.setWordWrap(True);scale_note.setObjectName('figureOrigin');scale_note.hide();window.readout_layout.addWidget(scale_note);canvas._signallab_scale_note=scale_note
    def vertical_detail(enabled):
        from .plot_scale import set_vertical_detail
        set_vertical_detail(canvas.figure,enabled);canvas.draw_idle()
    detail.toggled.connect(vertical_detail)
    canvas.setMinimumSize(0,0);canvas.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
    available=parent.screen().availableGeometry();window.resize(min(1000,available.width()-32),min(700,available.height()-48))
    canvas._signallab_window=window;canvas._signallab_launcher=launcher
    if not standalone:
        from .plot_actions import bind_canvas
        bind_canvas(canvas,parent)
    from .plot_probe import PlotProbe
    PlotProbe(canvas,toolbar,window.readout_layout)
    from .figure_controls import install as install_controls
    install_controls(toolbar,window.tools_layout,canvas)
    install_figure_layout(canvas)
    original_draw=canvas.draw
    original_draw_idle=canvas.draw_idle
    last=[None];pending=[False]
    def open_result():
        pending[0]=False
        if not window.isVisible():enlarge_plot(canvas, parent)
    def refresh_result():
        # New plot objects identify a new result; repainting/zooming a closed
        # figure must not reopen it. An empty placeholder is not a result.
        artists=[artist for axis in canvas.figure.axes for artist in [*axis.lines,*axis.collections,*axis.images,*axis.patches]
                 if artist is not axis.patch and not getattr(artist,'_signallab_probe',False)]
        ready=bool(artists)
        if ready != getattr(canvas,'_signallab_has_plot_result',None):
            canvas._signallab_has_plot_result=ready
            refresh=getattr(canvas,'_signallab_plot_action_refresh',None)
            if refresh is not None:refresh()
        signature=tuple(id(artist) for artist in artists)
        if artists and signature!=last[0] and not getattr(canvas, '_signallab_explicit_plot', False):
            last[0]=signature
            if not pending[0]:pending[0]=True;QTimer.singleShot(0,window,open_result)
    def draw(*args,**kwargs):
        # Qt may have queued a draw while this canvas still belonged to the page.
        if getattr(canvas,'_is_idle_drawing',False) and not window.isVisible():
            refresh_result()
            return
        result=original_draw(*args,**kwargs)
        refresh_result()
        return result
    def draw_idle():
        if window.isVisible():
            original_draw_idle()
        else:
            # Hidden figures only need to report availability. Qt draws them
            # at their actual viewport size when the user opens the window.
            refresh_result()
    canvas.draw=draw
    canvas.draw_idle=draw_idle
    refresh_result()



def legend_layout(figure, labels):
    import textwrap
    width, height = figure.get_size_inches()
    wrapped = [textwrap.fill(label, 30, break_long_words=False) for label in labels]
    longest = max((len(line) for label in wrapped for line in label.splitlines()), default=1)
    columns = max(1, min(3, len(labels), int(width / (0.062 * longest + 0.60))))
    rows = (len(labels) + columns - 1) // columns
    line_count = max((label.count('\n') + 1 for label in wrapped), default=1)
    legend_height = rows * (line_count * .14 + .12) + .25
    if width < 8.2 and height - legend_height >= 2.05 and legend_height < height / 3:
        return wrapped, 'outside lower center', columns
    return wrapped, 'outside right upper', 1


def prepare_figure(figure):
    """Keep references out of the plotting area when drawing or exporting."""
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
            if label not in seen:handles.append(handle);labels.append(label);seen.add(label)
    if previous is not None and previous in figure.legends:previous.remove()
    if handles and needs_legend:
        wrapped, location, columns = legend_layout(figure, labels)
        figure._signallab_legend_below = location == 'outside lower center'
        figure._signallab_legend=figure.legend(handles,wrapped,loc=location,ncols=columns,fontsize=8,frameon=False,title='Referencias',title_fontsize=9,labelcolor=C['text'],borderaxespad=.8)
        figure._signallab_legend.get_title().set_color(C['text'])
    else:figure._signallab_legend=None
    # Constrained layout calcula márgenes con títulos, unidades y leyenda al tamaño real.
    figure.set_layout_engine('constrained',w_pad=.09,h_pad=.09,hspace=.12,wspace=.08)
    from .plot_scale import apply_stable_scale
    return apply_stable_scale(figure)


def fit_axis_labels(canvas):
    """Keep labels vertical and adapt their size to the height of each row."""
    renderer = canvas.get_renderer()
    figure = canvas.figure
    compact = getattr(figure, '_signallab_compact_labels', False)
    legend = getattr(figure, '_signallab_legend', None)
    reference_height = legend.get_window_extent(renderer).height if legend is not None and getattr(figure, '_signallab_legend_below', False) else 0
    for axis in canvas.figure.axes:
        spec = axis.get_subplotspec()
        if spec is None or axis.name != 'rectilinear':
            continue
        label = axis.yaxis.label
        if not label.get_text() or label.get_rotation() not in (90, 270):
            continue
        from .signal_plot import vertical_axis_name
        text = vertical_axis_name(axis)
        label.set_text(text)
        current = label.get_fontsize()
        nominal, fitted = getattr(label, '_signallab_label_size', (current, current))
        if current != fitted:
            nominal = current
        label.set_fontsize(nominal)
        rows = spec.get_gridspec().nrows
        row_height = (figure.bbox.height - reference_height) * len(spec.rowspan) / rows
        available = row_height - min(32, max(12, row_height * .26))
        length = label.get_window_extent(renderer).height
        words = text.split()
        if compact and rows > 1 and length > available and len(words) > 1 and '\n' not in text and '$' not in text:
            # A second line keeps the full scientific label legible in short panes.
            splits = [(' '.join(words[:i]), ' '.join(words[i:])) for i in range(1, len(words))]
            label.set_text('\n'.join(min(splits, key=lambda pair: max(map(len, pair)))))
            length = label.get_window_extent(renderer).height
        floor = min(7, nominal)
        fitted = max(floor, nominal * available / length) if rows > 1 and length > available and length else nominal
        label.set_fontsize(fitted)
        label._signallab_label_size = nominal, fitted
        label._signallab_axis_text = text, label.get_text()


def install_figure_layout(canvas):
    if getattr(canvas,'_signallab_layout',False):return
    canvas._signallab_layout=True
    original_draw=canvas.draw;original_print=canvas.print_figure
    def draw(*args,**kwargs):
        window = getattr(canvas, '_signallab_window', None)
        if window is not None and not window.isVisible() and min(canvas.width(), canvas.height()) < 32:
            # Qt can deliver an idle repaint after the detached viewport has collapsed.
            return
        protected=prepare_figure(canvas.figure)
        fit_axis_labels(canvas)
        note=getattr(canvas,'_signallab_scale_note',None)
        if note is not None:
            if any(getattr(axis,'_signallab_db_focused',False) for axis in protected):
                note.setText('dB enfocados en paso y lóbulos. Para ver los nulos, elegí Rango completo.')
            else:
                note.setText('Para ver variaciones pequeñas, activá Detalle vertical.' if protected else '')
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
