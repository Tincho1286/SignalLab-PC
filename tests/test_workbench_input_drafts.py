"""Verify editable inputs, source switching and safe copies between tools."""
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QFileDialog, QPushButton

from signallab_pc import session
from signallab_pc.model import Signal
from signallab_pc.session_desktop import capture
from signallab_pc.storage import save_csv
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class WorkbenchInputContracts(DesktopSessionFixture):
    def test_csv_and_historical_result_remain_independent_after_reopen(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        page = window.pages[route]
        field = page.first
        field.entry_modes.select(1)
        field.samples.setText('pi, 2-3*i')
        draft = Signal([5, 9], -2, name='Archivo con eje')
        csv = self.path/'data.csv'
        save_csv(draft, csv)
        field.entry_modes.select(2)
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(csv), 'CSV')):
            field.open_file()
        self.assertEqual(field.loaded.origin, -2)
        np.testing.assert_array_equal(field.read(register=False).values, [5,9])
        fields = [window.project.add(Signal([i,i+1], -4, name=f'Registro {i}')) for i in range(25)]
        incompatible = window.project.add(Signal([729,730], 1, .125, 's', domain='continuous'))
        field.entry_modes.select(3)
        self.assertEqual(field.recent.count(), 21)
        self.assertEqual(field.recent.findData(incompatible), -1)
        with patch.object(window, 'choose_record', return_value=fields[0]):
            field.choose_project()
        self.assertEqual(field.recent.currentData(), fields[0])
        self.assertEqual(field.loaded_reference_id, fields[0])
        with patch('signallab_pc.signal_inspector.inspect_signal') as inspect:
            field.inspect_loaded()
        self.assertEqual(inspect.call_args.args[-1], 'Resultados de la sesión')
        path = self.path/'independent-inputs.json'
        session.save(path, window.project, capture(window))
        other = self.window()
        self.assertTrue(other.sessions.open_path(path))
        field = other.pages[route].first
        self.assertEqual(field.loaded_reference_id, fields[0])
        np.testing.assert_array_equal(field.read(register=False).values, [0,1])
        field.entry_modes.select(2)
        self.assertEqual(field.loaded.origin, -2)
        self.assertIsNone(field.loaded_reference_id)
        np.testing.assert_array_equal(field.read(register=False).values, [5,9])
        field.clear_source()
        with self.assertRaisesRegex(ValueError,'archivo'):
            field.read(register=False)
        field.entry_modes.select(3)
        self.assertEqual(field.loaded_reference_id, fields[0])
        field.entry_modes.select(1)
        self.assertEqual(field.samples.text(), 'pi, 2-3*i')
        np.testing.assert_allclose(field.read(register=False).values, [np.pi,2-3j])

    def test_first_filter_variant_copies_bands_then_preserves_its_own_existing_draft(self):
        window = self.window()
        window.show()
        fir = ('course_tools','fir')
        iir = ('course_tools','iir')
        analog = ('course_tools','analog')
        window.open_tool(ROUTES[fir])
        panel = window.pages[ROUTES[fir]].panel
        panel.band_edges.kind.setCurrentIndex(panel.band_edges.kind.findData('bandpass'))
        example = ('pi/6','pi/3','pi/2','2*pi/3')
        for field, text in zip(panel.band_edges.edits, example):
            field.setText(text)
        panel.fields['dp'].setText('0.08')
        window.variant_strip.select(iir)
        destination = window.pages[ROUTES[iir]].panel
        self.assertEqual([f.text() for f in destination.band_edges.edits], list(example))
        self.assertEqual(destination.fields['dp'].text(), '0.08')
        destination.fields['dp'].setText('0.13')
        window.variant_strip.select(fir)
        self.assertEqual(panel.fields['dp'].text(), '0.08')
        self.assertTrue(window.variant_strip.copy_button.isVisible())
        window.variant_strip.copy_button.click()
        self.assertEqual(panel.fields['dp'].text(), '0.13')
        self.assertTrue(window.variant_strip.copy_button.isHidden())
        window.variant_strip.select(analog)
        continuous = window.pages[ROUTES[analog]].panel
        self.assertTrue(continuous.band_edges.analog)
        self.assertNotIn('pi', continuous.band_edges.edits[0].text())
        self.assertIn('rad/s', window.statusBar().currentMessage())
        self.assertEqual(window.project.headers(), [])

    def test_frequency_mixed_spectrum_is_rejected_before_it_can_replace_input(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        pane = window.pages[route]
        field = pane.first
        sample = Signal([1.,-1.], -1, name='Secuencia para conservar')
        key = window.project.add(sample)
        field.set_source(sample,key)
        incompatible = Signal([3,4], 0, .125, 'rad/s', domain='frequency')
        with self.assertRaises(ValueError):
            field.set_source(incompatible)
        self.assertEqual(field.loaded_reference_id, key)
        np.testing.assert_array_equal(field.read().values, sample.values)
        self.assertEqual(len(window.project.headers()), 1)
        field.entry_modes.select(2)
        bad = self.path/'not-a-signal.json'
        bad.write_text('{"format":"unrelated"}',encoding='utf-8')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(bad), 'JSON')):
            field.open_file()
        self.warning.assert_called_once()
        self.assertIsNone(field.loaded)
        field.entry_modes.select(3)
        self.assertEqual(field.loaded_reference_id, key)
        remove = next(b for b in field.external_actions.findChildren(QPushButton) if b.text()=='Quitar')
        remove.click()
        with self.assertRaisesRegex(ValueError,'Resultados'):
            field.read(register=False)
        self.assertEqual(window.project.get(key).origin, -1)
