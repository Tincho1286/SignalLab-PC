import json,math,tempfile,unittest
from pathlib import Path
import numpy as np
from signallab_pc.filters import Transfer
from signallab_pc.frequency_analysis import frequency_grid,analyze_frequency,export_frequency


class FrequencyAnalysisTests(unittest.TestCase):
    def test_log_grid_and_zero_validation(self):
        grid=frequency_grid(.01,100,9,True)
        np.testing.assert_allclose(grid[1:]/grid[:-1],np.sqrt(10))
        with self.assertRaisesRegex(ValueError,'Desde'):frequency_grid(0,10,10,True)
        np.testing.assert_allclose(frequency_grid(-1,1,3),[-1,0,1])

    def test_analog_margins_against_closed_forms(self):
        data=analyze_frequency(Transfer([2],[1,3,2,0],'analog'),frequency_grid(.01,100,1001,True),margins=True)
        gain=data.margins['gain_crossings'];phase=data.margins['phase_crossings']
        self.assertEqual(len(gain),1);self.assertEqual(len(phase),1)
        self.assertAlmostEqual(phase[0]['frequency'],np.sqrt(2),places=10)
        self.assertAlmostEqual(phase[0]['gain_margin'],3,places=10)
        self.assertAlmostEqual(phase[0]['gain_margin_db'],20*np.log10(3),places=9)
        roots=np.roots([1,5,4,-4]);w=math.sqrt(next(x.real for x in roots if abs(x.imag)<1e-10 and x.real>0))
        self.assertAlmostEqual(gain[0]['frequency'],w,places=9)
        self.assertAlmostEqual(gain[0]['phase_margin_rad'],np.pi/2-np.arctan(w)-np.arctan(w/2),places=9)

    def test_zero_magnitude_endpoint_does_not_hide_crossing(self):
        data=analyze_frequency(Transfer([2,0],[1,1],'analog'),frequency_grid(0,1,2),margins=True)
        self.assertTrue(np.isneginf(data.db[0]));self.assertTrue(np.isnan(data.phase[0]))
        self.assertAlmostEqual(data.margins['gain_crossings'][0]['frequency'],1/np.sqrt(3),places=9)

    def test_digital_delay_nyquist_endpoint_and_group_delay(self):
        data=analyze_frequency(Transfer([0,2],[1]),frequency_grid(0,np.pi,401),margins=True)
        rows=data.margins['phase_crossings'];self.assertEqual(len(rows),1)
        self.assertAlmostEqual(rows[0]['frequency'],np.pi);self.assertAlmostEqual(rows[0]['gain_margin'],.5)
        np.testing.assert_allclose(data.delay,1);self.assertEqual(data.units,'rad/muestra')

    def test_unit_magnitude_tangency_and_flat_response(self):
        zeta=.3;system=Transfer([2*zeta*np.sqrt(1-zeta*zeta)],[1,2*zeta,1],'analog')
        data=analyze_frequency(system,frequency_grid(.1,10,101,True),margins=True)
        self.assertEqual(len(data.margins['gain_crossings']),1)
        self.assertAlmostEqual(data.margins['gain_crossings'][0]['frequency'],np.sqrt(1-2*zeta*zeta),places=6)
        flat=analyze_frequency(Transfer([1],[1]),frequency_grid(0,np.pi,101),margins=True)
        self.assertTrue(flat.margins['nonisolated_gain']);self.assertFalse(flat.margins['gain_crossings'])

    def test_no_crossing_is_not_an_infinite_margin(self):
        data=analyze_frequency(Transfer([.5],[1,1],'analog'),frequency_grid(.1,10,101,True),margins=True)
        self.assertFalse(data.margins['gain_crossings']);self.assertFalse(data.margins['phase_crossings'])
        self.assertNotIn('infinite',str(data.margins).lower())

    def test_complex_and_advance_stay_analyzable_without_causal_margins(self):
        complex_data=analyze_frequency(Transfer([1j],[1]),frequency_grid(.1,2,21),margins=True)
        self.assertFalse(complex_data.margins['available']);np.testing.assert_allclose(complex_data.magnitude,1)
        advanced=analyze_frequency(Transfer([0,0,1],[1]),frequency_grid(.1,2,21),advance=1,margins=True)
        np.testing.assert_allclose(advanced.response,np.exp(-1j*advanced.omega));np.testing.assert_allclose(advanced.delay,1)
        self.assertFalse(advanced.margins['available'])

    def test_exports_preserve_nonuniform_coordinates_and_undefined_values(self):
        data=analyze_frequency(Transfer([0],[1],'analog'),frequency_grid(.01,10,7,True))
        with tempfile.TemporaryDirectory() as directory:
            json_path=Path(directory)/'frequency.json';csv_path=Path(directory)/'frequency.csv'
            export_frequency(data,json_path);export_frequency(data,csv_path);document=json.loads(json_path.read_text())
            np.testing.assert_array_equal(document['frequency'],data.omega)
            self.assertTrue(all(x is None for x in document['phase_rad']));self.assertTrue(all(x is None for x in document['magnitude_db']))
            self.assertIn('-inf',csv_path.read_text(encoding='utf-8-sig'))


if __name__=='__main__':unittest.main()
