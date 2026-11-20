"""Shared styling for the desktop, tool forms and result surfaces."""
from .theme_tokens import colorize

STYLE='''
QWidget {font-size:10pt;}
QMainWindow,QWidget#desktop {background:@window@;}
QWidget#documentHeading {background:@window@;border:0;}
QLabel#pageTitle {font-size:20pt;font-weight:700;}
QToolButton#documentArea {text-align:left;color:@accent@;font-size:9pt;font-weight:600;border:1px solid transparent;border-radius:5px;padding:1px 4px;}
QToolButton#documentArea:hover {background:@hover@;}
QWidget#explorerPanel {background:@chrome@;border-right:1px solid @rule@;}
QLabel#brand {font-size:19pt;}
QLabel#brandCaption {font-size:8pt;color:@muted@;}
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
QTabBar#documents {background:@chrome@;padding:3px 16px 0;}
QTabBar#documents::tab {color:@muted@;border:1px solid transparent;border-bottom:2px solid transparent;border-radius:4px;padding:6px 10px;min-width:65px;margin-bottom:0;}
QTabBar#documents::tab:selected {color:@text@;background:@window@;border-bottom-color:@accent@;}
QTabWidget::pane {border:0;background:transparent;}
QTabBar::tab {border:0;background:transparent;border-radius:9px;padding:9px 11px;margin:0 3px 5px 0;}
QTabBar::tab:selected {background:@selected@;border:0;color:@text@;}
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
QLineEdit#homeSearch {font-size:10pt;padding:7px 10px;border-radius:7px;background:@input@;border:1px solid @border@;}
QLineEdit#homeSearch:focus {border-color:@accent@;}
QLabel#catalogTitle {font-size:23pt;font-weight:700;}
QScrollArea#catalogIndex,QWidget#catalogIndexContent {background:@chrome@;border-radius:8px;}
QScrollArea#catalogList,QWidget#catalogListContent {background:@panel@;border-radius:8px;}
QFrame#catalogGroup {background:transparent;}
QPushButton#catalogArea {text-align:left;padding:7px 8px;color:@muted@;border:1px solid transparent;border-radius:5px;background:transparent;}
QPushButton#catalogArea:hover {background:@hover@;color:@text@;}
QPushButton#catalogArea:checked {background:@selected@;border-left:3px solid @accent@;color:@text@;font-weight:600;}
QPushButton#toolLink {background:transparent;border:1px solid transparent;border-radius:6px;padding:0;}
QPushButton#toolLink:hover {background:@hover@;border-color:@border@;}
QLabel#linkTitle {font-size:11pt;font-weight:600;}
QLabel#linkArrow {color:@accent@;font-size:15pt;}
QLabel#sectionTitle {font-size:10pt;font-weight:700;color:@muted@;padding:7px 9px 6px;border-bottom:1px solid @rule@;}
QStatusBar {border:0;padding:2px 10px;}
QToolBar#studioToolbar {background:@chrome@;border:0;border-bottom:1px solid @rule@;padding:5px 12px;spacing:6px;}
QLabel#studioBrand {font-size:13pt;font-weight:700;padding:0 8px 0 2px;}
QToolButton#applicationMenu,QToolButton#chromeAction,QToolButton#studioCatalog {background:transparent;border:1px solid transparent;border-radius:6px;padding:6px 8px;}
QToolButton#studioCatalog {background:@selected@;border-color:@border@;font-weight:600;}
QToolButton#applicationMenu:hover,QToolButton#chromeAction:hover,QToolButton#studioCatalog:hover {background:@hover@;border-color:@border@;}
QToolButton#applicationMenu::menu-indicator {image:none;width:0;}
QLabel#searchTitle {font-size:22pt;font-weight:600;}
QLineEdit#commandSearch {font-size:12pt;padding:12px 14px;border-radius:16px;}
QListWidget#commandResults {background:transparent;border:0;padding:0;}
QListWidget#commandResults::item {padding:13px 12px;border-radius:13px;margin-bottom:5px;}
QFrame#inputSurface {background:@chrome@;border:1px solid @rule@;border-radius:8px;}
QFrame#resultSurface {background:@panel@;border:1px solid @border@;border-radius:8px;}
QFrame#inputSurface QLabel#surfaceTitle,QFrame#resultSurface QLabel#surfaceTitle {padding-bottom:5px;border-bottom:1px solid @rule@;}
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
QToolButton#documentArea:focus,QToolButton#studioCatalog:focus,QPushButton#catalogArea:focus,QPushButton#toolLink:focus {border:1px solid @accent@;}
QToolButton[segment="true"]:focus {border:1px solid @text@;}
QPushButton#primary:focus,QPushButton[primaryAction="true"]:focus {border:1px solid @text@;}
'''

def stylesheet():return colorize(STYLE)
