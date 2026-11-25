"""Filter study UI contracts with independent spectral computations."""
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QFileDialog

from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.storage import load_json
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class FilterStudyWorkbenchContracts(DesktopSessionFixture):
    def test_fft_reference_survives_recalculation_and_uses_same_frequency_and_phase(self):
        window = self.window()
        source = Signal([2-1j, 3, -1, 4], -3, metadata={'sample_rate_hz':32})
        key = window.publish(source, operation='Registro para comparar ventanas')
        route = ROUTES['course_tools','fft']
        window.send_signal(source, key, route)
        panel = window.pages[route].panel
        panel.fields['nfft'].setText('16')
        panel.fields['points'].setText('65')
        self.assertFalse(panel.overlay_enabled.isChecked())
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(panel.selector.currentIndex(), 0)
        self.assertGreaterEqual(len(panel.items), 2)
        dft, dtft = panel.items[:2]
        expected = np.exp(-1j*np.outer(dft.axis, np.arange(-3,1)))@source.values
        np.testing.assert_allclose(dft.values, expected, atol=1e-13)
        np.testing.assert_allclose(dtft.values,
                                   np.exp(-1j*np.outer(dtft.axis, np.arange(-3,1)))@source.values,
                                   atol=1e-13)
        panel.overlay_enabled.setChecked(True)
        axes = panel.view.figure.axes
        self.assertEqual(len(axes),2)
        self.assertEqual(axes[0].get_xlim(), axes[1].get_xlim())
        self.assertIn(dtft.name, axes[0].get_legend_handles_labels()[1])
        panel.pin_spectrum()
        reference = panel.reference_spectrum
        self.assertIsNotNone(reference)
        panel.fields['window'].setCurrentIndex(panel.fields['window'].findData('hann'))
        window.calculate_active()
        self.wait_for_calculation(window)
        current = panel.items[0]
        self.assertIs(panel.reference_spectrum, reference)
        np.testing.assert_array_equal(reference.values, dtft.values)
        expected = np.exp(-1j*np.outer(current.axis, np.arange(-3,1)))@(source.values*np.hanning(4))
        np.testing.assert_allclose(current.values, expected, atol=1e-13)
        panel.selector.setCurrentIndex(1)
        self.assertIn(reference.name,panel.view.figure.axes[0].get_legend_handles_labels()[1])
        panel.remove_reference()
        self.assertNotIn(reference.name,panel.view.figure.axes[0].get_legend_handles_labels()[1])
        path = self.path/'dtft.json'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'JSON')):
            panel.view.export()
        saved = load_json(path)
        np.testing.assert_array_equal(saved.values,panel.items[1].values)
        np.testing.assert_array_equal(saved.axis,panel.items[1].axis)

    def test_fir_comparison_uses_common_length_and_reuses_the_selected_design(self):
        window = self.window()
        route = ROUTES['course_tools','fir']
        window.open_tool(route)
        panel = window.pages[route].panel
        mode = panel.fields['comparison_mode']
        mode.setCurrentIndex(mode.findData('length'))
        panel.fields['common_length'].setText('31')
        panel.fields['amplitude_low'].setText('2')
        panel.fields['dp'].setText('0.15')
        panel.fields['ds'].setText('0.12')
        selector = panel.fields['tolerance_units']
        selector.setCurrentIndex(selector.findData('db'))
        self.assertEqual(panel.fields['ds'].text(),'40')
        panel.fields['ds'].setText('26')
        selector.setCurrentIndex(selector.findData('absolute'))
        self.assertEqual(panel.fields['ds'].text(),'0.12')
        self.assertEqual(panel.fields['dp'].text(),'0.15')
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=15000)
        systems = [item for item in panel.items if isinstance(item,Transfer)]
        self.assertGreaterEqual(len(systems),2)
        normalized = np.arange(31)-15
        base = .7*np.sinc(.35*normalized)
        hann = next(item for item in systems if 'hann' in item.name.lower())
        np.testing.assert_allclose(hann.b,base*np.hanning(31),atol=1e-15)
        panel.selector.setCurrentIndex(next(index for index, value in enumerate(panel.items) if value is hann))
        panel.show_all_systems.setChecked(True)
        panel.system_view.setCurrentIndex(3)
        axis = panel.view.figure.axes[0]
        data = next(line for line in axis.lines if line.get_label().startswith(hann.name))
        omega = data.get_xdata()
        np.testing.assert_allclose(data.get_ydata(),abs(np.exp(-1j*np.outer(omega, np.arange(31)))@hann.b),atol=1e-13)
        self.assertIn('|H|', axis.get_ylabel())
        self.assertIn('Transición especificada (entre bordes)',axis.get_legend_handles_labels()[1])
        panel.system_view.setCurrentIndex(2)
        delay = next(line for line in panel.view.figure.axes[0].lines if line.get_label().startswith(hann.name))
        active = np.isfinite(delay.get_ydata())
        self.assertTrue(active.any())
        np.testing.assert_allclose(delay.get_ydata()[active],15.,atol=1e-12)
        analyze = next(action for action in panel.system_actions.analysis.menu().actions()
                       if action.text()=='Respuesta en frecuencia')
        analyze.trigger()
        analysis = window.pages[ROUTES['system_analysis',0]].panel
        self.assertIsNotNone(analysis.input_id)
        np.testing.assert_array_equal(window.project.get(analysis.input_id).b,hann.b)
