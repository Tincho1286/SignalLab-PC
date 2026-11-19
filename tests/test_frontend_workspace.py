"""Interaction contracts for the refreshed shared desktop, without math reruns."""
import os,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QPushButton,QScrollArea,QComboBox
from PySide6.QtTest import QTest
from signallab_pc.tool_workspace import ToolWorkspace
from signallab_pc.result_toolbar import ResultActionBar,ORDER,attach
from signallab_pc.active_stack import ActiveTabs


class Frontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):self.widgets=[]
    def tearDown(self):
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.app.processEvents()
    def settle(self):self.app.processEvents();QTest.qWait(20);self.app.processEvents()
    def test_action_slots_do_not_move_when_an_action_is_unavailable(self):
        bar=ResultActionBar();self.widgets.append(bar)
        for role in ('export','cas','reuse','graph'):
            button=QPushButton(role);bar.add_action(button,role)
        bar.resize(800,100);bar.show();self.settle();positions=[bar.grid.getItemPosition(bar.grid.indexOf(bar.slots[role]))[:2] for role in ORDER];self.assertEqual(positions,[(0,0),(0,1),(0,2),(0,3)])
        bar.slots['reuse'].hide();self.settle();self.assertTrue(bar.placeholders['reuse'].isVisible());self.assertEqual(bar.grid.getItemPosition(bar.grid.indexOf(bar.slots['cas']))[:2],(0,2))
    def test_compact_action_grid_preserves_order_and_connections(self):
        bar=ResultActionBar();self.widgets.append(bar);clicked=[]
        for role in ORDER:
            button=QPushButton(role);button.clicked.connect(lambda checked=False,r=role:clicked.append(r));bar.add_action(button,role)
        bar.resize(430,100);bar.show();self.settle();positions=[bar.grid.getItemPosition(bar.grid.indexOf(bar.slots[role]))[:2] for role in ORDER];self.assertEqual(positions,[(0,0),(0,1),(1,0),(1,1)]);bar.slots['cas'].click();self.assertEqual(clicked,['cas'])
    def test_workspace_keeps_controls_and_result_when_changing_size(self):
        inputs=QWidget();form=QVBoxLayout(inputs);button=QPushButton('dato');form.addWidget(button);result=QWidget();space=ToolWorkspace(inputs,result);self.widgets.append(space);space.resize(1200,700);space.show();self.settle();self.assertFalse(space.compact);space.resize(700,600);self.settle();self.assertTrue(space.compact);space.show_results();self.assertEqual(space.tabs.currentIndex(),1);space.tabs.setCurrentIndex(0);self.assertTrue(button.isVisible());space.resize(1200,700);self.settle();self.assertFalse(space.compact);self.assertIs(space.inputs.content.widget(),inputs);self.assertIs(space.results.content,result)
    def test_graph_moves_with_the_active_result_action_set(self):
        result=QWidget();layout=QVBoxLayout(result);home=ResultActionBar();system=ResultActionBar();system.setProperty('systemResultActions',True);layout.addWidget(home);layout.addWidget(system);graph=QPushButton('graph');home.add_action(graph,'graph');system.hide();space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);space.show();self.settle();self.assertIs(graph.parentWidget(),home);home.hide();system.show();self.settle();self.assertIs(graph.parentWidget(),system);system.hide();home.show();self.settle();self.assertIs(graph.parentWidget(),home)
    def test_long_visible_choices_wrap_without_changing_the_selected_value(self):
        from signallab_pc.choice_buttons import ChoiceButtons
        combo=QComboBox();combo.addItems(['Una opción con un título extenso','Una segunda opción']);choices=ChoiceButtons(combo);self.widgets.append(choices);choices.resize(260,120);choices.show();self.settle();self.assertGreater(choices.buttons[1].y(),choices.buttons[0].y());choices.buttons[1].click();self.assertEqual(combo.currentIndex(),1);choices.resize(900,120);self.settle();self.assertEqual(choices.buttons[1].y(),choices.buttons[0].y())
    def test_nested_controls_use_one_scroll_container(self):
        content=QWidget();layout=QVBoxLayout(content);inner=QScrollArea();body=QWidget();inner.setWidget(body);layout.addWidget(inner);space=ToolWorkspace(content,QWidget());self.widgets.append(space);space.show();self.settle();self.assertEqual(len(space.inputs.findChildren(QScrollArea)),1);self.assertIs(body.parentWidget(),content)
    def test_result_choices_expose_complete_labels_and_keep_existing_callbacks(self):
        from signallab_pc.result_selector import install
        parent=QWidget();layout=QVBoxLayout(parent);bar=ResultActionBar();layout.addWidget(bar);tabs=ActiveTabs();layout.addWidget(tabs);self.widgets.append(parent);clicked=[];tabs.tabBar().tabBarClicked.connect(clicked.append)
        for title in ('Resumen','Respuesta en frecuencia','Una función de transferencia con título largo'):tabs.addTab(QWidget(),title)
        attach(tabs,bar);install(tabs);parent.resize(440,500);parent.show();self.settle();self.assertTrue(tabs.tabBar().isHidden());buttons=tabs.result_selector.row.findChildren(QPushButton)
        from PySide6.QtWidgets import QToolButton
        buttons=tabs.result_selector.row.findChildren(QToolButton);self.assertEqual([button.text() for button in buttons],['Resumen','Respuesta en frecuencia','Una función de transferencia con título largo']);buttons[-1].click();self.settle();self.assertEqual(tabs.currentIndex(),2);self.assertEqual(clicked,[2]);tabs.setTabVisible(1,False);self.settle();self.assertEqual([button.text() for button in tabs.result_selector.row.findChildren(QToolButton)],['Resumen','Una función de transferencia con título largo']);tabs.setTabVisible(1,True);self.settle();self.assertEqual(len(tabs.result_selector.row.findChildren(QToolButton)),3)
    def test_action_dock_tracks_the_selected_result_without_losing_commands(self):
        from signallab_pc.result_action_dock import install
        tabs=ActiveTabs();bars=[];clicked=[]
        for i in range(2):
            page=QWidget();layout=QVBoxLayout(page);bar=ResultActionBar();button=QPushButton('usar');button.clicked.connect(lambda checked=False,index=i:clicked.append(index));bar.add_action(button,'reuse');layout.addWidget(bar);tabs.addTab(page,str(i));bars.append(bar)
        space=ToolWorkspace(QWidget(),tabs);self.widgets.append(space);space.resize(1200,700);dock=install(space.results);wrappers={bar:wrapper for bar,_,wrapper in dock.entries};space.show();self.settle();self.assertTrue(wrappers[bars[0]].isVisible());self.assertFalse(wrappers[bars[1]].isVisible());tabs.setCurrentIndex(1);self.settle();self.assertFalse(wrappers[bars[0]].isVisible());self.assertTrue(wrappers[bars[1]].isVisible());bars[1].slots['reuse'].click();self.assertEqual(clicked,[1]);bars[1].hide();self.settle();self.assertTrue(dock.isHidden())
    def test_last_graph_stays_available_when_the_design_commands_are_disabled(self):
        from signallab_pc.result_action_dock import install
        result=QWidget();layout=QVBoxLayout(result);bar=ResultActionBar();layout.addWidget(bar);space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);dock=install(space.results);graph=QPushButton('graph');clicked=[];graph.clicked.connect(lambda:clicked.append(True));dock.set_graph(graph);space.show();self.settle();self.assertIs(graph.parentWidget(),bar);bar.setEnabled(False);self.settle();self.assertIs(graph.parentWidget(),dock.fallback);self.assertTrue(graph.isEnabled());graph.click();self.assertEqual(clicked,[True]);bar.setEnabled(True);self.settle();self.assertIs(graph.parentWidget(),bar)
    def test_task_search_accepts_keyboard_selection_and_filters_the_cas(self):
        from signallab_pc.studio_shell import TaskSearch
        from PySide6.QtCore import Qt
        parent=QWidget();dialog=TaskSearch(parent);self.widgets.extend([parent,dialog]);dialog.show();self.settle();QTest.keyClick(dialog.query,Qt.Key.Key_Down);self.assertEqual(dialog.list.currentRow(),1);dialog.query.setText('CAS');self.settle();self.assertEqual(dialog.list.item(0).data(Qt.ItemDataRole.UserRole),'cas');QTest.keyClick(dialog.query,Qt.Key.Key_Return);self.assertEqual(dialog.selection,'cas')
    def test_multiple_outputs_share_one_toolbar_with_an_explicit_target(self):
        from signallab_pc.result_action_dock import install
        result=QWidget();layout=QVBoxLayout(result);bars=[];clicked=[]
        for i in range(2):
            bar=ResultActionBar();button=QPushButton('Usar señal en…');button.clicked.connect(lambda checked=False,index=i:clicked.append(index));bar.add_action(button,'reuse');layout.addWidget(bar);bars.append(bar)
        bars[1].setProperty('systemResultActions',True);space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);dock=install(space.results);space.show();self.settle();self.assertTrue(dock.target_row.isVisible());self.assertIs(dock.chosen,bars[1]);dock.target.setCurrentIndex(dock.choices.index(bars[0]));self.settle();self.assertIs(dock.chosen,bars[0]);self.assertEqual(sum(wrapper.isVisible() for _,_,wrapper in dock.entries),1);bars[0].slots['reuse'].click();self.assertEqual(clicked,[0])
    def test_legacy_signal_result_is_ready_for_reuse_without_an_extra_plot(self):
        from signallab_pc.toolbox import ResultView,LocalContext
        from signallab_pc.model import Signal
        class Host(QWidget):
            def publish(self,value,**options):return 'captured-signal'
            def send_signal(self,*args):pass
            def open_cas(self):pass
        host=Host();self.widgets.append(host);layout=QVBoxLayout(host);view=ResultView();layout.addWidget(view);context=LocalContext(host,None,view);value=Signal([1,2]);before=len(view.figure.axes);context._remember_signal(value);self.assertIs(view.result,value);self.assertEqual(view.result_ids,['captured-signal']);self.assertTrue(view.send.isEnabled());self.assertTrue(view.cas_button.isEnabled());self.assertTrue(view.save.isEnabled());self.assertEqual(len(view.figure.axes),before);view.clear_result();self.assertFalse(any(button.isEnabled() for button in (view.send,view.cas_button,view.save)))
    def test_saved_results_keep_selection_and_disable_commands_for_an_empty_filter(self):
        from signallab_pc.results_browser import ResultsBrowser
        from signallab_pc.toolbox import ToolboxWindow
        from signallab_pc.project import Project
        from signallab_pc.model import Signal
        class Host(QWidget):
            refresh_project=ToolboxWindow.refresh_project
            show_record=ToolboxWindow.show_record
            def open_selected_signal(self):pass
            def prepare_selected_reuse(self):pass
            def export_selected(self):pass
            def save_project(self):pass
            def import_project(self):pass
        host=Host();host.project=Project();key=host.project.add(Signal([0,1,0],-1,name='Pulso'));self.widgets.append(host);layout=QVBoxLayout(host);browser=ResultsBrowser(host);layout.addWidget(browser);host.resize(1200,720);host.show();self.settle();self.assertEqual(host.visible_records[0]['id'],key);self.assertTrue(host.cas_selection.isEnabled());self.assertEqual(set(browser.actions.slots),set(ORDER));host.result_search.setText('no existe');self.settle();self.assertFalse(host.cas_selection.isEnabled());self.assertFalse(host.reuse_selection.isEnabled());host.result_search.clear();host.resize(700,620);self.settle();self.assertEqual([browser.workspace.tabs.tabText(i) for i in range(2)],['Resultados','Detalle']);self.assertTrue(host.cas_selection.isEnabled());self.assertEqual(host.visible_records[0]['id'],key)
    def test_theme_icon_refresh_handles_widgets_with_a_result_actions_attribute(self):
        from PySide6.QtGui import QAction
        from signallab_pc.design import refresh_icons,icon
        parent=QWidget();self.widgets.append(parent);parent.actions=ResultActionBar(parent);button=QPushButton(parent);button.setIcon(icon('signal'));action=QAction(parent);action.setIcon(icon('book'));parent.addAction(action);before=action.icon().cacheKey();refresh_icons(self.app);self.assertFalse(button.icon().isNull());self.assertNotEqual(action.icon().cacheKey(),before)


if __name__=='__main__':unittest.main()
