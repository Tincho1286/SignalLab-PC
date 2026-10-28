from pathlib import Path
"""Lenguaje visual y presentaciÃƒÆ’Ã‚Â³n de tareas para SignalLab Studio."""
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPalette, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QPushButton, QFormLayout
import matplotlib as mpl
from .theme_tokens import COLORS as C


def action_title(button):return button.property('actionTitle') or button.text()

def configure_theme():
    app = QApplication.instance()
    app.setStyle('Fusion')
    palette = QPalette()
    for role, color in {'Window':'#10151e','WindowText':'#e5eaf2','Base':'#111722',
        'AlternateBase':'#19212e','Text':'#e5eaf2','Button':'#1c2635','ButtonText':'#e5eaf2',
        'Highlight':'#315e80','HighlightedText':'#ffffff','ToolTipBase':'#222e40','ToolTipText':'#ffffff'}.items():
        palette.setColor(getattr(QPalette.ColorRole,role), QColor(color))
    app.setPalette(palette)
    mpl.rcParams.update({'figure.facecolor':'#171e29','axes.facecolor':'#171e29',
        'axes.edgecolor':'#354253','axes.labelcolor':'#91a0b5','text.color':'#e5eaf2',
        'xtick.color':'#91a0b5','ytick.color':'#91a0b5','grid.color':'#354253',
        'axes.spines.top':False,'axes.spines.right':False,'font.size':9,
        'savefig.facecolor':'#171e29','axes.prop_cycle':mpl.cycler(color=['#55d6c2','#8b9cfa','#efb56c','#ec819c'])})


def icon(kind, color=None):
    if color is None:color=C['muted']
    paths = {
        'run':'M8 5l12 7-12 7z',
        'search':'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0 M15 15l6 6',
        'calculator':'M5 2h14v20H5z M8 5h8v4H8z M8 13h1 M12 13h1 M16 13h1 M8 17h1 M12 17h1 M16 17h1',
        'home':'M3 11l9-8 9 8 M6 10v11h12V10 M10 21v-7h4v7',
        'wave':'M2 12h3l3-8 5 16 3-8h6',
        'chart':'M3 3v18h18 M6 15l4-6 4 3 6-8',
        'table':'M3 4h18v16H3z M3 9h18 M9 4v16 M15 4v16',
        'filter':'M3 5h18 M6 12h12 M10 19h4 M7 3v4 M16 10v4 M12 17v4',
        'sample':'M3 19V9 M9 19V4 M15 19V12 M21 19V7',
        'fourier':'M3 19h18 M6 18v-4 M10 18V5 M14 18V9 M18 18v-6',
        'math':'M8 5H4v14h4 M16 5h4v14h-4 M10 9l4 6 M14 9l-4 6',
        'book':'M12 5v15 M12 5C8 2 4 3 2 4v15c4-2 7-1 10 1 M12 5c4-3 8-2 10-1v15c-4-2-7-1-10 1',
        'folder':'M3 6h7l2 3h9v11H3z',
    }
    paths.update({'signal': 'M2 12h3l3-8 5 16 3-8h6', 'measure': 'M4 20V9h4v11 M10 20V4h4v16 M16 20v-7h4v7', 'convolution': 'M2 18l5-12 5 12 M12 18l5-12 5 12', 'correlation': 'M3 7h10l-3-3 M13 7l-3 3 M21 17H11l3-3 M11 17l3 3', 'spectrum': 'M3 20h18 M5 17v-5 M9 17V4 M13 17V8 M17 17v-3', 'harmonics': 'M3 18V7 M8 18V4 M13 18V9 M18 18v-5 M2 20h20', 'density': 'M3 20V4 M3 20h18 M5 18l4-12 4 4 3 7 4 1 M9 6v12 M13 10v8', 'blocks': 'M2 7h7v10H2z M15 7h7v10h-7z M9 12h6', 'response': 'M2 18h4V6h6c4 0 1 12 10 6', 'design': 'M3 18h4L9 6h7l2 12h3 M5 3v4 M19 3v4', 'convert': 'M4 7h15l-4-4 M19 7l-4 4 M20 17H5l4-4 M5 17l4 4', 'states': 'M3 3h6v6H3z M15 3h6v6h-6z M3 15h6v6H3z M15 15h6v6h-6z M9 6h6 M6 9v6 M18 9v6 M9 18h6', 'sampling': 'M3 19V9 M9 19V4 M15 19V12 M21 19V7', 'rate': 'M2 18V6 M7 18v-8 M12 18V4 M17 18v-8 M22 18V6 M2 21h20', 'quantize': 'M2 19h5v-5h5V9h5V4h5', 'laplace': 'M5 3v17h14 M11 4h8 M15 4v9 M11 13h8', 'zplane': 'M12 2v20 M2 12h20 M6 6h12L6 18h12', 'random': 'M2 14l3-8 3 13 3-16 3 12 3-7 3 10 2-5'})
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="{paths.get(kind,paths["wave"])}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    pixmap=QPixmap(24,24);pixmap.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pixmap);QSvgRenderer(QByteArray(svg.encode())).render(painter);painter.end()
    return QIcon(pixmap)


def install_tasks(form, tasks, common=()):
    """Mantener visibles sÃƒÆ’Ã‚Â³lo los controles necesarios para la tarea elegida.

    Cada tarea contiene nombre, descripciÃƒÆ’Ã‚Â³n, campos y textos de botones.
    Los widgets conservan sus conexiones y valores al cambiar de tarea.
    """
    rows=[]
    for row in range(form.rowCount()):
        widgets=[]
        for role in (QFormLayout.ItemRole.LabelRole,QFormLayout.ItemRole.FieldRole,QFormLayout.ItemRole.SpanningRole):
            item=form.itemAt(row,role)
            if item and item.widget() and item.widget() not in widgets:widgets.append(item.widget())
        rows.append((row,widgets))
    selector=QComboBox();selector.setObjectName('taskSelector');selector.addItems([task[0] for task in tasks])
    description=QLabel();description.setWordWrap(True);description.setObjectName('taskDescription')
    form.insertRow(0,selector);form.insertRow(1,description)
    def select(index):
        _, text, fields, actions=tasks[index]
        description.setText(text)
        primary=next((title for title in actions if not title.startswith(('Guardar','Cargar','Exportar','Leer','Usar'))),None)
        for row,widgets in rows:
            visible=any(widget in fields or widget in common or (isinstance(widget,QPushButton) and " ".join(action_title(widget).split()) in actions) for widget in widgets)
            form.setRowVisible(row+2,visible)
            for widget in widgets:
                if isinstance(widget,QPushButton):
                    widget.setProperty('primaryAction',visible and " ".join(action_title(widget).split())==primary)
                    widget.style().unpolish(widget);widget.style().polish(widget)
        parent=form.parentWidget()
        if parent:parent.adjustSize();parent.updateGeometry()
    selector.currentIndexChanged.connect(select);select(0)
    return selector


STYLE = '''
QWidget { color:#dce4ef; font-family:'Segoe UI'; font-size:10pt; }
QMainWindow, QWidget#appRoot, QWidget#workspace { background:#10151e; }
QWidget#sidebar { background:#141b26; border-right:1px solid #263141; }
QLabel { background:transparent; border:none; }
QLabel#brand { color:#f0f5fb; font-size:20pt; font-weight:700; }
QLabel#eyebrow { color:#667b97; font-size:8pt; font-weight:600; letter-spacing:1px; }
QLabel#pageTitle { font-size:23pt; font-weight:600; color:#eff4fc; }
QLabel#muted, QLabel#taskDescription { color:#8d9cb1; }
QLabel#taskDescription { padding:3px 0 14px; }
QLabel#badge { color:#6dd9c4; background:#1a3436; border:1px solid #284b4b; border-radius:13px; padding:6px 12px; font-size:9pt; }
QLabel#cardTitle { font-size:13pt; font-weight:600; color:#edf3fb; }
QLabel#loadedSignal { color:#b7c5d8; background:#1a2432; border:1px solid #29374a; border-radius:12px; padding:14px; }
QLabel#summary { color:#91a0b5; padding:6px 0; }
QFrame#card, QWidget#card { background:#171e29; border:1px solid #283343; border-radius:14px; }
QPushButton { background:#202b3b; border:1px solid #314056; border-radius:8px; padding:8px 13px; color:#d9e3f1; }
QPushButton:hover { background:#2a384b; border-color:#4b627d; }
QPushButton:pressed { background:#354b62; }
QPushButton:disabled { background:#1a2230; color:#56667b; border-color:#273344; }
QPushButton#primary, QPushButton[primaryAction="true"] { background:#53cbb6; border:1px solid #53cbb6; color:#0d2425; font-weight:600; }
QPushButton#primary:hover, QPushButton[primaryAction="true"]:hover { background:#78e1cd; }
QPushButton#navButton { background:transparent; border:none; text-align:left; padding:10px 14px; color:#93a4bb; border-radius:8px; }
QPushButton#navButton:hover { background:#1c2838; color:#e7effa; }
QPushButton#navButton:checked { background:#223747; color:#77e3ce; font-weight:600; }
QPushButton#chip { padding:5px 10px; background:#202a39; color:#9aacc4; border-color:#303e51; border-radius:7px; font-size:9pt; }
QLineEdit, QComboBox { background:#111823; border:1px solid #314055; border-radius:7px; padding:8px 10px; selection-background-color:#315e80; }
QLineEdit:focus, QComboBox:focus { border-color:#53cbb6; background:#141e2b; }
QLineEdit:disabled, QComboBox:disabled { color:#55667c; border-color:#253043; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox QAbstractItemView { background:#202c3d; color:#e4edf8; border:1px solid #3a4c65; selection-background-color:#315e80; padding:5px; }
QComboBox#taskSelector { background:#233247; color:#dbe9fb; border-color:#3b506c; font-weight:600; padding:10px; }
QGroupBox { background:#171e29; border:1px solid #283343; border-radius:12px; margin-top:16px; padding:18px; font-weight:600; }
QGroupBox::title { subcontrol-origin:margin; left:18px; padding:0 6px; color:#c6d4e6; }
QScrollArea { background:transparent; border:none; }
QScrollArea > QWidget > QWidget { background:transparent; }
QScrollBar:vertical { background:transparent; width:8px; margin:2px; }
QScrollBar::handle:vertical { background:#344458; min-height:32px; border-radius:3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:transparent; }
QScrollBar:horizontal { background:transparent; height:8px; }
QScrollBar::handle:horizontal { background:#344458; min-width:30px; border-radius:3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
QTabWidget::pane { border:none; background:transparent; padding-top:10px; }
QTabBar::tab { background:transparent; color:#8194ae; border:none; padding:9px 17px; margin-right:4px; border-bottom:2px solid transparent; }
QTabBar::tab:selected { color:#65d8c2; border-bottom:2px solid #53cbb6; }
QTabBar::tab:hover { color:#c4d5ec; }
QTableWidget, QTreeWidget, QListWidget, QPlainTextEdit { background:#151e2b; color:#b7c8dc; border:1px solid #2a384a; border-radius:10px; padding:8px; selection-background-color:#29465c; alternate-background-color:#1a2636; }
QHeaderView::section { background:#202d3e; color:#96afcd; border:none; padding:10px; }
QListWidget::item { padding:10px; border-radius:6px; }
QListWidget::item:selected { background:#284656; color:#8ee9d5; }
QToolBar { background:transparent; border:none; spacing:8px; }
QToolButton { background:transparent; border:none; border-radius:6px; padding:5px; }
QToolButton:hover { background:#2b3a50; }
QStatusBar { background:#10151e; color:#71849d; border-top:1px solid #202c3e; font-size:9pt; }
QSplitter::handle { background:#283547; width:1px; }
QCheckBox { spacing:8px; color:#aabbd0; }
QToolTip { background:#24344a; color:#e8f1fc; border:1px solid #3a526e; padding:8px; }
'''

STYLE += "QComboBox::down-arrow { image: url(\"" + (Path(__file__).parent / "assets" / "chevron.svg").as_posix() + "\"); width:16px; height:16px; }"

STYLE += """
QPushButton#choice { background:#182331; border:1px solid #304458; padding:9px 15px; border-radius:10px; }
QPushButton#choice:checked { background:#234b4c; border-color:#53cbb6; color:#93f0dd; }
QComboBox QAbstractItemView::item { min-height:34px; padding:6px 12px; }
"""

STYLE += "QPushButton#toolTile { text-align:left; padding:22px; min-height:44px; background:#192432; border:1px solid #2d3d50; border-radius:12px; font-size:12pt; } QPushButton#toolTile:hover { background:#233847; border-color:#53cbb6; }"

STYLE += "QTextBrowser#resultReport { background:#151e2b; border:1px solid #2a384a; border-radius:10px; padding:10px; selection-background-color:#29465c; }"

STYLE += "QLabel#pageTitle { font-size:17pt; } QPushButton#toolTile { padding:10px 14px; border-radius:4px; font-size:10pt; min-height:26px; } QGroupBox { border-radius:4px; padding:10px; } QLineEdit, QComboBox, QPushButton { border-radius:4px; } QTabWidget::pane { border:1px solid #293646; }"
