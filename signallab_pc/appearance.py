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
    def recolor_legend(legend):
        for handle in getattr(legend,'legend_handles',[]):
            if hasattr(handle,'get_color'):handle.set_color(remap(handle.get_color()))
            if hasattr(handle,'get_markeredgecolor'):handle.set_markeredgecolor(remap(handle.get_markeredgecolor()))
            if hasattr(handle,'get_markerfacecolor'):handle.set_markerfacecolor(remap(handle.get_markerfacecolor()))
            for channel in ('face','edge'):
                getter=getattr(handle,'get_'+channel+'colors',None)
                if getter is not None:
                    values=getter()
                    if len(values):getattr(handle,'set_'+channel+'color')([remap(value) for value in values])
    for canvas in canvases:
        from matplotlib.text import Text
        from matplotlib.patches import Patch
        for patch in canvas.figure.findobj(match=Patch):patch.set_facecolor(remap(patch.get_facecolor()));patch.set_edgecolor(remap(patch.get_edgecolor()))
        for text in canvas.figure.findobj(match=Text):
            text.set_color(remap(text.get_color()));box=text.get_bbox_patch()
            if box is not None:box.set_facecolor(remap(box.get_facecolor()));box.set_edgecolor(remap(box.get_edgecolor()))
        for axis in canvas.figure.axes:
            for line in axis.lines:
                line.set_color(remap(line.get_color()));line.set_markeredgecolor(remap(line.get_markeredgecolor()));line.set_markerfacecolor(remap(line.get_markerfacecolor()))
            for collection in axis.collections:
                if collection.get_array() is not None:continue
                for channel in ('face','edge'):
                    values=getattr(collection,'get_'+channel+'colors')()
                    if len(values):getattr(collection,'set_'+channel+'color')([remap(v) for v in values])
            for tick in [*axis.xaxis.get_major_ticks(),*axis.xaxis.get_minor_ticks(),*axis.yaxis.get_major_ticks(),*axis.yaxis.get_minor_ticks()]:
                for line in (tick.tick1line,tick.tick2line):line.set_color(remap(line.get_color()));line.set_markeredgecolor(remap(line.get_markeredgecolor()))
            legend=axis.get_legend()
            if legend is not None:recolor_legend(legend)
            for grid in [*axis.get_xgridlines(),*axis.get_ygridlines()]:grid.set_color(COLORS['grid'])
        for legend in canvas.figure.legends:recolor_legend(legend)
        probe=getattr(canvas,'_signallab_probe',None)
        if probe is not None:
            probe.background=None
            for artist in probe.artists:
                line=artist.line;line.set_color(remap(line.get_color()));line.set_markeredgecolor(remap(line.get_markeredgecolor()));line.set_markerfacecolor(remap(line.get_markerfacecolor()))
        toolbar=getattr(canvas,'toolbar',None)
        if toolbar is not None and hasattr(toolbar,'_icon'):
            for text,tip,image,callback in toolbar.toolitems:
                if image and callback in toolbar._actions:toolbar._actions[callback].setIcon(toolbar._icon(image+'.png'))
        if canvas.isVisible():canvas.draw_idle()
    from .design import icon
    if hasattr(window,'calculate_action'):window.calculate_action.setIcon(icon('run',COLORS['on_primary']))
    if hasattr(window,'help'):window.help.setIcon(icon('book',COLORS['green']))
    for widget in window.findChildren(QWidget):
        if widget.__class__.__module__.endswith('pole_zero_editor') and hasattr(widget,'refresh_cursor'):widget.refresh_cursor()
    from .design import refresh_icons
    refresh_icons(app)
    if hasattr(window,'navigation_rail'):window.navigation_rail.refresh_theme()
    for widget in app.allWidgets():
        if widget.__class__.__module__.endswith('tool_browser') and hasattr(widget,'refresh_theme'):widget.refresh_theme()
        if widget.__class__.__module__.endswith('wallpaper'):widget.update()
    from .wallpaper import refresh
    refresh(window)
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
        action.triggered.connect(lambda checked=False,value=key:choose(window,value));window.theme_actions[key]=action
    menu.addSeparator();menu.addAction('Configurar tema personalizado…',lambda:configure_custom(window))
    window.theme_action_group=group


def configure_custom(window):
    from .theme_custom_dialog import configure
    configure(window)


def choose(window,key):
    if key=='custom' and not theme_presets.HAS_CUSTOM:configure_custom(window)
    else:apply(window,key)
