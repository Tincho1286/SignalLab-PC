import threading
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.resources import ResourceLimitError
from signallab_pc.rf_analysis import cascade, load_reflection, measure, terminate
from signallab_pc.rf_network import NetworkConditionError, RFNetwork, convert, interpolate, renormalize


def network(matrix, *, grid=(1.0, 2.0, 3.0), **kwargs):
    array = np.asarray(matrix)
    return RFNetwork(grid, np.broadcast_to(array, (len(grid), *array.shape)), **kwargs)


class RFNetworkTests(unittest.TestCase):
    def test_input_snapshot_is_immutable_including_metadata(self):
        f = np.array([0, 1e9])
        s = np.zeros((2, 1, 1), dtype=complex)
        r = np.array([[50], [75]])
        data = {'source': ['test']}
        original = RFNetwork(f, s, reference_ohm=r, metadata=data, name='red')
        f[0] = 4
        s[0, 0, 0] = 1
        r[0, 0] = 99
        data['source'].append('later')
        original.metadata['source'].clear()
        assert_array_equal(original.frequencies_hz, [0, 1e9])
        assert_array_equal(original.values[:, 0, 0], [0, 0])
        assert_array_equal(original.reference_ohm[:, 0], [50, 75])
        self.assertEqual(original.metadata, {'source': ['test']})
        self.assertEqual(original.port_names, ('1',))
        self.assertEqual(original.wave_convention, 'power')
        for item in (original.frequencies_hz, original.values, original.reference_ohm):
            with self.assertRaises(ValueError):
                item.setflags(write=True)

    def test_model_validates_domain_and_keeps_two_port_chain_special(self):
        values = np.zeros((2, 1, 1))
        for f in ([1, 1], [-1, 2], [0, np.inf], [2, 1], [0], [1j, 2]):
            with self.subTest(f=f), self.assertRaises(ValueError):
                RFNetwork(f, values)
        for options in (
            {'representation': 'ABCD'}, {'representation': 'T'}, {'representation': 1},
            {'reference_ohm': 50 + 0j}, {'reference_ohm': 0}, {'reference_ohm': [50, 75]},
            {'reference_ohm': np.nan}, {'port_names': '1'}, {'port_names': ['', '2']},
            {'port_names': ['']}, {'name': 1}, {'metadata': '?'}, {'metadata': {'a': np.nan}},
        ):
            with self.subTest(options=options), self.assertRaises(ValueError):
                RFNetwork([1, 2], values, **options)
        for shape in ((2, 2), (2, 2, 1), (0, 1, 1), (2, 0, 0)):
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                RFNetwork([1, 2], np.zeros(shape))
        with self.assertRaises(ValueError):
            RFNetwork([1], [[[complex(np.inf, 1)]]])
        with self.assertRaises(ValueError):
            network(np.eye(2), port_names=['A', 'A'])
        with self.assertRaisesRegex(ValueError, 'dos puertos'):
            convert(network([[0]]), 'ABCD')

    def test_one_port_lumped_loads_and_ideal_singular_limits(self):
        z = 25 + 30j
        original = network([[z]], representation='Z')
        s = convert(original, 's')
        assert_allclose(s.values[:, 0, 0], (z - 50) / (z + 50), atol=1e-15)
        assert_allclose(convert(s, 'Z').values[:, 0, 0], z)
        assert_allclose(convert(original, 'Y').values[:, 0, 0], 1 / z)
        assert_allclose(convert(convert(original, 'Y'), 'Z').values[:, 0, 0], z)
        assert_allclose(convert(convert(original, 'Y'), 'S').values, s.values)
        assert_allclose(convert(network([[50]], representation='Z'), 'S').values, 0, atol=1e-15)
        opened = network([[1]])
        shorted = network([[-1]])
        assert_array_equal(convert(opened, 'Y').values, 0)
        assert_array_equal(convert(shorted, 'Z').values, 0)
        for model, target in ((opened, 'Z'), (shorted, 'Y'), (network([[1 - 1e-14]]), 'Z')):
            with self.assertRaisesRegex(NetworkConditionError, '1 Hz'):
                convert(model, target)
        self.assertIs(convert(s, 'S'), s)

    def test_unequal_complex_series_oracle_and_chain_units(self):
        r1, r2, impedance = 50, 75, 25 - 20j
        series = network([[1, impedance], [0, 1]], reference_ohm=(r1, r2), representation='ABCD')
        denominator = r1 + r2 + impedance
        mutual = (2 * np.sqrt(r1 * r2)) / denominator
        s = convert(series, 'S')
        expected = [[(r2 + impedance - r1) / denominator, mutual],
                    [mutual, (r1 + impedance - r2) / denominator]]
        assert_allclose(s.values[1], expected, atol=1e-15)
        assert_allclose(convert(s, 'ABCD').values, series.values, atol=5e-14)
        admittance = .03 + .01j
        shunt = network([[1, 0], [admittance, 1]], reference_ohm=[50, 50], representation='ABCD')
        # Nodal balance: V1 = V2 and the port currents supply the shunt admittance.
        transmission = 2 / (2 + 50 * admittance)
        assert_allclose(convert(shunt, 'S').values[0], [[transmission - 1, transmission],
                                                        [transmission, transmission - 1]], atol=1e-15)
        assert_allclose(convert(shunt, 'Z').values[0], np.full((2, 2), 1 / admittance))
        assert_allclose(convert(convert(shunt, 'Z'), 'ABCD').values, shunt.values, atol=1e-14)
        assert_allclose(convert(series, 'Y').values[0], np.array([[1, -1], [-1, 1]]) / impedance)
        assert_allclose(convert(convert(series, 'Y'), 'ABCD').values, series.values, atol=5e-14)

    def test_through_is_not_a_finite_z_or_y_representation(self):
        through = network([[0, 1], [1, 0]])
        assert_allclose(convert(through, 'ABCD').values[0], np.eye(2), atol=1e-15)
        for representation in ('Y', 'Z'):
            with self.assertRaises(NetworkConditionError):
                convert(through, representation)
        impedance = [[50, 10j], [-10j, 75]]
        z = network(impedance, representation='Z', reference_ohm=[50, 75])
        s = convert(z, 'S')
        assert_allclose(convert(s, 'Z').values[0], impedance, atol=1e-13)
        assert_allclose(convert(convert(s, 'Y'), 'S').values, s.values, atol=1e-15)
        assert_allclose(convert(convert(z, 'ABCD'), 'Z').values, z.values, atol=1e-13)

    def test_renormalization_preserves_through_and_physical_units(self):
        through = network([[0, 1], [1, 0]])
        z = np.array([[75, 50], [50, 50], [50, 100]])
        actual = renormalize(through, z)
        g = (z[:, 1] - z[:, 0]) / z.sum(axis=1)
        t = 2 * np.sqrt(z[:, 1] * z[:, 0]) / z.sum(axis=1)
        assert_allclose(actual.values[:, 0, 0], g, atol=1e-15)
        assert_allclose(actual.values[:, 1, 1], -g, atol=1e-15)
        assert_allclose(actual.values[:, 1, 0], t, atol=1e-15)
        assert_allclose(renormalize(actual, 50).values, through.values, atol=1e-15)
        source = network([[50 + 12j]], representation='z')
        new = renormalize(source, 75)
        assert_array_equal(new.values, source.values)
        self.assertIs(renormalize(source, 50), source)
        assert_allclose(convert(new, 'S').values[:, 0, 0], (-25 + 12j) / (125 + 12j))

    def test_interpolation_is_cartesian_and_never_extrapolates(self):
        s = RFNetwork([0, 4], [[[0]], [[1 + 2j]]], reference_ohm=[[50], [90]], port_names=['RF'])
        interp = interpolate(s, [1, 2, 4])
        assert_allclose(interp.values[:, 0, 0], [.25 + .5j, .5 + 1j, 1 + 2j])
        assert_allclose(interp.reference_ohm[:, 0], [60, 70, 90])
        self.assertEqual(interp.port_names, ('RF',))
        self.assertEqual(interp.metadata['interpolation'], 'linear_cartesian_in_band')
        self.assertIs(interpolate(s, [0, 4]), s)
        for bad_grid in ([], [1, 1], [4, 1], [-1], [5], [np.nan], [[1, 2]]):
            with self.subTest(bad_grid=bad_grid), self.assertRaises(ValueError):
                interpolate(s, bad_grid)

    def test_cascade_matches_series_impedances_and_respects_connection(self):
        first = network([[1, 15 + 8j], [0, 1]], representation='ABCD',
                        reference_ohm=[50, 65], port_names=['A', 'port'])
        second = network([[1, 30 - 4j], [0, 1]], representation='ABCD',
                         reference_ohm=[75, 30], port_names=['port', 'A'])
        with self.assertRaisesRegex(ValueError, 'referencias'):
            cascade(first, second)
        series = cascade(first, second, renormalize_internal=True)
        assert_allclose(convert(series, 'ABCD').values[0], [[1, 45 + 4j], [0, 1]], atol=1e-13)
        self.assertEqual(series.port_names, ('Entrada A', 'Salida A'))
        assert_array_equal(series.reference_ohm[0], [50, 30])
        isolator = network([[0, 0], [.7j, 0]])
        attenuator = network([[0, .5], [.5, 0]])
        assert_allclose(cascade(isolator, attenuator).values[0], [[0, 0], [.35j, 0]])
        with self.assertRaisesRegex(NetworkConditionError, 'Cascada a 1 Hz'):
            cascade(network(np.eye(2)), network(np.eye(2)))
        with self.assertRaisesRegex(ValueError, 'rejillas'):
            cascade(first, network(np.eye(2), grid=(2, 3, 4)))
        with self.assertRaisesRegex(ValueError, 'dos puertos'):
            cascade(first, network([[0]]))

    def test_termination_of_three_port_reduces_in_requested_order(self):
        scattering = [[.1, .2, .3], [.2, .1, .5], [.4, .6, .2]]
        source = network(scattering, reference_ohm=(50, 75, 60), port_names=('A', 'B', 'C'))
        out = terminate(source, (1, 0), load_ohm=90)
        gamma = (90 - 60) / (90 + 60)
        # bC = .6*aB + .4*aA + .2*gamma*bC
        k = gamma / (1 - .2 * gamma)
        expected = [[.1 + .5*.6*k, .2 + .5*.4*k], [.2 + .3*.6*k, .1 + .3*.4*k]]
        assert_allclose(out.values[0], expected, atol=1e-15)
        self.assertEqual(out.port_names, ('B', 'A'))
        self.assertEqual(out.metadata['terminated_ports'], ['C'])
        assert_array_equal(out.reference_ohm[0], [75, 50])
        reordered = terminate(source, (2, 0, 1))
        assert_allclose(reordered.values[0], [[.2, .4, .6], [.3, .1, .2], [.5, .2, .1]])
        through = network([[0, 1], [1, 0]])
        for load, value in (('short', -1), ('open', 1), ('matched', 0)):
            assert_array_equal(terminate(through, [0], load_ohm=load).values, value)
        assert_allclose(terminate(through, [0], reflection=.3j).values, .3j)
        with self.assertRaisesRegex(NetworkConditionError, 'Terminación a 1 Hz'):
            terminate(network(np.eye(2)), [0], load_ohm='open')
        for keep, load in (([], 'open'), ([0, 0], 'matched'), ([False], 'open'),
                           ([2], 'matched'), ([0], -50), ([0], 'lumped'), ([0], np.inf)):
            with self.subTest(keep=keep, load=load), self.assertRaises(ValueError):
                terminate(through, keep, load_ohm=load)
        with self.assertRaises(ValueError):
            terminate(through, [1], reflection=1.2)
        with self.assertRaises(ValueError):
            terminate(through, [1], reflection=.5, load_ohm=50)
        with self.assertRaises(ValueError):
            load_reflection('open', 50 + 1j)
        assert_allclose(load_reflection(1e300 + 1e300j, 50), 1)

    def test_group_delay_and_directional_measurements(self):
        f = np.array([1e6, 2e6, 3.5e6, 5e6, 6e6, 8e6, 9e6])
        delay = 20e-9
        values = np.zeros((len(f), 2, 2), complex)
        values[:, 1, 0] = .5 * np.exp(-2j * np.pi * f * delay)
        values[3, 1, 0] = 0
        values[:, 0, 1] = .001
        values[:, 0, 0] = .2
        result = measure(RFNetwork(f, values, reference_ohm=[50, 75]))
        assert_allclose(result.group_delay_s[[0, 1, 2, 4, 5, 6], 1, 0], delay, atol=1e-20)
        self.assertTrue(np.isnan(result.group_delay_s[3, 1, 0]))
        self.assertTrue(np.isnan(result.phase_rad[3, 1, 0]))
        self.assertTrue(np.isneginf(result.magnitude_db[3, 1, 0]))
        self.assertTrue(np.isnan(result.transmission[0, 0, 0]))
        assert_allclose(result.transmission[:, 1, 0], values[:, 1, 0])
        assert_allclose(result.return_loss_db[:, 0], -20 * np.log10(.2))
        assert_allclose(result.insertion_loss_db[0, 1, 0], -20 * np.log10(.5))
        assert_allclose(result.isolation_db[:, 1, 0], 60)
        assert_allclose(result.input_impedance_ohm[:, 0], 75)
        assert_allclose(result.input_admittance_siemens[:, 0], 1 / 75)
        assert_allclose(result.vswr[:, 0], 1.5)
        assert_array_equal(result.reciprocal, False)
        assert_array_equal(result.passive, True)
        assert_allclose(result.symmetry_error[0], abs(values[0, 1, 0] - .001))

    def test_measurement_ideal_limits_and_active_network(self):
        result = measure(RFNetwork([1, 2, 3, 4], [[[1]], [[-1]], [[1.1]], [[0]]]))
        self.assertTrue(np.isnan(result.input_impedance_ohm[0, 0]))
        self.assertTrue(np.isnan(result.input_admittance_siemens[1, 0]))
        assert_array_equal(result.input_impedance_ohm[[1, 3], 0], [0, 50])
        assert_array_equal(result.input_admittance_siemens[[0, 3], 0], [0, .02])
        assert_array_equal(result.vswr[:2, 0], [np.inf, np.inf])
        self.assertTrue(np.isnan(result.vswr[2, 0]))
        assert_array_equal(result.passive, [True, True, False, True])
        assert_array_equal(result.reciprocal, True)
        assert_array_equal(result.max_singular_value, [1, 1, 1.1, 0])
        result = measure(network([[0, .25], [.25, 0]], grid=(0,)))
        self.assertEqual(result.phase_rad[0, 1, 0], 0)
        self.assertTrue(np.isnan(result.group_delay_s[0, 1, 0]))
        with self.assertRaises(ValueError):
            measure(network([[0]]), tolerance=np.nan)

    def test_context_stops_and_releases_reservations(self):
        original = network([[0]], grid=np.arange(1024))
        with self.assertRaises(ResourceLimitError):
            convert(original, 'Z', context=ExecutionContext(max_work_bytes=1))

        class CancelBetweenBlocks(ExecutionContext):
            def checkpoint(self, percentage=None):
                calls.append(1)
                if len(calls) == 4:
                    event.set()
                return super().checkpoint(percentage)

        calls = []
        event = threading.Event()
        pool = ResourcePool(5_000_000)
        with self.assertRaises(OperationCancelled):
            convert(original, 'Z', context=CancelBetweenBlocks(cancel=event, pool=pool))
        with pool.reserve(5_000_000):
            pass
        assert_allclose(convert(original, 'Z').values[:, 0, 0], 50, rtol=1e-15)


if __name__ == '__main__':
    unittest.main()
