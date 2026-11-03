"""A dark scientific desktop with restrained accents and clear working surfaces."""
from pathlib import Path
from PySide6.QtGui import QPalette,QColor
from PySide6.QtWidgets import QApplication
import matplotlib as mpl
from .theme_tokens import COLORS as C,colorize


def configure_desktop():
    palette=QPalette()
    roles={'Window':'window','WindowText':'text','Base':'input','AlternateBase':'panel',
        'Text':'text','Button':'panel','ButtonText':'text','Highlight':'selected',
        'HighlightedText':'text','ToolTipBase':'panel','ToolTipText':'text',
        'Light':'border','Midlight':'rule','Mid':'border','Dark':'input','Shadow':'input',
        'Link':'accent','PlaceholderText':'muted'}
    for role,key in roles.items():palette.setColor(getattr(QPalette.ColorRole,role),QColor(C[key]))
    for role in ('WindowText','Text','ButtonText'):
        palette.setColor(QPalette.ColorGroup.Disabled,getattr(QPalette.ColorRole,role),QColor(C['disabled']))
    QApplication.instance().setPalette(palette)
    mpl.rcParams.update({'figure.facecolor':C['report'],'axes.facecolor':C['panel'],
        'savefig.facecolor':C['report'],'axes.edgecolor':C['disabled'],
        'axes.labelcolor':C['text'],'text.color':C['text'],'xtick.color':C['muted'],
        'ytick.color':C['muted'],'grid.color':C['grid'],'axes.spines.top':True,
        'axes.spines.right':True,'font.size':9,'mathtext.fontset':'stix',
        'legend.facecolor':C['report'],'legend.edgecolor':C['border'],
        'axes.prop_cycle':mpl.cycler(color=[C[k] for k in ('blue','amber','green','purple','red')])})


DESKTOP_STYLE = colorize("""
QWidget {font-family:'Segoe UI';font-size:9pt;color:@text@;}
QMainWindow,QWidget#desktop {background:@window@;}
QLabel {background:transparent;border:0;}
QLabel#muted,QLabel#taskDescription {color:@muted@;}
QLabel#pageTitle {font-size:14pt;font-weight:600;color:@text@;}
QWidget#documentHeading {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 @chrome@,stop:1 @panel@);border-bottom:1px solid @rule@;}
QWidget#explorerPanel {background:@chrome@;}
QLabel#brand {font-size:15pt;font-weight:600;color:@text@;}
QLabel#brandCaption {font-size:7pt;color:@green@;}
QToolBar,QMenuBar {background:@chrome@;border:0;spacing:4px;padding:4px;}
QToolBar {border-bottom:1px solid @rule@;}
QToolBar#mainToolbar {padding:5px 10px;spacing:5px;}
QMenuBar::item {padding:4px 8px;border-radius:5px;}
QMenu {background:@panel@;border:1px solid @border@;border-radius:9px;padding:5px;}
QMenu::item {padding:7px 24px 7px 12px;border-radius:5px;}
QMenu::item:selected,QMenuBar::item:selected {background:@selected@;color:@text@;}
QMenu::separator {height:1px;background:@border@;margin:5px 8px;}
QToolButton {background:transparent;border:1px solid transparent;border-radius:8px;padding:5px 7px;}
QToolButton:hover {background:@hover@;border-color:@border@;}
QToolButton:focus,QPushButton:focus {border-color:@accent@;}
QToolButton#contextHelp {background:@panel@;border:1px solid @border@;color:@green@;padding:7px 10px;}
QPushButton {background:@panel@;border:1px solid @border@;border-radius:9px;padding:6px 11px;}
QPushButton:hover {background:@hover@;border-color:#5d7ba3;}
QPushButton:pressed {background:@selected@;}
QPushButton:disabled {background:@chrome@;border-color:@rule@;color:@disabled@;}
QPushButton#primary,QPushButton[primaryAction="true"] {background:@primary@;border:1px solid @primary@;color:@on_primary@;font-weight:600;padding:7px 15px;}
QPushButton#primary:hover,QPushButton[primaryAction="true"]:hover {background:@primary_hover@;border-color:@primary_hover@;}
QPushButton#primary:pressed,QPushButton[primaryAction="true"]:pressed {background:#7695ee;}
QPushButton#primary:disabled,QPushButton[primaryAction="true"]:disabled {background:#293c59;border-color:@border@;color:@disabled@;}
QPushButton[actionRole="reuse"] {background:#1c363b;border:1px solid #416b70;color:@green@;}
QPushButton[actionRole="reuse"]:hover {background:#24464a;border-color:@green@;}
QPushButton[actionRole="analysis"] {background:@selected@;color:@accent@;}
QPushButton[actionRole="reuse"]:disabled,QPushButton[actionRole="analysis"]:disabled {background:@chrome@;border-color:@rule@;color:@disabled@;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {background:@input@;border:1px solid @border@;border-radius:8px;padding:5px 8px;selection-background-color:@selected@;selection-color:@text@;}
QLineEdit:hover,QComboBox:hover,QSpinBox:hover,QDoubleSpinBox:hover {border-color:#526b8d;}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus {border-color:@accent@;background:#162338;}
QLineEdit:disabled,QComboBox:disabled {background:@chrome@;color:@disabled@;}
QComboBox::drop-down {width:22px;border:0;}
QComboBox QAbstractItemView {background:@panel@;color:@text@;border:1px solid @border@;selection-background-color:@selected@;selection-color:@text@;padding:4px;}
QGroupBox {background:@panel@;border:1px solid @border@;border-radius:12px;margin-top:12px;padding:11px;}
QGroupBox::title {subcontrol-origin:margin;left:12px;padding:0 5px;color:@accent@;font-weight:500;}
QScrollArea {background:transparent;border:0;}
QScrollArea > QWidget > QWidget {background:@window@;}
QTreeWidget,QListWidget,QTableWidget,QTableView,QPlainTextEdit,QTextBrowser {background:@input@;color:@text@;border:1px solid @border@;border-radius:9px;alternate-background-color:@panel@;selection-background-color:@selected@;selection-color:@text@;padding:4px;}
QTextBrowser#resultReport {background:@report@;color:@text@;font-family:'Cambria';font-size:11pt;border:1px solid @border@;border-radius:12px;padding:9px;}
QTreeWidget::item,QListWidget::item {padding:5px 3px;}
QTreeWidget::item:selected,QListWidget::item:selected {background:@selected@;color:@text@;border-radius:7px;}
QHeaderView::section {background:@panel@;color:@muted@;border:0;border-right:1px solid @rule@;border-bottom:1px solid @border@;padding:6px;}
QDockWidget::title {background:@chrome@;color:@muted@;padding:5px 9px;font-weight:500;border-bottom:1px solid @rule@;}
QDockWidget::close-button,QDockWidget::float-button {padding:2px;}
QTabWidget::pane {background:@window@;border:1px solid @border@;border-radius:10px;top:-1px;}
QTabBar::tab {background:@chrome@;color:@muted@;border:1px solid @rule@;border-top-left-radius:8px;border-top-right-radius:8px;padding:6px 10px;margin-right:3px;}
QTabBar::tab:selected {background:@selected@;color:@text@;border-color:#536d97;}
QTabBar::tab:hover {background:@hover@;}
QTabBar#documents {background:@window@;padding:5px 8px 0 8px;}
QTabBar#documents::tab {min-width:65px;max-width:230px;padding:7px 12px;border-radius:8px;margin-bottom:4px;}
QTabBar#documents::tab:selected {background:@panel@;border-color:#5c78a1;}
QTabBar::close-button {width:10px;height:10px;}
QTabBar::close-button:hover {background:@selected@;border-radius:4px;}
QSplitter::handle {background:@rule@;width:3px;height:3px;}
QSplitter::handle:hover {background:@accent@;}
QScrollBar:vertical {background:@chrome@;width:11px;}
QScrollBar::handle:vertical {background:#4c6588;min-height:28px;border:2px solid @chrome@;border-radius:5px;}
QScrollBar:horizontal {background:@chrome@;height:11px;}
QScrollBar::handle:horizontal {background:#4c6588;min-width:28px;border:2px solid @chrome@;border-radius:5px;}
QScrollBar::add-line,QScrollBar::sub-line {width:0;height:0;}
QScrollBar::add-page,QScrollBar::sub-page {background:transparent;}
QStatusBar {background:@chrome@;color:@muted@;border-top:1px solid @rule@;font-size:8pt;}
QToolTip {background:@panel@;color:@text@;border:1px solid #5d7ba3;border-radius:6px;padding:7px;}
QFrame#browserSection {background:@panel@;border:1px solid @rule@;border-radius:14px;}
QFrame#welcomeCard {background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #223454,stop:.65 #1b2a43,stop:1 #18373d);border:1px solid #3c5879;border-radius:16px;}
QLabel#welcomeTitle {font-size:20pt;font-weight:600;color:@text@;}
QLabel#welcomeEyebrow {font-size:8pt;font-weight:600;color:@green@;}
QLabel#areaTitle {font-size:12pt;font-weight:600;color:@text@;}
QLabel#sectionTitle {font-size:10pt;font-weight:600;color:@text@;padding:6px 2px;}
QLabel#badgeCount {background:@chrome@;color:@muted@;border:1px solid @rule@;border-radius:7px;padding:3px 7px;font-size:8pt;}
QLabel#linkTitle {font-size:10pt;font-weight:500;color:@text@;}
QLabel#linkArrow {font-size:17pt;color:@muted@;}
QPushButton#toolLink {text-align:left;background:transparent;border:1px solid transparent;border-radius:10px;padding:0;}
QPushButton#toolLink:hover,QPushButton#toolLink:focus {background:@hover@;border-color:#4c6383;}
QPushButton[quickRole="signal"] {background:@green@;border-color:@green@;color:@on_primary@;font-weight:600;}
QPushButton[quickRole="signal"]:hover {background:#a2e6d5;}
QPushButton[quickRole="system"] {background:#2b4265;border-color:#5e7cae;color:@text@;}
QPushButton[quickRole="filter"] {background:#393352;border-color:#736195;color:#ded0ff;}
QPushButton[quickRole="system"]:hover,QPushButton[quickRole="filter"]:hover {border-color:@accent@;background:@hover@;}
QToolButton[segment="true"] {background:@input@;border:1px solid @border@;border-radius:7px;padding:5px 6px;color:@muted@;}
QToolButton[segment="true"]:checked {background:@selected@;border-color:#728fc4;color:@text@;}
QToolButton[segment="true"]:hover {background:@hover@;border-color:#627fa8;}
QToolButton#areaNavigation {text-align:left;background:transparent;border:1px solid transparent;border-radius:9px;padding:6px 8px;color:@muted@;}
QToolButton#areaNavigation:checked {background:@selected@;border-color:#4c6891;color:@text@;font-weight:600;}
QToolButton#areaNavigation:hover {background:@hover@;}
QTreeWidget {background:@chrome@;border:0;}
QCheckBox {spacing:8px;}
QLineEdit {font-family:'Consolas';font-size:10pt;}
QLineEdit#toolSearch,QLineEdit#librarySearch {font-family:'Segoe UI';font-size:9pt;}
""")
_assets=Path(__file__).parent/'assets'
DESKTOP_STYLE += 'QComboBox::down-arrow {image:url("'+(_assets/'chevron_technical.svg').as_posix()+'");width:12px;height:12px;}'
DESKTOP_STYLE += 'QTabBar::close-button {image:url("'+(_assets/'close_document.svg').as_posix()+'");}'

DESKTOP_STYLE += "QPlainTextEdit#casInput {font-family:'Consolas';font-size:11pt;}"

DESKTOP_STYLE += "QToolBar#casToolbar {spacing:0;padding:2px;} QToolBar#casToolbar QToolButton {padding:3px 3px;}"


def desktop_style():
    from .theme_presets import recolor
    return recolor(DESKTOP_STYLE)
