import math
import unittest

import numpy as np
from numpy.testing import assert_allclose

from signallab_pc.analog_design import bessel_prototype, design
from signallab_pc.amplitude_design import design as amplitude_design
from signallab_pc.communications_propagation import FreeSpaceLoss, LogDistanceLoss, PropagationSpec
from signallab_pc.rf_link import (
    RFStage, characterize_device, link_budget, noise_cascade, power_dbm, power_watts,
)


class RFLinkTests(unittest.TestCase):
    def test_absolute_power_reference_and_zero(self):
        self.assertAlmostEqual(power_dbm(1), 30)
        self.assertAlmostEqual(power_dbm(.001), 0)
        self.assertAlmostEqual(power_watts(-60), 1e-9)
        self.assertAlmostEqual(power_dbm(power_watts(47.23)), 47.23)
        self.assertEqual(power_dbm(0), -math.inf)
        self.assertEqual(power_watts(-math.inf), 0)
        for watts in (-1, math.nan, math.inf, False):
            with self.subTest(watts=watts), self.assertRaises(ValueError):
                power_dbm(watts)
        for dbm in (math.nan, math.inf, -5000, 5000):
            with self.subTest(dbm=dbm), self.assertRaises(ValueError):
                power_watts(dbm)

    def test_noise_temperature_and_friis_against_accumulated_output_power(self):
        temperatures = [290, 25, 50]
        losses = RFStage.passive('Cable', 3, 290)
        assert_allclose(losses.noise_figure_db, 3, rtol=1e-14)
        self.assertEqual(RFStage.passive('Ideal', 0, 123).noise_figure_db, 0)
        self.assertEqual(RFStage.passive('Frío', 6, 0).noise_figure_db, 0)
        rx = (losses, RFStage('LNA', 20, 2), RFStage('IF', 5, 4))
        b = 2e6
        k = 1.380649e-23
        cold_cable = RFStage.passive('Cable 145 K', 3, 145)
        assert_allclose(10**(cold_cable.noise_figure_db/10), 1 + (10**.3 - 1)/2)
        for temperature in temperatures:
            r = noise_cascade(rx, b, source_temperature_k=temperature, required_snr_db=9)
            output_w = k * b * temperature
            for stage in rx:
                output_w = 10**(stage.gain_db/10) * (output_w + k*b*290*(10**(stage.noise_figure_db/10)-1))
            self.assertAlmostEqual(r.output_noise_dbm, 10*np.log10(output_w*1000), places=12)
            self.assertAlmostEqual(r.gain_db, 22)
            self.assertAlmostEqual(r.sensitivity_dbm, r.input_noise_dbm + 9)
            self.assertAlmostEqual(r.input_density_dbm_per_hz, r.input_noise_dbm - 10*np.log10(b))
            self.assertAlmostEqual(r.noise_factor, 1 + r.equivalent_temperature_k/290)
        ideal = noise_cascade([], 1)
        self.assertEqual(ideal.equivalent_temperature_k, 0)
        self.assertEqual(ideal.noise_factor, 1)
        assert_allclose(ideal.input_noise_dbm, -173.975187194228)
        with self.assertRaises(ValueError):
            noise_cascade([], 0)
        with self.assertRaises(ValueError):
            noise_cascade([{'gain_db': 15}], 1)
        with self.assertRaises(ValueError):
            RFStage('', 10)
        with self.assertRaises(ValueError):
            RFStage('F', 10, -1)

    def test_link_dbi_and_propagation_ledger(self):
        frequency, distance = 2.4e9, 100
        path = PropagationSpec(FreeSpaceLoss(distance), gain_db=-1)
        answer = link_budget(10, path, 1e6, tx_antenna_dbi=7, rx_antenna_dbi=4, carrier_hz=frequency,
                             transmit_stages=[RFStage.passive('Cable TX', 2), RFStage.passive('Conector TX', .5)],
                             receive_stages=[RFStage.passive('Cable RX', 1), RFStage('LNA', 20, 2)],
                             required_snr_db=12)
        loss_db = 20*math.log10(4*math.pi*distance*frequency/299792458)
        self.assertAlmostEqual(answer.eirp_dbm, 14.5)
        self.assertAlmostEqual(answer.path_loss_db, loss_db)
        self.assertAlmostEqual(answer.received_at_antenna_dbm, 17.5-loss_db)
        self.assertAlmostEqual(answer.receiver_output_dbm, 36.5-loss_db)
        self.assertAlmostEqual(answer.margin_db, answer.snr_db - 12)
        self.assertEqual(answer.ledger[-1][0], 'LNA')
        self.assertEqual(answer.ledger[-1][2], answer.receiver_output_dbm)
        self.assertEqual(answer.carrier_hz, frequency)
        shadow = PropagationSpec(LogDistanceLoss(100, reference_loss_db=30), shadow_std_db=2, seed=4)
        s = link_budget(0, shadow, 100)
        self.assertEqual(s, link_budget(0, shadow, 100))
        self.assertAlmostEqual(s.received_at_antenna_dbm, -70 - s.shadow_loss_db)
        with self.assertRaises(ValueError):
            link_budget(0, path, 100, transmit_stages=['cable'], carrier_hz=frequency)

    def test_single_tone_at_p1db_and_two_tone_fourier_projection(self):
        with_known_ip = characterize_device(20, -20, iip3_dbm=1, tones=1)
        edge = characterize_device(20, with_known_ip.input_p1db_dbm, input_p1db_dbm=with_known_ip.input_p1db_dbm,
                                   tones=1)
        self.assertAlmostEqual(edge.iip3_dbm, 1)
        self.assertAlmostEqual(edge.compression_db, 1)
        self.assertAlmostEqual(edge.fundamental_per_tone_dbm, edge.output_p1db_dbm)
        self.assertIsNone(edge.im3_per_product_dbm)
        two = characterize_device(20, -20, iip3_dbm=1, output_noise_dbm=-100)
        self.assertAlmostEqual(two.sfdr_db, (2/3)*(21+100))
        self.assertAlmostEqual(two.im3_per_product_dbm, -42)
        theta = np.arange(1024)*(2*np.pi/1024)
        amp = math.sqrt(power_watts(-20))
        drive = amp*(np.cos(13*theta) + np.cos(19*theta))
        output = 10*(drive - (4/(3*power_watts(1)))*drive**3)
        for frequency, level in ((13, two.fundamental_per_tone_dbm), (7, two.im3_per_product_dbm),
                                 (25, two.im3_per_product_dbm), (39, two.third_harmonic_dbm)):
            measured = 2*np.mean(output*np.cos(frequency*theta))
            self.assertAlmostEqual(power_dbm(measured**2), level, places=11)
        invalid_sfdr = characterize_device(20, -30, iip3_dbm=1, output_noise_dbm=15)
        self.assertIsNone(invalid_sfdr.sfdr_db)
        self.assertIsNone(invalid_sfdr.sfdr_input_limit_dbm)
        for options in ({'iip3_dbm': -45}, {'tones': 3, 'iip3_dbm': 1}, {},
                        {'iip3_dbm': 1, 'input_p1db_dbm': -10}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                characterize_device(20, -20, **options)


class BesselDesignTests(unittest.TestCase):
    def test_second_order_delay_normalization_against_reverse_bessel_polynomial(self):
        system, = bessel_prototype(2, 4, normalization='delay')['systems']
        grid = np.array([0, 1, 4, 10])
        x = 1j*grid/4
        assert_allclose(system.response(grid), 3/(x**2+3*x+3), atol=1e-15)
        assert_allclose(system.group_delay(grid), (np.real((2*x+3)/(x**2+3*x+3)))/4, atol=1e-15)
        self.assertAlmostEqual(system.group_delay([0])[0], .25)
        self.assertEqual(system.roc['mode'], 'right')
        for mode in ('phase', 'mag'):
            result = bessel_prototype(2, 4, normalization=mode)
            self.assertEqual(result['design_metadata']['normalization'], mode)
            s, = result['systems']
            value, = s.response([4])
            if mode == 'phase':
                self.assertAlmostEqual(np.angle(value), -np.pi/2)
            else:
                self.assertAlmostEqual(abs(value), 1/np.sqrt(2))

    def test_fixed_frequency_transforms_match_analytic_substitution(self):
        frequency = np.array([.5, 1, 4, 7, 16])
        point = 1j * frequency
        for kind, edges, expected in (
            ('highpass', 2, point/(point+2)),
            ('bandpass', [2, 8], (6*point)/(point**2+6*point+16)),
            ('bandstop', [2, 8], (point**2+16)/(point**2+6*point+16)),
        ):
            result = bessel_prototype(1, edges, kind=kind, normalization='delay')
            assert_allclose(result['systems'][0].response(frequency), expected, atol=1e-15)
            if kind in ('bandpass', 'bandstop'):
                self.assertIn('Centro geométrico: 4 rad/s', result['report'])

    def test_band_design_and_comparison_preserve_original_entries(self):
        for wp, ws in (([1], [10]), ([10], [1]), ([4, 8], [.9, 40]), ([1, 16], [3.9, 4.1])):
            with self.subTest(wp=wp, ws=ws):
                result = design(wp, ws, .3, .2, 'bessel')
                filt, = result['systems']
                self.assertGreaterEqual(abs(filt.response(wp)).min(), .7)
                self.assertLessEqual(abs(filt.response(ws)).max(), .2)
        pass_edge = np.sqrt(1/.7**2 - 1)
        stop_edge = np.sqrt(1/.2**2 - 1)
        selected = np.sqrt(pass_edge * stop_edge / 10)
        single = design([1], [10], .3, .2, 'bessel')['systems'][0]
        assert_allclose(single.response([1, 10]), 1/(1+1j*selected*np.array([1,10])))
        legacy = design([1], [10], .3, .2, 'compare')
        expanded = design([1], [10], .3, .2, 'compare_rf')
        self.assertEqual(len(legacy['systems']), 4)
        self.assertEqual(len(expanded['systems']), 5)
        for first, second in zip(legacy['systems'], expanded['systems']):
            assert_allclose(first.response([0, 1, 10]), second.response([0, 1, 10]))
        result = amplitude_design([1], [10], .3, .2, 'compare_rf', analog=True)
        self.assertTrue(result['specification_met'])
        self.assertIn('reescalado', result['report'])
        with self.assertRaisesRegex(ValueError, 'hasta orden'):
            design([1], [1.01], .05, .001, 'bessel')
        issue = design([1], [1.4], .05, .01, 'compare_rf')
        self.assertIn('Bessel no cumple', issue['report'])
        self.assertEqual(len(issue['systems']), 4)

    def test_fixed_invalid_arguments(self):
        for order, frequencies, options in (
            (0, 1, {}), (26, 1, {}), (2, 0, {}), (2, [2,1], {'kind':'bandpass'}),
            (2, 4+1j, {}), (2, 1, {'kind':'bandpass'}), (1, [2,3], {}),
            (2, 1, {'normalization':'time'}), (2, 1, {'kind':'notch'}),
        ):
            with self.subTest(order=order, frequencies=frequencies, options=options), self.assertRaises(ValueError):
                bessel_prototype(order, frequencies, **options)

    def test_analog_edges_and_frequencies_respect_numeric_envelope(self):
        cases=(
            ([0],[1],.1,.01,'bessel','positivos'),
            ([1],[1],.1,.01,'bessel','ordenadas'),
            ([1,3],[2,4],.1,.01,'bessel','ordenadas'),
            ([1,3],[2],.1,.01,'bessel','positivos'),
            ([1],[3],1,.01,'bessel','δp'),
            ([1],[3],.1,.99,'bessel','δs'),
            ([1],[3],.1,.01,'no_filter','Familia'),
            ([1e-322],[1e308],.1,.01,'bessel','rango numérico'),
            ([1],[3],1e-16,.01,'bessel','resolución'),
        )
        with np.errstate(over='ignore'):
            for wp,ws,dp,ds,method,reason in cases:
                with self.subTest(wp=wp,ws=ws,method=method),self.assertRaisesRegex(ValueError,reason):
                    design(wp,ws,dp,ds,method)
            with self.assertRaisesRegex(ValueError,'rango numérico'):
                bessel_prototype(6,1e308)
        with self.assertRaisesRegex(ValueError,'escalado'):
            bessel_prototype(8,1e100)

    def test_representation_guard_distinguishes_a_true_pole_from_lost_precision(self):
        from signallab_pc.analog_design import _checked_transfer
        with np.errstate(all='ignore'):
            with self.assertRaisesRegex(ValueError,'Respuesta no finita'):
                _checked_transfer(([],[1j,-1j],1),'Oscilador sin amortiguación',[1])
            poles=np.asarray([-1e-4+1j]*8+[-1e-4-1j]*8)
            gain=(2e-4)**8
            with self.assertRaisesRegex(ValueError,'pierden precisión'):
                _checked_transfer(([],poles,gain),'Resonadores casi coincidentes',[.99,1,1.01])


if __name__ == '__main__':
    unittest.main()
