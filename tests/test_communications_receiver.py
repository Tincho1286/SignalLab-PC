import math
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_data import ConstellationSpec, SymbolClock, iq_signal
from signallab_pc.communications_modulation import decide_symbols, generate_bits, group_bits, modulate, ungroup_symbols
from signallab_pc.communications_pulses import PulseSpec, apply_pulse, design_pulse, upsample_symbols
from signallab_pc.communications_receiver import SynchronizationSpec, recover_symbols
from signallab_pc.dsp_application import store_signal
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class CommunicationsReceiverTests(unittest.TestCase):
    def test_ideal_matched_chain_recovers_useful_bits_without_noise(self):
        spec = ConstellationSpec('psk', 4, rotation_rad=math.pi/4)
        clock = SymbolClock(2400, time_start_s=0.5)
        for sps in (3, 8):
            with self.subTest(sps=sps):
                bits = generate_bits(257, 334)
                symbols = group_bits(bits, spec, clock=clock, pad=True)
                tx = modulate(symbols, spec)
                pulse = design_pulse(PulseSpec('rrc', sps, 9, 0.35, 'unit_peak'))
                rx = apply_pulse(apply_pulse(upsample_symbols(tx, sps), pulse), pulse, matched=True)
                known = pulse.taps.size-1
                receive = recover_symbols(rx, symbols.labels.size, sps, SynchronizationSpec(sample_offset=known),
                                          sample_gain=pulse.energy)
                self.assertEqual(receive.synchronization.state, 'ideal')
                self.assertEqual(receive.synchronization.sample_offset, known)
                self.assertEqual(receive.symbols.metadata['sample_rate_hz'], 2400)
                self.assertAlmostEqual(receive.symbols.metadata['time_start_s'], 0.5+known/(2400*sps))
                self.assertLess(np.linalg.norm(receive.symbols.values - tx.values)/math.sqrt(tx.values.size), 0.03)
                decoded = decide_symbols(receive.symbols, spec)
                np.testing.assert_array_equal(ungroup_symbols(decoded).values, bits.values)

    def test_assisted_alignment_preserves_source_index_clock_and_reported_gain(self):
        expected = np.array([1+2j, -3j, -2-1j])
        offset, sps, gain, phase = 5, 4, 1.7, -0.65
        values = np.zeros(19, dtype=complex)
        values[offset:offset+expected.size*sps:sps] = expected*gain*np.exp(1j*phase)
        x = iq_signal(values, SymbolClock(1000, sps, -0.25, 20_000), origin=-14, amplitude_units='V')
        result = recover_symbols(x, expected.size, sps, SynchronizationSpec('assisted', offset, phase),
                                 sample_gain=gain)
        np.testing.assert_allclose(result.symbols.values, expected, atol=3e-15)
        self.assertEqual(result.synchronization.state, 'assisted')
        self.assertEqual(result.synchronization.source_index, -14+offset)
        self.assertEqual(result.applied_sample_gain, gain)
        self.assertEqual(result.symbols.metadata['amplitude_units'], 'V')
        self.assertEqual(result.symbols.metadata['center_frequency_hz'], 20_000)
        self.assertAlmostEqual(result.symbols.metadata['time_start_s'], -0.25+offset/4000)

    def test_estimated_timing_and_phase_match_independent_window_scores(self):
        pilot = Signal([1, 1j, -1, -1j, 1, -1, 1j, 1j, -1])
        expected = np.r_[pilot.values, [1j, -1, 1, -1j]]
        sps, offset, phase = 3, 11, 1.2
        values = np.zeros(70, dtype=complex)
        values[offset:offset+expected.size*sps:sps] = expected*np.exp(1j*phase)
        source = Signal(values, origin=-16)
        last = 24
        result = recover_symbols(source, expected.size, sps, SynchronizationSpec('estimated', search_last=last),
                                 pilot=pilot)
        sync = result.synchronization
        self.assertEqual(sync.state, 'estimated')
        self.assertEqual(sync.sample_offset, offset)
        self.assertEqual(sync.source_index, -16+offset)
        self.assertEqual(sync.searched_offsets, (0, last))
        self.assertAlmostEqual(sync.phase_rad, phase)
        np.testing.assert_allclose(result.symbols.values, expected, atol=1e-14)
        oracle = []
        for index in range(last+1):
            window = values[index:index+pilot.values.size*sps:sps]
            denominator = math.sqrt(sum(abs(x)**2 for x in window)*sum(abs(y)**2 for y in pilot.values))
            numerator = abs(sum(x*y.conjugate() for x,y in zip(window, pilot.values, strict=True)))
            oracle.append(numerator/denominator if denominator else 0.0)
        self.assertAlmostEqual(sync.score, max(oracle))
        self.assertAlmostEqual(sync.runner_up, sorted(oracle)[-2])
        project = Project()
        parents = project.add(source), project.add(pilot)
        key = store_signal(project, result.symbols, parents=parents)
        np.testing.assert_array_equal(project.get(key).values, result.symbols.values)

    def test_estimate_survives_dynamic_range_between_candidate_windows(self):
        tiny = 1e-315
        raw = np.array([1, 1j, -1j, 1, -1, -1j, 1j], dtype=np.complex128)
        source = np.r_[1e200, np.zeros(7), tiny*raw, np.zeros(7)]
        pilot = Signal(tiny*raw)
        result = recover_symbols(Signal(source), len(raw), 1,
                                 SynchronizationSpec('estimated', minimum_score=0.99), pilot=pilot,
                                 sample_gain=tiny)
        self.assertEqual(result.synchronization.state, 'estimated')
        self.assertEqual(result.synchronization.sample_offset, 8)
        self.assertEqual(result.synchronization.phase_rad, 0.0)
        np.testing.assert_allclose(result.symbols.values, raw, atol=2e-14)

    def test_missing_ambiguous_and_short_records_have_unavailable_state(self):
        pilot = Signal([1, 1j, -1j, -1])
        ambiguous = Signal(np.r_[pilot.values, np.zeros(3), pilot.values])
        estimated = SynchronizationSpec('estimated')
        repeated = recover_symbols(ambiguous, 4, 1, estimated, pilot=pilot)
        self.assertEqual(repeated.synchronization.state, 'unavailable')
        self.assertIn('más de un', repeated.synchronization.reason)
        self.assertIsNone(repeated.symbols)
        self.assertAlmostEqual(repeated.synchronization.runner_up, 1)
        missing = recover_symbols(ambiguous, 4, 1, estimated)
        self.assertIn('piloto', missing.synchronization.reason)
        zero = recover_symbols(Signal(np.zeros(12)), 4, 1, estimated, pilot=pilot)
        self.assertIn('insuficiente', zero.synchronization.reason)
        short_search = recover_symbols(ambiguous, 8, 2, estimated, pilot=pilot)
        self.assertIn('intervalo', short_search.synchronization.reason)
        short_known = recover_symbols(ambiguous, 12, 1, SynchronizationSpec())
        self.assertIn('símbolos', short_known.synchronization.reason)
        bracketed = recover_symbols(ambiguous, 4, 1,
                                    SynchronizationSpec('estimated', search_first=7, search_last=7), pilot=pilot)
        self.assertEqual(bracketed.synchronization.sample_offset, 7)
        self.assertEqual(bracketed.synchronization.runner_up, 0)

    def test_validation_budgets_and_cancellation(self):
        for args in (
            {'mode': 'other'}, {'mode': 'estimated', 'sample_offset': 0},
            {'mode': 'assisted'}, {'search_last': 5}, {'minimum_score': 0},
            {'minimum_margin': 1.1}, {'mode': 'estimated', 'search_first': 3, 'search_last': 2},
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                SynchronizationSpec(**args)
        pilot = Signal(np.ones(5))
        source = Signal(np.ones(60))
        spec = SynchronizationSpec('estimated')
        with self.assertRaises(ValueError):
            recover_symbols(Signal([1], domain='frequency'), 1, 1, spec)
        with self.assertRaises(TypeError):
            recover_symbols(source, 1, 1, None)
        with self.assertRaises(ValueError):
            recover_symbols(source, 3, 1, spec, pilot=pilot)
        with self.assertRaises(ValueError):
            recover_symbols(source, 5, 1, SynchronizationSpec(), pilot=pilot)
        with self.assertRaisesRegex(ValueError, 'positiva'):
            recover_symbols(source, 5, 1, spec, pilot=Signal(np.zeros(5)))
        with self.assertRaisesRegex(ValueError, 'rango'):
            recover_symbols(Signal([1e300]), 1, 1, SynchronizationSpec(), sample_gain=1e-300)
        with self.assertRaises(ResourceLimitError):
            recover_symbols(source, 5, 1, spec, pilot=pilot, execution=ExecutionContext(max_work_bytes=200))
        long = Signal(np.ones(8192))
        with self.assertRaises(ResourceLimitError):
            recover_symbols(long, 4096, 1, spec, pilot=Signal(np.ones(4096)))

        cancelled = Event()

        def observe(progress):
            if progress >= 10:
                cancelled.set()

        with self.assertRaises(OperationCancelled):
            recover_symbols(source, 5, 1, spec, pilot=pilot,
                            execution=ExecutionContext(cancel=cancelled, progress=observe))


if __name__ == '__main__':
    unittest.main()
