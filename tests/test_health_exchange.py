"""Operation Health: independent exchange and convergence invariants."""
import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from numpy.testing import assert_allclose,assert_array_equal
from scipy.io import savemat
from signallab_pc.matlab_import import MatlabFile,make_signal
from signallab_pc.model import Signal
from signallab_pc.storage import save_csv,load_csv
from signallab_pc.project import Project
from signallab_pc.symbolic import execute
from signallab_pc.cas_transfer import payload,can_send
from signallab_pc.cas_import import import_result
from signallab_pc.cas_engine import calculate
from signallab_pc.result_expressions import expression_result

class HealthExchangeContracts(unittest.TestCase):
    def imported(self,unit='rad/muestra',cell=1,state=None):
        p=dict(kind='expression',source='Piecewise((1, abs(w)<pi/2),(0,True))',variable='w',frequency_units=unit,frequency_condition='True',conditions=['Dominio de origen conservado.'])
        return import_result(dict(cell=cell,state=state,payload=p))
    def test_mat_file_preserves_large_integer_axis(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'large.mat';axis=np.arange(3,dtype=np.int64)+(2**53+1)
            savemat(path,dict(n=axis,x=np.array([1.,2.,3.])))
            result=make_signal(MatlabFile(path),'x',0,'discrete','n')
            assert_array_equal(result.axis,axis);self.assertEqual(result.origin,2**53+1)
    def test_mat_axis_is_never_rounded_to_consecutive_indices(self):
        for axis in (np.array([0.,1.0000000001,2.]),np.array([2**53,2**53+1,2**53+2],dtype=float)):
            data=SimpleNamespace(path=Path('fixture.mat'),load={'x':np.ones(3),'n':axis}.__getitem__)
            with self.assertRaisesRegex(ValueError,'consecutivos'):make_signal(data,'x',0,'discrete','n')
    def test_mat_rejects_empty_and_multidimensional_channels(self):
        for values in (np.array([]),np.zeros((2,2,2))):
            data=SimpleNamespace(path=Path('fixture.mat'),load=lambda name:values)
            with self.assertRaises(ValueError):make_signal(data,'x',0,'discrete')
    def test_own_csv_preserves_descending_axis_and_complex_values(self):
        with tempfile.TemporaryDirectory() as directory:
            for domain,units in [('continuous','s'),('frequency','rad/muestra')]:
                original=Signal([1,2j,3],1,-.5,units,'descending',domain,metadata={'key':'value'})
                path=Path(directory)/(domain+'.csv');save_csv(original,path);restored=load_csv(path)
                assert_array_equal(restored.axis,original.axis);assert_array_equal(restored.values,original.values);self.assertEqual(restored.metadata,original.metadata)
    def test_invalid_signal_metadata_is_rejected_at_boundary(self):
        for metadata in ([],None,'bad'):
            with self.assertRaisesRegex(ValueError,'diccionario'):Signal([1],metadata=metadata)
    def test_malformed_project_does_not_modify_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';project=Project();project.add(Signal([1]));before=project.records()
            cases=[[],dict(format='signallab-project',schema_version=2,records=[dict(id='bad',kind='signal',data={})]),dict(format='signallab-project',schema_version=2,records=[dict(id='bad',kind='calculation',data={},title='bad',parents=[[]])])]
            for document in cases:
                path.write_text(json.dumps(document))
                with self.assertRaises(ValueError):project.merge(path)
                self.assertEqual(project.records(),before)
    def test_signal_json_reports_invalid_shape_and_missing_fields(self):
        from signallab_pc.storage import load_json
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'signal.json'
            for document in ([],dict(format='signallab-signal',schema_version=1),dict(format='signallab-signal',schema_version=1,samples=[1],origin=0,step=1,units='n',name='bad',domain='discrete')):
                path.write_text(json.dumps(document))
                with self.assertRaises(ValueError):load_json(path)

    def test_cas_rewrites_and_named_values_preserve_frequency_coordinate(self):
        answer=self.imported()
        for cell,command in enumerate(['simplify(r1)','a:=ans','expand(a)','ans()'],2):
            answer=calculate(dict(state=answer['state'],cell=cell,source=command))
            result=expression_result(dict(cas_answer=answer));self.assertEqual(result.units,'rad/muestra');self.assertEqual(result.variable,'w')
        reimported=import_result(dict(cell=9,payload=payload(dict(cas_answer={**answer,'encoded_value':answer['state']['results']['5']}))))
        self.assertEqual(reimported['frequency_units'],'rad/muestra')
    def test_cas_mixed_frequency_units_do_not_get_a_silent_default(self):
        first=self.imported();second=self.imported('rad/s',2,first['state'])
        mixed=calculate(dict(state=second['state'],cell=3,source='r1+r2'))
        self.assertEqual(mixed['frequency_units'],'incompatible')
        again=calculate(dict(state=mixed['state'],cell=4,source='ans'))
        self.assertEqual(again['frequency_units'],'incompatible')
    def test_cas_cancellation_and_reciprocal_retain_excluded_positions(self):
        from signallab_pc.analytic_frequency import analyze_expression
        first=self.imported()
        for command in ('simplify(r1/r1)','1/r1'):
            answer=calculate(dict(state=first['state'],cell=2,source=command))
            self.assertNotEqual(answer['frequency_condition'],'True')
            request=dict(operation='system_frequency_expression',domain='digital',expression=answer['expression'],source_calculation=dict(cas_answer=answer))
            exact,data=analyze_expression(execute(request),request,np.array([0.,1.,2.]))
            assert_allclose(data.response[:2],1);self.assertTrue(np.isnan(data.response[2]))
    def test_cas_assumptions_survive_simplification_and_later_purge(self):
        from signallab_pc.analytic_frequency import analyze_expression
        first=import_result(dict(cell=1,payload=dict(kind='expression',source='abs(w)',variable='w',frequency_units='rad/muestra',conditions=[])))
        assumed=calculate(dict(state=first['state'],cell=2,source='assume(w>0)'))
        answer=calculate(dict(state=assumed['state'],cell=3,source='simplify(r1)'))
        purged=calculate(dict(state=answer['state'],cell=4,source='purge(w)'))
        reused=calculate(dict(state=purged['state'],cell=5,source='r3'))
        for record in (answer,reused):
            request=dict(operation='system_frequency_expression',domain='digital',expression=record['expression'],source_calculation=dict(cas_answer=record))
            exact,data=analyze_expression(execute(request),request,np.array([-1.,0.,1.]))
            self.assertTrue(np.isnan(data.response[:2]).all());assert_allclose(data.response[2],1)
    def test_untyped_cas_frequency_keeps_assumption_for_explicit_unit_selection(self):
        first=calculate(dict(cell=1,source='assume(w,integer)'))
        answer=calculate(dict(state=first['state'],cell=2,source='simplify(cos(2*pi*w))'))
        self.assertEqual(answer.get('coordinate_variable'),'w');self.assertNotEqual(answer.get('frequency_condition'),'True')

    def test_conditioned_grid_keeps_real_zeros_and_all_excluded_positions(self):
        grid=execute(dict(operation='expression_grid',expression='0*w',condition='Ne(w,0)',allow_undefined=True,variable='w',start=-1,stop=1,count=3))
        self.assertEqual(grid['samples'],[[0.,0.],None,[0.,0.]]);self.assertEqual(grid['undefined_count'],1)
        pole=execute(dict(operation='expression_grid',expression='1/(w-1)',allow_undefined=True,variable='w',start=0,stop=2,count=3))
        self.assertEqual(pole['samples'],[[-1.,0.],None,[1.,0.]])
    def test_grid_with_undefined_positions_is_not_sent_as_partial_cas_data(self):
        grid=execute(dict(operation='expression_grid',expression='1/w',allow_undefined=True,variable='w',start=-1,stop=1,count=3))
        self.assertFalse(can_send(grid))
        with self.assertRaisesRegex(ValueError,'no se descartan'):payload(grid)
    def test_bilateral_z_report_and_cas_export_use_calculated_fourier_result(self):
        from signallab_pc.result_summary import transform_summary
        request=dict(operation='z_expression',expression='sin(0.5*pi*(n-4))/(pi*(n-4))',lower='-oo',upper='oo');result=execute(request)
        text=transform_summary(request,result).plain_text();self.assertNotIn('Sum(',text);self.assertIn('DTFT',text)
        exported=payload(dict(request=request,result=result));self.assertEqual(exported['variable'],'w');self.assertNotIn('Sum(',exported['source'])


    def test_cas_equivalent_systems_preserve_roc_and_clock_through_reimport(self):
        from signallab_pc.filters import Transfer
        from signallab_pc.transform_context import result_roc,result_period
        for domain,roc,period in [('digital',{'mode':'left'},.01),('digital',{'mode':'radius','radius':1},.02),('analog',{'mode':'line','sigma':-2},None)]:
            original=Transfer([1],[1,-.5],domain=domain,roc=roc,sample_period_s=period)
            result=import_result(dict(cell=1,payload=payload(original)))
            for cell,source in [(2,'simplify(r1)'),(3,'foo:=factor(r2)'),(4,'foo')]:
                result=calculate(dict(cell=cell,state=result['state'],source=source));record={'cas_answer':result}
                self.assertEqual(result_roc(record),roc);self.assertEqual(result_period(record),period)
            result=import_result(dict(cell=5,payload=payload(record)))
            self.assertEqual(result_roc({'cas_answer':result}),roc);self.assertEqual(result_period({'cas_answer':result}),period)

    def test_cas_changed_system_binding_and_assumption_do_not_inherit_roc(self):
        from signallab_pc.filters import Transfer
        from signallab_pc.transform_context import result_roc,result_period
        original=import_result(dict(cell=1,payload=payload(Transfer([1],[1,-.5],roc={'mode':'left'},sample_period_s=.01))))
        for source in ('2*r1','diff(r1,z)','r1/r1','subst(r1,z,2)'):
            result=calculate(dict(cell=2,state=original['state'],source=source));self.assertFalse(result['system_context']['preserved'])
            self.assertIsNone(result_roc({'cas_answer':result}));self.assertIsNone(result_period({'cas_answer':result}))
        binding=calculate(dict(cell=2,state=original['state'],source='z:=2'))
        result=calculate(dict(cell=3,state=binding['state'],source='simplify(r1)'));self.assertFalse(result['system_context']['preserved'])
        p=dict(kind='expression',source='sqrt(z^2)',variable='z',system_roc={'mode':'right'})
        r=import_result(dict(cell=1,payload=p));a=calculate(dict(cell=2,state=r['state'],source='assume(z>0)'))
        changed=calculate(dict(cell=3,state=a['state'],source='simplify(r1)'));self.assertFalse(changed['system_context']['preserved'])

    def test_cas_conflicting_roc_and_clocks_are_not_chosen_arbitrarily(self):
        from signallab_pc.filters import Transfer
        for changed in (dict(roc={'mode':'right'},sample_period_s=.01),dict(roc={'mode':'left'},sample_period_s=.02)):
            state=import_result(dict(cell=1,payload=payload(Transfer([1],[1,-.5],roc={'mode':'left'},sample_period_s=.01))))['state']
            state=import_result(dict(cell=2,state=state,payload=payload(Transfer([1],[1,-.5],**changed))))['state']
            r=calculate(dict(cell=3,state=state,source='r1+r2-r2'));self.assertFalse(r['system_context']['preserved'])

    def test_cas_project_clock_is_explicit_and_survives_export(self):
        from signallab_pc.filters import Transfer
        project=Project();system=Transfer([1],[1,-.5],roc={'mode':'left'},sample_period_s=.01);parent=project.add(system)
        imported=import_result(dict(cell=1,payload=payload(system)))
        same=calculate(dict(cell=2,state=imported['state'],source='simplify(r1)'))
        same_id=project.add({'cas_answer':same},parents=[parent]);self.assertEqual(project.sample_period(same_id),.01)
        changed=calculate(dict(cell=3,state=same['state'],source='2*r2'))
        changed_id=project.add({'cas_answer':changed},parents=[same_id]);self.assertIsNone(project.sample_period(changed_id))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cas.json';project.export_record(same_id,path);loaded=Project();loaded.merge(path)
            self.assertEqual(loaded.sample_period(loaded.records()[-1]['id']),.01)

    def test_nonrational_causal_z_retains_physical_dtft_after_cas(self):
        import sympy as sp
        from signallab_pc.symbolic import W,parse
        from signallab_pc.analytic_frequency import analyze_expression
        request=dict(operation='z_expression',expression='sin(pi*(n-4)/2)/(pi*(n-4))',lower='0',upper='oo')
        record=dict(request=request,result=execute(request));initial=import_result(dict(cell=1,payload=payload(record)))
        answer=calculate(dict(cell=2,state=initial['state'],source='simplify(r1)'));self.assertTrue(answer['system_context']['preserved'])
        value=expression_result({'cas_answer':answer});exact=execute(dict(operation='system_formula',expression=value.source,domain='digital'))
        omega=np.array([0.,float(sp.pi/4),float(sp.pi/2),float(3*sp.pi/4)])
        exact,data=analyze_expression(exact,dict(domain='digital',source_calculation={'cas_answer':answer}),omega)
        self.assertIn('DTFT calculada',exact['frequency_interpretation']);self.assertTrue(np.isnan(data.response[2]))
        want=execute(dict(operation='dtft_expression',expression=request['expression'],lower='0',upper='oo'))
        target=parse(want['result']);assert_allclose(data.response[[0,1,3]],[complex(target.subs(W,w).evalf()) for w in omega[[0,1,3]]],atol=2e-12)

if __name__=='__main__':unittest.main()
