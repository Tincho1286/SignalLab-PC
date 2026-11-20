"""Shared styling for the desktop, tool forms and result surfaces."""
from .theme_tokens import colorize

STYLE='''
QWidget {font-size:10pt;}
QMainWindow,QWidget#desktop {background:@window@;}
QWidget#documentHeading {background:transparent;border:0;}
QLabel#pageTitle {font-size:22pt;font-weight:700;}
QWidget#explorerPanel {background:@chrome@;border-right:1px solid @rule@;}
QLabel#brand {font-size:19pt;}
QLabel#brandCaption {font-size:8pt;color:@muted@;}
QToolBar#mainToolbar {background:@window@;border:0;padding:9px 14px;spacing:7px;}
QMenuBar {background:@window@;padding:2px 10px;}
QToolButton {border-radius:12px;padding:8px 10px;}
QPushButton {border-radius:12px;padding:8px 13px;min-height:18px;}
QPushButton#primary,QPushButton[primaryAction="true"] {border-radius:9px;padding:8px 18px;}
QToolButton#contextHelp {border:1px solid @rule@;border-radius:9px;background:@panel@;padding:8px 11px;}
QToolButton#resultLayoutAction {border:1px solid @rule@;border-radius:9px;background:@panel@;padding:8px 10px;}
QToolButton#resultLayoutAction:checked {background:@selected@;border-color:@accent@;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {border:1px solid @rule@;border-radius:11px;padding:7px 10px;}
QLineEdit:hover,QComboBox:hover {border-color:@border@;}
QLineEdit:focus,QComboBox:focus {border:1px solid @accent@;}
QGroupBox {background:@input@;border:1px solid @rule@;border-radius:16px;margin-top:14px;padding:14px;}
QGroupBox::title {left:14px;color:@text@;font-weight:600;}
QToolButton[segment="true"] {border-radius:10px;padding:8px 10px;}
QToolButton[segment="true"]:checked {border-color:@accent@;background:@selected@;font-weight:600;}
QToolButton#areaNavigation {border-radius:13px;padding:10px 11px;}
QToolButton#areaNavigation:checked {background:@selected@;border:1px solid transparent;}
QTabBar#documents {background:@chrome@;padding:2px 14px 0;}
QTabBar#documents::tab {border-radius:6px;padding:6px 12px;min-width:70px;border:1px solid transparent;}
QTabBar#documents::tab:selected {background:@window@;border:1px solid @rule@;border-bottom:2px solid @accent@;}
QTabWidget::pane {border:0;background:transparent;}
QTabBar::tab {border:0;background:transparent;border-radius:9px;padding:9px 11px;margin:0 3px 5px 0;}
QTabBar::tab:selected {background:@selected@;border:0;color:@text@;}
QFrame#inputSurface,QFrame#resultSurface {background:@panel@;border:1px solid @rule@;border-radius:20px;}
QFrame#inputSurface QScrollArea > QWidget > QWidget {background:transparent;}
QWidget#toolWorkspace {background:transparent;}
QLabel#surfaceTitle {font-size:12pt;font-weight:700;color:@text@;}
QFrame#inputSurface QLabel#surfaceTitle {color:@accent@;}
QLabel#surfaceCaption {font-size:9pt;color:@muted@;}
QLabel[resultStale="true"] {color:@amber@;}
QLabel#resultEmpty {font-size:12pt;color:@muted@;padding:26px;}
QWidget#resultActionBar {background:transparent;}
QWidget#resultActionBar QPushButton,QWidget#resultActionBar QToolButton {min-height:18px;border-radius:7px;padding:6px 8px;font-size:9pt;}
QWidget#resultActionBar QPushButton:disabled {border:1px solid @rule@;background:transparent;color:@disabled@;}
QToolButton#plotLauncher,QPushButton#plotLauncher {background:@selected@;border:1px solid @border@;padding:8px 10px;}
QTabWidget#workspaceModes > QTabBar::tab {padding:7px 15px;font-weight:600;}
QTextBrowser#resultReport {border:1px solid @rule@;border-radius:9px;background:@report@;padding:10px;}
QTableWidget,QTableView,QPlainTextEdit {border:1px solid @rule@;border-radius:12px;}
QHeaderView::section {padding:9px 8px;}
QScrollBar:vertical {width:10px;background:transparent;}
QScrollBar::handle:vertical {border:2px solid transparent;border-radius:5px;background:@disabled@;}
QDockWidget::title {padding:3px 9px;font-size:8pt;border:0;}
QFrame#welcomeCard {background:@panel@;border:1px solid @rule@;border-radius:24px;}
QLineEdit#homeSearch {font-family:'Segoe UI';font-size:11pt;padding:8px 11px;border-radius:9px;background:@input@;border:1px solid @border@;}
QLineEdit#homeSearch:focus {border-color:@accent@;}
QFrame#browserSection {background:@panel@;border:1px solid @rule@;border-radius:12px;}
QPushButton#toolLink {background:@input@;border:1px solid transparent;border-radius:7px;padding:0;}
QPushButton#toolLink:hover {background:@hover@;border-color:@border@;}
QLabel#linkTitle {font-size:11pt;font-weight:600;}
QLabel#sectionTitle {font-size:11pt;font-weight:700;padding:2px 5px 5px;}
QStatusBar {border:0;padding:2px 10px;}
QToolBar#studioToolbar {background:@chrome@;border:0;border-bottom:1px solid @rule@;padding:6px 12px;spacing:8px;}
QLabel#studioBrand {font-size:15pt;font-weight:700;}
QToolButton#applicationMenu {background:@panel@;border:1px solid @rule@;border-radius:8px;padding:7px;}
QPushButton#studioSearch {text-align:left;background:@window@;border:1px solid @rule@;border-radius:8px;color:@muted@;padding:7px 12px;font-weight:400;}
QPushButton#studioSearch:hover {background:@hover@;border-color:@accent@;}
QWidget#navigationRail {background:@chrome@;}
QScrollArea#railScroll,QScrollArea#railScroll > QWidget > QWidget {background:@chrome@;}
QScrollArea#railScroll {border-right:1px solid @rule@;}
QToolButton#railItem {background:transparent;border:1px solid transparent;border-left:3px solid transparent;border-radius:7px;padding:5px 4px;color:@muted@;font-size:9pt;}
QToolButton#railItem:hover {background:@hover@;}
QToolButton#railItem:checked {background:@selected@;border-left-color:@accent@;color:@text@;font-weight:700;}
QLabel#searchTitle {font-size:22pt;font-weight:600;}
QLineEdit#commandSearch {font-size:12pt;padding:12px 14px;border-radius:16px;}
QListWidget#commandResults {background:transparent;border:0;padding:0;}
QListWidget#commandResults::item {padding:13px 12px;border-radius:13px;margin-bottom:5px;}
QLabel#welcomeTitle {font-size:29pt;font-weight:700;}
QLabel#heroDescription {font-size:10pt;color:@muted@;}
QFrame#studioHero {border:1px solid @rule@;border-radius:14px;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 @panel@,stop:1 @input@);}
QLabel#browseHeading {font-size:12pt;font-weight:700;}
QPushButton#quickAction,QPushButton#areaCard {text-align:left;border:1px solid @rule@;border-radius:10px;padding:0;}
QPushButton#quickAction {background:@panel@;}
QPushButton#areaCard {background:@input@;}
QPushButton#quickAction:hover,QPushButton#areaCard:hover {background:@hover@;border-color:@accent@;}
QLabel#quickTitle {font-size:10pt;font-weight:700;}
QLabel#quickDescription {font-size:9pt;color:@muted@;}
QFrame#inputSurface {background:@panel@;border:1px solid @rule@;border-radius:12px;}
QFrame#resultSurface {background:@report@;border:1px solid @rule@;border-radius:12px;}
QGroupBox {background:transparent;border:0;border-radius:0;padding:8px 0px;margin-top:16px;}
QGroupBox::title {left:0;color:@text@;font-size:10pt;}
QToolButton[segment="true"] {background:@input@;border:1px solid @rule@;border-radius:7px;padding:6px 10px;}
QToolButton[segment="true"]:checked {background:@selected@;border:1px solid @accent@;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {background:@input@;border:1px solid @rule@;border-radius:7px;padding:6px 9px;}
QLineEdit:hover,QComboBox:hover {border-color:@border@;}
QWidget#resultActionDock {background:transparent;border:0;}
QWidget#resultActionDock QPushButton,QWidget#resultActionDock QToolButton {padding:6px 9px;border-radius:7px;}
QWidget#resultActionDock QPushButton::menu-indicator {subcontrol-origin:padding;subcontrol-position:right center;right:6px;}
QWidget#resultActionDock QToolButton#plotLauncher[hasPlotChoices="true"] {padding-right:38px;text-align:left;}
QToolButton#plotLauncher,QPushButton#plotLauncher {background:@selected@;border:1px solid @accent@;}
QSplitter::handle {background:@window@;border:0;}
QWidget#bandEdgesEditor {background:transparent;}
QWidget#libraryIndex {background:@panel@;border:1px solid @rule@;border-radius:12px;}
QWidget#libraryArticle {background:@report@;border:1px solid @rule@;border-radius:12px;}
QListWidget#savedResults {background:@input@;border:0;}
QListWidget#savedResults::item {padding:12px 10px;margin-bottom:4px;border-radius:10px;}
QWidget#casToolbar QToolButton {padding:8px 18px 8px 10px;border:1px solid @rule@;background:@input@;}
QWidget#casToolbar QToolButton::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
QDialog#scientificFigure {background:@window@;}
QToolBar#figureNavigation {background:@chrome@;border:1px solid @rule@;border-radius:7px;padding:2px 4px;spacing:3px;}
QToolBar#figureNavigation QToolButton {padding:4px 6px;border-radius:5px;}
QToolBar#figureNavigation QToolButton:checked {background:@selected@;border-color:@accent@;}
QToolButton[figureControl="true"] {background:@panel@;border:1px solid @rule@;border-radius:6px;padding:4px 8px;}
QToolButton[figureControl="true"]:checked,QToolButton[figureControl="true"]:hover {background:@selected@;border-color:@accent@;}
QToolButton#figureScale {padding-right:19px;}
QToolButton#figureScale::menu-indicator {subcontrol-position:right center;right:6px;}
QWidget#cursorPanel {background:@chrome@;border:1px solid @rule@;border-radius:7px;}
QLabel#cursorReadout {font-family:'Consolas';font-size:9pt;color:@text@;padding:2px 0;}
QWidget#cursorPanel QPushButton,QWidget#cursorPanel QToolButton {min-height:16px;padding:3px 8px;border-radius:5px;font-size:9pt;}
QWidget#cursorPanel QToolButton {border:1px solid @rule@;}
QWidget#cursorPanel QToolButton:checked {background:@selected@;border-color:@accent@;}
QTableWidget#cursorTable {border-radius:6px;padding:0;}
QTableWidget#cursorTable QHeaderView::section {padding:3px 7px;}
QPushButton:focus,QToolButton:focus,QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus,QPlainTextEdit:focus,QTableView:focus {border:1px solid @accent@;}
QToolButton#railItem:focus,QPushButton#quickAction:focus,QPushButton#areaCard:focus,QPushButton#studioSearch:focus {border:1px solid @accent@;}
QToolButton[segment="true"]:focus {border:1px solid @text@;}
QPushButton#primary:focus,QPushButton[primaryAction="true"]:focus {border:1px solid @text@;}
'''

def stylesheet():return colorize(STYLE)
