import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QElapsedTimer
from PySide6.QtTest import QTest

from signallab_pc.ui import SignalLabWindow
from signallab_pc.model import Signal


class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = SignalLabWindow()

    def tearDown(self):
        self.window._thread_pool.waitForDone()
        self.app.processEvents()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def finish(self):
        timer = QElapsedTimer(); timer.start()
        while self.window._workers and timer.elapsed() < 10000:
            QTest.qWait(10)
        self.assertFalse(self.window._workers, "El worker no devolvió el resultado")

    def test_worker_result_returns_to_gui_thread(self):
        threads = []
        self.window._run_operation("Prueba", lambda: 42,
            lambda value: threads.append((value, QThread.currentThread() == self.app.thread())))
        self.finish()
        self.assertEqual(threads, [(42, True)])

    def test_filter_design_and_impulse_reach_main_signal(self):
        panel = self.window.systems_panel
        panel.design_fir(); self.finish()
        self.assertEqual(len(panel.system.b), 51)
        panel.fields["count"].setText("80")
        panel.excitation("impulse"); self.finish()
        self.assertEqual(self.window.signal.values.size, 80)
        self.assertAlmostEqual(self.window.signal.values[25].real, .2)

    def test_paged_table_edit_targets_absolute_sample(self):
        self.window._set_signal(Signal([0]*4001))
        self.window._change_table_page(1)
        with patch("signallab_pc.ui.QMessageBox.warning") as warning:
            self.window.table.item(3, 1).setText("7")
            self.assertFalse(warning.called)
        self.assertEqual(self.window.signal.values[2003], 7)
        self.assertEqual(self.window.signal.values[3], 0)


if __name__ == "__main__":
    unittest.main()
