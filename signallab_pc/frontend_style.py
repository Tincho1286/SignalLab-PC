"""A calm, rounded desktop language, using every existing theme's tokens."""
from .theme_tokens import colorize

STYLE='''
QWidget {font-size:10pt;}
QMainWindow,QWidget#desktop {background:@window@;}
QWidget#documentHeading {background:transparent;border:0;}
QLabel#pageTitle {font-size:21pt;font-weight:600;}
QWidget#explorerPanel {background:@chrome@;border-right:1px solid @rule@;}
QLabel#brand {font-size:19pt;}
QLabel#brandCaption {font-size:8pt;color:@muted@;}
QToolBar#mainToolbar {background:@window@;border:0;padding:9px 14px;spacing:7px;}
QMenuBar {background:@window@;padding:2px 10px;}
QToolButton {border-radius:12px;padding:8px 10px;}
QPushButton {border-radius:12px;padding:8px 13px;min-height:18px;}
QPushButton#primary,QPushButton[primaryAction="true"] {border-radius:16px;padding:10px 21px;}
QToolButton#contextHelp {border:0;border-radius:14px;background:@panel@;padding:10px 14px;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {border:1px solid @rule@;border-radius:11px;padding:7px 10px;}
QLineEdit:hover,QComboBox:hover {border-color:@border@;}
QLineEdit:focus,QComboBox:focus {border:1px solid @accent@;}
QGroupBox {background:@input@;border:1px solid @rule@;border-radius:16px;margin-top:14px;padding:14px;}
QGroupBox::title {left:14px;color:@text@;font-weight:600;}
QToolButton[segment="true"] {border-radius:10px;padding:8px 10px;}
QToolButton[segment="true"]:checked {border-color:@accent@;background:@selected@;font-weight:600;}
QToolButton#areaNavigation {border-radius:13px;padding:10px 11px;}
QToolButton#areaNavigation:checked {background:@selected@;border:1px solid transparent;}
QTabBar#documents {padding:8px 14px 1px 14px;}
QTabBar#documents::tab {border-radius:12px;padding:9px 14px;min-width:70px;border:1px solid transparent;}
QTabBar#documents::tab:selected {background:@panel@;border:1px solid @rule@;}
QTabWidget::pane {border:0;background:transparent;}
QTabBar::tab {border:0;background:transparent;border-radius:9px;padding:9px 11px;margin:0 3px 5px 0;}
QTabBar::tab:selected {background:@selected@;border:0;color:@text@;}
QFrame#inputSurface,QFrame#resultSurface {background:@panel@;border:1px solid @rule@;border-radius:20px;}
QFrame#inputSurface QScrollArea > QWidget > QWidget {background:transparent;}
QWidget#toolWorkspace {background:transparent;}
QLabel#surfaceTitle {font-size:13pt;font-weight:600;color:@text@;}
QLabel#surfaceCaption {font-size:9pt;color:@muted@;}
QLabel#resultEmpty {font-size:12pt;color:@muted@;padding:26px;}
QWidget#resultActionBar {background:transparent;}
QWidget#resultActionBar QPushButton,QWidget#resultActionBar QToolButton {min-height:20px;border-radius:11px;padding:8px 8px;font-size:9pt;}
QWidget#resultActionBar QPushButton:disabled {border:1px solid @rule@;background:transparent;color:@disabled@;}
QToolButton#plotLauncher,QPushButton#plotLauncher {background:@selected@;border:1px solid @border@;padding:8px 10px;}
QTabWidget#workspaceModes > QTabBar::tab {padding:11px 20px;font-weight:600;}
QTextBrowser#resultReport {border:0;border-radius:14px;background:@report@;padding:14px;}
QTableWidget,QTableView,QPlainTextEdit {border:1px solid @rule@;border-radius:12px;}
QHeaderView::section {padding:9px 8px;}
QScrollBar:vertical {width:10px;background:transparent;}
QScrollBar::handle:vertical {border:2px solid transparent;border-radius:5px;background:@disabled@;}
QDockWidget::title {padding:3px 9px;font-size:8pt;border:0;}
QFrame#welcomeCard {background:@panel@;border:1px solid @rule@;border-radius:24px;}
QLabel#welcomeTitle {font-size:26pt;font-weight:600;}
QLabel#welcomeEyebrow {font-size:9pt;color:@accent@;}
QLineEdit#homeSearch {font-family:'Segoe UI';font-size:12pt;padding:12px 16px;border-radius:16px;background:@input@;}
QFrame#browserSection {border:1px solid @rule@;border-radius:20px;}
QPushButton#toolLink {border-radius:13px;}
QLabel#linkTitle {font-size:11pt;font-weight:600;}
QLabel#sectionTitle {font-size:12pt;}
QLabel#badgeCount {border:0;border-radius:10px;padding:5px 8px;}
QStatusBar {border:0;padding:2px 10px;}
QToolBar#studioToolbar {background:@window@;border:0;padding:10px 18px;spacing:10px;}
QLabel#studioBrand {font-size:17pt;font-weight:600;letter-spacing:0.3px;}
QToolButton#applicationMenu {background:@panel@;border:0;border-radius:16px;padding:11px;}
QPushButton#studioSearch {text-align:left;background:@panel@;border:1px solid @rule@;border-radius:16px;color:@muted@;padding:10px 16px;font-weight:400;}
QPushButton#studioSearch:hover {background:@hover@;border-color:@accent@;}
QWidget#navigationRail {background:@window@;}
QScrollArea#railScroll,QScrollArea#railScroll > QWidget > QWidget {background:@window@;}
QToolButton#railItem {background:transparent;border:0;border-radius:19px;padding:9px 2px;color:@muted@;font-size:8pt;}
QToolButton#railItem:hover {background:@hover@;}
QToolButton#railItem:checked {background:@selected@;color:@text@;font-weight:600;}
QLabel#searchTitle {font-size:22pt;font-weight:600;}
QLineEdit#commandSearch {font-size:12pt;padding:12px 14px;border-radius:16px;}
QListWidget#commandResults {background:transparent;border:0;padding:0;}
QListWidget#commandResults::item {padding:13px 12px;border-radius:13px;margin-bottom:5px;}
QLabel#welcomeTitle {font-size:32pt;}
QFrame#studioHero {border:0;background:transparent;}
QPushButton#quickAction {text-align:left;background:@input@;border:1px solid @rule@;border-radius:18px;padding:0;}
QPushButton#quickAction:hover {background:@hover@;border-color:@accent@;}
QLabel#quickTitle {font-size:12pt;font-weight:600;}
QLabel#quickDescription {font-size:9pt;color:@muted@;}
QFrame#inputSurface {background:@panel@;border:0;border-radius:24px;}
QFrame#resultSurface {background:@report@;border:0;border-radius:24px;}
QGroupBox {background:transparent;border:0;border-radius:0;padding:8px 0px;margin-top:16px;}
QGroupBox::title {left:0;color:@text@;font-size:10pt;}
QToolButton[segment="true"] {background:@input@;border:1px solid transparent;border-radius:12px;padding:8px 11px;}
QToolButton[segment="true"]:checked {background:@selected@;border:1px solid @accent@;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {background:@input@;border:1px solid transparent;border-radius:12px;padding:8px 10px;}
QLineEdit:hover,QComboBox:hover {border-color:@border@;}
QWidget#resultActionDock {background:@chrome@;border:1px solid @rule@;border-radius:18px;}
QWidget#resultActionDock QPushButton,QWidget#resultActionDock QToolButton {padding:9px 10px;border-radius:13px;}
QToolButton#plotLauncher,QPushButton#plotLauncher {background:@selected@;border:1px solid @accent@;}
QSplitter::handle {background:@window@;border:0;}
QWidget#libraryIndex {background:@panel@;border-radius:24px;}
QWidget#libraryArticle {background:@report@;border-radius:24px;}
QListWidget#savedResults {background:@input@;border:0;}
QListWidget#savedResults::item {padding:12px 10px;margin-bottom:4px;border-radius:10px;}
QWidget#casToolbar QToolButton {padding:8px 18px 8px 10px;border:1px solid @rule@;background:@input@;}
QWidget#casToolbar QToolButton::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
'''

def stylesheet():return colorize(STYLE)
