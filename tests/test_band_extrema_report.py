import sys
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from scipy.signal import firwin
sys.path.insert(0,str(Path.cwd()))
from signallab_pc.band_extrema import evaluate, measure
from signallab_pc.filters import Transfer

class BandReport(unittest.TestCase):
    def test_all_bands_and_units_without_remeasuring(self):
        for domain,end,unit in [('digital',np.pi,'rad/muestra'),('analog',np.inf,'rad/s')]:
            for kind,passing,stopping in [('bandpass',1,2),('bandstop',2,1)]:
                spec={'kind':kind,'wp':[.3,.7],'ws':[.2,.8] if kind=='bandpass' else [.4,.6],
                      'pass_lower':[.98]*passing,'pass_upper_bands':[1.02]*passing,'amplitudes':[1.]*passing,'stop_upper':.15}
                metrics={'passing':[dict(minimum=.99,minimum_at=.3,maximum=1.01,maximum_at=.5)]*passing,
                         'stopping':[dict(minimum=.001,minimum_at=.8,maximum=.1,maximum_at=.9)]*stopping,
                         'failed_refinements':0,'scope':'refined'}
                with patch('signallab_pc.band_extrema.measure',return_value=metrics) as measured:
                    accepted,report=evaluate(Transfer([1],[1],domain),spec)
                self.assertTrue(accepted);measured.assert_called_once()
                self.assertEqual(report.count('Mínimo |H| ='),passing+stopping)
                self.assertEqual(report.count('Máximo |H| ='),passing+stopping)
                self.assertIn('Rechazo '+str(stopping),report);self.assertIn('Paso '+str(passing),report)
                self.assertIn(unit,report);self.assertIn('amplitud lineal',report)
                if domain=='analog':self.assertIn('∞',report)

    def test_kaiser_example_reports_the_computed_extrema(self):
        spec={'kind':'lowpass','wp':[.63*np.pi],'ws':[.65*np.pi],'pass_lower':[.98],
              'pass_upper_bands':[1.02],'amplitudes':[1.],'stop_upper':.15}
        system=Transfer(firwin(183,.64,window=('kaiser',2.652339138368929),scale=False),[1],'digital')
        metrics=measure(system,spec['wp'],spec['ws'],spec['kind'])
        accepted,report=evaluate(system,spec)
        self.assertTrue(accepted)
        for band in ('passing','stopping'):
            for key in ('minimum','maximum','minimum_at','maximum_at'):
                self.assertIn(format(metrics[band][0][key],'.12g'),report)
        print(report)

if __name__=='__main__':unittest.main()
