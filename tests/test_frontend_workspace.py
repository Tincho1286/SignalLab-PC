"""Interaction contracts for the refreshed shared desktop, without math reruns."""
import os,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QPushButton,QScrollArea,QComboBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt
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
        labels = ('Abrir gráfico', 'Usar señal en otra herramienta…', 'Enviar a CAS', 'Exportar resultado…')
        for role, label in zip(ORDER, labels):
            button=QPushButton(label);button.clicked.connect(lambda checked=False,r=role:clicked.append(r));bar.add_action(button,role)
        bar.resize(350,100);bar.show();self.settle();positions=[bar.grid.getItemPosition(bar.grid.indexOf(bar.slots[role]))[:2] for role in ORDER];self.assertEqual(positions,[(0,0),(0,1),(1,0),(1,1)]);bar.slots['cas'].click();self.assertEqual(clicked,['cas'])
    def test_workspace_keeps_controls_and_result_when_changing_size(self):
        inputs=QWidget();form=QVBoxLayout(inputs);button=QPushButton('dato');form.addWidget(button);result=QWidget();space=ToolWorkspace(inputs,result);self.widgets.append(space);space.resize(1200,700);space.show();self.settle();self.assertFalse(space.compact);space.resize(700,600);self.settle();self.assertTrue(space.compact);space.show_results();self.assertEqual(space.tabs.currentIndex(),1);space.tabs.setCurrentIndex(0);self.assertTrue(button.isVisible());space.resize(1200,700);self.settle();self.assertFalse(space.compact);self.assertTrue(space.inputs.content.widget().isAncestorOf(inputs));self.assertIs(space.results.content,result)
    def test_wrapping_document_header_does_not_force_the_preferred_workspace_height(self):
        from PySide6.QtWidgets import QLabel
        from signallab_pc.problem_document import ProblemDocument
        document=ProblemDocument({});header=QLabel('Opciones del cálculo');header.setWordWrap(True);document.layout().insertWidget(0,header);page=QWidget();page.tool_item=('Prueba','test',0,None);root=QVBoxLayout(page);root.setContentsMargins(0,0,0,0);space=ToolWorkspace(QWidget(),QWidget());root.addWidget(space);document.select_page(page);view=QScrollArea();view.setWidgetResizable(True);view.setWidget(document);self.widgets.append(view);view.resize(650,400);view.show();self.settle();self.assertEqual(view.verticalScrollBar().maximum(),0);self.assertLess(space.height(),600);self.assertTrue(space.inputs.isVisibleTo(view));self.assertTrue(space.tabs.isVisibleTo(view))
    def test_expanded_output_preserves_the_same_result_across_resize(self):
        result = QWidget()
        space = ToolWorkspace(QWidget(), result)
        self.widgets.append(space)
        space.resize(1200, 700)
        space.show()
        self.settle()
        initial = space.split.sizes()
        space.set_output_expanded(True)
        self.assertTrue(space.inputs.isHidden())
        self.assertTrue(result.isVisible())
        space.resize(680, 500)
        self.settle()
        self.assertIs(space.tabs.currentWidget(), space.results)
        self.assertTrue(space.tabs.tabBar().isHidden())
        space.resize(1200, 700)
        self.settle()
        space.show_inputs()
        self.settle()
        self.assertFalse(space.output_expanded)
        self.assertEqual(space.split.sizes(), initial)
        self.assertIs(space.results.content, result)
        space.resize(680, 500)
        self.settle()
        self.assertTrue(space.tabs.tabBar().isVisible())
    def test_graph_moves_with_the_active_result_action_set(self):
        result=QWidget();layout=QVBoxLayout(result);home=ResultActionBar();system=ResultActionBar();system.setProperty('systemResultActions',True);layout.addWidget(home);layout.addWidget(system);graph=QPushButton('graph');home.add_action(graph,'graph');system.hide();space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);space.show();self.settle();self.assertIs(graph.parentWidget(),home);home.hide();system.show();self.settle();self.assertIs(graph.parentWidget(),system);system.hide();home.show();self.settle();self.assertIs(graph.parentWidget(),home)
    def test_long_visible_choices_wrap_without_changing_the_selected_value(self):
        from signallab_pc.choice_buttons import ChoiceButtons
        combo=QComboBox();combo.addItems(['Una opción con un título extenso','Una segunda opción']);choices=ChoiceButtons(combo);self.widgets.append(choices);choices.resize(260,120);choices.show();self.settle();self.assertGreater(choices.buttons[1].y(),choices.buttons[0].y());choices.buttons[1].click();self.assertEqual(combo.currentIndex(),1);choices.resize(900,120);self.settle();self.assertEqual(choices.buttons[1].y(),choices.buttons[0].y())
    def test_nested_controls_use_one_scroll_container(self):
        content=QWidget();layout=QVBoxLayout(content);inner=QScrollArea();body=QWidget();inner.setWidget(body);layout.addWidget(inner);space=ToolWorkspace(content,QWidget());self.widgets.append(space);space.show();self.settle();self.assertEqual(len(space.inputs.findChildren(QScrollArea)),1);self.assertIs(body.parentWidget(),content)

    def test_wrapped_controls_reserve_all_rows_in_a_short_scroll_view(self):
        from signallab_pc.wrapping_row import WrappingRow
        scroll = QScrollArea()
        self.widgets.append(scroll)
        scroll.setWidgetResizable(True)
        body = QWidget()
        layout = QVBoxLayout(body)
        choices = WrappingRow()
        layout.addWidget(choices)
        buttons = [QPushButton('Una opción amplia ' + str(index)) for index in range(5)]
        for button in buttons:
            choices.flow.addWidget(button)
        last = QPushButton('Último control')
        layout.addWidget(last)
        scroll.setWidget(body)
        scroll.resize(320, 125)
        scroll.show()
        self.settle()
        self.assertGreater(buttons[-1].y(), buttons[0].y())
        self.assertTrue(choices.rect().contains(buttons[-1].geometry()))
        self.assertLess(choices.geometry().bottom(), last.geometry().top())
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
        self.assertTrue(scroll.viewport().rect().contains(last.mapTo(scroll.viewport(), last.rect().center())))

    def test_short_figure_keeps_vertical_axis_titles(self):
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
        from signallab_pc.plot_view import fit_axis_labels
        figure = Figure(figsize=(5.6, 3.1))
        canvas = FigureCanvasAgg(figure)
        axes = figure.subplots(3, 1, sharex=True)
        expected = ('Módulo (dB)', 'Fase continua (rad)', 'Retardo (muestras)')
        for axis, label in zip(axes, expected):
            axis.set_ylabel(label)
        fit_axis_labels(canvas)
        self.assertEqual(tuple(axis.get_ylabel() for axis in axes), expected)
        self.assertTrue(all(axis.yaxis.label.get_rotation() == 90 for axis in axes))
    def test_result_choices_expose_complete_labels_and_keep_existing_callbacks(self):
        from signallab_pc.result_selector import install
        parent=QWidget();layout=QVBoxLayout(parent);bar=ResultActionBar();layout.addWidget(bar);tabs=ActiveTabs();layout.addWidget(tabs);self.widgets.append(parent);clicked=[];tabs.tabBar().tabBarClicked.connect(clicked.append)
        titles = ['Resumen', 'Respuesta en frecuencia', 'Una función de transferencia con título largo']
        for title in titles:
            tabs.addTab(QWidget(), title)
        attach(tabs,bar);install(tabs);parent.resize(920,500);parent.show();self.settle()
        selector = tabs.result_selector
        self.assertTrue(tabs.tabBar().isHidden())
        self.assertTrue(selector.row.isVisible())
        self.assertEqual([button.text() for button in selector.buttons.values()], titles)
        selector.buttons[2].click()
        self.assertEqual(tabs.currentIndex(), 2)
        self.assertEqual(clicked, [2])
        tabs.setTabVisible(1, False)
        self.assertEqual([button.text() for button in selector.buttons.values()], [titles[0], titles[2]])
        tabs.setTabVisible(1, True)
        parent.resize(340, 500)
        self.settle()
        self.assertTrue(selector.picker.isVisible())
        self.assertEqual([selector.picker.itemText(i) for i in range(selector.picker.count())], titles)
        selector.picker.activated.emit(selector.picker.findData(1))
        self.assertEqual(tabs.currentIndex(), 1)
        self.assertEqual(clicked, [2, 1])
        tabs.hide();self.settle();self.assertTrue(selector.container.isHidden())
        tabs.show();parent.resize(920,500);self.settle();self.assertTrue(selector.row.isVisible())
        selected=selector.buttons[0];parent.activateWindow();selected.setFocus();QTest.keyClick(selected,Qt.Key.Key_Space);self.settle();self.assertIs(selector.buttons[0],selected);self.assertIs(self.app.focusWidget(),selected)
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
        from signallab_pc.command_palette import TaskSearch, TARGET
        from signallab_pc.project import Project
        from PySide6.QtWidgets import QTabBar
        from PySide6.QtCore import Qt
        parent = QWidget()
        parent.documents = QTabBar(parent)
        parent.favorite_tools = parent.recent_tools = []
        parent.project = Project()
        dialog = TaskSearch(parent)
        self.widgets.extend([parent, dialog])
        dialog.show()
        self.settle()
        first = dialog.list.currentRow()
        QTest.keyClick(dialog.query, Qt.Key.Key_Down)
        self.assertGreater(dialog.list.currentRow(), first)
        self.assertIsNotNone(dialog.list.currentItem().data(TARGET))
        dialog.query.setText('CAS')
        self.assertEqual(dialog.list.currentItem().data(TARGET), ('command', 'cas'))
        QTest.keyClick(dialog.query, Qt.Key.Key_Return)
        self.assertEqual(dialog.selection, ('command', 'cas'))
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
    def test_export_menu_keeps_original_callbacks_and_tracks_new_result_availability(self):
        from signallab_pc.result_action_dock import install
        from signallab_pc.result_exports import mark_export
        result=QWidget();layout=QVBoxLayout(result);bar=ResultActionBar();layout.addWidget(bar);saved=[];original=QPushButton('Exportar señal');original.clicked.connect(lambda:saved.append('signal'));original.setEnabled(False);bar.add_action(original,'export');table=mark_export(QPushButton('Exportar tabla'));table.clicked.connect(lambda:saved.append('table'));table.setEnabled(False);layout.addWidget(table)
        space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);dock=install(space.results);space.show();self.settle();hub=space.results.result_exports;proxy=bar.slots['export'];self.assertFalse(proxy.isEnabled());original.setEnabled(True);table.setEnabled(True);self.settle();self.assertTrue(proxy.isEnabled());self.assertTrue(original.isHidden());self.assertTrue(table.isHidden());hub.prepare(bar)
        for action in proxy.menu().actions():
            if not action.isSeparator():action.trigger()
        self.assertEqual(saved,['signal','table']);table.show();self.settle();self.assertTrue(table.isHidden());original.setEnabled(False);table.setEnabled(False);self.settle();self.assertFalse(proxy.isEnabled())
    def test_report_exports_follow_available_result_tabs_without_duplicate_formats(self):
        from unittest.mock import patch
        from signallab_pc.result_action_dock import install
        from signallab_pc.report_view import ReportView,report_panel
        result=QWidget();layout=QVBoxLayout(result);bar=ResultActionBar();layout.addWidget(bar);tabs=ActiveTabs();report=ReportView();report.setPlainText('Informe disponible');tabs.addTab(report_panel(report),'Informe');other=QPushButton('otra vista');tabs.addTab(other,'Valores');layout.addWidget(tabs);bar.use_report(report);space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);install(space.results);space.show();self.settle();hub=space.results.result_exports;hub.prepare(bar);actions=[a for a in bar.slots['export'].menu().actions() if not a.isSeparator()];self.assertEqual(len(actions),3);calls=[]
        with patch.object(report,'export_document',side_effect=calls.append):
            for action in actions:action.trigger()
        self.assertEqual(calls,[True,False]);self.assertEqual(self.app.clipboard().text(),'Informe disponible');tabs.setCurrentIndex(1);self.settle();hub.prepare(bar);self.assertEqual(len([a for a in bar.slots['export'].menu().actions() if not a.isSeparator()]),3);tabs.setTabVisible(0,False);self.settle();hub.prepare(bar);self.assertFalse(any(a.isEnabled() for a in bar.slots['export'].menu().actions()))
    def test_replaced_result_commands_cannot_reappear_over_their_replacement(self):
        bar=ResultActionBar();self.widgets.append(bar);old=QPushButton('Usar señal');bar.add_action(old,'reuse');new=QPushButton('Usar tasa en muestreo');bar.replace_action('reuse',new);bar.show();self.settle();old.show();self.settle();self.assertTrue(old.isHidden());self.assertTrue(new.isVisible());self.assertIs(bar.slots['reuse'],new)
    def test_diagram_commands_share_the_figure_launcher_and_original_handler(self):
        from signallab_pc.result_action_dock import install
        result=QWidget();layout=QVBoxLayout(result);bar=ResultActionBar();layout.addWidget(bar);tabs=ActiveTabs();page=QWidget();inside=QVBoxLayout(page);button=QPushButton('Abrir diagrama');button.setProperty('resultGraphAction','Diagrama');button.setEnabled(False);called=[];button.clicked.connect(lambda:called.append(True));inside.addWidget(button);tabs.addTab(page,'Realización');tabs.addTab(QWidget(),'Informe');layout.addWidget(tabs);space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);dock=install(space.results);space.show();self.settle();self.assertTrue(button.isHidden());self.assertFalse(dock.graph.isEnabled());button.setEnabled(True);self.settle();self.assertTrue(dock.graph.isEnabled());tabs.setCurrentIndex(1);self.settle();self.assertEqual(len(dock.graph.available()),1);dock.graph.open_default();self.assertEqual(called,[True]);tabs.setTabVisible(0,False);self.settle();dock.graph.refresh();self.assertFalse(dock.graph.isEnabled())
    def test_contextual_model_destinations_join_the_primary_reuse_menu(self):
        from PySide6.QtWidgets import QMenu
        from signallab_pc.result_action_dock import install
        result=QWidget();layout=QVBoxLayout(result);bar=ResultActionBar();bar.setProperty('systemResultActions',True);reuse=QPushButton('Usar sistema en…');menu=QMenu(reuse);reuse.setMenu(menu)
        def rebuild():menu.clear();menu.addAction('Destino habitual')
        menu.aboutToShow.connect(rebuild);bar.add_action(reuse,'reuse');layout.addWidget(bar);source=QPushButton('Usar modelo');source.setProperty('resultReuseMenu','Modelo de la realización');model=QMenu(source);source.setMenu(model);called=[];model.addAction('Simular',lambda:called.append(True));layout.addWidget(source);space=ToolWorkspace(QWidget(),result);self.widgets.append(space);space.resize(1200,700);install(space.results);space.show();self.settle();self.assertTrue(source.isHidden());menu.aboutToShow.emit();self.assertEqual(menu.actions()[-1].text(),'Modelo de la realización');menu.actions()[-1].menu().actions()[0].trigger();self.assertEqual(called,[True]);menu.aboutToShow.emit();self.assertEqual(len(menu.actions()),3)
    def test_file_and_saved_result_views_keep_distinct_sources_and_matching_controls(self):
        from signallab_pc.toolbox import LocalInput
        from signallab_pc.model import Signal
        field=LocalInput('Entrada');self.widgets.append(field);field.show();file=Signal([1,2],name='Archivo');saved=Signal([7,8],name='Resultado');field.set_source(file);field.entry_modes.select(3);self.settle();self.assertIsNone(field.loaded);self.assertNotIn('MATLAB',field.file_note.text());load=next(b for b in field.findChildren(QPushButton) if b.text()=='Elegir archivo…');self.assertTrue(load.isHidden())
        with self.assertRaisesRegex(ValueError,'Resultados'):field.read()
        field.set_source(saved,'saved-id');field.entry_modes.select(2);self.settle();self.assertIs(field.loaded,file);self.assertFalse(load.isHidden());field.entry_modes.select(3);self.assertIs(field.loaded,saved);self.assertEqual(field.loaded_reference_id,'saved-id');field.clear_source();field.entry_modes.select(2);self.assertIs(field.loaded,file)
    def test_swapping_drafts_keeps_both_external_sources_and_empty_source_views(self):
        from signallab_pc.toolbox import LocalInput
        from signallab_pc.model import Signal
        from signallab_pc.input_drafts import swap
        from signallab_pc.workflow_inputs import copy_local_input
        first=LocalInput('x');second=LocalInput('w');self.widgets.extend((first,second));a=Signal([1]);b=Signal([2]);c=Signal([3]);first.set_source(a);first.set_source(b,'result-b');second.set_source(c);second.entry_modes.select(0);swap(first,second);first.entry_modes.select(2);self.assertEqual(first.read().values[0],3);first.entry_modes.select(3);self.assertIsNone(first.loaded);second.entry_modes.select(3);self.assertEqual(second.loaded_reference_id,'result-b');second.entry_modes.select(2);self.assertEqual(second.read().values[0],1);copy_local_input(first,second);self.assertEqual(second.entry_modes.view,3);self.assertIsNone(second.loaded)
    def test_live_band_hints_do_not_select_partial_expressions_but_calculation_still_validates(self):
        from signallab_pc.band_edges import BandEdgesEditor
        editor=BandEdgesEditor();self.widgets.append(editor);editor.show();field=editor.edits[0];field.setFocus();field.selectAll();QTest.keyClicks(field,'0.2*pi');self.settle();self.assertEqual(field.text(),'0.2*pi');self.assertFalse(field.property('inputError'));field.setText('incompleto');self.assertFalse(field.property('inputError'))
        with self.assertRaises(ValueError):editor.frequencies()
        self.assertTrue(field.property('inputError'));self.assertTrue(field.hasSelectedText())
    def test_coefficient_order_is_visible_for_both_domains_without_parsing_the_values(self):
        from signallab_pc.coefficient_editor import CoefficientEditor
        editor=CoefficientEditor('pi, 0, 10^(-3)');self.widgets.append(editor);self.assertIn('s², s, 1',editor.order_note.text());editor.set_domain(True);self.assertIn('1, z⁻¹, z⁻²',editor.order_note.text());self.assertEqual(editor.text(),'pi, 0, 10^(-3)')
    def test_resize_keeps_the_focused_surface_and_splitter_proportions(self):
        from PySide6.QtWidgets import QLineEdit
        inputs=QWidget();left=QVBoxLayout(inputs);entry=QLineEdit('dato');left.addWidget(entry);result=QWidget();right=QVBoxLayout(result);output=QLineEdit('salida');right.addWidget(output);space=ToolWorkspace(inputs,result);self.widgets.append(space);space.resize(1200,700);space.show();space.activateWindow();self.settle();space.split.setSizes([450,700]);before=space.split.sizes();space.show_results();entry.setFocus();space.resize(700,600);self.settle();self.assertEqual(space.tabs.currentIndex(),0);self.assertIs(self.app.focusWidget(),entry);space.resize(1200,700);self.settle();after=space.split.sizes();self.assertAlmostEqual(after[0]/sum(after),before[0]/sum(before),places=2);output.setFocus();space.resize(700,600);self.settle();self.assertEqual(space.tabs.currentIndex(),1);self.assertIs(self.app.focusWidget(),output)
    def test_result_freshness_stays_with_the_output_and_keeps_its_input_tracking(self):
        from PySide6.QtWidgets import QLineEdit,QFormLayout,QHBoxLayout
        from signallab_pc.result_state import ResultState
        from signallab_pc.tool_workspace import install
        page=QWidget();self.widgets.append(page);root=QHBoxLayout(page);inputs=QWidget();form=QFormLayout(inputs);field=QLineEdit('1');button=QPushButton('Calcular');state=ResultState([field],button);form.addRow(state);form.addRow('Entrada',field);form.addRow(button);output=QWidget();QVBoxLayout(output);root.addWidget(inputs);root.addWidget(output);space=install(page);self.assertIs(state.parentWidget(),space.results);self.assertTrue(state.isHidden());state.accept(state.snapshot());self.assertFalse(state.isHidden());field.setText('2');self.assertTrue(state.property('resultStale'));self.assertEqual(button.text(),'Recalcular');state.accept(state.snapshot());self.assertFalse(state.property('resultStale'));self.assertEqual(button.text(),'Calcular')
    def test_desktop_shortcuts_route_to_the_active_workspace_and_leave_dialogs_alone(self):
        from PySide6.QtWidgets import QMainWindow,QLineEdit,QTabBar,QStackedWidget,QDialog,QMenu
        from PySide6.QtCore import Qt
        from signallab_pc.desktop_keys import DesktopKeys
        from signallab_pc.result_action_dock import install
        class Host(QMainWindow):
            def calculate_active(self):self.calls.append('calculate')
            def close_document(self,index):self.calls.append('close');self.documents.removeTab(index)
        host=Host();host.calls=[];self.widgets.append(host);root=QWidget();layout=QVBoxLayout(root);host.setCentralWidget(root);host.documents=QTabBar();host.documents.addTab('Primero');host.documents.addTab('Segundo');layout.addWidget(host.documents);host.stack=QStackedWidget();layout.addWidget(host.stack);page=QWidget();body=QVBoxLayout(page);inputs=QWidget();left=QVBoxLayout(inputs);entry=QLineEdit('entrada');left.addWidget(entry);result=QWidget();right=QVBoxLayout(result);bar=ResultActionBar();graph=QPushButton('Abrir gráfico');graph.clicked.connect(lambda:host.calls.append('graph'));bar.add_action(graph,'graph');export=QPushButton('Exportar datos');export.clicked.connect(lambda:host.calls.append('export'));bar.add_action(export,'export');right.addWidget(bar);output=QLineEdit('resultado');right.addWidget(output);page.workspace=ToolWorkspace(inputs,result);body.addWidget(page.workspace);host.stack.addWidget(page);install(page.workspace.results);keys=DesktopKeys(host);host.resize(1200,760);host.show();host.activateWindow();entry.setFocus();self.settle()
        QTest.keyClick(entry,Qt.Key.Key_Return,Qt.KeyboardModifier.ControlModifier);QTest.keyClick(entry,Qt.Key.Key_Enter,Qt.KeyboardModifier.ControlModifier);self.assertEqual(host.calls,['calculate','calculate']);output.setFocus();QTest.keyClick(output,Qt.Key.Key_1,Qt.KeyboardModifier.AltModifier);self.settle();self.assertIs(self.app.focusWidget(),entry);QTest.keyClick(entry,Qt.Key.Key_2,Qt.KeyboardModifier.AltModifier);self.settle();self.assertIs(self.app.focusWidget(),output);QTest.keyClick(output,Qt.Key.Key_G,Qt.KeyboardModifier.AltModifier);self.assertEqual(host.calls[-1],'graph');QTest.keyClick(graph,Qt.Key.Key_E,Qt.KeyboardModifier.AltModifier);self.settle();menu=bar.slots['export'].menu();self.assertIs(self.app.activePopupWidget(),menu);next(action for action in menu.actions() if not action.isSeparator()).trigger();menu.hide();self.assertEqual(host.calls[-1],'export');QTest.keyClick(graph,Qt.Key.Key_Tab,Qt.KeyboardModifier.ControlModifier);self.assertEqual(host.documents.currentIndex(),1);QTest.keyClick(graph,Qt.Key.Key_W,Qt.KeyboardModifier.ControlModifier);self.assertEqual(host.documents.count(),1)
        from signallab_pc.plot_actions import PlotLauncher
        launcher=PlotLauncher(bar);diagram=QPushButton('Diagrama',result);diagram.clicked.connect(lambda:host.calls.append('diagram'));launcher.register(diagram,[],'Diagrama');bar.replace_action('graph',launcher);self.settle();QTest.keyClick(output,Qt.Key.Key_G,Qt.KeyboardModifier.AltModifier);self.assertEqual(host.calls[-1],'diagram')
        dialog=QDialog(host);self.widgets.append(dialog);dialog.show();dialog.activateWindow();self.settle();before=list(host.calls);keys.commands['calculate'].trigger();self.assertEqual(host.calls,before)
        from PySide6.QtCore import QCoreApplication,QEvent
        host.stack.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);self.assertIsNone(keys.active_page());keys.remember_focus(None,dialog)
    def test_theme_change_updates_existing_axes_and_legends_without_changing_data_or_view(self):
        import numpy as np
        from numpy.testing import assert_array_equal
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.colors import to_hex
        from signallab_pc.appearance import apply
        from signallab_pc import theme_presets
        from signallab_pc.theme_tokens import COLORS as C
        old=theme_presets.CURRENT;host=QWidget();self.widgets.append(host);layout=QVBoxLayout(host);figure=Figure(facecolor=C['report']);canvas=FigureCanvasQTAgg(figure);layout.addWidget(canvas);axis=figure.subplots();axis.set_facecolor(C['panel']);axis.set_xlabel('ω',color=C['text']);axis.set_ylabel('|H|',color=C['text']);line=axis.plot([0,1,2],[0,1,0],color=C['blue'],label='Curva')[0];axis.scatter([1],[1],color=C['green'],label='Muestra');legend=axis.legend(facecolor=C['report'],edgecolor=C['border']);figure.legend([line],['Curva']);axis.set_xlim(.2,1.8);limits=axis.get_xlim();values=line.get_ydata().copy();canvas.draw();host.hide()
        try:
            apply(host,'light',persist=False);self.assertEqual(to_hex(axis.get_facecolor()),C['panel']);self.assertEqual(to_hex(figure.get_facecolor()),C['report']);self.assertEqual(to_hex(axis.xaxis.label.get_color()),C['text']);self.assertEqual(to_hex(legend.legend_handles[1].get_facecolors()[0]),C['green']);self.assertEqual(to_hex(figure.legends[0].legend_handles[0].get_color()),C['blue']);self.assertEqual(axis.get_xlim(),limits);assert_array_equal(line.get_ydata(),values);self.assertFalse(host.isVisible())
        finally:apply(host,old,persist=False)
    def test_transparent_photo_keeps_reading_surfaces_and_restores_normal_viewports(self):
        from unittest.mock import patch
        from PySide6.QtWidgets import QLabel
        from signallab_pc import wallpaper,theme_presets
        from signallab_pc.theme_tokens import COLORS as C
        host=QWidget();self.widgets.append(host);layout=QVBoxLayout(host);label=QLabel('Datos de entrada');layout.addWidget(label);area=QScrollArea();area.setWidget(QWidget());layout.addWidget(area);before=area.viewport().autoFillBackground();config=dict(photo='local-photo.png',opacity=100,surface_opacity=0)
        with patch.object(theme_presets,'CURRENT','custom'),patch.object(theme_presets,'CUSTOM',config):
            wallpaper.refresh(host);self.assertTrue(label.property('photoReading'));self.assertEqual(wallpaper.panel_color(C['panel'],0).alpha(),0);self.assertEqual(wallpaper.reading_opacity(config),92);self.assertIn('photoReading',wallpaper.stylesheet());self.assertFalse(area.viewport().autoFillBackground())
        wallpaper.refresh(host);self.assertFalse(label.property('photoReading'));self.assertEqual(area.viewport().autoFillBackground(),before)


if __name__=='__main__':unittest.main()
