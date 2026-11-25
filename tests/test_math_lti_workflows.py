"""Independent time, frequency and tolerance oracles for LTI study workflows."""
from copy import deepcopy
import unittest

import numpy as np

from signallab_pc import amplitude_design, control
from signallab_pc.continuous_expression import sample_continuous
from signallab_pc.distributions import dirac_terms
from signallab_pc.filters import Transfer
from signallab_pc.frequency_analysis import analyze_frequency, frequency_grid, frequency_summary
from signallab_pc.model import Signal


class ResponseContracts(unittest.TestCase):
    def test_step_and_impulse_report_the_direct_term_exactly(self):
        for num, den, direct, transient in [([2], [1], 2, 0),
                                             ([2, 7], [1, 3], 2, 1),
                                             ([0], [1, 3], 0, 0)]:
            with self.subTest(num=num, den=den):
                system = Transfer(num, den, 'analog')
                step = control.analog_response(system, 1, 9, 'step')
                impulse = control.analog_response(system, 1, 9, 'impulse')
                np.testing.assert_allclose(step.values, direct+transient*(1-np.exp(-3*step.axis))/3, atol=1e-13)
                np.testing.assert_allclose(impulse.values, transient*np.exp(-3*impulse.axis), atol=1e-13)
                self.assertEqual(impulse.metadata.get('dirac_at_zero'), [direct, 0.] if direct else None)
                self.assertNotIn('dirac_at_zero', step.metadata)
                self.assertEqual(impulse.step, .125)

    def test_temporal_tools_reject_incompatible_domain_roc_and_excitation(self):
        analog = Transfer([1], [1, 2], 'analog')
        for system, duration, count, kind, reason in [
            (Transfer([1], [1]), 1, 3, 'step', 'H\\(s\\)'),
            (analog, -1, 3, 'step', 'Duración'),
            (analog, 1, 1, 'step', 'dos puntos'),
            (analog, 1, 3, 'ramp', 'step o impulse'),
            (Transfer([1, 0], [1], 'analog'), 1, 3, 'impulse', 'impropia'),
            (Transfer([1], [1, 2], 'analog', roc={'mode': 'left'}), 1, 3, 'step', 'causal'),
        ]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                control.analog_response(system, duration, count, kind)

    def test_held_and_linear_input_follow_distinct_closed_forms_from_nonzero_origin(self):
        system = Transfer([1], [1, 0], 'analog')
        source = Signal([0, 1, 2, 3], -2, .25, 's', 'Experimento', 'continuous')
        ramp = control.forced_response(system, source)
        held = control.forced_response(system, source, 'hold')
        np.testing.assert_allclose(ramp.values, [.0, .125, .5, 1.125])
        np.testing.assert_allclose(held.values, [0, 0, .25, .75])
        self.assertEqual(ramp.metadata['initial_rest_at'], -2)
        self.assertEqual(held.metadata['input_interpolation'], 'hold')
        np.testing.assert_array_equal(held.axis, source.axis)
        for bad_system, bad_source, interpolation, reason in [
            (Transfer([1], [1]), source, 'hold', 'dominio'),
            (system, source, 'previous', 'interpolación'),
            (system, source.copy_with(values=[1]), 'linear', 'dos puntos'),
            (Transfer([1, 0], [1], 'analog'), source, 'linear', 'propia'),
        ]:
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                control.forced_response(bad_system, bad_source, interpolation)

    def test_impulsive_input_keeps_weight_for_feedthrough_and_tail_for_dynamics(self):
        source = sample_continuous('1+3*DiracDelta(t-0.5)', 0, .25, 9)
        for b, a, direct, transient in [([2], [1], 2, 0), ([2, 5], [1, 2], 2, 1)]:
            with self.subTest(b=b, a=a):
                result = control.forced_response(Transfer(b, a, 'analog'), source)
                t = source.axis
                expected = direct+transient*((1-np.exp(-2*t))/2+3*(t>=.5)*np.exp(-2*(t-.5)))
                np.testing.assert_allclose(result.values, expected, atol=2e-13)
                self.assertEqual(dirac_terms(result), [(.5, 3*direct)])
                self.assertEqual(result.metadata['input_dirac_terms'], [[.5, [3., 0.]]])

    def test_root_locus_accounts_for_a_pole_that_goes_to_infinity(self):
        system = Transfer([-1, 1], [1, 3, 2], 'analog')
        gains, poles, domain = control.root_locus(system, 0, 2, 5)
        self.assertEqual(domain, 'analog')
        self.assertTrue(np.isfinite(poles).all())
        for gain, row in zip(gains, poles):
            np.testing.assert_allclose(row**2+(3-gain)*row+(2+gain), 0, atol=1e-12)
        gains, poles, _ = control.root_locus(Transfer([-1, 1], [1, 3], 'analog'), 0, 2, 3)
        np.testing.assert_allclose(gains, [0, 1, 2])
        np.testing.assert_allclose(poles[[0, 2], 0], [-3, 5])
        self.assertTrue(np.isnan(poles[1, 0]))
        with self.assertRaisesRegex(ValueError, 'estática'):
            control.root_locus(Transfer([1], [1]), 0, 1, 2)
        with self.assertRaisesRegex(ValueError, 'ganancias'):
            control.root_locus(system, 3, 1, 3)

    def test_discrete_root_locus_includes_the_degree_from_an_advance(self):
        gains, poles, domain = control.root_locus(Transfer([1], [1], advance=2), 0, 4, 5)
        self.assertEqual(domain, 'digital')
        self.assertTrue(np.isnan(poles[0]).all())
        for gain, row in zip(gains[1:], poles[1:]):
            np.testing.assert_allclose(1+gain*row**2, 0, atol=1e-13)

    def test_feedback_keeps_the_open_loop_advance_and_its_clock(self):
        system = Transfer([1], [1, -.25], advance=2, sample_period_s=.01)
        omega = np.array([0., .3, 1.3, np.pi])
        z = np.exp(1j*omega)
        open_loop = z**2/(1-.25/z)
        for gain in [0, .4, -.2+.1j]:
            for positive in (True, False):
                with self.subTest(gain=gain, positive=positive):
                    closed = control.feedback(system, gain, positive)
                    expected = gain*open_loop/(1+(-1 if positive else 1)*gain*open_loop)
                    np.testing.assert_allclose(closed.response(omega), expected, atol=1e-13)
                    self.assertEqual(closed.sample_period_s, .01)
        with self.assertRaisesRegex(ValueError, 'K debe ser finito'):
            control.feedback(system, np.nan)
        with self.assertRaisesRegex(ValueError, 'denominador cero'):
            control.feedback(Transfer([1], [1]), 1, positive=True)

    def test_connections_intersect_regions_and_reject_incompatible_clocks(self):
        right = Transfer([1], [1, -.25], sample_period_s=.02, roc={'mode': 'right'})
        left = Transfer([1], [1, -2], sample_period_s=.02, roc={'mode': 'left'})
        w = np.linspace(0, np.pi, 9)
        exp = np.exp(-1j*w)
        cascade = control.interconnect(right, left)
        self.assertEqual(cascade.roc, {'mode': 'radius', 'radius': 1.125})
        np.testing.assert_allclose(cascade.response(w), 1/((1-.25*exp)*(1-2*exp)), atol=1e-13)
        gain = Transfer([2], [1])
        self.assertEqual(control.interconnect(right, gain).roc, {'mode': 'right'})
        self.assertEqual(control.interconnect(gain, left).roc, {'mode': 'left'})
        bad = Transfer([1], [1, -.125], roc={'mode': 'left'})
        with self.assertRaisesRegex(ValueError, 'no se intersectan'):
            control.interconnect(right, bad, 'parallel')
        with self.assertRaisesRegex(ValueError, 'período'):
            control.interconnect(right, Transfer([1], [1], sample_period_s=.01))
        with self.assertRaisesRegex(ValueError, 'dominio'):
            control.interconnect(right, Transfer([1], [1], 'analog'))
        with self.assertRaisesRegex(ValueError, 'Conexión desconocida'):
            control.interconnect(right, left, 'subtraction')

    def test_continuous_crossover_margins_match_the_cubic_closed_forms(self):
        system = Transfer([4], [1, 3, 3, 1], 'analog')
        omega = frequency_grid(.03, 100, 161, logarithmic=True)
        data = analyze_frequency(system, omega, logarithmic=True, margins=True)
        np.testing.assert_allclose(data.response, 4/(1+1j*omega)**3, atol=2e-13)
        np.testing.assert_allclose(data.delay, 3/(1+omega**2), atol=2e-13)
        gain_cross, = data.margins['gain_crossings']
        phase_cross, = data.margins['phase_crossings']
        power_cross = np.sqrt(4**(2/3)-1)
        self.assertAlmostEqual(gain_cross['frequency'], power_cross, places=11)
        self.assertAlmostEqual(gain_cross['phase_margin_rad'], np.pi-3*np.arctan(power_cross), places=11)
        self.assertAlmostEqual(phase_cross['frequency'], np.sqrt(3), places=11)
        self.assertAlmostEqual(phase_cross['gain_margin'], 2, places=11)
        self.assertAlmostEqual(phase_cross['gain_margin_db'], 20*np.log10(2), places=11)
        report = frequency_summary({'transfer':'4/(s+1)^3','factored':'4/(s+1)^3'}, data)
        self.assertIn('Cruces de fase', report.plain_text())

    def test_disabled_crossover_and_nonisolated_gain_do_not_invent_margins(self):
        w = np.linspace(0, np.pi, 13)
        data = analyze_frequency(Transfer([1],[1]), w, margins=True)
        self.assertTrue(data.margins['nonisolated_gain'])
        self.assertEqual(data.margins['gain_crossings'], [])
        for system, omega, reason in [
            (Transfer([1+1j],[1]), w, 'coeficientes reales'),
            (Transfer([1],[1],advance=1), w, 'avance temporal'),
            (Transfer([1],[1]), np.array([-2,-1]), 'dos frecuencias'),
        ]:
            with self.subTest(reason=reason):
                data = analyze_frequency(system, omega, margins=True)
                self.assertFalse(data.margins['available'])
                self.assertIn(reason, data.margins['reason'])
                self.assertEqual(data.margins['phase_crossings'], [])
                self.assertTrue(np.isfinite(data.response).all())

    def test_section_cascade_and_closed_loop_follow_the_product_of_biquads(self):
        first = Transfer.from_sos([[1,0,0,1,-.5,0]], sample_period_s=.125)
        second = Transfer.from_sos([[.5,0,.25,1,0,.125]], sample_period_s=.125)
        omega = np.linspace(0, np.pi, 11)
        q = np.exp(-1j*omega)
        one = 1/(1-.5*q)
        two = (.5+.25*q**2)/(1+.125*q**2)
        cascade = control.interconnect(first,second)
        self.assertEqual(cascade.sos.shape, (2,6))
        np.testing.assert_allclose(cascade.response(omega), one*two, atol=2e-13)
        negative = control.interconnect(first,second,'negative_feedback')
        np.testing.assert_allclose(negative.response(omega), one/(1+one*two), atol=2e-13)
        closed = control.feedback(first, .25+.125j)
        gain = .25+.125j
        np.testing.assert_allclose(closed.response(omega), gain*one/(1+gain*one), atol=2e-13)
        self.assertEqual(closed.sample_period_s, first.sample_period_s)


class BandToleranceContracts(unittest.TestCase):
    def test_bandstop_accepts_distinct_gains_and_reports_actual_extrema(self):
        wp = np.pi*np.array([.2, .78])
        ws = np.pi*np.array([.34, .61])
        result = amplitude_design.design(wp, ws, .04, .05, 'kaiser', window='blackman',
                                         amplitudes=(1, 2), units='relative', fixed_length=51)
        system, = result['systems']
        ideal, window, actual = result['signals']
        np.testing.assert_allclose(actual.values, ideal.values*window.values, atol=2e-15)
        np.testing.assert_allclose(system.b, system.b[::-1], atol=1e-16)
        w = np.r_[np.linspace(0, wp[0], 512), np.linspace(ws[0], ws[1], 512), np.linspace(wp[1], np.pi, 512)]
        direct = abs(np.exp(-1j*np.outer(w, np.arange(51)))@system.b)
        self.assertLessEqual(direct[:512].max(), 1.04)
        self.assertGreaterEqual(direct[:512].min(), .96)
        self.assertLessEqual(direct[512:1024].max(), .1)
        self.assertLessEqual(direct[1024:].max(), 2.08)
        self.assertGreaterEqual(direct[1024:].min(), 1.92)
        self.assertTrue(result['specification_met'])
        self.assertEqual(result['fir_metadata']['type'], 'I')
        for method, length, reason in [('kaiser', 50, 'longitud impar'), ('ellip', None, 'sola ganancia')]:
            with self.subTest(method=method), self.assertRaisesRegex(ValueError, reason):
                amplitude_design.design(wp, ws, .04, .05, method, amplitudes=(1, 2),
                                        units='relative', fixed_length=length)

    def test_decibel_limits_and_analog_highpass_use_amplitude_ratios(self):
        a, low, high, stop = amplitude_design.limits('highpass', (2,), 1, 30, 'db')
        np.testing.assert_array_equal(a, [2])
        self.assertAlmostEqual(20*np.log10(low[0]/2), -1)
        self.assertAlmostEqual(20*np.log10(high[0]/2), 1)
        self.assertAlmostEqual(20*np.log10(stop/2), -30)
        result = amplitude_design.design([10], [3], 1, 30, 'ellip', analog=True,
                                         amplitudes=(2,), units='db')
        system, = result['systems']
        self.assertEqual(result['specifications']['kind'], 'highpass')
        self.assertIn('ω ≤ ∞ rad/s', result['report'])
        for omega, bound in [(2., stop), (20., high[0])]:
            gain = abs(np.polyval(system.b, 1j*omega)/np.polyval(system.a, 1j*omega))
            self.assertLessEqual(gain, bound+1e-12)
            if omega == 20:
                self.assertGreaterEqual(gain, low[0]-1e-12)

    def test_tolerances_reject_impossible_or_undefined_masks(self):
        for args, reason in [
            (('bandstop', (1,), .1, .1, 'absolute'), 'amplitud positiva'),
            (('lowpass', (np.inf,), .1, .1, 'absolute'), 'amplitud positiva'),
            (('lowpass', (1,), 0, .1, 'absolute'), 'tolerancias deben'),
            (('lowpass', (1,), .1, .1, 'unknown'), 'Unidad'),
            (('lowpass', (1,), .1, .95, 'absolute'), 'rechazo debe'),
        ]:
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, reason):
                amplitude_design.limits(*args)


class TransferRecordContracts(unittest.TestCase):
    def test_all_transfer_document_schemas_reopen_without_altering_plane_or_clock(self):
        cases = [
            (1, Transfer([1], [1, 2], 'analog'), lambda w: 1/(2+1j*w)),
            (2, Transfer([2], [1], advance=2), lambda w: 2*np.exp(2j*w)),
            (3, Transfer([1, .5], [1], sample_period_s=.125), lambda w: 1+.5*np.exp(-1j*w)),
            (4, Transfer([1], [1, -2], roc={'mode':'radius', 'radius':1}),
             lambda w: 1/(1-2*np.exp(-1j*w))),
            (5, Transfer([1], [1, 2], 'analog', roc={'mode':'line', 'sigma':0}),
             lambda w: 1/(2+1j*w)),
        ]
        omega = np.array([-.5, 0, .8, np.pi])
        for version, original, oracle in cases:
            with self.subTest(version=version):
                document = original.to_document()
                self.assertEqual(document['version'], version)
                recovered = Transfer.from_document(document)
                self.assertEqual(recovered.to_document(), document)
                np.testing.assert_allclose(recovered.response(omega), oracle(omega), atol=1e-13)

    def test_corrupt_transfer_records_fail_before_a_definition_can_be_reused(self):
        system = Transfer.from_sos([[1,0,0,1,-.5,0]], sample_period_s=.125)
        intact = system.to_document()
        bad_cases = [
            ({'version': True}, 'Versión'),
            ({'format': 'signal'}, 'Archivo|archivo'),
            ({'advance': False}, 'avance'),
            ({'domain': 'spectral'}, 'dominio'),
            ({'name': []}, 'nombre'),
            ({'a': [[1,0], [float('inf'),0]]}, 'finitos'),
            ({'b': [[True,0]]}, 'par numérico'),
            ({'b': []}, 'coeficientes'),
            ({'sample_period_s': None}, 'registrar sample_period_s'),
            ({'sample_period_s': -1}, 'positivo'),
            ({'roc': {'mode':'right'}}, 'requiere formato 4'),
            ({'sos': []}, 'seis números'),
            ({'sos': [[1,0,0,0,0,0]]}, 'a0 distinto'),
            ({'sos': [[1,0,0,1,.25,0]]}, 'no coinciden'),
        ]
        for change, reason in bad_cases:
            document = {**deepcopy(intact), **change}
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, reason):
                Transfer.from_document(document)
        recovered = Transfer.from_document(intact)
        np.testing.assert_allclose(recovered.response([0,np.pi]), [2,2/3], atol=1e-14)
        self.assertEqual(system.to_document(), intact)

    def test_advanced_sos_cancels_only_exact_delays_before_export(self):
        sos = [[0,1,0,1,-.5,0], [0,0,1,1,0,.125]]
        system = Transfer([1], [1], sos=sos, advance=2, sample_period_s=.01)
        self.assertEqual(system.advance, 0)
        np.testing.assert_array_equal(system.sos[:,:3], [[1,0,0], [0,1,0]])
        recovered = Transfer.from_document(system.to_document())
        omega = np.array([0,.5,1.5,np.pi])
        q = np.exp(-1j*omega)
        np.testing.assert_allclose(recovered.response(omega), q/((1-.5*q)*(1+.125*q**2)), atol=1e-13)
        z, p = recovered.poles_zeros()
        self.assertIn(0j,z)
        self.assertIn(.5+0j,p)
