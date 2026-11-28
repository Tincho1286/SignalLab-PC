import json
import math
from pathlib import Path
import tempfile
import threading
import unittest

import numpy as np
from numpy.testing import assert_allclose

from signallab_pc.communications_propagation import PropagationSpec
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.monte_carlo import CampaignSpec, Scenario, load_campaign
from signallab_pc.probability import Distribution
from signallab_pc.rf_experiments import (
    LinkUncertainty, bessel_sensitivity, link_campaign, matching_sweep, matching_tolerance, noise_figure_sweep,
)
from signallab_pc.rf_link import RFStage, link_budget
from signallab_pc.rf_matching import synthesize_matching
from signallab_pc.resources import ResourceLimitError


class RFExperimentTests(unittest.TestCase):
    def test_swept_quarter_wave_load_and_sensitivity_at_design_point(self):
        f = 100e6
        design, = synthesize_matching('quarter_wave', f, 50, 100)
        values = np.array([90, 100, 115])
        sweep = matching_sweep(design,'resistance_ohm',values,[f,2*f])
        gamma = (100-values)/(100+values)
        assert_allclose(sweep.reflection[:,0], gamma, atol=4e-16)
        assert_allclose(sweep.reflection[:,1], (values-50)/(values+50), atol=5e-16)
        assert_allclose(sweep.delivered_power_fraction[:,0],1-gamma**2,atol=1e-15)
        t = matching_tolerance(design,'resistance_ohm',99.999,100.002)
        assert_allclose(t['sensitivity_per_unit'],-.005,rtol=4e-10)
        for parameter, axes in (('no',values),('reactance_ohm',[0,0]),('resistance_ohm',[-2]),('line_m',[])):
            with self.subTest(parameter=parameter, axes=axes),self.assertRaises(ValueError):
                matching_sweep(design,parameter,axes,[f])
        with self.assertRaises(ValueError):
            matching_tolerance(design,'resistance_ohm',101,111)

    def test_bessel_sensitivity_against_first_order_derivatives(self):
        edge=4.
        f=np.array([0,1,4,10])
        p=1j*f
        results=bessel_sensitivity(1,edge,1e-5,f,normalization='delay')
        assert_allclose(results['derivative'],p/(edge+p)**2,atol=7e-12)
        assert_allclose(results['delay_derivative'],(f**2-edge**2)/(edge**2+f**2)**2,atol=6e-12)
        with self.assertRaises(ValueError):
            bessel_sensitivity(1, edge, .1, f, edge_index=1)

    def test_noise_figure_sweep_preserves_prior_gain_and_source_temperature(self):
        stages=(RFStage('LNA',10,2),RFStage('Mixer',-4,6))
        output=noise_figure_sweep(stages,1,[3,6,12],1e3,source_temperature_k=30,required_snr_db=7)
        for fig,row in zip(output['figures_db'],output['noise']):
            noise_temperature=30+290*(10**.2-1)+29*(10**(fig/10)-1)
            independent=10*np.log10(1.380649e-23*noise_temperature*1e6)
            self.assertAlmostEqual(row.sensitivity_dbm,independent+7)
        self.assertEqual(output['stage'],'Mixer')
        with self.assertRaises(ValueError):
            noise_figure_sweep(stages,2,[0,6,12],1)

    def test_component_and_velocity_sweeps_respect_geometry_and_budget(self):
        f=17e6
        design,=synthesize_matching('quarter_wave',f,50,100,velocity_factor=.8)
        heights=[.75,.8,.9]
        result=matching_sweep(design,'velocity_factor',heights,[f])
        theta=.8/np.asarray(heights)*np.pi/2
        tangent=np.tan(theta)
        line=np.sqrt(5000)
        zin=line*(100+1j*line*tangent)/(line+1j*100*tangent)
        assert_allclose(result.reflection[:,0],(zin-50)/(zin+50),atol=5e-16)
        reactive=matching_sweep(design,'reactance_ohm',[-4,0,2],[f])
        z=5000/(100+1j*np.array([-4,0,2]))
        assert_allclose(reactive.reflection[:,0],(z-50)/(z+50),atol=5e-16)
        lengths=dict(design.elements)['line_m']*np.array([.5,1,2])
        changed=matching_sweep(design,'line_m',lengths,[f])
        tangent=np.tan(np.pi/2*np.array([.5,1,2]))
        zin=line*(100+1j*line*tangent)/(line+1j*100*tangent)
        assert_allclose(changed.reflection[:,0],(zin-50)/(zin+50),atol=5e-16)
        with self.assertRaises(ValueError):
            matching_sweep(design,'line_m','2',[f])
        with self.assertRaises(ResourceLimitError):
            matching_sweep(design,'line_m',np.arange(513),[f])
        with self.assertRaises(ResourceLimitError):
            matching_sweep(design,'line_m',np.arange(512),np.arange(3000)+f)

    def test_link_campaign_reuses_checkpoint_rng_batches_and_provenance(self):
        f=3e9
        budget=link_budget(-170,PropagationSpec(gain_db=-4),1,carrier_hz=f)
        scenario=LinkUncertainty('Ruido de enlace',budget,propagation_std_db=3,
                                 gain_std_db=4,noise_level_std_db=2)
        with tempfile.TemporaryDirectory() as directory:
            first=Path(directory)/'interrupted'
            second=Path(directory)/'independent'
            event=threading.Event()
            options={'seed':42,'replicas':16,'samples':64,'batch':4}

            def cancel(percent):
                if percent>=50:
                    event.set()

            with self.assertRaises(OperationCancelled):
                link_campaign([scenario],first,context=ExecutionContext(progress=cancel,cancel=event),**options)
            partial=load_campaign(first)
            self.assertEqual(len(partial.replicas),8)
            self.assertEqual(partial.report['status'],'incomplete')
            resumed=link_campaign([scenario],first,**options)
            repeat=link_campaign([scenario],second,**options)
            self.assertEqual(resumed.replicas,repeat.replicas)
            self.assertEqual(resumed.fingerprint,repeat.fingerprint)
            settings=json.loads(resumed.spec.scientific_context)
            self.assertEqual(settings['scenarios'][0]['budget']['carrier_hz'],f)
            self.assertAlmostEqual(resumed.report['summaries'][0]['theory']['value'],budget.margin_db)
            self.assertLess(abs(resumed.report['summaries'][0]['value']-budget.margin_db),.6)
            prob=link_campaign([scenario],Path(directory)/'probability',metric='probability',**options)
            theoretical=.5*(1+math.erf(budget.margin_db/np.sqrt(58)))
            self.assertAlmostEqual(prob.report['summaries'][0]['theory']['value'],theoretical)
            with self.assertRaisesRegex(ValueError,'otra configuración'):
                link_campaign([LinkUncertainty('Ruido de enlace',budget,propagation_std_db=np.sqrt(29))],
                              first,**options)
        historical=CampaignSpec((Scenario('Normal',Distribution('normal',{'mean':0,'std':1})),),'mean',42)
        self.assertNotIn('scientific_context',historical.document())
        with self.assertRaises(ValueError):
            link_campaign([scenario],'.',metric='median',seed=2)
        with self.assertRaises(ValueError):
            link_campaign([scenario.name],'.',seed=2)
        with self.assertRaises(ValueError):
            link_campaign([LinkUncertainty('',budget,1)],'.',seed=2)
        with self.assertRaises(ValueError):
            link_campaign([LinkUncertainty('Sin incertidumbre',budget)],'.',seed=2)


if __name__=='__main__':
    unittest.main()
