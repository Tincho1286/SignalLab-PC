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


if __name__=='__main__':unittest.main()
