"""Apply a palette to existing views without recalculating or replacing data."""
from PySide6.QtWidgets import QApplication,QWidget
from .theme_tokens import COLORS
from . import theme_presets


def apply(window,key,*,persist=True):
    previous=dict(COLORS);key=theme_presets.select(key)
    from .desktop_theme import configure_desktop,desktop_style
    configure_desktop();app=QApplication.instance();style=desktop_style();app.setStyleSheet(style)
    from .report_view import ReportView
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.colors import to_hex,to_rgba
    figures=set();canvases=[]
    for widget in app.allWidgets():
        stylesheet=widget.styleSheet()
        if stylesheet:widget.setStyleSheet(theme_presets.recolor(stylesheet,previous))
        if isinstance(widget,ReportView):widget.refresh_theme(previous)
        if isinstance(widget,FigureCanvasQTAgg) and id(widget.figure) not in figures:
            figures.add(id(widget.figure));canvases.append(widget)
    window.setStyleSheet(style)
    def remap(value):
        try:
            rgba=to_rgba(value);return to_rgba(theme_presets.color(to_hex(rgba),previous),rgba[3])
        except (ValueError,TypeError):return value
    for canvas in canvases:
        for axis in canvas.figure.axes:
            for line in axis.lines:
                line.set_color(remap(line.get_color()));line.set_markeredgecolor(remap(line.get_markeredgecolor()));line.set_markerfacecolor(remap(line.get_markerfacecolor()))
            for collection in axis.collections:
                if collection.get_array() is not None:continue
                for channel in ('face','edge'):
                    values=getattr(collection,'get_'+channel+'colors')()
                    if len(values):getattr(collection,'set_'+channel+'color')([remap(v) for v in values])
            for patch in axis.patches:
                patch.set_facecolor(remap(patch.get_facecolor()));patch.set_edgecolor(remap(patch.get_edgecolor()))
            for grid in [*axis.get_xgridlines(),*axis.get_ygridlines()]:grid.set_color(COLORS['grid'])
        probe=getattr(canvas,'_signallab_probe',None)
        if probe is not None:
            probe.background=None
            for artist in probe.artists:
                line=artist.line;line.set_color(remap(line.get_color()));line.set_markeredgecolor(remap(line.get_markeredgecolor()));line.set_markerfacecolor(remap(line.get_markerfacecolor()))
        canvas.draw_idle()
    from .design import icon
    if hasattr(window,'calculate_action'):window.calculate_action.setIcon(icon('run',COLORS['on_primary']))
    if hasattr(window,'help'):window.help.setIcon(icon('book',COLORS['green']))
    for widget in window.findChildren(QWidget):
        if widget.__class__.__module__.endswith('pole_zero_editor') and hasattr(widget,'refresh_cursor'):widget.refresh_cursor()
    if persist:
        from PySide6.QtCore import QSettings
        QSettings('SignalLab','Desktop071').setValue('appearance/theme',key)
    actions=getattr(window,'theme_actions',{})
    for name,action in actions.items():action.setChecked(name==key)


def install_menu(window,menu):
    from PySide6.QtGui import QActionGroup
    group=QActionGroup(window);group.setExclusive(True);window.theme_actions={}
    for key,(name,_) in theme_presets.PRESETS.items():
        action=menu.addAction(name);action.setCheckable(True);action.setChecked(key==theme_presets.CURRENT);group.addAction(action)
        action.triggered.connect(lambda checked=False,value=key:apply(window,value));window.theme_actions[key]=action
    window.theme_action_group=group
