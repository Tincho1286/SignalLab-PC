"""Result handoff, scientific views and session persistence through Qt."""
import json
from unittest.mock import patch

import numpy as np
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QFileDialog, QInputDialog

from signallab_pc import session
from signallab_pc.cas_engine import restore
from signallab_pc.cas_panel import CAS_ROUTE
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.realization_graph import Block, RealizationGraph, Wire
from signallab_pc.session_desktop import capture
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class TransferWorkflowContracts(DesktopSessionFixture):
    def test_comparing_saved_systems_excludes_other_domains_and_generates_a_shared_grid(self):
        from signallab_pc.result_comparison import open_comparison

        window = self.window()
        first = window.publish(Transfer([1],[1,2],'analog','Sistema A'), operation='Ensayo')
        second = window.publish(Transfer([2],[1,4],'analog','Sistema B'), operation='Ensayo')
        digital = window.publish(Transfer([1],[1,-.25],name='Sistema discreto'), operation='Ensayo')
        open_comparison(window)
        dialog = window._result_comparison
        dialog.a.setCurrentIndex(dialog.a.findData(first))
        self.assertEqual(dialog.b.currentData(),second)
        self.assertEqual(dialog.b.findData(digital),-1)
        self.assertEqual(dialog.unit.text(),'rad/s')
        self.assertTrue(dialog.alignment.isHidden())
        dialog.start.setText('-3')
        dialog.stop.setText('7')
        dialog.count.setText('21')
        dialog.calculate_button.click()
        self.wait_for_calculation(window)
        omega = np.linspace(-3,7,21)
        expected = 2/(4+1j*omega)-1/(2+1j*omega)
        np.testing.assert_array_equal(dialog.data['omega'],omega)
        np.testing.assert_allclose(dialog.data['trace']['error'],expected,atol=1e-14)
        self.assertAlmostEqual(dialog.data['metrics']['rms'],np.sqrt(np.mean(abs(expected)**2)))
        dialog.mode.setCurrentIndex(1)
        self.assertEqual(dialog.figure.axes[0].get_ylabel(),'Módulo')
        self.assertEqual(dialog.figure.axes[-1].get_xlabel(),'Frecuencia angular (rad/s)')
        self.assertEqual(window.project.headers()[-1]['parents'],[first,second])
        open_comparison(window)
        self.assertIs(window._result_comparison,dialog)
        self.assertEqual(dialog.a.currentData(),first)

    def test_physical_comparison_exhibits_no_overlap_when_indices_match_but_times_do_not(self):
        from signallab_pc.result_comparison import open_comparison

        window = self.window()
        keys=[window.publish(Signal([2,3,4],-1,metadata={'sample_rate_hz':8,'time_start_s':t}),
                             operation='Registros con distinto reloj') for t in (0,1)]
        open_comparison(window)
        dialog=window._result_comparison
        self.assertEqual(dialog.a.currentData(),keys[0])
        self.assertEqual(dialog.b.currentData(),keys[1])
        dialog.calculate_button.click()
        self.wait_for_calculation(window)
        self.assertEqual(dialog.data['metrics']['count'],3)
        self.assertIn('sólo a los índices', dialog.data['clock_note'])
        dialog.alignment.setCurrentIndex(1)
        dialog.calculate_button.click()
        self.wait_for_calculation(window)
        self.assertEqual(dialog.data['metrics']['count'],0)
        self.assertIsNone(dialog.data['metrics']['rms'])
        self.assertFalse(dialog.export_button.isEnabled())
        dialog.trace_mode.setCurrentIndex(1)
        message,=dialog.figure.axes[0].texts
        self.assertIn('Sin coordenadas',message.get_text())

    def test_cas_reuses_piecewise_definitions_as_samples_with_the_exact_value_at_the_jump(self):
        window = self.window()
        window.open_cas()
        worksheet = window.pages[CAS_ROUTE]
        worksheet.input.setPlainText('where(x==0,4,where(x<0,2*x,-x))')
        worksheet.calculate()
        self.wait_for_calculation(window)
        key = worksheet.selected_entry()['result_id']
        worksheet.send_result('discrete')
        route = ROUTES['basic','generate']
        self.assertEqual(window.current_operation,route)
        page = window.pages[route]
        page.first.origin.setText('-2')
        page.first.count.setText('5')
        window.calculate_active()
        self.wait_for_calculation(window)
        result = page.basic_result.result
        self.assertEqual(result.origin,-2)
        np.testing.assert_array_equal(result.values,[-4,-2,4,-1,-2])
        parents = {item['id']:item['parents'] for item in window.project.headers()}
        self.assertEqual(parents[page.first.reference_id], [key])
        self.assertIn(page.first.reference_id, parents[page.basic_result.result_ids[0]])

    def test_cas_result_actions_retain_history_and_reject_ambiguous_reuse(self):
        import sympy as sp

        window = self.window()
        window.open_cas()
        worksheet = window.pages[CAS_ROUTE]
        worksheet.send_result('analog')
        self.info.assert_not_called()
        x, y = sp.symbols('x y')
        worksheet.input.setPlainText('1/((x+1)*(x+y))')
        worksheet.calculate()
        self.wait_for_calculation(window)
        source = worksheet.selected_entry()['result_id']
        with patch.object(QInputDialog,'getItem',return_value=('',False)):
            worksheet.operate_result('apart')
        self.assertEqual(worksheet.selected,1)
        self.assertEqual(len(window.project.headers()),1)
        with patch.object(QInputDialog,'getItem',return_value=('x',True)):
            worksheet.operate_result('apart')
        self.wait_for_calculation(window)
        self.assertEqual(worksheet.selected,2)
        self.assertEqual(window.project.headers()[-1]['parents'],[source])
        formula = restore(worksheet.state['results']['2'])
        original = 1/((x+1)*(x+y))
        self.assertEqual(sp.cancel(formula-original),0)
        worksheet.send_result('analog')
        self.info.assert_called_once()
        self.assertEqual(window.current_operation,CAS_ROUTE)
        worksheet.input.setPlainText('[1,2]')
        worksheet.calculate()
        self.wait_for_calculation(window)
        self.info.reset_mock()
        worksheet.send_result('discrete')
        self.info.assert_called_once()
        self.assertEqual(window.current_operation,CAS_ROUTE)

    def test_analog_analysis_reopens_frequency_after_roots_and_exports_the_same_response(self):
        window = self.window()
        route = ROUTES['system_analysis', 0]
        window.open_tool(route)
        panel = window.pages[route].panel
        panel.b.setText('1')
        panel.a.setText('1, 1, 1')
        panel.count.setText('81')
        window.calculate_active()
        self.wait_for_calculation(window)
        data = panel.frequency_data
        self.assertIsNotNone(data)
        np.testing.assert_allclose(data.response, 1/(1+1j*data.omega-data.omega**2), atol=1e-13)
        with patch('signallab_pc.plot_view.enlarge_plot') as open_plot:
            panel.result_tabs.setCurrentIndex(1)
            panel.result_tabs.setCurrentIndex(2)
            self.wait_for_calculation(window)
            panel.result_tabs.setCurrentIndex(panel.transfer_index)
            panel.result_tabs.setCurrentIndex(1)
        self.assertEqual([call.args[0] for call in open_plot.call_args_list],
                         [panel.canvas, panel.roots_view.canvas, panel.transfer_view.canvas, panel.canvas])
        self.assertIs(panel.frequency_data, data)
        panel.response_components.setCurrentIndex(1)
        self.assertEqual(panel.figure.axes[0].get_ylabel(), 'Parte real')
        np.testing.assert_array_equal(panel.figure.axes[1].lines[0].get_ydata(), data.response.imag)
        panel.response_components.setCurrentIndex(0)
        panel.magnitude_scale.setCurrentIndex(1)
        np.testing.assert_allclose(panel.figure.axes[0].lines[0].get_ydata(),
                                   20*np.log10(abs(data.response)), atol=1e-13)
        target = self.path/'respuesta'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(target), 'Análisis completo JSON')):
            panel.export_response()
        document = json.loads(target.with_suffix('.json').read_text(encoding='utf-8'))
        self.assertEqual(document['format'], 'signallab-frequency-analysis')
        np.testing.assert_array_equal(document['frequency'], data.omega)
        np.testing.assert_array_equal(document['response_real'], data.response.real)
        np.testing.assert_array_equal(document['response_imag'], data.response.imag)
        records = {item['id']: item for item in window.project.headers()}
        self.assertEqual(records[panel.input_id]['parents'], [panel._definition_id])
        self.assertEqual(next(reversed(records.values()))['parents'], [panel._definition_id, panel.input_id])

    def test_cas_history_failure_and_frequency_handoff_preserve_original_cell(self):
        window = self.window()
        window.open_cas()
        panel = window.pages[CAS_ROUTE]
        panel.input.setPlainText('1/(1+w^2)')
        panel.calculate()
        self.wait_for_calculation(window)
        record = panel.selected_entry()['result_id']
        panel.input.setPlainText('borrador')
        panel.recall(-1)
        self.assertEqual(panel.input.toPlainText(), '1/(1+w^2)')
        panel.recall(1)
        self.assertEqual(panel.input.toPlainText(), 'borrador')
        panel.input.setPlainText('sqrt(')
        panel.calculate()
        self.wait_for_calculation(window)
        self.assertEqual(panel.entries[-1]['status'], 'error')
        self.assertEqual(len(window.project.headers()), 1)
        self.assertEqual(panel.state['ans'], 1)
        panel.input.clear()
        panel.follow_link(QUrl('cas-result:1'))
        self.assertEqual(panel.input.toPlainText(), 'r1')
        panel.copy_result()
        self.assertEqual(self.app.clipboard().text(), panel.selected_entry()['answer']['text'])
        panel.result_digits.setText('0')
        self.info.reset_mock()
        panel.operate_result('approx')
        self.info.assert_called_once()
        with patch.object(QInputDialog, 'getItem', return_value=('', False)):
            panel.send_result('frequency')
        self.assertEqual(window.current_operation, CAS_ROUTE)
        with patch.object(QInputDialog, 'getItem', return_value=('rad/s', True)):
            panel.send_result('frequency')
        route = ROUTES['system_analysis', 0]
        self.assertEqual(window.current_operation, route)
        analysis = window.pages[route].panel
        self.assertEqual(analysis.input_id, record)
        self.assertEqual(analysis.definition_mode.currentIndex(), 2)
        self.assertEqual(analysis.domain.currentIndex(), 0)
        analysis.count.setText('31')
        window.calculate_active()
        self.wait_for_calculation(window)
        data = analysis.frequency_data
        self.assertIsNotNone(data)
        np.testing.assert_allclose(data.response, 1/(1+data.omega**2), atol=1e-13)
        definition = next(item for item in window.project.headers() if item['id'] == analysis._definition_id)
        self.assertEqual(definition['parents'], [record])

    def test_sessions_keep_both_domain_diagrams_and_reject_invalid_graph_atomically(self):
        window = self.window()
        route = ROUTES['system_analysis', 0]
        window.open_tool(route)
        panel = window.pages[route].panel
        diagrams = {}
        for domain, formula in [('analog', '1/(s+1)'), ('digital', 'z**(-1)')]:
            blocks = (Block(1, 'input', 0, 0), Block(2, 'output', 500, 0),
                      Block(3, 'transfer', 220, 0, formula=formula,
                            sample_period_s=.02 if domain == 'digital' else None))
            graph = RealizationGraph(domain, blocks, (Wire(1, 3), Wire(3, 2)))
            panel.load_diagram(graph)
            diagrams[domain] = graph
        path = self.path/'diagramas.json'
        session.save(path, window.project, capture(window))
        restored = self.window()
        self.assertTrue(restored.sessions.open_path(path))
        panel = restored.pages[route].panel
        self.assertEqual(panel.diagram_input.graphs, diagrams)
        self.assertEqual(panel.diagram_input.graph, diagrams['digital'])
        panel.count.setText('17')
        restored.calculate_active()
        self.wait_for_calculation(restored)
        self.assertEqual(panel.analyzed_system.sample_period_s, .02)
        data = panel.frequency_data
        np.testing.assert_allclose(data.response, np.exp(-1j*data.omega), atol=1e-13)
        self.assertIn('Diagrama de entrada', panel.report.toPlainText())
        state = json.loads(path.read_text(encoding='utf-8'))
        inputs = state['workspace']['tools'][0]['inputs']['fields']
        inputs['diagram_input']['analog']['domain'] = 'digital'
        path.write_text(json.dumps(state), encoding='utf-8')
        project = restored.project
        self.assertFalse(restored.sessions.open_path(path))
        self.assertIs(restored.project, project)
        self.assertEqual(panel.diagram_input.graphs, diagrams)
        self.warning.assert_called_once()

    def test_filter_band_drafts_survive_tool_reopen_with_both_transition_widths(self):
        window = self.window()
        route = ROUTES['course_tools', 'fir']
        window.open_tool(route)
        editor = window.pages[route].panel.band_edges
        last = editor.kind.findData('lowpass')
        editor.edits[0].setText('pi/6')
        editor.edits[1].setText('pi/3')
        editor.kind.setCurrentIndex(editor.kind.findData('bandpass'))
        for field, text in zip(editor.edits, ('pi/4', 'pi/3', '3*pi/5', '7*pi/10')):
            field.setText(text)
        path = self.path/'bandas.json'
        key = window.project.add(Signal([1], name='Referencia de sesión'))
        session.save(path, window.project, capture(window))
        restored = self.window()
        self.assertTrue(restored.sessions.open_path(path))
        self.assertEqual(restored.project.get(key).values[0], 1)
        editor = restored.pages[route].panel.band_edges
        self.assertEqual(editor.kind.currentData(), 'bandpass')
        pass_edges, stop_edges = editor.bands()
        np.testing.assert_allclose(pass_edges, np.pi*np.array([1/3, 3/5]))
        np.testing.assert_allclose(stop_edges, np.pi*np.array([1/4, 7/10]))
        self.assertIn('Transición izquierda', editor.status.text())
        self.assertIn('Transición derecha', editor.status.text())
        editor.kind.setCurrentIndex(last)
        self.assertEqual([field.text() for field in editor.edits[:2]], ['pi/6', 'pi/3'])
