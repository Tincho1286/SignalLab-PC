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

    def wait_for_recovery(self, window):
        from PySide6.QtCore import QDeadlineTimer
        from PySide6.QtTest import QTest

        timeout = QDeadlineTimer(5000)
        while window.sessions.writing is not None and not timeout.hasExpired():
            QTest.qWait(15)
        self.assertIsNone(window.sessions.writing)

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
        self.wait_for_recovery(window)
        checkpoint = window.sessions.path
        self.assertTrue(checkpoint.is_file())
        original = checkpoint.read_bytes()
        window.pages[route].first.expression.setText('n^3')
        with patch('signallab_pc.atomic_file.os.replace', side_effect=OSError('Interrumpido')):
            window.sessions.autosave()
            self.wait_for_recovery(window)
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

    def test_recovery_writes_a_snapshot_and_remains_responsive_during_io(self):
        from threading import Event
        from PySide6.QtCore import QTimer
        from PySide6.QtTest import QTest

        window = self.window()
        window.show()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        panel = window.pages[route]
        panel.first.expression.setText('n^2')
        original = window.publish(Signal([2]), operation='Entrada')
        window.sessions.autosave()
        self.wait_for_recovery(window)
        path = window.sessions.path
        before = path.read_bytes()
        entered, release, pulse = Event(), Event(), []
        self.addCleanup(release.set)
        real_save = session.save

        def blocked_save(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise TimeoutError('El test no liberó la escritura.')
            return real_save(*args, **kwargs)

        panel.first.expression.setText('n^3')
        with patch('signallab_pc.session_desktop.session.save', side_effect=blocked_save) as save:
            try:
                window.sessions.autosave()
                self.assertTrue(entered.wait(2))
                QTimer.singleShot(0, window, lambda: pulse.append(True))
                QTest.qWait(30)
                self.assertEqual(pulse, [True])
                second = window.publish(Signal([4]), parents=[original], operation='Edición')
                panel.first.expression.setText('n^4')
                window.sessions.autosave()
                self.assertEqual(save.call_count, 1)
                self.assertEqual(path.read_bytes(), before)
            finally:
                release.set()
                self.wait_for_recovery(window)
        snapshot, _ = session.load(path)
        self.assertEqual([row['id'] for row in snapshot.headers()], [original])
        self.assertIn(b'n^3', path.read_bytes())
        window.sessions.autosave()
        self.wait_for_recovery(window)
        snapshot, _ = session.load(path)
        self.assertEqual([row['id'] for row in snapshot.headers()], [original, second])
        self.assertIn(b'n^4', path.read_bytes())

    def test_cas_session_reopens_exact_bindings_published_parents_and_draft_without_evaluation(self):
        from signallab_pc.cas_reference import CAS_ROUTE
        from signallab_pc.cas_engine import restore as decode

        window = self.window()
        window.open_cas()
        worksheet = window.pages[CAS_ROUTE]
        for source in ('a := 2 + 3*i', 'f(x) := a*x', 'assume(y>0)', '2*r1'):
            worksheet.input.setPlainText(source)
            worksheet.calculate()
            self.wait_for_calculation(window)
        self.assertEqual(worksheet.selected, 4)
        worksheet.input.setPlainText('sqrt(')
        worksheet.change_math_size(4)
        worksheet.result_digits.setText('24')
        source_id = worksheet.entries[0]['result_id']
        last_id = worksheet.entries[-1]['result_id']
        for extension in ('json', 'slproj'):
            with self.subTest(extension=extension):
                path = self.path/f'cas.{extension}'
                session.save(path, window.project, capture(window))
                reopened = self.window()
                with patch('signallab_pc.cas_panel.run_request', side_effect=AssertionError('Unexpected evaluation')) as worker:
                    self.assertTrue(reopened.sessions.open_path(path))
                    worker.assert_not_called()
                restored = reopened.pages[CAS_ROUTE]
                self.assertEqual(restored.input.toPlainText(), 'sqrt(')
                self.assertEqual((restored.selected, restored.math_size, restored.result_digits.text()), (4, 21, '24'))
                self.assertEqual(restored.state, worksheet.state)
                self.assertEqual(restored.variables.topLevelItemCount(), 3)
                records = {row['id']: row for row in reopened.project.headers()}
                self.assertEqual(records[last_id]['parents'], [source_id])
                self.assertEqual(reopened.current_operation, CAS_ROUTE)
                restored.input.setPlainText('f(2) + r1')
                restored.calculate()
                self.wait_for_calculation(reopened)
                self.assertEqual(complex(decode(restored.state['results']['5'])), 6+9j)
                self.assertEqual(reopened.project.headers()[-1]['parents'], [source_id])

        corrupt = capture(window)
        corrupt['cas']['entries'][0]['result_id'] = 'missing'
        path = self.path/'missing-cas.json'
        session.save(path, window.project, corrupt)
        self.assertFalse(window.sessions.open_path(path))
        self.assertIs(window.pages[CAS_ROUTE], worksheet)
        self.assertEqual(worksheet.input.toPlainText(), 'sqrt(')
        self.warning.assert_called_once()

    def test_recover_legacy_checkpoint_respects_exclusive_lock_and_refusal(self):
        legacy = self.path/'recovery.signallab.json'
        project = Project()
        record = project.add(Signal([3-2j], origin=-4))
        session.save(legacy, project, session.empty_workspace())
        before = legacy.read_bytes()
        owner, other = self.window(), self.window()
        self.question.return_value = QMessageBox.StandardButton.No
        owner.sessions.offer_recovery()
        self.assertTrue(owner.sessions.protected)
        self.assertEqual(legacy.read_bytes(), before)
        self.assertFalse(owner.project.headers())
        other.sessions.offer_recovery()
        self.assertIn('Otra instancia', other.statusBar().currentMessage())
        self.assertFalse(other.project.headers())
        self.question.return_value = QMessageBox.StandardButton.Yes
        owner.sessions.offer_recovery()
        self.assertTrue(owner.sessions.recovered_legacy)
        self.assertEqual(owner.project.get(record).values[0], 3-2j)
        self.assertEqual(owner.project.get(record).origin, -4)
        self.assertFalse(owner.sessions.protected)
        self.info.assert_called_once()
        self.question.return_value = QMessageBox.StandardButton.Discard

    def test_cancelled_close_keeps_last_checkpoint_of_session_being_edited(self):
        from threading import Event
        from PySide6.QtTest import QTest

        window = self.window()
        window.show()
        window.publish(Signal([3]), operation='Primer punto')
        window.sessions.autosave()
        self.wait_for_recovery(window)
        path = window.sessions.path
        before = path.read_bytes()
        save, entered, release = session.save, Event(), Event()

        def delayed(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise TimeoutError()
            return save(*args, **kwargs)

        window.publish(Signal([4]), operation='Edición posterior')
        self.question.return_value = QMessageBox.StandardButton.Cancel
        with patch('signallab_pc.session_desktop.session.save', side_effect=delayed):
            try:
                window.sessions.autosave()
                self.assertTrue(entered.wait(2))
                self.assertFalse(window.close())
                self.assertTrue(window.isVisible())
                self.assertTrue(window.sessions.writing[2].is_set())
            finally:
                release.set()
                self.wait_for_recovery(window)
        QTest.qWait(25)
        self.assertTrue(window.isVisible())
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(window.sessions.lock.isLocked())
        self.question.return_value = QMessageBox.StandardButton.Discard

    def test_invalid_session_navigation_leaves_current_inputs_and_published_records(self):
        window = self.window()
        route = ROUTES['basic', 'generate']
        window.open_tool(route)
        original = window.pages[route]
        original.first.expression.setText('n+2')
        record = window.publish(Signal([2]), operation='Actual')
        good = capture(window)
        original_tool = good['tools'][0]
        invalid = [
            ({**good, 'tools': [{'route': ['basic','missing'], 'inputs': {}}]}, 'desconocida'),
            ({**good, 'tools': [{'route': ['basic','generate']}]}, 'incompleta'),
            ({**good, 'tools': [original_tool, original_tool]}, 'repetida'),
            ({**good, 'tools': []}, 'ausente'),
            ({**good, 'tabs': [[], good['tabs'][-1]]}, 'inválida'),
            ({**good, 'tabs': [['browser','absent'], good['tabs'][-1]]}, 'desconocida'),
            ({**good, 'tabs': [good['tabs'][-1]]*2}, 'repetidas'),
        ]
        path = self.path/'invalid.json'
        for state, message in invalid:
            with self.subTest(message=message):
                session.save(path, Project(), state)
                self.assertFalse(window.sessions.open_path(path))
                self.assertIn(message, self.warning.call_args.args[-1])
                self.assertEqual(window.project.headers()[0]['id'], record)
                self.assertIs(window.pages[route], original)
                self.assertEqual(original.first.expression.text(), 'n+2')

    def test_hidden_cas_draft_can_be_reopened_and_does_not_leak_to_other_session(self):
        from signallab_pc.cas_reference import CAS_ROUTE

        window = self.window()
        window.open_cas()
        window.pages[CAS_ROUTE].input.setPlainText('factor(x^2-4)')
        window.close_document(window.documents.currentIndex())
        path = self.path/'with-draft.json'
        session.save(path, window.project, capture(window))
        new = self.window()
        self.assertTrue(new.sessions.open_path(path))
        self.assertNotEqual(new.current_operation, CAS_ROUTE)
        new.open_cas()
        self.assertEqual(new.pages[CAS_ROUTE].input.toPlainText(), 'factor(x^2-4)')
        empty = self.path/'ordinary.json'
        session.save(empty, Project(), session.empty_workspace())
        self.assertTrue(new.sessions.open_path(empty))
        new.open_cas()
        self.assertEqual(new.pages[CAS_ROUTE].input.toPlainText(), '')

    def test_root_editor_commits_exact_origin_and_polar_roots_to_filter(self):
        from signallab_pc.coefficient_editor import split_coefficients

        window = self.window()
        route = ROUTES['systems', 6]
        window.open_tool(route)
        page = window.pages[route]
        panel, editor = page.panel, page.root_entry
        panel.fields['zeros'].clear()
        panel.fields['poles'].clear()
        editor.representation.setCurrentIndex(1)
        editor.radius.setText('1/2')
        editor.angle.setText('pi/2')
        editor.add_button.click()
        self.assertEqual(editor.table.rowCount(), 2)
        first = editor.table.item(0, 1).text()
        self.assertIn('1/2', first)
        editor.table.item(0, 1).setText('n')
        self.assertEqual(editor.table.item(0, 1).text(), first)
        self.assertIn('valor anterior', editor.note.text())
        editor.kind.setCurrentIndex(1)
        editor.radius.setText('0')
        editor.add_button.click()
        self.assertEqual(split_coefficients(panel.fields['zeros'].text()), ['0'])
        self.assertIn('no definido', editor.table.item(2, 1).toolTip())
        panel.design_roots()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        record = window.project.headers('system')[-1]
        system = window.project.get(record['id'])
        zero, pole = system.poles_zeros()
        np.testing.assert_allclose(zero, [0], atol=1e-14)
        np.testing.assert_allclose(sorted(pole, key=lambda value: value.imag), [-.5j, .5j], atol=1e-14)
        angles = np.array([0, .3, 1.2])
        z = np.exp(1j*angles)
        np.testing.assert_allclose(system.response(angles), z/(z*z+.25), atol=1e-14)
        self.assertTrue(page.system_actions.reuse.isEnabled())

    def test_returning_dragged_real_root_to_axis_keeps_original_order(self):
        from types import SimpleNamespace

        window = self.window()
        route = ROUTES['systems', 6]
        window.open_tool(route)
        page = window.pages[route]
        editor = page.pole_editor
        page.panel.fields['zeros'].clear()
        page.panel.fields['poles'].setText('1/2')
        editor.manual()
        editor.mode.setCurrentIndex(2)

        def pointer(x, y, name):
            axis = page.panel.figure.axes[0]
            px, py = axis.transData.transform((x,y))
            return SimpleNamespace(button=1, inaxes=axis, xdata=x, ydata=y, x=px, y=py, name=name)

        press = pointer(.5, 0., 'button_press_event')
        editor.press(press)
        editor.move(pointer(.25, .4, 'motion_notify_event'))
        np.testing.assert_allclose(editor.data()[1], [.25+.4j, .25-.4j])
        editor.move(pointer(.3, 0., 'motion_notify_event'))
        editor.release(pointer(.3, 0., 'button_release_event'))
        self.wait_for_calculation(window)
        record = window.project.headers('system')[-1]
        system = window.project.get(record['id'])
        np.testing.assert_allclose(system.a, [1, -.3])
        np.testing.assert_allclose(editor.data()[1], [.3])

    def test_convolution_projects_the_same_complex_values_in_inspector_table_and_csv(self):
        import csv
        from PySide6.QtWidgets import QFileDialog

        window = self.window()
        window.show()
        route = ROUTES['basic','convolve']
        window.open_tool(route)
        page = window.pages[route]
        x, h = Signal([1+1j, 2], -2), Signal([3, -1j], 1)
        source = window.publish(x, operation='x[n]')
        impulse = window.publish(h, operation='h[n]')
        page.first.set_source(x, source)
        page.second.set_source(h, impulse)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        result = window.project.headers('signal')[-1]
        self.assertEqual(result['parents'], [source, impulse])
        expected = [3+3j, 7-1j, -2j]
        signal = window.project.get(result['id'])
        self.assertEqual(signal.origin, -1)
        np.testing.assert_allclose(signal.values, expected, atol=1e-14)

        inspector = page.convolution_inspector
        self.assertTrue(page.basic_result.views.isTabVisible(page.convolution_step_index))
        inspector.next.click()
        self.assertEqual(inspector.data['index'], 0)
        self.assertEqual(inspector.table.rowCount(), 2)
        self.assertEqual([row['k'] for row in inspector.data['rows']], [-2, -1])
        self.assertAlmostEqual(sum(row['product'] for row in inspector.data['rows']), 7-1j)
        inspector.index.setText('4')
        inspector.index.returnPressed.emit()
        self.assertEqual(inspector.table.rowCount(), 0)
        self.assertIsNone(inspector.data)
        inspector.index.setText('0')
        inspector.index.returnPressed.emit()
        self.assertEqual(inspector.table.rowCount(), 2)

        destination = self.path/'convolution.csv'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(destination), 'CSV')):
            page.basic_result.export()
        with destination.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.reader(stream))
        self.assertIn('origin=-1', rows[0])
        self.assertEqual(rows[1], ['axis', 'real', 'imag'])
        self.assertEqual([int(row[0]) for row in rows[2:]], [-1, 0, 1])
        np.testing.assert_allclose([complex(float(row[1]), float(row[2])) for row in rows[2:]],
                                   expected, atol=1e-14)

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
