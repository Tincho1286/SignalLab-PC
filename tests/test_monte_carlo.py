import csv
import json
import math
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

import numpy as np

from signallab_pc import session
from signallab_pc.campaign_files import campaign_writer
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.monte_carlo import (CampaignSpec, Scenario, campaign_spec, campaign_trajectory, export_campaign_csv,
                                    load_campaign, run_campaign)
from signallab_pc.monte_carlo_bootstrap import bootstrap_record
from signallab_pc.probability import Distribution
from signallab_pc.resources import ResourceLimitError
from signallab_pc.stochastic_cli import main


def event_campaign(**options):
    scenario = Scenario('Eventos',Distribution('bernoulli',{'p':0.}))
    return CampaignSpec((scenario,),'probability',123,samples=20,replicas=8,batch=4,low=1,high=1,**options)


class MonteCarloTests(unittest.TestCase):
    def test_native_campaign_writer_excludes_a_separate_process_and_retries(self):
        worker = '''
from pathlib import Path
import sys
from signallab_pc.campaign_files import campaign_writer
try:
    with campaign_writer(Path(sys.argv[1])):
        print("acquired")
except ValueError as error:
    print(error)
    raise SystemExit(2)
'''
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            for contents in (b'',b'\x00'):
                path = folder/'campaign.lock'
                path.write_bytes(contents)

                def start_worker():
                    return subprocess.run([sys.executable,'-B','-X','utf8','-c',worker,str(folder)],
                                          capture_output=True,encoding='utf-8',timeout=20)

                with campaign_writer(folder):
                    contender = start_worker()
                    self.assertEqual(contender.returncode,2,contender.stderr)
                    self.assertIn('Otro proceso',contender.stdout)
                reopened = start_worker()
                self.assertEqual(reopened.returncode,0,reopened.stderr)
                self.assertEqual(reopened.stdout.strip(),'acquired')
                self.assertEqual(path.read_bytes(),contents)

    def test_zero_observed_events_have_exact_positive_upper_bound(self):
        with TemporaryDirectory() as folder:
            result=run_campaign(event_campaign(),folder)
        summary=result.report['summaries'][0]
        self.assertEqual(summary['successes'],0)
        self.assertEqual(summary['trials'],160)
        self.assertAlmostEqual(summary['interval'][1],1-.025**(1/160))
        self.assertEqual(summary['theory']['value'],0)
        self.assertEqual(result.report['status'],'max_replicas')

    def test_precision_stop_accounts_for_planned_binomial_looks(self):
        with TemporaryDirectory() as folder:
            spec=event_campaign(target_half_width=.04)
            result=run_campaign(spec,folder)
            self.assertEqual(load_campaign(folder),result)
        self.assertEqual(result.report['status'],'target_precision')
        self.assertEqual(len(result.replicas),4)
        self.assertAlmostEqual(result.report['summaries'][0]['interval'][1],1-.0125**(1/80))

    def test_common_random_numbers_pair_shifted_normal_models_replica_by_replica(self):
        rows=tuple(Scenario(name,Distribution('normal',{'mean':location,'std':2.}))
                   for name,location in [('Nivel base',0.),('Nivel desplazado',4.)])
        spec=CampaignSpec(rows,'mean',9,samples=128,replicas=8,batch=4,common_random_numbers=True)
        with TemporaryDirectory() as common, TemporaryDirectory() as separate:
            paired=run_campaign(spec,common)
            independent=run_campaign(replace(spec,common_random_numbers=False),separate)
        np.testing.assert_allclose(np.diff(paired.replicas),4.,atol=1e-14)
        self.assertAlmostEqual(paired.report['differences'][0]['standard_error'],0.)
        self.assertGreater(independent.report['differences'][0]['standard_error'],.01)
        counts, estimated=campaign_trajectory(paired,points=4)
        self.assertEqual((counts[0],counts[-1]),(1,8))
        np.testing.assert_allclose(estimated[-1],[item['value'] for item in paired.report['summaries']])

    def test_variance_merges_at_chunk_boundary_and_preserves_degrees_of_freedom(self):
        spec=CampaignSpec((Scenario('Ruido',Distribution('normal',{'mean':4.,'std':2.})),),
                          'variance',5,samples=17001,replicas=2,batch=2)
        with TemporaryDirectory() as folder:
            result=run_campaign(spec,folder)
        expected=[np.var(np.random.default_rng(np.random.SeedSequence(5,spawn_key=(i,0))).normal(4.,2.,17001),
                         ddof=1) for i in range(2)]
        np.testing.assert_allclose(np.asarray(result.replicas)[:,0],expected,atol=1e-13)
        self.assertAlmostEqual(result.report['summaries'][0]['theory']['value'],4.)

    def test_unfinished_single_replica_has_prediction_and_no_false_interval(self):
        scenario=Scenario('Constante',Distribution('discrete_uniform',{'low':7,'high':7}))
        spec=CampaignSpec((scenario,),'mean',10,samples=12,replicas=4,batch=1)
        with TemporaryDirectory() as folder:
            for stop_at in (0,25):
                event=Event()
                context=ExecutionContext(cancel=event,progress=lambda percent:event.set() if percent>=stop_at else None)
                with self.assertRaises(OperationCancelled):
                    run_campaign(spec,folder,context)
                observed=load_campaign(folder)
                self.assertEqual(len(observed.replicas),stop_at//25)
                if stop_at:
                    self.assertIsNone(observed.report['summaries'][0]['interval'])
                    self.assertEqual(observed.report['summaries'][0]['value'],7.)
                else:
                    counts,_=campaign_trajectory(observed)
                    self.assertEqual(counts.size,0)
        with TemporaryDirectory() as folder:
            result=run_campaign(event_campaign(),folder)
            counts,values=campaign_trajectory(result,4)
            np.testing.assert_array_equal(values[:,0],np.zeros(len(counts)))

    def test_interrupt_resume_conflict_and_export_reproduce_fresh_replicas(self):
        spec=event_campaign()
        with TemporaryDirectory() as interrupted, TemporaryDirectory() as reference:
            folder=Path(interrupted)
            stop=Event()
            context=ExecutionContext(cancel=stop,progress=lambda value:stop.set() if value>=62 else None)
            with self.assertRaises(OperationCancelled):
                run_campaign(spec,folder,context)
            partial=load_campaign(folder)
            self.assertEqual(partial.report['status'],'incomplete')
            self.assertEqual(len(partial.replicas),4)
            with campaign_writer(folder,operation='estudio',filename='monte-carlo.lock'):
                with self.assertRaisesRegex(ValueError,'Otro proceso'):
                    run_campaign(spec,folder)
            with self.assertRaisesRegex(ValueError,'otra configuración'):
                run_campaign(replace(spec,seed=124),folder)
            resumed=run_campaign(spec,folder)
            fresh=run_campaign(spec,reference)
            self.assertEqual(resumed.fingerprint,fresh.fingerprint)
            self.assertEqual(resumed.replicas,fresh.replicas)
            path=folder/'replicas.csv'
            export_campaign_csv(resumed,path)
            with path.open(encoding='utf-8',newline='') as handle:
                rows=list(csv.reader(handle))
            self.assertEqual(rows[0],['replica','Escenario: Eventos'])
            self.assertEqual(rows[-1],['8','0'])
            with self.assertRaises(ValueError):
                export_campaign_csv(resumed,folder/'monte-carlo.json')

    def test_modified_block_and_gap_fail_verification(self):
        with TemporaryDirectory() as case:
            folder=Path(case)
            run_campaign(event_campaign(),folder)
            path=folder/'batch-0000000000.json'
            document=json.loads(path.read_text(encoding='utf-8'))
            document['rows'][0][0]=1
            path.write_text(json.dumps(document),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'huella del bloque'):
                load_campaign(folder)
            path.rename(folder/'interrumpido.json')
            with self.assertRaisesRegex(ValueError,'secuencia'):
                load_campaign(folder)

    def test_rejects_unfit_estimators_and_resources_before_writing(self):
        rows=(Scenario('Cauchy',Distribution('cauchy',{'location':0.,'scale':1.})),)
        with self.assertRaisesRegex(ValueError,'momento poblacional'):
            CampaignSpec(rows,'mean',0)
        with self.assertRaises(ValueError):
            campaign_spec({'metric':'mean','seed':1})
        with TemporaryDirectory() as folder:
            location=Path(folder)/'new'
            with self.assertRaises(ResourceLimitError):
                run_campaign(event_campaign(),location,ExecutionContext(max_work_bytes=1))
            self.assertFalse(location.exists())

    def test_user_configuration_rejects_ambiguous_event_and_invalid_forecast(self):
        scenario=Scenario('Normal',Distribution('normal',{'mean':0,'std':1}))
        for options in (
            {'scenarios':[]}, {'scenarios':[scenario,scenario]}, {'metric':'median'},
            {'common_random_numbers':1}, {'confidence':1}, {'metric':'probability','low':1,'high':0},
            {'low':0}, {'samples':9_007_199_254_740_992},
        ):
            with self.subTest(options=options),self.assertRaises(ValueError):
                CampaignSpec(**({'scenarios':[scenario],'metric':'mean','seed':3}|options))
        with self.assertRaises(ValueError):
            Scenario('\n',scenario.distribution)
        with self.assertRaises(ValueError):
            Scenario('Sin distribución',None)

    def test_interrupted_archive_refuses_unbound_or_invalid_batches(self):
        spec=event_campaign()
        with TemporaryDirectory() as directory:
            folder=Path(directory)
            checkpoint=folder/'monte-carlo.json'
            batch=folder/'batch-0000000000.json'
            checkpoint.write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Formato'):
                load_campaign(folder)
            checkpoint.unlink()
            batch.write_text('[]',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'sin su definición'):
                run_campaign(spec,folder)
            batch.unlink()
            run_campaign(spec,folder)
            for raw,match in (('[]','debe ser un objeto'), ('{"rows":[]}','cantidad de réplicas'),
                              ('{"rows":[[],[0],[0],[0]]}','por escenario')):
                batch.write_text(raw,encoding='utf-8')
                with self.assertRaisesRegex(ValueError,match):
                    load_campaign(folder)
            document=json.loads(checkpoint.read_text(encoding='utf-8'))
            document['sha256']='0'*64
            checkpoint.write_text(json.dumps(document),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'huella de la campaña'):
                load_campaign(folder)

    def test_cli_builds_and_reopens_project_and_loads_existing_campaign(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            model,checkpoint,output=(root/name for name in ('monte.json','checkpoint','result.slproj'))
            model.write_text(json.dumps(event_campaign().document()),encoding='utf-8')
            for arguments in (['--model',str(model)],[]):
                stdout,stderr=StringIO(),StringIO()
                with redirect_stdout(stdout),redirect_stderr(stderr):
                    code=main(['monte-carlo','--directory',str(checkpoint),'--output',str(output),*arguments])
                self.assertEqual(code,0,stderr.getvalue())
                saved,_=session.load(output)
                payload=saved.get(json.loads(stdout.getvalue())['result_id'])
                self.assertEqual(payload['replicate_summaries'],[[0]]*8)

    def test_cli_rejects_campaign_destinations_before_creating_or_resuming_files(self):
        with TemporaryDirectory() as directory:
            folder=Path(directory)
            model, checkpoint=folder/'definition.json', folder/'campaign'
            model.write_text(json.dumps(event_campaign().document()),encoding='utf-8')
            base=['monte-carlo','--model',str(model),'--directory',str(checkpoint)]
            output=folder/'results.slproj'
            for args in (['--output',str(checkpoint)], ['--output',str(checkpoint/'monte-carlo.json')],
                         ['--output',str(output),'--csv',str(checkpoint/'monte-carlo.json')],
                         ['--output',str(output),'--csv',str(output)]):
                stderr=StringIO()
                with self.subTest(args=args), redirect_stderr(stderr):
                    self.assertEqual(main([*base,*args]),1)
                    self.assertIn('Elegí',stderr.getvalue())
                    self.assertFalse(checkpoint.exists())
                    self.assertFalse(output.exists())
            csv_file=checkpoint/'replicas.csv'
            stdout,stderr=StringIO(),StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main([*base,'--output',str(output),'--csv',str(csv_file)]),0,stderr.getvalue())
            self.assertEqual(len(load_campaign(checkpoint).replicas),8)
            self.assertIn('Escenario: Eventos',csv_file.read_text(encoding='utf-8'))


class BootstrapTests(unittest.TestCase):
    def test_iid_and_moving_block_quantiles_match_direct_reference(self):
        values=np.array([-2.,1.,1.5,3.,2.,8.,7.])
        source=Signal(values,origin=-5)
        for block in (1,3):
            result=bootstrap_record(source,metric='variance',seed=3,replicas=19,block_length=block,confidence=.9)
            expected=[]
            for replicate in range(19):
                generator=np.random.default_rng(np.random.SeedSequence(3,spawn_key=(replicate,)))
                draws=generator.integers(0,len(values)-block+1,math.ceil(len(values)/block))
                made=np.concatenate([values[start:start+block] for start in draws])[:len(values)]
                expected.append(sum((made-made.mean())**2)/(len(made)-1))
            np.testing.assert_allclose(result['replicate_estimates'],expected)
            np.testing.assert_allclose(result['interval'],np.quantile(expected,[.05,.95]))
            self.assertAlmostEqual(result['estimate'],np.var(values,ddof=1))

    def test_degenerate_resampling_cannot_certify_zero_or_one_probability(self):
        for low,high in ((-5.,-1.),(0.,10.)):
            result=bootstrap_record(Signal([0,1,5,2]),metric='probability',low=low,high=high,seed=1,replicas=8)
            self.assertIsNone(result['interval'])
            self.assertIn('incertidumbre',result['scope'])
        with self.assertRaisesRegex(ValueError,'serie real'):
            bootstrap_record(Signal([1j,.5]),seed=6)
        with self.assertRaises(ValueError):
            bootstrap_record(Signal([1]),seed=6)

    def test_rejects_invalid_metric_event_and_confidence(self):
        source=Signal([-1,0,1,3])
        for options in ({'metric':'quartile'},{'metric':'probability','low':3,'high':2},
                        {'low':0},{'confidence':1}):
            with self.subTest(options=options),self.assertRaises(ValueError):
                bootstrap_record(source,seed=1,replicas=8,**options)
