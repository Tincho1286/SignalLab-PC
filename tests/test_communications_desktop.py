import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from matplotlib.figure import Figure
import numpy as np
from PySide6.QtCore import QCoreApplication, QDeadlineTimer, QEvent, QPoint, QRect, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QTabBar, QToolButton

from signallab_pc import communications_figures as figures
from signallab_pc.communications_data import SymbolClock, iq_signal
from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading
from signallab_pc.communications_pipeline import load_channel_pipeline
from signallab_pc.communications_storage import load_experiment
from signallab_pc.library_content import default_content
from signallab_pc.tool_browser import CatalogCard
from signallab_pc.workbench import WorkbenchWindow
from signallab_pc.workspaces import ROUTES


class CommunicationsDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.folder = self.enterContext(TemporaryDirectory())
        settings = QSettings(str(Path(self.folder)/'settings.ini'), QSettings.Format.IniFormat)
        self.enterContext(patch('signallab_pc.workbench.desktop_settings', return_value=settings))
        self.enterContext(patch('signallab_pc.update_ui.installed', return_value=None))
        self.enterContext(patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Discard))
        self.warning = self.enterContext(patch.object(QMessageBox, 'warning'))
        self.error = self.enterContext(patch('signallab_pc.runtime_diagnostics.report_error'))
        self.window = WorkbenchWindow(recovery_directory=self.folder)
        self.window.resize(940, 700)
        self.window.show()
        self.addCleanup(self.close_window)

    def close_window(self):
        if self.window._workers:
            self.window._cancel_operations()
            self.wait_for_idle()
        self.window.close()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()

    def open(self, name):
        route = ROUTES['communications', name]
        self.window.open_tool(route)
        self.app.processEvents()
        page = self.window.pages[route]
        return page, page.panel

    def wait_for_idle(self):
        timeout = QDeadlineTimer(12_000)
        while self.window._workers and not timeout.hasExpired():
            self.app.processEvents()
            # Release the GIL while the Python calculation runs in the Qt worker.
            sleep(0.01)
        self.assertFalse(self.window._workers, 'El cálculo no se detuvo dentro del plazo de la prueba.')

    def wait(self):
        self.wait_for_idle()
        self.warning.assert_not_called()
        self.error.assert_not_called()

    def calculate(self):
        self.window.calculate_active()
        self.wait()

    def test_closing_calculated_link_restores_readable_catalog_and_inset_close_buttons(self):
        self.window.resize(700, 540)
        self.window.show_area('communications')
        QTest.qWait(25)
        browser = self.window.pages['browser',]
        cards = [card for card in browser.findChildren(CatalogCard) if card.isVisible()]
        self.assertTrue(cards)
        heights = [(card.title.height(), card.summary.height()) for card in cards]
        link = next(card for card in cards if card.accessibleName() == 'Enlace digital')
        browser.ensureWidgetVisible(link)
        QTest.mouseClick(link, Qt.MouseButton.LeftButton)
        panel = self.window.pages[ROUTES['communications', 'link']].panel
        panel.fields['bit_count'].setText('160')
        self.calculate()
        tab_bar = self.window.documents
        index = tab_bar.currentIndex()
        slot = tab_bar.tabButton(index, QTabBar.ButtonPosition.RightSide)
        close = slot.findChild(QToolButton, 'documentClose')
        self.assertIsNotNone(close)
        self.assertTrue(close.isVisible())
        close_rect = QRect(close.mapTo(tab_bar, QPoint()), close.size())
        self.assertTrue(tab_bar.tabRect(index).adjusted(6, 3, -6, -3).contains(close_rect))
        records = self.window.project.headers()
        self.assertTrue(records)
        QTest.mouseClick(close, Qt.MouseButton.LeftButton)
        QTest.qWait(25)
        self.assertIs(self.window.stack.currentWidget(), browser)
        self.assertEqual(browser.area, 'communications')
        self.assertEqual(tab_bar.count(), 1)
        self.assertEqual(self.window.project.headers(), records)
        for card, (title_height, summary_height) in zip(cards, heights, strict=True):
            self.assertTrue(card.isVisible())
            self.assertGreaterEqual(card.title.height(), title_height)
            self.assertGreaterEqual(card.summary.height(), summary_height)

    def test_workbench_link_matches_python_and_has_reopenable_figures(self):
        page, panel = self.open('link')
        panel.fields['bit_count'].setText('160')
        panel.fields['seed'].setText('15')
        self.window.resize(640, 420)
        QTest.qWait(25)
        self.assertTrue(page.workspace.compact)
        self.assertTrue(self.window.calculate_action.isVisible())
        self.calculate()
        self.assertEqual(page.workspace.tabs.currentIndex(), 1)
        row = next(row for row in self.window.project.headers() if row['title'] == 'Experimento de comunicaciones')
        result = load_experiment(self.window.project, row['id'])
        expected = run_experiment(ExperimentSpec(bit_count=160, seed=15))
        self.assertEqual(result.report['metrics'], expected.report()['metrics'])
        self.assertEqual(len(self.window.project.headers()), 1+len(result.records))
        for key, signal in expected.signals().items():
            np.testing.assert_array_equal(self.window.project.get(result.records[key]).values, signal.values)
        self.assertIn('BER', panel.result.text.toPlainText())
        launcher = page.workspace.results.graph_launcher
        entries = {item[2]: item for item in launcher.available()}
        self.assertEqual(set(entries), {
            'Constelación', 'I/Q', 'Ojo', 'Espectro', 'PSD', 'Impulso del filtro', 'Respuesta del filtro', 'Tasas de error',
        })
        for name in (*entries, 'Espectro'):
            launcher.open_entry(entries[name])
            self.wait()
            self.app.processEvents()
            canvas = entries[name][0]()
            self.assertTrue(canvas._signallab_window.isVisible())
            self.assertTrue(canvas.figure.axes)
            if name == 'Constelación':
                filename = Path(self.folder)/'constelacion.png'
                canvas.print_figure(filename, dpi=140)
                self.assertEqual(filename.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
            canvas._signallab_window.hide()
        self.assertEqual(set(item[2] for item in launcher.available()), set(entries))
        self.window.resize(1200, 800)
        QTest.qWait(25)
        self.assertFalse(page.workspace.compact)
        self.assertTrue(launcher.isEnabled())

    def test_independent_routes_show_help_and_exchange_clocked_iq(self):
        articles, guides, _ = default_content()
        for name in ('modulate', 'pulse', 'awgn', 'multipath', 'fading', 'carrier', 'impairments',
                     'interference', 'propagation', 'channel_pipeline', 'receive', 'decide', 'measure'):
            with self.subTest(name=name):
                self.assertIn(('communications', name), articles)
                self.assertIn(('communications', name), guides)
                page, panel = self.open(name)
                self.assertIsNotNone(page.workspace)
        _, tx = self.open('modulate')
        tx.fields['manual_bits'].setText('01 10 01 00')
        self.calculate()
        symbols, identifier = tx.records['Símbolos I/Q']
        route = ROUTES['communications', 'pulse']
        self.window.send_signal(symbols, identifier, route)
        pulse = self.window.pages[route].panel
        self.assertTrue(pulse.fields['apply'].isChecked())
        self.assertEqual(pulse.fields['filter_kind'].currentData(), 'interpolate')
        pulse.fields['sps'].setText('4')
        self.calculate()
        waveform, key = next(iter(pulse.records.values()))
        self.assertEqual(waveform.metadata['sample_rate_hz'], 48000)
        route = ROUTES['communications', 'awgn']
        self.window.send_signal(waveform, key, route)
        noisy = self.window.pages[route].panel
        self.calculate()
        self.assertIn('Varianza nominal I', noisy.result.text.toPlainText())
        noisy_signal, _ = next(iter(noisy.records.values()))
        self.assertEqual(noisy_signal.metadata['sample_rate_hz'], 48000)
        _, measure = self.open('measure')
        measure.fields['tx_labels'].setText('1, 2, 3')
        measure.fields['rx_labels'].setText('1, 2, 2')
        self.calculate()
        self.assertIn('1 / 6', measure.result.text.toPlainText())
        self.assertIn('1 / 3', measure.result.text.toPlainText())

    def test_multipath_keeps_a_reusable_result_and_opens_its_graphs(self):
        source = iq_signal([1+2j, 3-1j], SymbolClock(4000, 2, -0.25), origin=-3)
        key = self.window.publish(source, operation='Entrada de prueba')
        route = ROUTES['communications', 'multipath']
        self.window.send_signal(source, key, route)
        page, panel = self.open('multipath')
        panel.fields['paths'].setPlainText('0 = 1\n2 = -i/2')
        self.calculate()
        result, record = panel.records['Salida multitrayecto']
        np.testing.assert_array_equal(result.values, [1+2j, 3-1j, 1-0.5j, -0.5-1.5j])
        self.assertIn('Último índice', panel.result.text.toPlainText())
        launcher = page.workspace.results.graph_launcher
        entries = {item[2]: item for item in launcher.available()}
        self.assertEqual(set(entries), {'I/Q', 'Espectro', 'Impulso y perfil de potencia', 'Respuesta del canal'})
        for name in ('Espectro', 'Impulso y perfil de potencia', 'Respuesta del canal'):
            launcher.open_entry(entries[name])
            self.wait()
        panel.fields['paths'].setPlainText('0 = 1')
        self.assertTrue(panel.result_state.property('resultStale'))
        receive = ROUTES['communications', 'receive']
        self.window.send_signal(result, record, receive)
        self.assertEqual(self.window.pages[receive].panel.source.loaded_reference_id, record)

    def test_fading_matches_python_and_exposes_each_path(self):
        source = iq_signal([1, 1j, -2], SymbolClock(4000, 2, -0.25), origin=-3)
        key = self.window.publish(source, operation='Entrada de prueba')
        route = ROUTES['communications', 'fading']
        self.window.send_signal(source, key, route)
        page, panel = self.open('fading')
        panel.fields['paths'].setPlainText('0 = 1\n2 = 0.5, 10, pi/4')
        panel.fields['k_scale'].setCurrentIndex(1)
        panel.fields['seed'].setText('43')
        panel.fields['diagnostic_path'].setText('2')
        self.calculate()
        expected = apply_fading(source, FadingSpec((FadingPath(), FadingPath(2, 0.5, 10, math.pi/4)), 43))
        values = [expected.signal, *(part.coefficients for part in expected.realizations)]
        self.assertEqual(len(panel.records), 3)
        for source_record, (actual, record) in zip(values, panel.records.values(), strict=True):
            np.testing.assert_array_equal(actual.values, source_record.values)
            self.assertEqual(self.window.project.get(record).origin, source_record.origin)
        self.assertIn('Rician', panel.result.text.toPlainText())
        launcher = page.workspace.results.graph_launcher
        entry = next(item for item in launcher.available() if item[2] == 'Evolución del fading')
        launcher.open_entry(entry)
        self.wait()
        name = 'Distribuciones de envolvente y fase'
        launcher.open_entry(next(item for item in launcher.available() if item[2] == name))
        self.wait()
        canvas, _ = panel.canvas[name]
        phase, = canvas.figure.axes[1].lines
        reference = expected.realizations[1].distributions()
        np.testing.assert_array_equal(phase.get_xdata(), reference.phase.reference_axis)
        np.testing.assert_array_equal(phase.get_ydata(), reference.phase.theoretical)
        self.assertEqual(len(canvas.figure.axes[1].patches), 1)

        panel.fields['process'].setCurrentIndex(1)
        panel.fields['max_doppler_hz'].setText('120')
        self.calculate()
        signal, key = next(iter(panel.records.values()))
        self.assertEqual(signal.metadata['communications_fading']['specification']['max_doppler_hz'], 120)
        self.assertIn('Coherencia teórica', panel.result.text.toPlainText())
        entry = next(item for item in launcher.available() if item[2] == 'Autocorrelación y PSD Doppler')
        launcher.open_entry(entry)
        self.wait()
        carrier_route = ROUTES['communications', 'carrier']
        self.window.send_signal(signal, key, carrier_route)
        _, carrier = self.open('carrier')
        carrier.fields['frequency_hz'].setText('-1000')
        self.calculate()
        shifted, _ = next(iter(carrier.records.values()))
        np.testing.assert_allclose(shifted.values, signal.values*np.exp(-1j*math.pi/4*np.arange(signal.values.size)),
                                   atol=1e-14)

    def test_impairments_select_models_and_publish_phase_trajectory(self):
        source = iq_signal([1, 1j, -2, 3j], SymbolClock(4000, 2, -0.25), origin=-3)
        key = self.window.publish(source, operation='Entrada de prueba')
        route = ROUTES['communications', 'impairments']
        self.window.send_signal(source, key, route)
        page, panel = self.open('impairments')
        panel.fields['delay_samples'].setText('1')
        self.calculate()
        signal, _ = next(iter(panel.records.values()))
        np.testing.assert_array_equal(signal.values, [0, 1, 1j, -2])
        panel.fields['impairment'].setCurrentIndex(1)
        self.assertFalse(panel.fields['delay_samples'].isVisible())
        self.calculate()
        output, _ = panel.records['Salida con ruido de fase']
        phase, _ = panel.records['Trayectoria de fase']
        np.testing.assert_allclose(output.values, source.values*np.exp(1j*phase.values))
        launcher = page.workspace.results.graph_launcher
        entry = next(item for item in launcher.available() if item[2] == 'Trayectoria de fase')
        launcher.open_entry(entry)
        self.wait()
        panel.fields['impairment'].setCurrentIndex(2)
        panel.fields['dc_i'].setText('1/4')
        self.calculate()
        altered, _ = next(iter(panel.records.values()))
        np.testing.assert_array_equal(altered.values, source.values + .25)
        self.assertIn('Sin componente imagen', panel.result.text.toPlainText())

    def test_interference_panel_switches_sources_and_saves_components(self):
        clock = SymbolClock(4000, 2, -0.25)
        desired = iq_signal([1]*16, clock, origin=-3)
        external = iq_signal([1j]*16, clock, origin=-3)
        a = self.window.publish(desired, operation='Entrada de prueba')
        b = self.window.publish(external, operation='Entrada de prueba')
        route = ROUTES['communications', 'interference']
        self.window.send_signal(desired, a, route)
        page, panel = self.open('interference')
        panel.fields['interference_mode'].setCurrentIndex(2)
        panel.interferer_input.set_source(external, b)
        panel.fields['calibration'].setCurrentIndex(1)
        panel.fields['interference_power'].setText('1/4')
        self.calculate()
        mix, key = panel.records['Salida con interferencia']
        interference, _ = panel.records['Componente interferente']
        np.testing.assert_allclose(mix.values, 1+.5j)
        np.testing.assert_allclose(interference.values, .5j)
        self.assertIn('SINR', panel.result.text.toPlainText())
        self.assertEqual(self.window.project.get(key).origin, -3)
        panel.fields['add_noise'].setChecked(True)
        self.calculate()
        self.assertIn('Ruido aditivo de la interferencia', panel.records)
        launcher = page.workspace.results.graph_launcher
        entry = next(item for item in launcher.available() if item[2] == 'Espectros de los componentes')
        launcher.open_entry(entry)
        self.wait()

    def test_propagation_panel_uses_the_recorded_carrier_and_exposes_loss(self):
        values = [1, 1j, -2]
        clock = SymbolClock(4000, 2, 0.1, 1e9)
        source = iq_signal(values, clock, origin=3)
        key = self.window.publish(source, operation='Entrada de prueba')
        self.window.send_signal(source, key, ROUTES['communications', 'propagation'])
        _, panel = self.open('propagation')
        panel.fields['propagation_model'].setCurrentIndex(1)
        panel.fields['distance_m'].setText('1000')
        self.calculate()
        result, record = panel.records['Salida de propagación']
        expected = (299_792_458/(1e9*4*np.pi*1000))*np.array(values)
        np.testing.assert_allclose(result.values, expected)
        self.assertEqual(self.window.project.get(record).metadata['sample_rate_hz'], 8000)
        self.assertIn('Pérdida por distancia', panel.result.text.toPlainText())

    def test_channel_pipeline_editor_reorders_and_binds_external_signals(self):
        source = iq_signal([1, 2, 3], SymbolClock(4000, 2, -.25), origin=-3)
        peer = source.copy_with(values=np.full(3, 1j), name='Interferente')
        tx, external = (self.window.publish(signal, operation='Entrada de prueba') for signal in (source, peer))
        self.window.send_signal(source, tx, ROUTES['communications', 'channel_pipeline'])
        _, panel = self.open('channel_pipeline')
        editor = panel.fields['pipeline']
        editor.preset.setCurrentIndex(editor.preset.findText('Interferencia externa'))
        editor.append()
        editor.choices['interferente'].setCurrentIndex(editor.choices['interferente'].findData(external))
        editor.preset.setCurrentIndex(editor.preset.findText('Retardo'))
        editor.append()
        editor.reorder(-1)
        self.calculate()
        output, _ = panel.records['Salida de la cadena']
        np.testing.assert_array_equal(output.values, [1j, 1+1j, 2+1j])
        reports = [item['id'] for item in self.window.project.headers('calculation') if item['title'] == 'Cadena de canal']
        _, report = load_channel_pipeline(self.window.project, reports[-1])
        self.assertEqual(report['external_records']['interferente'], external)
        self.assertIn('Potencia de entrada', panel.result.text.toPlainText())

    def test_link_workbench_reuses_channel_pipeline_and_exposes_receiver_status(self):
        page, panel = self.open('link')
        panel.fields['bit_count'].setText('100')
        panel.fields['noise_enabled'].setChecked(False)
        panel.fields['channel_enabled'].setChecked(True)
        editor = panel.fields['pipeline']
        editor.preset.setCurrentIndex(editor.preset.findText('Multitrayecto'))
        editor.append()
        self.calculate()
        self.assertIn('Cadena de canal', panel.result.text.toPlainText())
        self.assertIn('Salida de la cadena', panel.records)
        self.assertIn('Símbolos recibidos', panel.records)
        launcher = page.workspace.results.graph_launcher
        entry = next(item for item in launcher.available() if item[2] == 'I/Q después de la cadena')
        launcher.open_entry(entry)
        self.wait()
        editor.preset.setCurrentIndex(editor.preset.findText('Error de reloj'))
        editor.append()
        self.calculate()
        self.assertIn('corregir el SFO', panel.result.text.toPlainText())
        self.assertIn('Después del filtro adaptado', panel.records)
        self.assertNotIn('Símbolos recibidos', panel.records)

    def test_sweep_workbench_selects_channel_axes_and_displays_replica_means(self):
        page, panel = self.open('sweep')
        panel.fields['directory'].setText(str(Path(self.folder)/'channel-campaign'))
        panel.fields['bit_count'].setText('80')
        panel.fields['channel_enabled'].setChecked(True)
        editor = panel.fields['pipeline']
        editor.preset.setCurrentIndex(editor.preset.findText('Doppler o CFO'))
        editor.append()
        axis = panel.fields['axis']
        axis.setCurrentIndex(axis.findData('channel.1.frequency_hz'))
        self.assertEqual(axis.currentData(), 'channel.1.frequency_hz')
        panel.fields['axis_values'].setText('0,50')
        panel.fields['repetitions'].setText('2')
        self.calculate()
        self.assertEqual(len(panel.campaign.runs), 4)
        self.assertIn('Medias por punto', panel.result.text.toPlainText())
        launcher = page.workspace.results.graph_launcher
        entry = next(item for item in launcher.available() if item[2] == 'Comparación de corridas')
        launcher.open_entry(entry)
        self.wait()

    def test_receive_and_decide_publish_labels_that_metrics_can_load(self):
        _, mapper = self.open('modulate')
        mapper.fields['manual_bits'].setText('00 11 01 10')
        self.calculate()
        emitted, _ = mapper.records['Símbolos I/Q']
        samples = np.zeros(12, dtype=complex)
        samples[2::3] = emitted.values
        source = iq_signal(samples, SymbolClock(12000, 3), origin=-7)
        key = self.window.project.add(source)
        route = ROUTES['communications', 'receive']
        self.window.send_signal(source, key, route)
        receiver = self.window.pages[route].panel
        receiver.fields['count'].setText('4')
        receiver.fields['offset'].setText('2')
        self.calculate()
        observed, identifier = next(iter(receiver.records.values()))
        np.testing.assert_array_equal(observed.values, emitted.values)
        self.assertEqual(observed.metadata['samples_per_symbol'], 1)
        route = ROUTES['communications', 'decide']
        self.window.send_signal(observed, identifier, route)
        self.calculate()
        _, quality = self.open('measure')
        headers = self.window.project.headers('calculation')
        for field, title in (('tx_record', 'Etiquetas transmitidas'), ('rx_record', 'Etiquetas recibidas')):
            identifier = next(row['id'] for row in headers if row['title'] == title)
            combo = quality.fields[field]
            self.assertGreater(combo.findData(identifier), 0)
            combo.setCurrentIndex(combo.findData(identifier))
        self.calculate()
        self.assertIn('0 / 8', quality.result.text.toPlainText())

    def test_fourier_figures_use_physical_frequency_or_rad_per_sample(self):
        rate, n, bin_index = 8000, 16, 3
        x = np.exp(2j*math.pi*bin_index*np.arange(n)/n)
        original = iq_signal(x, SymbolClock(rate))
        for with_clock in (True, False):
            with self.subTest(with_clock=with_clock):
                source = original if with_clock else original.copy_with(metadata={})
                figure = Figure()
                spec = figures.spectrum_data(source)
                figures.spectrum_figure(figure, spec)
                axis = figure.axes[0]
                curve = axis.lines[0]
                peak = np.argmax(curve.get_ydata())
                expected = rate*bin_index/n if with_clock else math.tau*bin_index/n
                self.assertAlmostEqual(curve.get_xdata()[peak], expected)
                self.assertAlmostEqual(curve.get_ydata()[peak], 1.0)
        density = Figure()
        figures.spectrum_figure(density, figures.spectrum_data(original, density=True), density=True)
        self.assertEqual(density.axes[0].get_xlabel(), 'Frecuencia (Hz)')
        self.assertIn('/Hz', density.axes[0].get_ylabel())

    def test_sweep_tool_compares_and_imports_its_verified_runs(self):
        page, panel = self.open('sweep')
        folder = Path(self.folder)/'campaign'
        panel.fields['directory'].setText(str(folder))
        panel.fields['axis_values'].setText('0, 4')
        panel.fields['bit_count'].setText('360')
        self.calculate()
        self.assertEqual(panel.run_choice.count(), 2)
        self.assertTrue(panel.campaign.complete)
        self.assertIn('2 de 2', panel.result.text.toPlainText())
        self.assertFalse(panel.resume_sweep.isEnabled())
        launcher = page.workspace.results.graph_launcher
        launcher.open_default()
        self.wait()
        self.app.processEvents()
        canvas = panel.canvas['Comparación de corridas'][0]
        self.assertEqual([axis.get_ylabel() for axis in canvas.figure.axes], ['BER', 'SER', 'EVM (%)'])
        self.assertEqual(canvas.figure.axes[-1].get_xlabel(), 'Eb/N₀ (dB)')
        canvas._signallab_window.hide()
        panel._open_sweep()
        self.wait()
        panel.import_run.click()
        self.wait()
        records = self.window.project.headers('calculation')
        self.assertTrue(any(row['title'] == 'Experimento de comunicaciones' for row in records))


if __name__ == '__main__':
    unittest.main()
