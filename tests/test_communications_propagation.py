import math
from threading import Event
import unittest

import numpy as np
from scipy.stats import kstest, norm

from signallab_pc.communications_propagation import (
    FreeSpaceLoss, LogDistanceLoss, PropagationSpec, apply_propagation, evaluate_propagation, free_space_loss_db,
)
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError


class PropagationContracts(unittest.TestCase):
    def test_space_loss_matches_friis_and_preserves_sample_clock_and_units(self):
        wavelength = 299_792_458 / 1e9
        loss = -10*math.log10((wavelength/(4*np.pi*1000))**2)
        self.assertAlmostEqual(free_space_loss_db(1000, 1e9), loss, places=12)
        self.assertAlmostEqual(free_space_loss_db(2000, 1e9)-loss, 20*math.log10(2))
        self.assertAlmostEqual(free_space_loss_db(1000, 2e9)-loss, 20*math.log10(2))
        x = Signal([2-3j, 4], origin=-4, metadata={
            'sample_rate_hz': 4096, 'time_start_s': .1, 'amplitude_units': 'V', 'center_frequency_hz': 1e9,
        })
        y = apply_propagation(x, PropagationSpec(FreeSpaceLoss(1000)))
        np.testing.assert_allclose(y.signal.values, x.values*(wavelength/(4*np.pi*1000)), rtol=1e-14)
        self.assertAlmostEqual(y.statistics.net_gain_db, -loss)
        self.assertEqual(y.signal.origin, x.origin)
        for key in ('sample_rate_hz', 'time_start_s', 'amplitude_units', 'center_frequency_hz'):
            self.assertEqual(y.signal.metadata[key], x.metadata[key])

    def test_log_distance_reference_and_per_decade_loss(self):
        x = Signal([1, 2j])
        for distance, value in ((10, 40), (100, 72), (1000, 104)):
            spec = PropagationSpec(LogDistanceLoss(distance, 10, 3.2, 40), gain_db=2)
            y = apply_propagation(x, spec)
            self.assertAlmostEqual(y.statistics.path_loss_db, value)
            self.assertAlmostEqual(y.statistics.reference_loss_db, 40)
            self.assertAlmostEqual(y.statistics.net_gain_db, 2-value)
        equivalent = evaluate_propagation(PropagationSpec(LogDistanceLoss(50, 2, 2, carrier_hz=915e6)))
        self.assertAlmostEqual(equivalent.path_loss_db, free_space_loss_db(50, 915e6))
        with self.assertRaisesRegex(ValueError, 'distancia'):
            LogDistanceLoss(1, 2, 2)

    def test_log_normal_shadow_is_reproducible_and_fixed_for_a_record(self):
        sigma = 4
        values = np.array([evaluate_propagation(PropagationSpec(shadow_std_db=sigma, seed=seed)).shadow_loss_db
                           for seed in range(512)])
        self.assertLess(kstest(values, norm(scale=sigma).cdf).statistic, .09)
        self.assertLess(abs(float(np.std(values))/sigma - 1), .1)
        spec = PropagationSpec(LogDistanceLoss(100, 10, 3, 40), shadow_std_db=sigma, seed=70)
        source = Signal([1, -2, 3j])
        first = apply_propagation(source, spec)
        second = apply_propagation(source, spec)
        np.testing.assert_array_equal(first.signal.values, second.signal.values)
        np.testing.assert_allclose(first.signal.values / source.values, first.statistics.amplitude_factor)
        self.assertEqual(first.signal.metadata['communications_propagation']['specification']['seed'], 70)

    def test_mismatched_carrier_near_field_and_execution_limits(self):
        x = Signal(np.ones(128), metadata={'center_frequency_hz': 9e8})
        with self.assertRaisesRegex(ValueError, 'coincidir'):
            apply_propagation(x, PropagationSpec(FreeSpaceLoss(100, 2.4e9)))
        with self.assertRaisesRegex(ValueError, 'espacio libre'):
            free_space_loss_db(.0001, 1e6)
        with self.assertRaisesRegex(ValueError, 'portadora'):
            evaluate_propagation(PropagationSpec(FreeSpaceLoss(100)))
        np.testing.assert_array_equal(apply_propagation(x, PropagationSpec()).signal.values, x.values)
        with self.assertRaises(ResourceLimitError):
            apply_propagation(x, PropagationSpec(), ExecutionContext(max_work_bytes=16))
        stop = Event()
        with self.assertRaises(OperationCancelled):
            apply_propagation(x, PropagationSpec(), ExecutionContext(cancel=stop, progress=lambda _: stop.set()))
