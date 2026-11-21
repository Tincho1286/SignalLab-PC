import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PySide6.QtCore import QSettings
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
        self.app.processEvents()

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
