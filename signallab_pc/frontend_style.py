"""Shared styling for the desktop, tool forms and result surfaces."""
from .theme_tokens import colorize

STYLE='''
QWidget {font-size:10pt;}
QMainWindow,QWidget#desktop {background:@window@;}
QWidget#documentHeading {background:@window@;border:0;}
QLabel#pageTitle {font-size:22pt;font-weight:700;}
QLabel#pageTitle[shortHeader="true"] {font-size:17pt;}
QToolButton#documentArea {text-align:left;color:@accent@;font-size:9pt;font-weight:600;border:1px solid transparent;border-radius:6px;padding:1px 5px;}
QToolButton#documentArea:hover {background:@hover@;}
QWidget#explorerPanel {background:@chrome@;border-right:1px solid @rule@;}
QLabel#brand {font-size:19pt;}
QLabel#brandCaption {font-size:8pt;color:@muted@;}
QMenuBar {background:@window@;padding:2px 10px;}
QToolButton {border-radius:12px;padding:8px 10px;}
QPushButton {border-radius:12px;padding:8px 13px;min-height:18px;}
QPushButton#primary,QPushButton[primaryAction="true"] {border-radius:9px;padding:8px 18px;}
QToolButton#contextHelp {border:1px solid @rule@;border-radius:9px;background:@panel@;padding:8px 11px;}
QToolButton#favoriteTool {border:1px solid @rule@;border-radius:9px;background:@panel@;padding:8px;}
QToolButton#favoriteTool:hover,QToolButton#favoriteTool:focus {border-color:@amber@;}
QToolButton#favoriteTool:checked {border-color:@amber@;background:@selected@;}
QToolButton#resultLayoutAction {border:1px solid @rule@;border-radius:9px;background:@panel@;padding:8px 10px;}
QToolButton#resultLayoutAction:checked {background:@selected@;border-color:@accent@;}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox {border:1px solid @rule@;border-radius:11px;padding:7px 10px;}
QLineEdit:hover,QComboBox:hover {border-color:@border@;}
QLineEdit[clockInput="true"]:read-only {background:@panel@;color:@muted@;}
QLineEdit:focus,QComboBox:focus {border:1px solid @accent@;}
QGroupBox {background:@input@;border:1px solid @rule@;border-radius:16px;margin-top:14px;padding:14px;}
QGroupBox::title {left:14px;color:@text@;font-weight:600;}
QToolButton[segment="true"] {border-radius:10px;padding:8px 10px;}
QToolButton[segment="true"]:checked {border-color:@accent@;background:@selected@;font-weight:600;}
QToolButton#areaNavigation {border-radius:13px;padding:10px 11px;}
QToolButton#areaNavigation:checked {background:@selected@;border:1px solid transparent;}
QTabBar#documents {background:@chrome@;padding:5px 16px 0;}
QTabBar#documents::tab {color:@muted@;border:1px solid transparent;border-top:2px solid transparent;border-radius:6px;padding:6px 10px;min-width:65px;margin-bottom:0;}
QTabBar#documents::tab:selected {color:@text@;background:@window@;border-top-color:@accent@;}
QTabBar#documents QToolButton#documentClose {background:transparent;border:0;border-radius:5px;padding:0;}
QTabBar#documents QToolButton#documentClose:hover {background:@selected@;}
QTabWidget::pane {border:0;background:transparent;}
QTabBar::tab {border:0;background:transparent;border-radius:9px;padding:9px 11px;margin:0 3px 5px 0;}
QTabBar::tab:selected {background:@selected@;border:0;color:@text@;}
QFrame#inputSurface QScrollArea > QWidget > QWidget {background:transparent;}
QWidget#workspaceInputForm,QWidget#workspaceInputForm > QWidget {background:transparent;}
QWidget#workflowSelector {background:@window@;}
QLabel#variantCaption {color:@muted@;font-size:9pt;font-weight:600;}
QToolButton#variantMenuButton {background:@selected@;border:1px solid @border@;border-radius:8px;padding:6px 29px 6px 11px;font-weight:650;text-align:left;}
QToolButton#variantMenuButton::menu-indicator {subcontrol-origin:padding;subcontrol-position:right center;right:10px;width:9px;}
QToolButton#variantCopyButton {background:@panel@;border:1px solid @rule@;border-radius:8px;padding:6px 10px;}
QToolButton#variantMenuButton:hover,QToolButton#variantMenuButton:focus,QToolButton#variantCopyButton:hover,QToolButton#variantCopyButton:focus {border-color:@accent@;}
QMenu#variantMenu::item {padding:6px 18px 6px 25px;}
QMenu#variantMenu::item:disabled {color:@accent@;background:@chrome@;padding:5px 16px 5px 10px;font-weight:700;}
QWidget#toolWorkspace {background:transparent;}
QLabel#surfaceTitle {font-size:12pt;font-weight:700;color:@text@;}
QFrame#inputSurface QLabel#surfaceTitle {color:@accent@;}
QLabel#surfaceCaption {font-size:9pt;color:@muted@;}
QLabel[resultStale="true"] {color:@amber@;}
QLabel#resultEmpty {font-size:12pt;color:@muted@;padding:26px;}
QLabel#inputGridPreview {color:@accent@;background:@input@;border:1px solid @rule@;border-radius:7px;padding:5px 8px;}
QWidget#resultActionBar {background:transparent;}
QWidget#resultActionBar QPushButton,QWidget#resultActionBar QToolButton {min-height:18px;border-radius:7px;padding:6px 8px;font-size:9pt;}
QWidget#resultActionBar QPushButton:disabled {border:1px solid @rule@;background:transparent;color:@disabled@;}
QToolButton#plotLauncher,QPushButton#plotLauncher {background:@selected@;border:1px solid @border@;padding:8px 10px;}
QTabWidget#workspaceModes > QTabBar::tab {padding:7px 15px;font-weight:600;}
QTextBrowser#resultReport {border:1px solid @rule@;border-radius:9px;background:@report@;padding:10px;}
QTableWidget,QTableView,QPlainTextEdit {border:1px solid @rule@;border-radius:12px;}
QHeaderView::section {padding:9px 8px;}
QTableView#resultValues QHeaderView::section:vertical {padding:3px 8px;}
QToolButton#resultPageStep {border:1px solid @rule@;background:@panel@;border-radius:7px;padding:8px;}
QToolButton#resultPageStep:hover,QToolButton#resultPageStep:focus {border-color:@accent@;}
QPushButton#resultTableCopy {padding-right:24px;}
QPushButton#resultTableCopy::menu-indicator {subcontrol-origin:padding;subcontrol-position:right center;right:7px;}
QScrollBar:vertical {width:10px;background:transparent;}
QScrollBar::handle:vertical {border:2px solid transparent;border-radius:5px;background:@disabled@;}
QDockWidget::title {padding:3px 9px;font-size:8pt;border:0;}
QScrollArea#catalogScroll,QWidget#catalogCanvas {background:@window@;}
QFrame#welcomeCard {
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0.63,stop:0 @selected@,stop:0.55 @panel@,stop:1 @chrome@);
    border:1px solid @border@;border-radius:18px;
}
QLabel#welcomeTitle {font-size:24pt;font-weight:700;}
QLabel#catalogIntro {color:@muted@;font-size:10pt;}
QLabel#catalogSectionTitle {color:@text@;font-size:12pt;font-weight:650;}
QLineEdit#homeSearch {
    font-family:'Segoe UI';font-size:10pt;padding:9px 11px;
    border-radius:9px;background:@input@;border:1px solid @border@;
}
QLineEdit#homeSearch:focus {border-color:@accent@;}
QPushButton#launchPalette {
    text-align:left;background:@input@;border:1px solid @border@;
    color:@text@;border-radius:9px;padding:10px 12px;font-weight:600;
}
QPushButton#launchPalette:hover,QPushButton#launchPalette:focus {border-color:@accent@;background:@hover@;}
QPushButton#catalogArea,QPushButton#toolLink,QPushButton#catalogShortcut,QPushButton#favoriteShortcut {
    text-align:left;background:@panel@;border:1px solid @rule@;border-radius:13px;padding:0;
}
QPushButton#catalogShortcut {background:@chrome@;border-radius:11px;}
QPushButton#favoriteShortcut {border-left:2px solid @amber@;}
QPushButton#catalogArea:hover,QPushButton#toolLink:hover,QPushButton#catalogShortcut:hover,QPushButton#favoriteShortcut:hover {
    background:@hover@;border-color:@accent@;
}
QPushButton#catalogArea:pressed,QPushButton#toolLink:pressed,QPushButton#catalogShortcut:pressed,QPushButton#favoriteShortcut:pressed {background:@selected@;}
QLabel#catalogMark {background:@input@;border:1px solid @rule@;border-radius:9px;}
QLabel#linkTitle {font-size:11pt;font-weight:650;color:@text@;}
QLabel#catalogSummary {font-size:9pt;color:@muted@;}
QLabel#linkArrow {color:@accent@;font-size:18pt;}
QLabel#sectionTitle {font-size:10pt;font-weight:700;color:@muted@;padding:7px 9px 6px;border-bottom:1px solid @rule@;}
QStatusBar {border:0;padding:2px 10px;}
QToolBar#studioToolbar {background:@chrome@;border:0;border-bottom:1px solid @rule@;padding:8px 13px;spacing:6px;}
QLabel#studioBrand {font-size:15pt;font-weight:700;padding:0 8px 0 2px;}
QToolButton#applicationMenu,QToolButton#chromeAction,QToolButton#studioSearch {background:transparent;border:1px solid transparent;border-radius:8px;padding:6px 8px;}
QToolButton#studioSearch {background:@input@;border-color:@border@;color:@muted@;}
QToolButton#applicationMenu:hover,QToolButton#chromeAction:hover,QToolButton#studioSearch:hover {background:@hover@;border-color:@border@;color:@text@;}
QToolButton#applicationMenu::menu-indicator {image:none;width:0;}
QScrollArea#desktopNavigation,QWidget#desktopNavigationBody {background:@chrome@;}
QScrollArea#desktopNavigation {border-right:1px solid @rule@;}
QToolButton#desktopNavigationButton {
    border:1px solid transparent;border-left:2px solid transparent;border-radius:10px;
    color:@muted@;font-size:9pt;font-weight:600;padding:3px;
}
QToolButton#desktopNavigationButton:hover {background:@hover@;color:@text@;}
QToolButton#desktopNavigationButton:checked {border-left-color:@accent@;background:@selected@;color:@text@;}
QToolButton#desktopNavigationButton:focus {border-color:@accent@;}
QDialog#commandPalette {background:@chrome@;}
QLabel#searchTitle {font-size:20pt;font-weight:700;}
QLineEdit#commandSearch {font-family:'Segoe UI';font-size:11pt;padding:10px 12px;border-radius:10px;}
QListWidget#commandResults {background:@window@;border:1px solid @rule@;border-radius:11px;padding:4px;}
QLabel#commandHint {color:@muted@;font-size:9pt;padding:3px 2px;}
QFrame#inputSurface {background:@chrome@;border:1px solid @rule@;border-radius:14px;}
QFrame#resultSurface {background:@panel@;border:1px solid @border@;border-radius:14px;}
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
QSplitter#toolSplit::handle:horizontal:hover {background:@selected@;border-radius:4px;}
QWidget#bandEdgesEditor {background:transparent;}
QLabel#bandEdgeBadge {background:@panel@;border-radius:10px;font-weight:600;}
QLabel#bandEdgeBadge[bandRole="pass"] {color:@green@;border:1px solid @green@;}
QLabel#bandEdgeBadge[bandRole="stop"] {color:@amber@;border:1px solid @amber@;}
QLabel#bandStatus {color:@muted@;}
QWidget#libraryIndex {background:@panel@;border:1px solid @rule@;border-radius:12px;}
QWidget#libraryArticle {background:@report@;border:1px solid @rule@;border-radius:12px;}
QSplitter#librarySplit::handle {background:transparent;border:3px solid transparent;border-radius:4px;}
QSplitter#librarySplit::handle:hover {background:@border@;}
QTreeWidget#libraryTopics::item {padding:2px 4px;}
QPushButton#guideChapter {background:@input@;border:1px solid @rule@;border-radius:7px;padding:5px 9px;}
QPushButton#guideChapter:hover,QPushButton#guideChapter:focus {border-color:@accent@;}
QListWidget#savedResults {background:@input@;border:1px solid @rule@;border-radius:9px;padding:4px;}
QLineEdit#resultHistorySearch {font-family:'Segoe UI';}
QLabel#resultHistoryTitle {font-size:15pt;font-weight:600;color:@text@;}
QToolButton#formulaMenu,QToolButton#libraryOutline {background:@panel@;border-color:@border@;border-radius:7px;padding:6px 21px 6px 9px;}
QToolButton#formulaMenu::menu-indicator,QToolButton#libraryOutline::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
QTextBrowser#formulaPreview {background:@report@;border:1px solid @rule@;border-radius:7px;padding:2px;}
QToolButton#fieldSectionToggle {background:@input@;border:1px solid @border@;border-radius:7px;padding:6px 8px;text-align:left;}
QToolButton#fieldSectionToggle:hover,QToolButton#fieldSectionToggle:checked {background:@selected@;}
QWidget#fieldSectionBody {background:@panel@;border-radius:7px;}
QFrame#inputHandoff {background:@panel@;border:1px solid @border@;border-left:2px solid @green@;border-radius:8px;}
QFrame#inputHandoff QPushButton,QFrame#inputHandoff QToolButton {padding:3px 7px;border-radius:5px;}
QToolButton#resultHistoryMenu {background:@panel@;border-color:@border@;border-radius:8px;padding:7px 22px 7px 9px;}
QToolButton#resultHistoryMenu::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
QDialog#scientificFigure {background:@window@;}
QLabel#figureHeading {font-size:17pt;font-weight:700;color:@text@;}
QLabel#figureOrigin {font-size:9pt;color:@muted@;}
QToolButton#figureAlternatives,QToolButton#figureFocus,QToolButton#figureCompactControls {
    background:@panel@;border:1px solid @border@;border-radius:9px;padding:7px 9px;
}
QToolButton#figureAlternatives {padding-right:22px;}
QToolButton#figureAlternatives::menu-indicator {subcontrol-position:right center;right:7px;width:8px;}
QToolButton#figureAlternatives:hover,QToolButton#figureFocus:hover,QToolButton#figureFocus:checked,QToolButton#figureCompactControls:hover,QToolButton#figureCompactControls:checked {
    background:@selected@;border-color:@accent@;
}
QFrame#figureCanvasFrame {background:@report@;border:1px solid @rule@;border-radius:9px;}
QSplitter#figureSplit::handle:hover {background:@hover@;border-radius:3px;}
QFrame#curveInspector {background:@panel@;border:1px solid @border@;border-radius:10px;}
QWidget#curveInspectorPage {background:@panel@;}
QLabel#curveInspectorTitle {font-size:13pt;font-weight:700;}
QToolButton#curveInspectorClose {font-size:13pt;padding:1px 7px;}
QLabel#curveMeasureSummary {background:@input@;border:1px solid @rule@;border-radius:7px;padding:6px;}
QTabWidget#curveInspectorTabs QTabBar::tab {padding:6px 8px;margin-bottom:2px;}
QDialog#realizationEditor {background:@window@;}
QLabel#diagramTitle {font-size:18pt;font-weight:700;}
QLabel#diagramDomain {background:@selected@;border-radius:8px;color:@text@;padding:5px 8px;}
QLabel#diagramSectionTitle {font-size:11pt;font-weight:700;}
QFrame#diagramPalette {background:@chrome@;border:1px solid @rule@;border-radius:10px;}
QGraphicsView#diagramCanvas {background:@report@;border:1px solid @border@;border-radius:8px;}
QPushButton#diagramBlockButton {text-align:left;background:@panel@;border-radius:8px;padding:8px 9px;}
QToolButton#diagramTool,QToolButton#diagramFileMenu,QToolButton#diagramConnect {
    background:@panel@;border:1px solid @border@;border-radius:7px;padding:5px 8px;
}
QToolButton#diagramTool:hover,QToolButton#diagramFileMenu:hover,QToolButton#diagramConnect:hover,QToolButton#diagramConnect:checked {
    background:@selected@;border-color:@accent@;
}
QToolButton#diagramFileMenu {padding-right:22px;}
QToolButton#diagramFileMenu::menu-indicator {subcontrol-position:right center;right:7px;width:8px;}
QToolButton#diagramConnect {padding-right:30px;}
QToolButton#diagramConnect::menu-button {subcontrol-origin:border;subcontrol-position:right center;width:24px;border-left:1px solid @border@;}
QLabel#diagramHint {color:@muted@;padding:2px 3px;}
QLabel#diagramConnectionState {color:@amber@;font-weight:600;}
QLabel#diagramConnectionState[complete="true"] {color:@green@;}
QToolBar#figureNavigation {background:@chrome@;border:1px solid @rule@;border-radius:7px;padding:2px 4px;spacing:3px;}
QToolBar#figureNavigation QToolButton {padding:4px 6px;border-radius:5px;}
QToolBar#figureNavigation QToolButton:checked {background:@selected@;border-color:@accent@;}
QToolButton#figureViewMenu {background:@panel@;border:1px solid @rule@;padding:4px 18px 4px 8px;}
QToolButton#figureViewMenu::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
QToolButton[figureControl="true"] {background:@panel@;border:1px solid @rule@;border-radius:6px;padding:4px 8px;}
QToolButton[figureControl="true"]:checked,QToolButton[figureControl="true"]:hover {background:@selected@;border-color:@accent@;}
QToolButton#figureScale {padding-right:19px;}
QToolButton#figureScale::menu-indicator {subcontrol-position:right center;right:6px;}
QWidget#cursorPanel {background:@chrome@;border:1px solid @rule@;border-radius:7px;}
QLabel#sampleReadout {color:@green@;}
QLabel#cursorReadout {font-family:'Consolas';font-size:9pt;color:@text@;padding:2px 0;}
QWidget#cursorPanel QPushButton,QWidget#cursorPanel QToolButton {min-height:16px;padding:3px 8px;border-radius:5px;font-size:9pt;}
QWidget#cursorPanel QToolButton {border:1px solid @rule@;}
QWidget#cursorPanel QToolButton:checked {background:@selected@;border-color:@accent@;}
QWidget#cursorPanel QToolButton#cursorCurveMenu {background:@selected@;border-color:@border@;padding-right:22px;}
QToolButton#cursorCurveMenu::menu-indicator {subcontrol-position:right center;right:6px;width:8px;}
QTableWidget#cursorTable {border-radius:6px;padding:0;}
QTableWidget#cursorTable QHeaderView::section {padding:3px 7px;}
QPushButton:focus,QToolButton:focus,QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus,QPlainTextEdit:focus,QTableView:focus {border:1px solid @accent@;}
QFrame#inputIssue {background:@input@;border:1px solid @red@;border-radius:8px;}
QLabel#inputIssueTitle {color:@red@;font-weight:700;}
QFrame#inputIssue QPushButton,QFrame#inputIssue QToolButton {min-height:16px;padding:3px 7px;}
QLineEdit[inputError="true"],QComboBox[inputError="true"],QSpinBox[inputError="true"],QDoubleSpinBox[inputError="true"],QPlainTextEdit[inputError="true"],QWidget[inputError="true"] QLineEdit {border:1px solid @red@;}
QToolButton#documentArea:focus,QToolButton#studioSearch:focus,QPushButton#catalogArea:focus,QPushButton#toolLink:focus,QPushButton#catalogShortcut:focus,QPushButton#favoriteShortcut:focus {border:1px solid @accent@;}
QToolButton[segment="true"]:focus {border:1px solid @text@;}
QPushButton#primary:focus,QPushButton[primaryAction="true"]:focus {border:1px solid @text@;}
'''

def stylesheet():return colorize(STYLE)
