import json
import math
from pathlib import Path
from threading import Event
import unittest

import numpy as np

from signallab_pc.communications_data import BitSequence, ConstellationSpec, SymbolClock, SymbolSequence, iq_signal
from signallab_pc.communications_modulation import (
    build_constellation, decide_symbols, generate_bits, group_bits, modulate, parse_bits, ungroup_symbols,
)
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


REFERENCE = json.loads((Path(__file__).resolve().parents[1] / 'docs' / 'engineering' /
                        'phase_03' / 'evidence' / 'analytical-reference-v1.json').read_text(encoding='utf-8'))


class CommunicationsDataTests(unittest.TestCase):
    def test_binary_vectors_are_owned_and_read_only(self):
        data = np.array([0, 1, 0], dtype=np.int16)
        bits = BitSequence(data)
        data[:] = 1
        np.testing.assert_array_equal(bits.values, [0, 1, 0])
        self.assertEqual(bits.values.dtype, np.uint8)
        with self.assertRaises(ValueError):
            bits.values.flags.writeable = True
        np.testing.assert_array_equal(BitSequence([False, np.bool_(True)]).values, [0, 1])
        np.testing.assert_array_equal(BitSequence(np.array([False, True])).values, [0, 1])
        for bad in ([], (), '01', [[0, 1]], np.array([[0, 1]]), [-1, 1],
                    [1.0], np.array([0.0, 1.0]), np.array([2], np.uint64)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                BitSequence(bad)

    def test_orders_labels_padding_and_phase_are_validated(self):
        for order in (True, np.bool_(True), 2.0, 0, 3, 2**33):
            with self.subTest(order=order), self.assertRaises(ValueError):
                ConstellationSpec('psk', order)
        for args in (
            ('qam', 8), ('other', 4), ('psk', 4, 'other'),
            ('psk', 4, 'gray', math.inf), ('psk', 4, 'gray', 0, 'other'),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                ConstellationSpec(*args)
        self.assertEqual(ConstellationSpec('psk', 4, rotation_rad=math.pi).rotation_rad, -math.pi)
        self.assertEqual(ConstellationSpec('psk', 4, rotation_rad=7*math.tau+0.125).rotation_rad, 0.125)
        labels = SymbolSequence(np.array([15, 8], dtype=np.uint8), 16, 5)
        self.assertEqual(labels.padding_bits, 3)
        with self.assertRaises(ValueError):
            labels.labels.flags.writeable = True
        for labels, useful, clock in (
            ([16], None, None), ([True], 1, None), ([-1], 1, None),
            ([0, 1], 4, None), ([0, 1], 9, None),
            ([0], None, SymbolClock(1, 2)), ([0], None, '1000'),
        ):
            with self.subTest(labels=labels, useful=useful, clock=clock), self.assertRaises(ValueError):
                SymbolSequence(labels, 16, useful, clock)

    def test_iq_clock_resolution_units_and_signal(self):
        clock = SymbolClock(4000, 4, -0.125, -300_000)
        waveform = iq_signal([1+2j, 3-1j], clock, origin=-18, amplitude_units='V')
        self.assertEqual((waveform.origin, waveform.units, waveform.data_kind), (-18, 'n', 'temporal'))
        self.assertEqual(waveform.metadata['sample_rate_hz'], 16000)
        self.assertEqual(waveform.metadata['symbol_rate_hz'], 4000)
        self.assertEqual(waveform.metadata['time_start_s'], -0.125)
        self.assertEqual(waveform.metadata['center_frequency_hz'], -300_000)
        self.assertEqual(waveform.metadata['amplitude_units'], 'V')
        self.assertNotIn('time_start_s', SymbolClock(1000, time_start_s=None).metadata(3))
        with self.assertRaisesRegex(ValueError, 'resolución'):
            SymbolClock(10_000, time_start_s=1e20).metadata(3)
        for kwargs in ({'symbol_rate_hz': 0}, {'symbol_rate_hz': '1000'}, {'symbol_rate_hz': 10**400},
                       {'symbol_rate_hz': math.nan}, {'symbol_rate_hz': True},
                       {'symbol_rate_hz': 1e308, 'samples_per_symbol': 3}, {'samples_per_symbol': 0},
                       {'samples_per_symbol': 2.5}, {'center_frequency_hz': math.inf}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SymbolClock(**({'symbol_rate_hz': 1000} | kwargs))
        for data, timing, units in (([1], None, 'V'), ([1], clock, ''),
                                    ([[1]], clock, 'V'), (np.array(['1']), clock, 'V'),
                                    (np.array([[0, 1]]), clock, 'V'), ([math.nan], clock, 'V')):
            with self.subTest(data=data, units=units), self.assertRaises(ValueError):
                iq_signal(data, timing, amplitude_units=units)


class CommunicationsModulationTests(unittest.TestCase):
    def test_parse_seeded_bits_and_reproducibility_across_blocks(self):
        np.testing.assert_array_equal(parse_bits('01 10\n 0\t1\r').values, [0, 1, 1, 0, 0, 1])
        for bad in ('', '02', [0, 1], '0π1', '0,1'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_bits(bad)
        count = 70_003
        seed = 2183
        a = generate_bits(count, seed)
        reference = np.random.default_rng(seed).integers(0, 2, count, dtype=np.uint8)
        np.testing.assert_array_equal(a.values, reference)
        self.assertEqual(a.seed, seed)
        self.assertFalse(np.array_equal(a.values, generate_bits(count, seed + 1).values))
        for count, seed in ((0, 0), (16, -1), (16, 2**128), (16, True)):
            with self.subTest(count=count, seed=seed), self.assertRaises(ValueError):
                generate_bits(count, seed)

    def test_msb_grouping_and_padding_round_trip(self):
        words = parse_bits('1011 0001 11')
        spec = ConstellationSpec('qam', 16)
        with self.assertRaisesRegex(ValueError, 'múltiplo de 4'):
            group_bits(words, spec)
        with self.assertRaises(ValueError):
            group_bits(words, spec, pad=1)
        clock = SymbolClock(12_000, time_start_s=-0.01)
        labels = group_bits(words, spec, pad=True, clock=clock)
        np.testing.assert_array_equal(labels.labels, [11, 1, 12])
        self.assertEqual((labels.valid_bits, labels.padding_bits, labels.clock), (10, 2, clock))
        np.testing.assert_array_equal(ungroup_symbols(labels).values, words.values)
        high = ConstellationSpec('psk', 2**32)
        high_word = parse_bits('1'*32)
        np.testing.assert_array_equal(group_bits(high_word, high).labels, [2**32 - 1])
        np.testing.assert_array_equal(ungroup_symbols(group_bits(high_word, high)).values, high_word.values)
        for callable_, args in ((group_bits, ('01', spec)), (ungroup_symbols, ([1],)),
                                (build_constellation, (4,)), (modulate, ([0], spec)),
                                (decide_symbols, ([0], spec))):
            with self.subTest(function=callable_.__name__), self.assertRaises(TypeError):
                callable_(*args)

    def test_psk_geometry_gray_cycle_and_minimum_distance(self):
        rotation = math.pi / 4
        for order in (2, 4, 8, 32):
            with self.subTest(order=order):
                spec = ConstellationSpec('psk', order, rotation_rad=rotation)
                result = build_constellation(spec)
                expected = [complex(math.cos(rotation + math.tau*i/order), math.sin(rotation + math.tau*i/order))
                            for i in range(order)]
                np.testing.assert_allclose(result.points, expected, atol=2e-12)
                distances = np.abs(result.points - np.roll(result.points, 1))
                self.assertAlmostEqual(result.minimum_distance, float(min(distances)), places=13)
                self.assertAlmostEqual(np.mean(abs(result.points)**2), result.mean_symbol_energy, places=13)
                self.assertTrue(all((int(a)^int(b)).bit_count() == 1
                                    for a, b in zip(result.labels, np.roll(result.labels, 1), strict=True)))
                natural = build_constellation(ConstellationSpec('psk', order, 'natural', rotation, 'raw'))
                np.testing.assert_array_equal(natural.labels, np.arange(order))
                np.testing.assert_allclose(natural.points, expected, atol=2e-12)
        words = REFERENCE['gray_cycle_8']
        np.testing.assert_array_equal(build_constellation(ConstellationSpec('psk', 8)).labels,
                                      [int(word, 2) for word in words])

    def test_square_qam_labels_neighbors_and_energy_from_independent_grids(self):
        for order, energy in REFERENCE['square_qam_raw_energy'] + [[1024, 682.0]]:
            with self.subTest(order=order):
                side = math.isqrt(order)
                raw = build_constellation(ConstellationSpec('qam', order, normalization='raw'))
                expected = [complex(i, q) for i in range(1-side, side, 2) for q in range(1-side, side, 2)]
                np.testing.assert_array_equal(raw.points, expected)
                self.assertAlmostEqual(raw.mean_symbol_energy, energy, places=12)
                self.assertEqual(raw.minimum_distance, 2)
                self.assertEqual(len(set(raw.labels)), order)
                grid = raw.labels.reshape(side, side)
                for g in (grid, grid.T):
                    self.assertTrue(all(int(diff).bit_count() == 1 for diff in (g[:, 1:]^g[:, :-1]).ravel()))
                angle = -0.3
                spec = ConstellationSpec('qam', order, 'natural', angle)
                result = build_constellation(spec)
                np.testing.assert_allclose(result.points,
                                           np.array(expected)*complex(math.cos(angle), math.sin(angle))/math.sqrt(energy),
                                           atol=2e-12)
                np.testing.assert_array_equal(result.labels, np.arange(order))
                self.assertAlmostEqual(np.mean(abs(result.points)**2), 1, places=12)
        gray16 = build_constellation(ConstellationSpec('qam', 16)).labels
        axis_gray = REFERENCE['gray_axis_4']
        np.testing.assert_array_equal(gray16, [int(i+q, 2) for i in axis_gray for q in axis_gray])

    def test_decisions_match_exhaustive_distances_and_round_trip_bits(self):
        rng = np.random.default_rng(1321)
        readings = (rng.normal(size=255) + 1j*rng.normal(size=255)) * 2
        for family, order in (('psk', 2), ('psk', 4), ('psk', 16), ('qam', 4), ('qam', 64), ('qam', 256)):
            for labeling in ('gray', 'natural'):
                with self.subTest(family=family, order=order, labeling=labeling):
                    spec = ConstellationSpec(family, order, labeling, rotation_rad=0.393)
                    reference = build_constellation(spec)
                    expected = reference.labels[np.argmin(abs(readings[:, None] - reference.points), axis=1)]
                    actual = decide_symbols(Signal(readings), spec)
                    np.testing.assert_array_equal(actual.labels, expected)
                    size = 7*spec.bits_per_symbol - (spec.bits_per_symbol > 1)
                    clock = SymbolClock(4_000, time_start_s=-0.01, center_frequency_hz=20e6)
                    source = generate_bits(size, 3)
                    grouped = group_bits(source, spec, clock=clock, pad=True)
                    waveform = modulate(grouped, spec)
                    decoded = decide_symbols(waveform, spec)
                    np.testing.assert_array_equal(decoded.labels, grouped.labels)
                    np.testing.assert_array_equal(ungroup_symbols(decoded).values, source.values)
                    self.assertEqual(decoded.clock, clock)
                    self.assertEqual(decoded.valid_bits, size)
                    self.assertEqual(waveform.metadata['communications']['bits_per_symbol'], spec.bits_per_symbol)

    def test_nearest_geometry_ties_and_large_finite_observations(self):
        spec = ConstellationSpec('psk', 4, 'natural')
        np.testing.assert_array_equal(decide_symbols(Signal([0, 1+1j, 1-1j]), spec).labels, [0, 1, 0])
        spec = ConstellationSpec('qam', 16, 'natural', normalization='raw')
        test = [0, 0+2j, -2-2j, -2+3j, complex(1.7e308, -1.7e308)]
        with np.errstate(over='raise', invalid='raise'):
            decoded = decide_symbols(Signal(test), spec)
        np.testing.assert_array_equal(decoded.labels, [10, 11, 5, 7, 12])

    def test_incompatible_input_and_mutation_are_detected(self):
        spec = ConstellationSpec('psk', 4)
        with self.assertRaisesRegex(ValueError, 'mismo orden'):
            modulate(SymbolSequence([0], 8), spec)
        for signal in (Signal([0], units='k'), Signal([0], domain='continuous'),
                       iq_signal([1], SymbolClock(1000, 2)),
                       Signal([1], metadata={'symbol_rate_hz': 1000, 'sample_rate_hz': 2000})):
            with self.subTest(signal=signal), self.assertRaises(ValueError):
                decide_symbols(signal, spec)
        signal = Signal([1, 0])
        signal.values[0] = np.inf
        with self.assertRaisesRegex(ValueError, 'finitas'):
            decide_symbols(signal, spec)
        signal.values[0] = 1
        self.assertNotIn('sample_rate_hz', modulate(SymbolSequence([1], 4), spec).metadata)
        imported = Signal([1, -1], metadata={'sample_rate_hz': 48_000})
        self.assertEqual(decide_symbols(imported, spec).clock, SymbolClock(48_000, time_start_s=None))
        imported.values = np.empty((2, 1), dtype=np.complex128)
        with self.assertRaisesRegex(ValueError, 'vector'):
            decide_symbols(imported, spec)

        def mutate(progress):
            if progress == 100:
                signal.values[0] = -1

        with self.assertRaisesRegex(ValueError, 'cambió'):
            decide_symbols(signal, spec, execution=ExecutionContext(progress=mutate))

    def test_budget_and_cancellation_release_shared_reservation(self):
        spec = ConstellationSpec('qam', 64)
        actions = [
            lambda ctx: parse_bits('10000111', ctx),
            lambda ctx: generate_bits(32, 123, ctx),
            lambda ctx: group_bits(BitSequence([0, 1]*6), spec, execution=ctx),
            lambda ctx: ungroup_symbols(SymbolSequence([0, 1], 64), ctx),
            lambda ctx: build_constellation(spec, ctx),
            lambda ctx: modulate(SymbolSequence([0, 42], 64), spec, ctx),
            lambda ctx: decide_symbols(Signal([1, -1]), spec, execution=ctx),
        ]
        pool = ResourcePool(20_000)
        for action in actions:
            with self.subTest(action=action):
                with self.assertRaises(ResourceLimitError):
                    action(ExecutionContext(max_work_bytes=1))
                event = Event()

                def cancel_last(percentage):
                    if percentage == 100:
                        event.set()

                with self.assertRaises(OperationCancelled):
                    action(ExecutionContext(cancel=event, progress=cancel_last, pool=pool))
                with pool.reserve(20_000):
                    pass
                self.assertIsNotNone(action(ExecutionContext(pool=pool)))

    def test_grouping_keeps_frame_alignment_across_multiple_blocks(self):
        spec = ConstellationSpec('psk', 8)
        bits = generate_bits(66_000 * 3 + 1, 313)
        symbols = group_bits(bits, spec, pad=True)
        self.assertEqual((symbols.labels.size, symbols.padding_bits), (66_001, 2))
        sample = symbols.labels[65_535:65_537]
        expected = [int(''.join(map(str, bits.values[3*i:3*i+3])), 2) for i in (65_535, 65_536)]
        np.testing.assert_array_equal(sample, expected)
        np.testing.assert_array_equal(ungroup_symbols(symbols).values, bits.values)
        event = Event()
        reported = []

        def stop(progress):
            reported.append(progress)
            if progress >= 50:
                event.set()

        with self.assertRaises(OperationCancelled):
            group_bits(bits, spec, pad=True, execution=ExecutionContext(cancel=event, progress=stop))
        self.assertLess(reported[-1], 100)


if __name__ == '__main__':
    unittest.main()
