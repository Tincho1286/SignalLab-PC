import json
import math
from pathlib import Path
import sys
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_data import SymbolClock, iq_signal
from signallab_pc.communications_pulses import (
    PulseSpec, _raised_cosine_samples, apply_pulse, design_pulse, matched_pulse_isi, upsample_symbols,
)
from signallab_pc.dsp_application import store_signal
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


REFERENCE = json.loads((Path(__file__).resolve().parents[1] / 'docs' / 'engineering' /
                        'phase_03' / 'evidence' / 'analytical-reference-v1.json').read_text(encoding='utf-8'))


class CommunicationsPulseTests(unittest.TestCase):
    def test_pulse_limits_and_neighbors_match_independent_spectral_quadrature(self):
        with np.errstate(divide='raise', invalid='raise', over='raise'):
            for reference in REFERENCE['pulses']:
                kind, beta = reference['kind'], reference['rolloff']
                with self.subTest(kind=kind, beta=beta):
                    times, expected = np.asarray(reference['samples']).T
                    root = kind == 'rrc'
                    np.testing.assert_allclose(_raised_cosine_samples(times, beta, root=root),
                                               expected, atol=2e-11, rtol=0)
                    np.testing.assert_allclose(_raised_cosine_samples(-times, beta, root=root),
                                               expected, atol=2e-11, rtol=0)
        # The vanishing sidelobes of the zero-rolloff Nyquist pulse are exact.
        np.testing.assert_array_equal(_raised_cosine_samples([0, 1, -2, 3], 0, root=True), [1, 0, 0, 0])

    def test_symmetry_energy_peak_and_fractional_group_delay(self):
        for family, sps, span in (('rectangular', 4, 1), ('rc', 5, 3), ('rrc', 8, 8)):
            with self.subTest(family=family, sps=sps, span=span):
                pulse = design_pulse(PulseSpec(family, sps, span))
                count = sps*span + (family != 'rectangular')
                self.assertEqual(pulse.taps.size, count)
                self.assertEqual(pulse.group_delay_samples, (count - 1) / 2)
                np.testing.assert_array_equal(pulse.taps, pulse.taps[::-1])
                with self.assertRaises(ValueError):
                    pulse.taps.setflags(write=True)
                self.assertAlmostEqual(sum(v*v for v in pulse.taps), 1, places=14)
                self.assertAlmostEqual(pulse.energy, 1, places=14)
                peak = design_pulse(PulseSpec(family, sps, span, normalization='unit_peak'))
                self.assertAlmostEqual(peak.center_amplitude, 1, places=15)
                if count % 2:
                    self.assertAlmostEqual(peak.taps[count//2], 1, places=14)
        pulse = design_pulse(PulseSpec('rectangular', 4, 1, normalization='unit_peak'))
        np.testing.assert_array_equal(pulse.taps, np.ones(4))
        self.assertEqual(pulse.energy, 4)

    def test_fir_frequency_response_matches_direct_dtft(self):
        for sps in (3, 4):
            pulse = design_pulse(PulseSpec('rrc', sps, 7, 0.2))
            model = pulse.transfer(12_000)
            self.assertEqual(model.sample_period_s, 1/12_000)
            omega = np.linspace(-math.pi, math.pi, 31)
            direct = [sum(complex(math.cos(n*w), -math.sin(n*w))*h for n, h in enumerate(pulse.taps))
                      for w in omega]
            np.testing.assert_allclose(model.response(omega), direct, atol=4e-14)
            # After removing its known delay, a symmetric FIR has a real response.
            np.testing.assert_allclose((model.response(omega)*np.exp(1j*omega*pulse.group_delay_samples)).imag,
                                       0, atol=4e-14)

    def test_upsampling_and_full_matched_convolution_preserve_clocks_and_tails(self):
        clock = SymbolClock(1000, time_start_s=-0.125, center_frequency_hz=25_000)
        source = iq_signal([1+1j, 0, -1j], clock, origin=-3, amplitude_units='V')
        for sps in (1, 3, 4):
            with self.subTest(sps=sps):
                pulse = design_pulse(PulseSpec('rrc', sps, 3, 0.25))
                up = upsample_symbols(source, sps)
                expected = np.zeros(2*sps+1, dtype=np.complex128)
                expected[::sps] = source.values
                np.testing.assert_array_equal(up.values, expected)
                tx = apply_pulse(up, pulse)
                rx = apply_pulse(tx, pulse, matched=True)
                tx_expected = np.convolve(expected, pulse.taps)
                rx_expected = np.convolve(tx_expected, pulse.taps[::-1])
                np.testing.assert_allclose(tx.values, tx_expected, atol=1e-14)
                np.testing.assert_allclose(rx.values, rx_expected, atol=1e-14)
                self.assertEqual(rx.values.size, expected.size + 2*(pulse.taps.size-1))
                self.assertFalse(tx.metadata['communications_pulse']['matched'])
                self.assertTrue(rx.metadata['communications_pulse']['matched'])
                self.assertEqual(tx.metadata['communications_pulse']['group_delay_samples'],
                                 (pulse.taps.size-1)/2)
                for record in (up, tx, rx):
                    self.assertEqual(record.origin, -3*sps)
                    self.assertEqual(record.metadata['time_start_s'], -0.125)
                    self.assertEqual(record.metadata['sample_rate_hz'], 1000*sps)
                    self.assertEqual(record.metadata['symbol_rate_hz'], 1000)
                    self.assertEqual(record.metadata['amplitude_units'], 'V')
                    self.assertEqual(record.metadata['center_frequency_hz'], 25_000)
        unknown = upsample_symbols(Signal([1, -1]), 3)
        self.assertNotIn('sample_rate_hz', unknown.metadata)
        self.assertNotIn('sample_rate_hz', apply_pulse(unknown, pulse=design_pulse(PulseSpec('rc', 3))).metadata)

    def test_isi_reports_peak_and_rms_relative_to_matched_main_tap(self):
        for spec in (PulseSpec('rectangular', 8, 1), PulseSpec('rrc', 8, 6, 0.35),
                     PulseSpec('rrc', 5, 3, 0.25, 'unit_peak')):
            pulse = design_pulse(spec)
            measured = matched_pulse_isi(pulse)
            taps = pulse.taps.tolist()
            main = math.fsum(x*x for x in taps)
            reference = []
            for lag in measured.lags_symbols:
                shift = abs(int(lag))*spec.samples_per_symbol
                reference.append(math.fsum(x*y for x,y in zip(taps[shift:], taps))/main)
            side = [value for lag, value in zip(measured.lags_symbols, reference, strict=True) if lag != 0]
            np.testing.assert_allclose(measured.relative_amplitudes, reference, atol=2e-14)
            self.assertAlmostEqual(measured.main_tap, main, places=13)
            self.assertAlmostEqual(measured.peak, max(map(abs, side), default=0), places=14)
            self.assertAlmostEqual(measured.rms, math.sqrt(math.fsum(x*x for x in side)/len(side)) if side else 0,
                                   places=14)

    def test_invalid_input_resource_estimates_and_cooperative_cancellation(self):
        for args in (('unspecified',), ('rectangular', 8, 3, 0.35), ('rrc', True),
                     ('rc', 0), ('rrc', 8, -1), ('rrc', 8, 3, 1.1), ('rc', 8, 4, 0, 'raw')):
            with self.subTest(args=args), self.assertRaises(ValueError):
                PulseSpec(*args)
        with self.assertRaisesRegex(ValueError, 'espacio'):
            design_pulse(PulseSpec('rrc', sys.maxsize, 2))
        for function in (design_pulse, matched_pulse_isi):
            with self.assertRaises(TypeError):
                function(None)
        pulse = design_pulse(PulseSpec('rc', 4, 4, 0.5))
        with self.assertRaisesRegex(ValueError, 'temporal'):
            upsample_symbols(Signal([1], units='bin k'), 2)
        with self.assertRaisesRegex(ValueError, 'espacio'):
            upsample_symbols(Signal([1], origin=2**62), 4)
        with self.assertRaisesRegex(ValueError, 'espacio'):
            apply_pulse(Signal([1], origin=2**63-2), pulse)
        with self.assertRaisesRegex(ValueError, 'registradas'):
            apply_pulse(iq_signal([1], SymbolClock(1000, 2)), pulse)
        with self.assertRaises(ValueError):
            apply_pulse(Signal([1]), None)
        with self.assertRaises(ValueError):
            apply_pulse(Signal([1]), pulse, matched=1)
        pool = ResourcePool(32_000)
        for action in (
            lambda ctx: design_pulse(pulse.specification, ctx),
            lambda ctx: upsample_symbols(Signal([1, 0]), 4, ctx),
            lambda ctx: apply_pulse(Signal([1, 0]), pulse, execution=ctx),
            lambda ctx: matched_pulse_isi(pulse, ctx),
        ):
            with self.subTest(action=action):
                with self.assertRaises(ResourceLimitError):
                    action(ExecutionContext(max_work_bytes=1))
                cancel = Event()

                def stop(value):
                    if value >= 85:
                        cancel.set()

                with self.assertRaises(OperationCancelled):
                    action(ExecutionContext(cancel=cancel, progress=stop, pool=pool))
                with pool.reserve(32_000):
                    pass

    def test_filter_result_can_be_published_with_verified_parents(self):
        pulse = design_pulse(PulseSpec('rectangular', 4, 1))
        source = upsample_symbols(iq_signal([1, 0, -1], SymbolClock(1000)), 4)
        result = apply_pulse(source, pulse)
        project = Project()
        parents = project.add(source), project.add(pulse.transfer(4000))
        key = store_signal(project, result, parents=parents)
        np.testing.assert_array_equal(project.get(key).values, result.values)
        result.metadata['communications_pulse']['tap_count'] += 1
        before = project.headers()
        with self.assertRaises(ValueError):
            store_signal(project, result, parents=parents)
        self.assertEqual(project.headers(), before)


if __name__ == '__main__':
    unittest.main()
