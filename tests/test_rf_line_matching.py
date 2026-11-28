from dataclasses import replace
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc.execution import ExecutionContext
from signallab_pc.resources import ResourceLimitError
from signallab_pc.rf_line import LIGHT_SPEED_M_S, rlgc_line, smith_grid, smith_values, uniform_line
from signallab_pc.rf_matching import element_label, evaluate_matching, synthesize_matching
from signallab_pc.rf_network import convert


class RFLineTests(unittest.TestCase):
    def test_lossless_quarter_and_half_wavelength(self):
        f = 1e9
        wavelength = .8 * LIGHT_SPEED_M_S / f
        line = uniform_line([0, f, 2*f], wavelength / 4, 50, velocity_factor=.8, load_ohm=100)
        assert_allclose(line.phase_rad, [0, np.pi / 2, np.pi])
        assert_allclose(line.input_impedance_ohm, [100, 25, 100], atol=1e-13)
        assert_allclose(line.input_voltage_reflection, [1/3, -1/3, 1/3], atol=1e-15)
        assert_allclose(line.input_reference_vswr, 2)
        assert_allclose(line.velocity_factor, .8)
        assert_allclose(line.wavelength_m, [np.inf, wavelength, wavelength / 2])
        assert_array_equal(line.intrinsic_loss_db, 0)
        assert_allclose(line.network.values[1], [[0, -1j], [-1j, 0]], atol=1e-15)

    def test_open_short_and_standing_wave_nodes(self):
        f = 1e9
        quarter = LIGHT_SPEED_M_S / (4*f)
        opened = uniform_line([f], quarter, load_ohm='open')
        shorted = uniform_line([f], quarter, load_ohm='short')
        assert_allclose(opened.input_impedance_ohm, 0, atol=2e-14)
        self.assertTrue(np.isnan(shorted.input_impedance_ohm[0]))
        assert_allclose(shorted.input_admittance_siemens, 0, atol=2e-17)
        voltage, current = opened.standing_waves(0, [0, quarter])
        assert_allclose(voltage, [2, 0], atol=1e-14)
        assert_allclose(current, [0, .04], atol=1e-15)
        for index, distance in ((1, 0), (-1, 0), (0, -1), (0, 2*quarter)):
            with self.subTest(index=index, distance=distance), self.assertRaises(ValueError):
                opened.standing_waves(index, distance)

    def test_loss_voltage_reflection_and_unequal_references(self):
        f = np.array([1e6, 2e6])
        length = 15
        matched = uniform_line(f, length, attenuation_db_per_m=[.2, .4])
        expected = 10 ** (-np.array([3, 6])/20) * np.exp(-2j*np.pi*f*length/LIGHT_SPEED_M_S)
        assert_allclose(matched.network.values[:, 1, 0], expected)
        assert_allclose(matched.input_impedance_ohm, 50)
        assert_allclose(matched.input_reference_vswr, 1)
        unequal = uniform_line(f, length, characteristic_ohm=50, attenuation_db_per_m=.2,
                               reference_ohm=[75, 50], load_ohm=[50, 150])
        gamma = np.array([0, .5])*np.exp(-4j*np.pi*f*length/LIGHT_SPEED_M_S)*10**(-6/20)
        zin = 50*(1+gamma)/(1-gamma)
        assert_allclose(unequal.input_voltage_reflection, gamma, atol=1e-15)
        assert_allclose(unequal.input_impedance_ohm, zin, atol=3e-14)
        assert_allclose(unequal.input_reference_reflection, (zin-75)/(zin+75), atol=1e-15)
        long = uniform_line(f, 10000, attenuation_db_per_m=20, load_ohm='short')
        assert_array_equal(long.network.values[:, 1, 0], 0)
        assert_allclose(long.input_impedance_ohm, 50)

    def test_rlgc_distortionless_reference_and_physical_chain(self):
        f = np.array([10e3, 2e6])
        resistance, inductance, capacitance, length = 5, 250e-9, 100e-12, 2
        conductance = resistance * capacitance / inductance
        line = rlgc_line(f, length, resistance_ohm_per_m=resistance, inductance_h_per_m=inductance,
                         conductance_s_per_m=conductance, capacitance_f_per_m=capacitance, load_ohm=100+50j)
        zc = 50
        gamma = (resistance + 2j*np.pi*f*inductance)/zc
        assert_allclose(line.characteristic_ohm, zc, atol=1e-13)
        assert_allclose(line.propagation_per_m, gamma, atol=1e-15)
        assert_allclose(line.phase_velocity_m_s, 1/np.sqrt(inductance*capacitance))
        a = convert(line.network, 'ABCD').values
        assert_allclose(a[:, 0, 0], np.cosh(gamma*length), atol=1e-15)
        assert_allclose(a[:, 0, 1], zc*np.sinh(gamma*length), atol=1e-13)
        assert_allclose(a[:, 1, 0], np.sinh(gamma*length)/zc, atol=1e-15)
        load = 100+50j
        expected = zc * (load + zc*np.tanh(gamma*length))/(zc+load*np.tanh(gamma*length))
        assert_allclose(line.input_impedance_ohm, expected, atol=1e-13)

    def test_rlgc_lossless_and_frequency_dependent_values(self):
        f = np.array([1e6, 2e6, 3e6])
        inductance, capacitance = [250e-9, 350e-9, 100e-9], 100e-12
        model = rlgc_line(f, 1, resistance_ohm_per_m=0, inductance_h_per_m=inductance,
                          conductance_s_per_m=0, capacitance_f_per_m=capacitance)
        assert_allclose(model.characteristic_ohm, np.sqrt(np.array(inductance)/capacitance))
        assert_allclose(model.propagation_per_m.real, 0, atol=1e-15)
        assert_allclose(model.propagation_per_m.imag, 2*np.pi*f*np.sqrt(np.array(inductance)*capacitance))

    def test_line_validation_and_budget(self):
        for options in ({'length_m': -1}, {'characteristic_ohm': 0}, {'velocity_factor': 0},
                        {'velocity_factor': 1.1}, {'attenuation_db_per_m': -1}, {'load_ohm': [-50]},
                        {'length_m': 1e100}, {'length_m': np.inf}, {'load_ohm': [1, 2]}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                uniform_line([1e9], **({'length_m': 1} | options))
        for grid in ([0], [2,1], [], [np.nan]):
            with self.subTest(grid=grid), self.assertRaises(ValueError):
                rlgc_line(grid, 2, resistance_ohm_per_m=.1, inductance_h_per_m=2e-9,
                          conductance_s_per_m=.1, capacitance_f_per_m=2e-9)
        with self.assertRaises(ResourceLimitError):
            uniform_line([1e9], 1, context=ExecutionContext(max_work_bytes=1))

    def test_smith_curves_keep_constant_component_and_physical_point(self):
        for mode in ('impedance', 'admittance'):
            grid = smith_grid(mode, real=[0, .5, 2], imaginary=[.3])
            index = mode == 'admittance'
            for value, locus in grid['constant_real']:
                response = smith_values(locus[1:-1])[index]
                assert_allclose(response.real, value, atol=2e-12)
                self.assertLessEqual(np.abs(locus).max(), 1 + 2e-15)
            for value, locus in grid['constant_imaginary']:
                assert_allclose(smith_values(locus[:-1])[index].imag, value, atol=2e-12)
            self.assertEqual(len(grid['real_axis']), 257)
        z, y = smith_values([0, 1, -1, .5j])
        assert_allclose(z[[0, 3]], [1, (1+.5j)/(1-.5j)])
        assert_allclose(z[[0, 3]] * y[[0, 3]], [1, 1])
        self.assertTrue(np.isnan(z[1]))
        self.assertTrue(np.isnan(y[2]))
        for options in ({'mode': 'Z/Y'}, {'points': 1}, {'imaginary': (0,)}, {'real': (-1,)}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                smith_grid(**options)


class RFMatchingTests(unittest.TestCase):
    def test_l_network_matches_real_or_complex_and_sweeps_physical_elements(self):
        center = 1e9
        frequency = np.array([.9, 1, 1.1]) * center
        for load in (100, 20, 30+40j, 50+20j, 50):
            for solution in synthesize_matching('l', center, 50, load):
                with self.subTest(load=load, solution=solution):
                    result = evaluate_matching(solution, frequency)
                    assert_allclose(result.input_impedance_ohm[1], 50, atol=2e-13)
                    assert_allclose(result.delivered_power_fraction[1], 1, atol=1e-15)
                    assert_allclose(result.vswr[1], 1, atol=1e-15)
                    measured = []
                    for f in frequency:
                        z = complex(load)
                        for side in reversed(solution.topology.split('_')):
                            for part, coefficient in solution.elements:
                                if part.startswith(side):
                                    omega = 2*np.pi*f
                                    impedance = (1j*omega*coefficient if '_L_' in part else
                                                 1/(1j*omega*coefficient))
                                    z = z+impedance if side == 'series' else 1/(1/z + 1/impedance)
                        measured.append(z)
                    assert_allclose(result.input_impedance_ohm, measured, atol=3e-13)
                    reflection = (np.asarray(measured)-50)/(np.asarray(measured)+50)
                    assert_allclose(result.delivered_power_fraction, 1-np.abs(reflection)**2, atol=1e-15)

    def test_quarter_wave_geometric_mean_and_off_design_load(self):
        design, = synthesize_matching('quarter_wave', 1e9, 50, 100, velocity_factor=.7)
        self.assertEqual(design.topology, 'quarter_wave')
        parts = dict(design.elements)
        assert_allclose(parts['line_ohm'], np.sqrt(50*100))
        assert_allclose(parts['line_m'], .7*LIGHT_SPEED_M_S/(4e9))
        primary = evaluate_matching(design, [1e9, 2e9])
        assert_allclose(primary.input_impedance_ohm, [50, 100], atol=1e-13)
        changed = evaluate_matching(design, [1e9, 2e9], load_ohm=[125, 80])
        assert_allclose(changed.input_impedance_ohm, [40, 80], atol=1e-13)
        self.assertIn('Ω', element_label('line_ohm'))

    def test_shunt_stubs_match_both_branches_by_admittance(self):
        f, load, source, vf = 77e6, 125-50j, 50, .9
        beta = 2*np.pi*f/(LIGHT_SPEED_M_S*vf)
        for kind in ('open', 'short'):
            designs = synthesize_matching('stub', f, source, load, stub=kind, velocity_factor=vf)
            self.assertEqual(len(designs), 2)
            for design in designs:
                with self.subTest(kind=kind, design=design):
                    parts = dict(design.elements)
                    tangent = np.tan(beta*parts['line_m'])
                    zin = source*(load+1j*source*tangent)/(source+1j*load*tangent)
                    stub_tangent = np.tan(beta*parts['stub_m'])
                    added = 1j/source*(stub_tangent if kind == 'open' else -1/stub_tangent)
                    assert_allclose(1/zin + added, 1/source, atol=1e-15)
                    response = evaluate_matching(design, [f*.8, f, f*1.2])
                    assert_allclose(response.reflection[1], 0, atol=1e-15)
                    self.assertGreater(abs(response.reflection[0]), .01)
                    self.assertGreater(response.effective_insertion_loss_db[0], 0)
        empty, = synthesize_matching('stub', f, source, source)
        self.assertEqual(empty.elements, ())
        assert_allclose(evaluate_matching(empty, [f]).delivered_power_fraction, 1)

    def test_validation_rejects_unrealizable_or_malformed_designs(self):
        for method, f, source, load in (('quarter_wave', 10, 50, 50+10j), ('not-a-method', 10, 50, 50),
                                         ('l', 0, 50, 50), ('l', 1e9, 50, 1j), ('l', 1e9, 50, np.inf)):
            with self.subTest(method=method, load=load), self.assertRaises(ValueError):
                synthesize_matching(method, f, source, load)
        design = synthesize_matching('l', 1e9, 50, 90)[0]
        for bad in (replace(design, method='bad'), replace(design, topology='not-l'),
                    replace(design, elements=(('BAD', 1),)), replace(design, elements=(('series_C_F', 0),)),
                    replace(design, elements=design.elements + (design.elements[0],)),
                    replace(design, elements=(('series_L_H', 1), ('series_C_F', 1)))):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evaluate_matching(bad, [1e9])
        with self.assertRaises(ValueError):
            evaluate_matching(design, [1e9], load_ohm=[50, 100])


if __name__ == '__main__':
    unittest.main()
