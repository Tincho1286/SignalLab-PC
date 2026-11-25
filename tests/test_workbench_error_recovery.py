"""Calculation delivery retains the last accepted result across recoverable failures."""
from threading import Event
from unittest.mock import patch

import numpy as np

from signallab_pc.model import Signal
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class CalculationDeliveryContracts(DesktopSessionFixture):
    def test_late_input_error_does_not_switch_tools_or_replace_the_accepted_result(self):
        window=self.window()
        route=ROUTES['basic','dft']
        another_route=ROUTES['basic','generate']
        window.open_tool(route)
        page=window.pages[route]
        page.dft_phase_reference.setCurrentIndex(page.dft_phase_reference.findData('sample_indices'))
        first=Signal([3,2],-1)
        page.first.set_source(first)
        window.calculate_active()
        self.wait_for_calculation(window)
        old=page.basic_result.result
        old_records=window.project.headers()
        self.assertIsNotNone(old)
        page.first.set_source(Signal([7,-3j,2],-5))
        started,release=Event(),Event()

        def rejected(*_args,**_kwargs):
            started.set()
            if not release.wait(10):
                raise TimeoutError('Timed out waiting for the alternate surface.')
            raise ValueError('El cálculo de prueba no pudo leer el registro.')

        with patch('signallab_pc.operations.dft',side_effect=rejected):
            window.calculate_active()
            try:
                self.assertTrue(started.wait(4))
                window.open_tool(another_route)
                concurrent=window.pages[another_route]
                concurrent.first.expression.setText('5*n')
                window.calculate_active()
                self.info.assert_called_once()
            finally:
                release.set()
            self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(window.current_operation,another_route)
        self.assertEqual(window.project.headers(),old_records)
        self.assertIs(page.basic_result.result,old)
        self.assertIn('no pudo leer',page.workspace.input_issue.message.text())
        window.open_tool(route)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIsNot(page.basic_result.result,old)
        self.assertTrue(page.workspace.input_issue.isHidden())
        value=page.basic_result.result
        k=np.arange(-1,2)
        expected=np.exp(-2j*np.pi*np.outer(k,[-5,-4,-3])/3)@np.array([7,-3j,2])
        np.testing.assert_allclose(value.values,expected,atol=1e-13)

    def test_incompatible_input_clocks_leave_no_records_and_recovery_links_sources(self):
        window=self.window()
        route=ROUTES['signal_product',0]
        window.open_tool(route)
        page=window.pages[route]
        panel=page.panel
        panel.first.set_source(Signal([2,3,5],-1,metadata={'sample_rate_hz':8}))
        panel.second.set_source(Signal([7,11],0,metadata={'sample_rate_hz':4}))
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(window.project.headers(),[])
        self.assertFalse(page.workspace.input_issue.isHidden())

        panel.second.set_source(Signal([7,11],0,metadata={'sample_rate_hz':8}))
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertTrue(page.workspace.input_issue.isHidden())
        self.assertEqual(panel.result.origin,-1)
        self.assertEqual(panel.result.metadata['sample_rate_hz'],8)
        np.testing.assert_array_equal(panel.result.values,[0,21,55])
        result_id=panel.output.result_ids[0]
        header=next(row for row in window.project.headers() if row['id']==result_id)
        self.assertCountEqual(header['parents'],[panel.first.reference_id,panel.second.reference_id])

    def test_cancelled_product_discards_the_draft_even_if_the_worker_finishes(self):
        from signallab_pc.windowing import multiply_signals

        window=self.window()
        route=ROUTES['signal_product',0]
        window.open_tool(route)
        panel=window.pages[route].panel
        panel.first.set_source(Signal([2,3],-1))
        panel.second.set_source(Signal([7,11],0))
        started,release=Event(),Event()

        def compute(first,second):
            started.set()
            if not release.wait(10):
                raise TimeoutError('Timed out waiting for cancellation.')
            return multiply_signals(first,second)

        with patch('signallab_pc.signal_combination_panel.multiply_signals',side_effect=compute):
            window.calculate_active()
            try:
                self.assertTrue(started.wait(4))
                window.cancel_button.click()
            finally:
                release.set()
            self.wait_for_calculation(window)
        self.assertIsNone(panel.result)
        self.assertEqual(window.project.headers(),[])
        self.assertIn('cancelado',window.statusBar().currentMessage().lower())

    def test_psd_validation_registers_only_the_recovered_input_and_power(self):
        window=self.window()
        route=ROUTES['fourier',7]
        window.open_tool(route)
        page=window.pages[route]
        panel=page.panel
        field=page.context.source
        field.set_source(Signal([2,-2,2,-2],metadata={'sample_rate_hz':8}))
        panel.estimator.setCurrentIndex(0)
        panel.window.setCurrentIndex(0)
        panel.segment.setText('5')
        window.calculate_active()
        self.assertFalse(window._workers)
        self.assertEqual(window.project.headers(),[])
        self.assertIsNone(field.reference_id)

        panel.segment.setText('4')
        panel.overlap.setText('0')
        window.calculate_active()
        self.wait_for_calculation(window)
        result = panel.result
        self.assertEqual(result.units,'Hz')
        self.assertAlmostEqual(float(result.values.real.sum()*result.step),4.)
        output_id=window.published_value_id(result)
        rows={row['id']:row for row in window.project.headers()}
        self.assertEqual(rows[output_id]['parents'],[field.reference_id])

    def test_restoring_inherited_resampling_clock_keeps_the_source_as_a_draft(self):
        window=self.window()
        route=ROUTES['rational_resampling',0]
        window.open_tool(route)
        panel=window.pages[route].panel
        source=Signal([1,-2,3],-1,metadata={'sample_rate_hz':8,'time_start_s':.125})
        panel.source.set_source(source)
        panel.override.setChecked(True)
        panel.rate.setText('12')
        panel.start.setText('-2')
        panel.read_clock()
        self.assertFalse(panel.override.isChecked())
        self.assertEqual(float(panel.rate.text()),8.)
        self.assertEqual(float(panel.start.text()),.125)
        self.assertEqual(window.project.headers(),[])

        panel.up.setText('1')
        panel.down.setText('1')
        window.calculate_active()
        self.wait_for_calculation(window)
        result=panel.result.result
        self.assertEqual(result.metadata['sample_rate_hz'],8.)
        self.assertEqual(result.metadata['time_start_s'],.125)
        np.testing.assert_array_equal(result.values,source.values)
        output_id=panel.result.result_ids[0]
        rows={row['id']:row for row in window.project.headers()}
        self.assertEqual(rows[output_id]['parents'],[panel.source.reference_id,panel.filter_actions.key])
        self.assertEqual(rows[panel.filter_actions.key]['parents'],[panel.source.reference_id])
        np.testing.assert_allclose(panel.filter_actions.system.response([0,.5,1]),1)
