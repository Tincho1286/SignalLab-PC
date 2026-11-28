import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.rf_application import RFRequest, run_rf, store_rf
from signallab_pc.rf_network import RFNetwork
from signallab_pc.rf_storage import load_network
from signallab_pc.session import load
from signallab_pc.touchstone import read_touchstone


class RFApplicationTests(unittest.TestCase):
    def test_headless_cli_matches_python_and_reopens_existing_network(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            request_file=root/'request.json'
            touchstone=root/'sample.s2p'
            touchstone.write_text('# MHz S RI R 50\n10 .1 0 .8 -.3 .02 0 -.1 .1\n',encoding='ascii')
            request=RFRequest('renormalize',{'reference_ohm':[50,75]})
            request_file.write_text(json.dumps(request.document()),encoding='utf-8')
            output=root/'candidate.slproj'
            helper=(
                "import sys; from importlib.abc import MetaPathFinder\n"
                "class NoQt(MetaPathFinder):\n"
                " def find_spec(self, fullname, *args):\n"
                "  if fullname.startswith(('PySide','PyQt','shiboken')): raise AssertionError(fullname)\n"
                "sys.meta_path.insert(0, NoQt())\n"
                "from signallab_pc.__main__ import main\n"
                "raise SystemExit(main(['rf', *sys.argv[1:]]))"
            )
            def invoke(*arguments):
                return subprocess.run([sys.executable,'-B','-X','utf8','-c',helper,*map(str,arguments)],
                                      capture_output=True,text=True,encoding='utf-8',timeout=30)

            cli=invoke('--request',request_file,'--network',touchstone,'--output',output)
            self.assertEqual(cli.returncode,0,cli.stderr)
            receipt=json.loads(cli.stdout)
            project,_=load(output)
            result=run_rf(request,(read_touchstone(touchstone),))
            self.assertEqual(project.get(receipt['result_id']),result.document())
            assert_array_equal(load_network(project,receipt['product_id']).values,result.network.values)
            request_file.write_text(json.dumps(RFRequest('analyze').document()),encoding='utf-8')
            second=root/'analysis.json'
            check=invoke('--request',request_file,'--source-session',output,'--record-id',receipt['product_id'],
                         '--output',second)
            self.assertEqual(check.returncode,0,check.stderr)
            converted=json.loads(check.stdout)
            self.assertEqual(converted['product_id'],receipt['product_id'])
            self.assertIn(receipt['product_id'],load(second)[0]._records[converted['result_id']]['parents'])
            broken=invoke('--request',request_file,'--output',output)
            self.assertEqual(broken.returncode,1)
            self.assertEqual(load(output)[0].get(receipt['result_id']),result.document())

    def test_publish_cancel_with_no_partial_records_and_guard_mutations(self):
        project=Project()
        original=RFNetwork([10,20],[[[.3]],[[.5]]])
        result=run_rf(RFRequest('analyze'),(original,))
        self.assertEqual(result.document(vectors=True)['result']['scattering']['values'],[[[[.3,0]]],[[[.5,0]]]])
        event=Event()
        event.set()
        with self.assertRaises(OperationCancelled):
            store_rf(project,result,context=ExecutionContext(cancel=event))
        self.assertEqual(project.headers(),[])
        receipt=store_rf(project,result)
        self.assertEqual(receipt['source_ids'],[receipt['product_id']])
        self.assertEqual(len(project.headers()),2)
        source=Signal([1,2],-1)
        zoom=run_rf(RFRequest('zoom',{'start':-1,'stop':1,'count':3}),(source,))
        saved=store_rf(project,zoom)
        assert_array_equal(project.get(saved['product_id']).axis,[-1,0,1])
        assert_allclose(project.get(saved['product_id']).values,[2+np.exp(-1j),3,2+np.exp(1j)])
        zoom.signal.values[1]=44
        with self.assertRaisesRegex(ValueError,'resultado RF cambió'):
            store_rf(project,zoom)
        source.values[0]=7
        with self.assertRaisesRegex(ValueError,'entradas ya no coinciden'):
            store_rf(project,zoom)

    def test_error_boundary_and_structured_operation_inputs(self):
        for document in ({}, {'schema':True,'operation':'line','parameters':{}},
                         {'schema':1,'operation':'else','parameters':{}},
                         {'schema':1,'operation':'match','parameters':{'x':float('nan')}}):
            with self.subTest(document=document),self.assertRaises(ValueError):
                RFRequest.from_document(document)
        for request,inputs in ((RFRequest('define',{}),()), (RFRequest('czt'),()),
                               (RFRequest('line'),()), (RFRequest('noise',{'stages':[None]}),()),
                               (RFRequest('device',{'iip3_dbm':0}),())):
            with self.subTest(request=request),self.assertRaises(ValueError):
                run_rf(request,inputs)
        r=run_rf(RFRequest('match',{'frequencies_hz':[1e9], 'method':'quarter_wave','frequency_hz':1e9,
                                    'source_ohm':50,'load_ohm_pairs':[100,0]}))
        assert_allclose(r.data['responses'][0].reflection,[0],atol=1e-15)
        self.assertTrue(r.network is not None)

    def test_boundary_network_operations_and_result_lineage(self):
        through=RFNetwork([1,3],np.broadcast_to([[0,1],[1,0]],(2,2,2)))
        cutoff=run_rf(RFRequest('terminate',{'keep':[0],'load_ohm_pairs':[100,25]}),(through,))
        assert_allclose(cutoff.network.values[:,0,0],(50+25j)/(150+25j))
        reflection=run_rf(RFRequest('terminate',{'keep':[1],'reflection_pairs':[0,.3]}),(through,))
        assert_allclose(reflection.network.values[:,0,0],.3j)
        direct=run_rf(RFRequest('cascade'),(through,through))
        assert_allclose(direct.network.values,through.values)
        sampled=run_rf(RFRequest('interpolate',{'frequencies_hz':[2]}),(through,))
        self.assertEqual(sampled.network.frequencies_hz[0],2)
        model=run_rf(RFRequest('convert',{'representation':'ABCD'}),(through,))
        net=run_rf(RFRequest('define',{'frequencies_hz':[2],'value_pairs':[[[[50,0]]]],
                                      'representation':'Z'}))
        self.assertEqual(net.network.values[0,0,0],50)
        assert_allclose(model.network.values[0],np.eye(2))
        with self.assertRaisesRegex(ValueError,'redes'):
            run_rf(RFRequest('cascade'),(Signal([1]),through))
        with self.assertRaisesRegex(ValueError,'sin entradas'):
            run_rf(RFRequest('noise'),(through,))
        with self.assertRaises(TypeError):
            run_rf({})
        with self.assertRaisesRegex(ValueError,'no coincide'):
            store_rf(Project(),direct,source_ids=('a','b'))

    def test_units_and_new_live_services(self):
        line=run_rf(RFRequest('line',{'frequencies_hz':[1e6,2e6],'length_m':0,'load_ohm_pairs':[150,0]}))
        assert_allclose(line.data.input_impedance_ohm,150)
        rlgc={'frequencies_hz':[1e6,2e6],'length_m':.1,'resistance_ohm_per_m':0,'conductance_s_per_m':0,
              'inductance_h_per_m':250e-9,'capacitance_f_per_m':1e-10}
        assert_allclose(run_rf(RFRequest('rlgc',rlgc)).data.characteristic_ohm,50)
        configs=[None,{'kind':'free_space','distance_m':100},{'kind':'log_distance','distance_m':100,
                                                          'reference_loss_db':30}]
        for model in configs:
            specification={'transmitted_dbm':0,'carrier_hz':1e9,'bandwidth_hz':1e6,'propagation':{'model':model},
                           'transmit_stages':[{'name':'Cable','loss_db':2}],
                           'receive_stages':[{'name':'LNA','gain_db':15,'noise_figure_db':3}]}
            result=run_rf(RFRequest('link',specification)).document()
            self.assertEqual(result['result']['eirp_dbm'],-2)
        for model in ('free_space',{'kind':'invalid'}):
            with self.assertRaises(ValueError):
                run_rf(RFRequest('link',{'propagation':{'model':model}}))
        with self.assertRaises(ValueError):
            run_rf(RFRequest('link',{'propagation':[]}))
        noise=run_rf(RFRequest('noise',{'bandwidth_hz':1e6})).data
        self.assertAlmostEqual(noise.input_noise_dbm,-113.975187194228)
        device=run_rf(RFRequest('device',{'gain_db':18,'iip3_dbm':0,'input_per_tone_dbm':-20}))
        self.assertAlmostEqual(device.data.im3_per_product_dbm,-42)
        signal=Signal([1,2],-2)
        czt=run_rf(RFRequest('czt',{'count':4,'radius_ratio':2,'angle_step_rad':0}),(signal,))
        assert_allclose(czt.data.samples.values,[3,8,24,80])
        project=Project()
        w=run_rf(RFRequest('window',{'window':'boxcar','length':2}))
        b=run_rf(RFRequest('bessel',{'order':1,'characteristic_rad_s':4}))
        self.assertEqual(store_rf(project,w)['source_ids'],[])
        bessel=store_rf(project,b)['product_id']
        self.assertAlmostEqual(abs(project.get(bessel).response([4])[0]),1/np.sqrt(2))

    def test_console_rejects_invalid_destinations_and_loads_signal_records(self):
        from signallab_pc.rf_cli import main
        from signallab_pc.session import empty_workspace, save
        from signallab_pc.storage import save_json
        with TemporaryDirectory() as directory:
            root=Path(directory)
            request=root/'request.json'
            request.write_text(json.dumps(RFRequest('zoom',{'start':-1,'stop':1,'count':3}).document()),encoding='utf-8')
            signal=Signal([1,2],-1)
            sig_file=root/'signal.json'
            save_json(signal,sig_file)
            source=Project()
            key=source.add(signal)
            session=root/'origin.slproj'
            save(session,source,empty_workspace())
            out=root/'out.json'
            def invoke(*values):
                sink=StringIO()
                with redirect_stdout(sink),redirect_stderr(sink):
                    status=main(['--request',str(request),*map(str,values)])
                return status,sink.getvalue()
            for arguments in (('--output',request),('--source-session',session,'--output',out),
                              ('--record-id',key,'--output',out)):
                with self.subTest(arguments=arguments):
                    code,_=invoke(*arguments)
                    self.assertEqual(code,1)
            for arguments in (('--signal',sig_file),('--source-session',session,'--record-id',key)):
                code,summary=invoke(*arguments,'--output',out)
                self.assertEqual(code,0,summary)
                receipt=json.loads(summary)
                expected=[2+np.exp(-1j),3,2+np.exp(1j)]
                assert_allclose(load(out)[0].get(receipt['product_id']).values,expected)
            code,_=invoke('--signal',sig_file,'--output',out,'--max-work-bytes',1)
            self.assertEqual(code,1)


if __name__=='__main__':
    unittest.main()
