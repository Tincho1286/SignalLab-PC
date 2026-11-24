import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import numpy as np
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from signallab_pc import ar_estimation
from signallab_pc.model import Signal
from signallab_pc.signal_segment import extract


class SampleCoordinateTests(unittest.TestCase):
    def test_extract_requires_both_clock_fields_to_move_the_time_reference(self):
        for metadata, expected in [
            ({'sample_rate_hz': 8}, {'sample_rate_hz': 8}),
            ({'time_start_s': 12}, {}),
            ({'sample_rate_hz': 8, 'time_start_s': 12},
             {'sample_rate_hz': 8, 'time_start_s': 12.125}),
        ]:
            with self.subTest(metadata=metadata):
                part = extract(Signal([1, 2, 3, 4], -4, metadata=metadata), -3, -2)
                np.testing.assert_array_equal(part.axis, [-3, -2])
                np.testing.assert_array_equal(part.values, [2, 3])
                self.assertEqual({name: part.metadata[name] for name in ('sample_rate_hz', 'time_start_s')
                                  if name in part.metadata}, expected)

    def test_extract_preserves_order_on_a_descending_axis(self):
        source = Signal([10, 20, 30, 40], 3, -1, 's', domain='continuous')
        part = extract(source, 1, 2)
        np.testing.assert_array_equal(part.axis, [2, 1])
        np.testing.assert_array_equal(part.values, [20, 30])
        self.assertEqual(part.metadata['sample_rate_hz'], 1)
        with self.assertRaisesRegex(ValueError, 'coincidir'):
            extract(source, 1, 2.25)

    def test_extraction_accepts_the_zero_coordinate_after_rounding(self):
        source = Signal([1, 2, 3, 4], 0.3, -0.1, 's', domain='continuous')
        np.testing.assert_array_equal(extract(source, '0', '0').values, [4])
        with self.assertRaisesRegex(ValueError, 'coincidir'):
            extract(source, '0.002', '0.002')

    def test_ar_can_use_large_indices_and_a_rate_without_an_absolute_start(self):
        source = Signal([1, 2, 3, 4], 2**55, metadata={'sample_rate_hz': 8})
        data = ar_estimation.prepare(source)
        np.testing.assert_array_equal(data['x'], [.25, .5, .75, 1])
        part = ar_estimation.temporal(source, [2, 3], 1, 'Estimación', 'prueba')
        self.assertEqual(part.origin, 2**55+1)
        self.assertNotIn('time_start_s', part.metadata)

    def test_windowed_impulse_keeps_the_aligned_clock_from_the_impulse(self):
        from signallab_pc.windowing import window_impulse

        impulse = Signal([1, 2, 3, 4], -1, metadata={'sample_rate_hz': 8, 'time_start_s': 12})
        window = Signal([1, .5, 1], 0, metadata={'sample_rate_hz': 8})
        result = window_impulse(impulse, custom=window)
        np.testing.assert_array_equal(result.windowed.axis, [0, 1, 2])
        np.testing.assert_array_equal(result.windowed.values, [2, 1.5, 4])
        self.assertEqual(result.windowed.metadata['time_start_s'], 12.125)
        self.assertEqual(result.system.sample_period_s, .125)
        self.assertNotIn('time_start_s', window.metadata)
        misaligned = window.copy_with(metadata={'sample_rate_hz': 8, 'time_start_s': 13})
        with self.assertRaisesRegex(ValueError, 'mismos índices'):
            window_impulse(impulse, custom=misaligned)

    def test_inverse_dtft_and_series_keep_the_available_clock(self):
        from signallab_pc.fourier import dtft, discrete_series, synthesize_discrete
        from signallab_pc.inverse_dtft import inverse_dtft

        source = Signal([1,2,3],-4,metadata={'time_start_s':12})
        spectrum = dtft(source,count=65)
        self.assertEqual(inverse_dtft(spectrum,-4,3).metadata['time_start_s'],12)
        self.assertNotIn('time_start_s',inverse_dtft(spectrum,-3,2).metadata)
        complete = source.copy_with(metadata={'time_start_s':12,'sample_rate_hz':8})
        self.assertEqual(inverse_dtft(dtft(complete,count=65),-3,2).metadata['time_start_s'],12.125)
        restored = synthesize_discrete(discrete_series(complete))
        np.testing.assert_array_equal(restored.axis,[-4,-3,-2])
        np.testing.assert_allclose(restored.values,[1,2,3],atol=1e-14)
        self.assertEqual(restored.metadata['time_start_s'],12)
        self.assertEqual(restored.metadata['sample_rate_hz'],8)

    def test_periodic_inverse_retains_a_representable_subnormal_endpoint(self):
        from signallab_pc.frequency_filter import analyze
        from signallab_pc.inverse_dtft import inverse_dtft

        smallest = math.ulp(0.0)
        spectrum = Signal([smallest,smallest],-math.pi,math.tau,'rad/muestra',domain='frequency')
        self.assertEqual(inverse_dtft(spectrum,0,1).values[0],smallest)
        identity = spectrum.copy_with(values=[1,1],metadata={'operation':'frequency_response'})
        results, _ = analyze(identity,'discrete',0,2,1,Signal([smallest]))
        self.assertEqual(results[-1].values[0],smallest)

    def test_continuous_integrals_keep_representable_extreme_products(self):
        from signallab_pc.continuous import convolution, correlation, periodic_correlation

        for amplitude, step, expected in ((1e-170,1e100,1e-240),(1e200,1e-120,1e280)):
            with self.subTest(amplitude=amplitude,step=step):
                source = Signal([amplitude,amplitude],0,step,'s',domain='continuous')
                np.testing.assert_allclose(convolution(source,source).values,[0,expected,0],rtol=1e-14,atol=0)
                np.testing.assert_allclose(correlation(source).values,[0,expected,0],rtol=1e-14,atol=0)
                np.testing.assert_allclose(periodic_correlation(source).values,[2*expected]*2,rtol=1e-14,atol=0)


class ClockFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        settings = QSettings(str(Path(directory)/'settings.ini'), QSettings.Format.IniFormat)
        self.enterContext(patch('signallab_pc.workbench.desktop_settings', return_value=settings))
        self.enterContext(patch('signallab_pc.update_ui.installed', return_value=None))
        from signallab_pc.workbench import WorkbenchWindow
        self.window = WorkbenchWindow(recovery_directory=directory)
        self.addCleanup(self.close_window)

    def close_window(self):
        self.window.deleteLater()
        self.app.processEvents()

    def test_new_source_clears_old_auto_clock_and_preserves_explicit_values(self):
        from signallab_pc.rational_resampling_panel import RationalResamplingPanel
        from signallab_pc.reconstruction_panel import ReconstructionPanel
        for kind in (RationalResamplingPanel, ReconstructionPanel):
            with self.subTest(tool=kind.__name__):
                panel = kind(self.window)
                self.addCleanup(panel.deleteLater)
                anchored = Signal([1, 2], metadata={'sample_rate_hz': 8, 'time_start_s': 12})
                panel.source.set_source(anchored)
                self.assertEqual((float(panel.rate.text()), float(panel.start.text())), (8, 12))
                panel.source.set_source(Signal([3, 4]))
                self.assertEqual((panel.rate.text(), panel.start.text()), ('', ''))
                panel.source.set_source(anchored)
                panel.rate.setText('125')
                panel.start.setText('15')
                panel.source.set_source(Signal([5, 6]))
                self.assertEqual((panel.rate.text(), panel.start.text()), ('125', '15'))

    def test_editor_pastes_a_descending_table_without_reordering_samples(self):
        from signallab_pc.sample_paste import parse
        from signallab_pc.sample_paste_dialog import PasteSignalDialog
        from signallab_pc.signal_editor_panel import SignalEditorPanel

        source = Signal([10, 20, 30, 40, 50], 0.4, -0.1, 's', domain='continuous')
        table = '0.3 80\n0.2 90\n0.1 100'
        with self.assertRaisesRegex(ValueError, 'creciente'):
            parse(table, 'continuous', layout='axis_value')

        editor = SignalEditorPanel(self.window)
        self.addCleanup(editor.deleteLater)
        editor.receive(source)
        dialog = PasteSignalDialog(table, 'continuous', parent=editor, allow_descending=True)
        dialog.layout_choice.setCurrentIndex(dialog.layout_choice.findData('axis_value'))
        editor.paste_values(dialog.read())
        result = editor.extract_segment('0', '0.2')
        np.testing.assert_allclose(result.axis, [.2, .1, 0], atol=5e-17)
        np.testing.assert_array_equal(result.values, [90, 100, 50])
        self.assertEqual(result.step, -0.1)
        self.assertEqual(result.metadata['sample_rate_hz'], 10)
        self.assertAlmostEqual(result.metadata['time_start_s'], .2)
        editor.history.stack.undo()
        np.testing.assert_array_equal(editor.staged_signal().values, source.values)
