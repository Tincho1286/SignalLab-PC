import unittest,json,tempfile
from pathlib import Path
import numpy as np
from signallab_pc.filters import Transfer
from signallab_pc.system_import import load_transfer
from signallab_pc.control import interconnect
from signallab_pc.state_space import StateModel

class SystemFlowTests(unittest.TestCase):
    def test_round_trip_documents_bom_sos_and_advance(self):
        systems=[Transfer([1+2j,0,.25],[1,-.4]),Transfer([1,.2],[1,-.3],advance=2),Transfer.from_sos([[.2,.1,.05,1,-.4,.1],[1,0,0,1,-.2,0]])]
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'filtro señal.json'
            for model in systems:
                path.write_text(json.dumps(model.to_document()),encoding='utf-8-sig');loaded=load_transfer(path)
                np.testing.assert_allclose(loaded.response(np.linspace(-np.pi,np.pi,257)),model.response(np.linspace(-np.pi,np.pi,257)),atol=2e-14)
                self.assertEqual(loaded.advance,model.advance)
                if model.sos is not None:np.testing.assert_array_equal(loaded.sos,model.sos)

    def test_bad_documents_reject_missing_or_contradictory_definition(self):
        valid=Transfer([1],[1],advance=2).to_document()
        examples=[]
        missing=dict(valid);missing.pop('advance');examples.append(missing)
        version=dict(valid,version=1);examples.append(version)
        examples.extend([dict(valid,b=[[True,0]]),dict(valid,b=[[float('inf'),0]]),dict(valid,b=[1]),dict(valid,advance=1.5)])
        mismatch=Transfer.from_sos([[1,0,0,1,-.5,0]]).to_document();mismatch['b']=[[2,0]];examples.append(mismatch)
        for example in examples:
            with self.assertRaises(ValueError):Transfer.from_document(example)

    def test_advanced_connections_match_complete_responses(self):
        first=Transfer([.6,-.2],[1,-.5],advance=2);second=Transfer([0,.4],[1,.2]);w=np.linspace(.03,3.,301)
        a,b=first.response(w),second.response(w)
        expected={'cascade':a*b,'parallel':a+b,'negative_feedback':a/(1+a*b),'positive_feedback':a/(1-a*b)}
        for mode,values in expected.items():
            result=interconnect(first,second,mode)
            np.testing.assert_allclose(result.response(w),values,atol=2e-13,rtol=2e-12)
        self.assertEqual(first.advance,2);np.testing.assert_array_equal(second.b,[0,.4])

    def test_feedback_advance_sos_delay_cancellation_and_state_guard(self):
        result=interconnect(Transfer([1,1],[1]),Transfer([-1],[1]),'negative_feedback')
        self.assertEqual(result.advance,1);w=np.array([.1,.5,1.])
        np.testing.assert_allclose(result.response(w),-np.exp(1j*w)-1,atol=2e-14)
        with self.assertRaises(ValueError):interconnect(Transfer([1],[1]),Transfer([1],[1]),'positive_feedback')
        delayed=Transfer.from_sos([[0,1,0,1,-.5,0]])
        advanced=Transfer([1],[1],advance=1);cascade=interconnect(delayed,advanced)
        self.assertEqual(cascade.advance,0);self.assertIsNotNone(cascade.sos)
        np.testing.assert_allclose(cascade.response(w),1/(1-.5*np.exp(-1j*w)),atol=2e-14)
        self.assertEqual(delayed.sos[0,0],0)
        with self.assertRaises(ValueError):StateModel.from_transfer(advanced,1)

if __name__=='__main__':unittest.main()
