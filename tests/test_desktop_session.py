import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PySide6.QtCore import QCoreApplication, QEvent, QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

from signallab_pc import session
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.session_desktop import capture
from signallab_pc.workbench import WorkbenchWindow
from signallab_pc.workspaces import ROUTES


class SessionFileTests(unittest.TestCase):
    def test_legacy_files_remain_usable_and_incorporation_allocates_new_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'project.json'
            source = Project()
            parent = source.add(Signal([2]))
            child = source.add(Signal([4]), parents=[parent])
            source.save(path)
            project, state = session.load(path)
            self.assertEqual(state, session.empty_workspace())
            self.assertEqual(project.headers()[-1]['parents'], [parent])
            self.assertEqual(project.get(child).values[0], 4)
            self.assertEqual(project.merge(path), 2)
            records = project.headers()
            self.assertNotEqual(records[2]['id'], parent)
            self.assertEqual(records[3]['parents'], [records[2]['id']])

    def test_interrupted_write_preserves_the_previous_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'recovery.json'
            project = Project()
            first = project.add(Signal([3]))
            session.save(path, project, session.empty_workspace())
            checksum = path.read_bytes()
            project.add(Signal([10]), parents=[first])
            with patch('signallab_pc.atomic_file.os.replace', side_effect=OSError('Escritura interrumpida')):
                with self.assertRaises(OSError):
                    session.save(path, project, session.empty_workspace())
            self.assertEqual(path.read_bytes(), checksum)
            recovered, _ = session.load(path)
            self.assertEqual(len(recovered.headers()), 1)
            self.assertEqual(recovered.get(first).values[0], 3)
            self.assertEqual(list(Path(folder).iterdir()), [path])


class DesktopSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name)
        settings = QSettings(str(self.path/'settings.ini'), QSettings.Format.IniFormat)
        self.windows = []
        self.question = self.enterContext(patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Discard))
        self.warning = self.enterContext(patch.object(QMessageBox, 'warning'))
        self.info = self.enterContext(patch.object(QMessageBox, 'information'))
        self.enterContext(patch('signallab_pc.workbench.desktop_settings', return_value=settings))
        self.enterContext(patch('signallab_pc.update_ui.installed', return_value=None))
        self.addCleanup(self.close_windows)

    def window(self):
        window = WorkbenchWindow(recovery_directory=self.path)
        self.windows.append(window)
        return window

    def close_windows(self):
        for window in self.windows:
            window.close()
            window.deleteLater()
        # The offscreen suite has no application exec() loop to deliver these.
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def wait_for_calculation(self, window):
        from PySide6.QtCore import QDeadlineTimer
        from PySide6.QtTest import QTest

        timeout = QDeadlineTimer(5000)
        while window._workers and not timeout.hasExpired():
            QTest.qWait(15)
        self.assertFalse(window._workers)

    def test_compact_psd_keeps_visible_action_and_produces_calibrated_power(self):
        window = self.window()
        route = ROUTES['fourier', 7]
        window.open_tool(route)
        window.resize(640, 420)
        window.show()
        self.app.processEvents()
        page = window.pages[route]
        panel = page.panel
        samples = Signal([2, -2, 2, -2], metadata={'sample_rate_hz': 8})
        source = window.publish(samples, operation='Entrada PSD de prueba')
        page.context.source.set_source(samples, source)
        panel.window.setCurrentIndex(0)
        self.assertEqual(window.calculate_action.text(), 'Calcular')
        self.assertIn('densidad espectral', window.calculate_action.accessibleName())
        window.resize(1200, 768)
        self.app.processEvents()
        self.assertEqual(window.calculate_action.text(), 'Calcular densidad espectral')
        window.resize(640, 420)
        self.app.processEvents()
        window.calculate_action.click()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        result = window.project.get(window.project.headers('signal')[-1]['id'])
        np.testing.assert_allclose(result.values, [2, 0, 0, 0], rtol=2e-15, atol=0)
        self.assertEqual((result.origin, result.step, result.units), (-4, 2, 'Hz'))
        self.assertEqual((result.metadata['segment'], result.metadata['overlap']), (4, 2))
        self.assertEqual(window.project.headers('signal')[-1]['parents'], [source])
        panel.segment.setText('5')
        before = window.project.headers()
        window.calculate_action.click()
        self.assertEqual(window.project.headers(), before)
        self.assertIs(page.workspace.input_issue.field(), panel.segment)
        window.resize(1200, 768)
        self.app.processEvents()
        self.assertEqual(window.calculate_action.text(), 'Recalcular')

    def test_scientific_session_chooser_roundtrips_tabs_and_result(self):
        from PySide6.QtWidgets import QFileDialog
        from signallab_pc.session_desktop import _BINARY_SESSION

        window = self.window()
        window.open_tool(ROUTES['basic', 'dft'])
        record = window.publish(Signal([3.25, -1j], -4), operation='Entrada')
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(self.path/'session.json'), _BINARY_SESSION)):
            self.assertTrue(window.sessions.save_dialog())
        binary = self.path/'session.slproj'
        self.assertFalse((self.path/'session.json').exists())
        loaded, workspace = session.load(binary)
        self.assertEqual(workspace, capture(window))
        np.testing.assert_array_equal(loaded.get(record).values, [3.25, -1j])
        other = self.window()
        self.assertTrue(other.sessions.open_path(binary))
        self.assertEqual(other.current_operation, ROUTES['basic', 'dft'])
        self.assertEqual(other.project.get(record).origin, -4)

    def test_analog_bilinear_conversion_preserves_clock_and_dc_gain_in_results(self):
        from signallab_pc.filters import Transfer

        window = self.window()
        route = ROUTES['course_tools', 'convert']
        window.open_tool(route)
        panel = window.pages[route].panel
        model = Transfer([1], [1, 2], 'analog')
        parent = window.publish(model, operation='H(s) de prueba')
        panel.set_system(model, parent)
        panel.fields['method'].setCurrentIndex(panel.fields['method'].findData('bilinear'))
        panel.fields['period'].setText('0.25')
        panel.fields['analog_cutoffs'].setText('2')
        panel.calculate()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        digital = [item for item in panel.items if isinstance(item, Transfer) and item.domain == 'digital']
        self.assertTrue(digital)
        self.assertAlmostEqual(digital[0].sample_period_s, .25)
        theta = np.array([0.0, .3, .9])
        np.testing.assert_allclose(digital[0].response(theta), 1/(2+8j*np.tan(theta/2)), rtol=1e-13)
        self.assertIn('Conversión', panel.report.toPlainText())

    def test_bandpass_clock_handoff_and_csv_agree_with_nonoverlap_bounds(self):
        import csv
        from PySide6.QtWidgets import QFileDialog

        window = self.window()
        route = ROUTES['course_tools', 'bandpass_sampling']
        window.open_tool(route)
        panel = window.pages[route].panel
        for key, value in {'low': '4', 'high': '5', 'candidate': '5'}.items():
            panel.fields[key].setText(value)
        panel.calculate()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        self.assertTrue(panel.export_bands_button.isEnabled())
        self.assertFalse(panel.use_rate_button.isEnabled())

        panel.fields['candidate'].setText('6')
        panel.calculate()
        self.wait_for_calculation(window)
        self.assertTrue(panel.use_rate_button.isEnabled())
        path = self.path/'bandpass.csv'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(path), 'CSV')):
            panel.export_bands_button.click()
        with path.open(encoding='utf-8', newline='') as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[0], ['omega_low_rad_s', '4.0', 'omega_high_rad_s', '5.0'])
        self.assertEqual(rows[3][:3], ['2', '5.0', '8.0'])
        panel.use_rate_button.click()
        sample = ROUTES['sampling', 0]
        self.assertEqual(window.current_operation, sample)
        self.assertAlmostEqual(float(window.pages[sample].panel.rate.text()), 3/np.pi, places=14)

    def test_dft_workspace_uses_the_pilot_and_retains_the_input_and_output(self):
        from signallab_pc.dft_application import DFTRequest, calculate_dft
        from signallab_pc.operations import idft
        from test_math_dft_pilot import direct_sum

        window = self.window()
        route = ROUTES['basic','dft']
        window.open_tool(route)
        page = window.pages[route]
        signal = Signal([1+1j, 2j, -3], -2, metadata={'sample_rate_hz': 8, 'time_start_s': -.125})
        page.first.set_source(signal)
        for reference in ('sample_indices', 'record_offset'):
            with self.subTest(reference=reference):
                page.dft_phase_reference.setCurrentIndex(page.dft_phase_reference.findData(reference))
                page.result_state.button.click()
                self.wait_for_calculation(window)
                parent, *results = window.project.headers()
                output = window.project.get(results[-1]['id'])
                self.assertEqual(results[-1]['parents'], [parent['id']])
                self.assertEqual(page.basic_result.result_ids, [results[-1]['id']])
                self.assertEqual(results[-1]['tool']['route'], list(route))
                expected = calculate_dft(DFTRequest(signal, phase_reference=reference)).spectrum
                np.testing.assert_allclose(output.values, expected.values, atol=1e-14)
                np.testing.assert_allclose(output.values, direct_sum(signal, 3, True, reference), atol=1e-13)
                self.assertEqual(output.metadata, expected.metadata)
                recovered = idft(output, restore_origin=True)
                np.testing.assert_allclose(recovered.values, signal.values, atol=1e-13)
                self.assertEqual(recovered.origin, -2)
        self.assertEqual(len(window.project.headers()), 3)

    def test_cancelling_dft_before_handoff_keeps_the_project_free_of_partial_records(self):
        from threading import Event
        from signallab_pc.operations import dft

        window = self.window()
        route = ROUTES['basic','dft']
        window.open_tool(route)
        page = window.pages[route]
        page.first.set_source(Signal([1, 2, 3], 1))
        started, release = Event(), Event()

        def delayed(*args, **kwargs):
            started.set()
            if not release.wait(5):
                raise TimeoutError('Test did not release the DFT worker.')
            return dft(*args, **kwargs)

        with patch('signallab_pc.operations.dft', side_effect=delayed):
            page.result_state.button.click()
            try:
                self.assertTrue(started.wait(4))
                self.assertEqual(window.project.headers(), [])
                window._cancel_operations()
            finally:
                release.set()
            self.wait_for_calculation(window)
        self.assertEqual(window.project.headers(), [])
        self.assertEqual(page.basic_result.result_ids, [])

    def test_released_dft_session_reopens_with_its_original_phase_reference(self):
        from signallab_pc.operations import idft

        fixture = Path(__file__).parent/'fixtures'/'session-v3-dft-2.0.0.json'
        window = self.window()
        self.assertTrue(window.sessions.open_path(fixture))
        route = ROUTES['basic','dft']
        self.assertEqual(window.current_operation, route)
        page = window.pages[route]
        self.assertEqual(page.dft_phase_reference.currentData(), 'record_offset')
        source, spectrum = window.project.headers()
        self.assertEqual(spectrum['parents'], [source['id']])
        stored = window.project.get(spectrum['id'])
        self.assertNotIn('dft_phase_reference', stored.metadata)
        restored = idft(stored, restore_origin=True)
        np.testing.assert_allclose(restored.values, [1, 2, 0, 0], atol=1e-14)
        self.assertEqual(restored.origin, 3)
        self.assertEqual(restored.metadata['sample_rate_hz'], 8)
        self.assertEqual(restored.metadata['time_start_s'], .375)

        phase = page.dft_phase_reference
        phase.setCurrentIndex(phase.findData('sample_indices'))
        saved = self.path/'phase-reference.json'
        session.save(saved, window.project, capture(window))
        self.assertTrue(window.sessions.open_path(saved))
        self.assertEqual(window.pages[route].dft_phase_reference.currentData(), 'sample_indices')
        np.testing.assert_array_equal(window.project.get(spectrum['id']).values, stored.values)

    def test_historical_sessions_migrate_to_schema_three_without_changing_results(self):
        from signallab_pc.operations import idft

        expected = [1+2j, -1, 3j]
        route = ROUTES['basic','dft']
        for schema, version in ((1, '1.9.3'), (2, '1.9.4')):
            with self.subTest(schema=schema):
                fixture = Path(__file__).parent/'fixtures'/f'session-v{schema}-draft-{version}.json'
                migrated = self.path/f'migrated-v{schema}.json'
                window = self.window()
                self.assertTrue(window.sessions.open_path(fixture))
                self.assertEqual(window.current_operation, route)
                self.assertEqual(window.pages[route].dft_phase_reference.currentData(), 'record_offset')
                source, spectrum = window.project.headers()
                self.assertEqual(spectrum['parents'], [source['id']])
                session.save(migrated, window.project, capture(window))
                self.assertEqual(json.loads(migrated.read_text(encoding='utf-8'))['schema_version'], 3)
                self.assertTrue(window.sessions.open_path(migrated))
                self.assertEqual(window.project.headers(), [source, spectrum])
                signal = window.project.get(source['id'])
                np.testing.assert_array_equal(signal.values, expected)
                restored = idft(window.project.get(spectrum['id']), restore_origin=True)
                np.testing.assert_allclose(restored.values, expected, atol=1e-14)
                self.assertEqual(restored.origin, -2)
                self.assertEqual(restored.metadata['sample_rate_hz'], 4)
                self.assertEqual(restored.metadata['time_start_s'], -.5)

    def test_real_workspace_restores_reference_clock_tool_order_and_inactive_input(self):
        window = self.window()
        root = window.project.add(Signal([1,2], -1, metadata={'sample_rate_hz':8,'time_start_s':.25}))
        child = window.project.add(Signal([2,4], -1, metadata={'sample_rate_hz':8,'time_start_s':.25}), parents=[root])
        generate = ROUTES['basic','generate']
        window.open_tool(generate)
        page = window.pages[generate]
        page.discrete_source.set_source(window.project.get(child), child)
        page.source_domain.setCurrentIndex(1)
        page.continuous_source.expression.setText('sin(2*pi*t)')
        analysis = ROUTES['system_analysis',0]
        window.open_tool(analysis)
        window.pages[analysis].panel.a.setText('1, pi, 1')
        window.documents.setCurrentIndex(1)
        workspace = capture(window)
        path = self.path/'work.json'
        session.save(path, window.project, workspace)
        window = self.window()
        self.assertTrue(window.sessions.open_path(path))
        self.assertEqual(capture(window),workspace)
        self.assertEqual(window.current_operation,generate)
        self.assertEqual(window.project.headers()[-1]['parents'], [root])
        page = window.pages[generate]
        self.assertEqual(page.continuous_source.expression.text(), 'sin(2*pi*t)')
        self.assertEqual(page.discrete_source.loaded_reference_id, child)
        self.assertEqual(page.discrete_source.loaded.metadata['time_start_s'], .25)
        self.assertEqual(window.pages[analysis].panel.a.text(), '1, pi, 1')
        self.warning.assert_not_called()

    def test_preflight_rejects_missing_project_reference_without_replacing_active_work(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        project = window.project
        key = project.add(Signal([4]))
        page = window.pages[route]
        page.first.set_source(project.get(key), key)
        path = self.path/'invalid.json'
        session.save(path, project, capture(window))
        bad = json.loads(path.read_text(encoding='utf-8'))
        bad['workspace']['tools'][0]['inputs']['fields']['discrete_source']['sources']['3']['record'] = 'missing'
        path.write_text(json.dumps(bad), encoding='utf-8')
        self.assertFalse(window.sessions.open_path(path))
        self.assertIs(window.project, project)
        self.assertIs(window.pages[route], page)
        np.testing.assert_array_equal(page.first.loaded.values, [4])
        self.warning.assert_called_once()

    def test_recovery_reopens_edits_and_corruption_cannot_replace_the_checkpoint(self):
        window = self.window()
        window.show()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        window.pages[route].first.expression.setText('n^2')
        window.sessions.autosave()
        checkpoint = window.sessions.path
        self.assertTrue(checkpoint.is_file())
        original = checkpoint.read_bytes()
        window.pages[route].first.expression.setText('n^3')
        with patch('signallab_pc.atomic_file.os.replace', side_effect=OSError('Interrumpido')):
            window.sessions.autosave()
        self.assertEqual(original,checkpoint.read_bytes())
        # Release only the process lock, as it would be released by termination.
        window.sessions.lock.unlock()
        restored = self.window()
        self.question.return_value = QMessageBox.StandardButton.Yes
        restored.sessions.offer_recovery()
        self.assertEqual(restored.pages[route].first.expression.text(), 'n^2')
        self.assertTrue(restored.project.dirty)
        self.info.assert_called_once()
        self.question.return_value = QMessageBox.StandardButton.Discard

    def test_change_rate_clears_the_previously_copied_unrelated_start(self):
        window = self.window()
        route = ROUTES['rational_resampling',0]
        window.open_tool(route)
        panel = window.pages[route].panel
        panel.source.set_source(Signal([1,2], metadata={'sample_rate_hz':8,'time_start_s':12}))
        self.assertEqual(float(panel.start.text()), 12)
        panel.source.set_source(Signal([3,4], metadata={'sample_rate_hz':8}))
        self.assertEqual(panel.start.text(), '')
        panel.start.setText('3.5')
        panel.source.set_source(Signal([5,6], metadata={'sample_rate_hz':8}))
        self.assertEqual(panel.start.text(), '3.5')

    def test_sample_edits_invalidate_the_model_after_reopening(self):
        window = self.window()
        route = ROUTES['signal_editor',0]
        window.open_tool(route)
        editor = window.pages[route].panel
        original = Signal([0,1,2],expression='n',metadata={'full_axis_definition':'n'})
        editor.receive(original)
        editor.history.values([1],[99])
        draft = editor.staged_signal()
        self.assertEqual(draft.expression, '')
        self.assertIsNone(draft.full_definition)
        path = self.path/'edits.json'
        session.save(path,window.project,capture(window))
        document = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(document['schema_version'],3)
        self.assertTrue(window.sessions.open_path(path))
        editor = window.pages[route].panel
        self.assertEqual(editor.changed_rows,{1})
        np.testing.assert_array_equal(editor.staged_signal().values,[0,99,2])
        editor.history.values([1],[1])
        self.assertEqual(editor.staged_signal().full_definition,'n')
        editor.history.stack.undo()
        result = editor.commit()
        self.assertEqual(result.metadata['source_expression'],'n')
        self.assertEqual(result.metadata['edited_offsets'],[1])
        self.assertIsNone(result.full_definition)

        # Older drafts contain the modified values but no sample edit history.
        document['schema_version'] = 2
        document['workspace']['tools'][0]['inputs']['table'].pop('edits')
        path.write_text(json.dumps(document),encoding='utf-8')
        self.assertTrue(window.sessions.open_path(path))
        result = window.pages[route].panel.commit()
        np.testing.assert_array_equal(result.values,[0,99,2])
        self.assertEqual(result.expression,'')
        self.assertIsNone(result.full_definition)

    def test_reused_expression_keeps_conditions_after_reopening(self):
        from signallab_pc.result_expressions import ExpressionResult
        window = self.window()
        key = window.project.add({'report': 'Señal con condición'})
        route = ROUTES['expression_measures','global']
        window.open_tool(route)
        editor = window.pages[route].panel
        editor.load_expression(ExpressionResult('exp(-abs(t))','t',conditions=('a > 0',)),key)
        path = self.path/'conditions.json'
        session.save(path,window.project,capture(window))
        restored = self.window()
        self.assertTrue(restored.sessions.open_path(path))
        panel = restored.pages[route].panel
        self.assertEqual(panel.request()['input_conditions'], ['a > 0'])
        self.assertEqual(panel._expression_origin[1], key)
        panel.expression.setText('0')
        self.assertEqual(panel.request()['input_conditions'], [])

    def test_malformed_project_cannot_replace_active_session(self):
        window = self.window()
        window.show_menu('Proyecto')
        active = window.project
        active.add(Signal([4]))
        path = self.path/'invalid-header.json'
        session.save(path,active,capture(window))
        malformed = json.loads(path.read_text(encoding='utf-8'))
        malformed['project']['records'][0]['operation'] = []
        path.write_text(json.dumps(malformed),encoding='utf-8')
        self.assertFalse(window.sessions.open_path(path))
        self.assertIs(window.project, active)
        self.warning.assert_called_once()

    def test_mimo_matrix_and_both_channel_banks_survive_the_session(self):
        from signallab_pc.state_simulation_inputs import prepare_inputs
        window = self.window()
        route = ROUTES['state_space','simulation']
        window.open_tool(route)
        panel = window.pages[route].panel
        for label, text in {'A':'0', 'B':'1, 2', 'C':'1', 'D':'0, 0'}.items():
            panel.fields[label].setText(text)
        panel.inputs.field(1).expression.setText('t+7')
        panel.domain.setCurrentIndex(1)
        panel.step.setText('1/8')
        first = panel.inputs.field(0)
        first.entry_modes.select(1)
        first.samples.setText('1, 2')
        key = window.project.add(Signal([4,5],metadata={'sample_rate_hz':8,'time_start_s':12}))
        panel.inputs.field(1).set_source(window.project.get(key),key)
        panel.inputs.channel.setCurrentIndex(1)
        path = self.path/'mimo.json'
        session.save(path,window.project,capture(window))
        restored = self.window()
        self.assertTrue(restored.sessions.open_path(path))
        panel = restored.pages[route].panel
        self.assertEqual(panel.inputs.channel.currentIndex(),1)
        self.assertEqual(panel.inputs.field(1,kind='continuous').expression.text(),'t+7')
        self.assertEqual(panel.inputs.field(1).loaded_reference_id,key)
        model = panel.read_model()
        grid = prepare_inputs(model,panel.inputs.read())
        self.assertIsNone(grid.time_start)
        time, y, _ = model.simulate(grid.values)
        np.testing.assert_array_equal(time,[0,1/8])
        np.testing.assert_array_equal(y[:,0],[0,9])

    def test_schema_one_ignores_a_result_selector_from_an_old_calculation(self):
        window = self.window()
        route = ROUTES['course_tools','fir']
        window.open_tool(route)
        selector = window.pages[route].panel.selector
        self.assertEqual(selector.count(),0)
        path = self.path/'schema1.json'
        session.save(path,window.project,capture(window))
        old = json.loads(path.read_text(encoding='utf-8'))
        old['schema_version'] = 1
        old['workspace']['tools'][0]['inputs']['fields']['selector'] = 1
        path.write_text(json.dumps(old),encoding='utf-8')
        self.assertTrue(window.sessions.open_path(path))
        self.assertEqual(window.pages[route].panel.selector.currentIndex(),-1)
        self.warning.assert_not_called()

    def test_result_export_can_include_dependencies_of_a_signal(self):
        window = self.window()
        source = window.project.add(Signal([1,2]))
        window.project.add(Signal([2,4]),parents=[source])
        window.show_menu('Proyecto')
        window.project_list.setCurrentRow(0)
        destination = self.path/'signal-with-inputs.json'
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(destination),'Resultado con dependencias (*.json)')):
            window.export_selected()
        result, state = session.load(destination)
        self.assertEqual(state,session.empty_workspace())
        records = result.headers()
        self.assertEqual(len(records),2)
        self.assertEqual(records[1]['parents'],[source])
        np.testing.assert_array_equal(result.get(records[1]['id']).values,[2,4])

    def test_transfer_editors_restore_both_orders_of_the_domain_selector(self):
        from signallab_pc.filters import Transfer
        from signallab_pc.session_fields import restore_page, snapshot_page
        from signallab_pc.toolbox import ToolPage
        from signallab_pc.transfer_input import read_system
        window = self.window()
        for operation, system in (
            (0, Transfer([2], [1], sample_period_s=.25)),
            (2, Transfer([1], [1,3], domain='analog')),
        ):
            with self.subTest(domain=system.domain):
                route = ROUTES['systems',operation]
                original = ToolPage(window,route)
                key = window.project.add(system)
                original.context.ready = False
                original.panel._accept_system(system)
                original.context.system_id = key
                saved = snapshot_page(original,{key})
                restored = ToolPage(window,route)
                restore_page(restored,saved,window.project)
                self.assertEqual(restored.context.system_id,key)
                self.assertIs(restored.panel.system,restored.panel._preserved_system)
                reread = read_system(restored.panel)
                self.assertEqual(reread.domain,system.domain)
                self.assertEqual(reread.sample_period_s,system.sample_period_s)
                np.testing.assert_array_equal(reread.a,system.a)
                original.deleteLater()
                restored.deleteLater()
