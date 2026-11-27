"""Exercise expanded family selection on the existing identification route."""

import numpy as np

from signallab_pc.model import Signal
from signallab_pc.time_series_identification import fit_arma
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class TimeSeriesWorkbenchTests(DesktopSessionFixture):
    def test_integrated_fit_exports_model_and_forecast_from_existing_panel(self):
        window = self.window()
        route = ROUTES['random_model','fit']
        source = Signal([0,3,4,7,11,12,14,25],origin=4,metadata={'sample_rate_hz':4,'time_start_s':2})
        parent = window.publish(source, operation='Trayectoria')
        window.send_signal(source,parent,route)
        panel = window.pages[route].panel
        panel.family.setCurrentIndex(panel.family.findData('arima'))
        panel.order.setText('0')
        panel.ma_order.setText('0')
        panel.reserve.setText('1')
        panel.horizon.setText('4')
        window.calculate_active()
        self.wait_for_calculation(window)
        key = panel.view.result_ids[0]
        fit = window.project.get(key)
        expected = fit_arma(source,0,0,differences=1,validation=1)
        self.assertEqual({name:fit[name] for name in expected},expected)
        self.assertEqual(window.project.headers('calculation')[-1]['parents'],[parent])
        forecast = next(record for record in panel.result['signals'] if record.metadata.get('operation')=='arma_forecast')
        np.testing.assert_allclose(forecast.values, 25+np.arange(1,5)*(14/6), atol=2e-12)
        self.assertTrue(panel.actions.reuse.isEnabled())
        self.assertIn('niveles originales',panel.report.toPlainText())

    def test_ma_comparison_keeps_common_support_and_allows_selecting_another_row(self):
        window = self.window()
        route = ROUTES['random_model','fit']
        source = Signal([4,4.5,2,4,2,5,6,3,8,9,7,8,7,4,7,6,8,6,9,7])
        parent = window.publish(source, operation='Datos')
        window.send_signal(source,parent,route)
        panel=window.pages[route].panel
        panel.family.setCurrentIndex(panel.family.findData('ma'))
        panel.mode.setCurrentIndex(1)
        panel.minimum.setText('0')
        panel.maximum.setText('2')
        window.calculate_active()
        # This worker fits three candidates with native optimization under coverage.
        self.wait_for_calculation(window, timeout_ms=12_000)
        self.assertEqual({row['fitted_samples'] for row in panel.comparison['rows']},{18})
        panel.choose_order(1)
        self.wait_for_calculation(window)
        self.assertEqual(panel.result['fit']['q'],1)
        row=window.project.get(panel.view.result_ids[0])
        self.assertEqual(row['hold_back'],2)
