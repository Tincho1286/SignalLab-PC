"""Exchange reliability: independent exchange and convergence invariants."""
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
    def test_matlab_arithmetic_uses_matlab_precedence_and_matrix_whitespace(self):
        from signallab_pc.matlab_import import read_script
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'syntaxis.m'
            path.write_text(
                "a=[1,2]; b=[3,4]; c=a+b'; d=(a+b)'; "
                "p=2^3^2; q=2^(3^2); x=[1 + 2]; y=[1 -2]; "
                "stop=0:0.1:0.299999999999; exact=0:0.1:0.3; "
                "inside=sin(0:pi/2:pi);",encoding='utf-8')
            variables=read_script(path)
        assert_array_equal(variables['c'],[[4,5],[5,6]])
        assert_array_equal(variables['d'],[[4],[6]])
        self.assertEqual(variables['p'],64)
        self.assertEqual(variables['q'],512)
        assert_array_equal(variables['x'],[[3]])
        assert_array_equal(variables['y'],[[1,-2]])
        assert_allclose(variables['stop'],[[0,.1,.2]],rtol=0,atol=1e-15)
        assert_allclose(variables['exact'],[[0,.1,.2,.3]],rtol=0,atol=1e-15)
        assert_allclose(variables['inside'],[[0,1,0]],rtol=0,atol=1e-15)

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
    def test_fft_convolutions_and_correlation_with_extreme_compensating_scales(self):
        from signallab_pc.operations import linear_convolution,linear_correlation,circular_convolution,correlation
        large=Signal(np.full(6000,1e306));small=Signal(np.full(6000,1e-306))
        for operation,index in ((linear_convolution,5999),(linear_correlation,5999),(circular_convolution,0)):
            with self.subTest(operation=operation.__name__):
                assert_allclose(operation(large,small).values[index],6000,rtol=2e-13,atol=1e-10)
        assert_allclose(correlation(large,small,circular=True,normalization='mean').values,1,atol=1e-13)

    def test_group_delay_jump_is_independent_of_gain(self):
        from signallab_pc.analytic_frequency import smooth_frequency_derivative
        from signallab_pc.symbolic import parse
        for gain in ('1','1e-12'):
            _,jumps=smooth_frequency_derivative(
                parse(f'{gain}*Piecewise((1,w<0),(2,True))'),np.array([-1.,0.,1.]))
            assert_array_equal(jumps,[False,True,False])

    def test_frequency_mask_does_not_broaden_repeated_polynomial_zeros(self):
        import sympy as sp
        from signallab_pc.analytic_frequency import _condition_mask
        from signallab_pc.symbolic import W
        axis=np.array([0.,1e-9,1e-8,1e-6])
        for order in (1,2,6):
            assert_array_equal(_condition_mask(sp.Ne(W**order,0),axis),[False,True,True,True])
        assert_array_equal(_condition_mask(sp.Ne(sp.sin(W),0),np.array([0.,.5,np.pi])),[False,True,False])

    def test_sampling_clock_cannot_be_mixed_or_fabricated(self):
        from signallab_pc.operations import linear_correlation,circular_convolution,correlation
        from signallab_pc.sampling import resample,resample_rational
        one=Signal([1,2,3],metadata={'sample_rate_hz':100})
        other=Signal([1,2,3],metadata={'sample_rate_hz':200})
        for operation in (linear_correlation,correlation,circular_convolution):
            with self.assertRaisesRegex(ValueError,'distintas tasas'):operation(one,other)
        self.assertNotIn('time_start_s',resample(one,2,'decimate',1).metadata)
        self.assertEqual(resample(one,2,'decimate',1).metadata['sample_rate_hz'],50)
        with self.assertRaisesRegex(ValueError,'reinterpretación'):resample_rational(one,1,1,rate=200)
        self.assertEqual(resample_rational(one,1,1,rate=200,override_clock=True).metadata['sample_rate_hz'],200)

    def test_inverse_fourier_report_and_cas_picker_retain_data_roles(self):
        from signallab_pc.fourier import ictft
        from signallab_pc.result_summary import signal_summary
        source=Signal([1,1,1],-1,1,'rad/s',domain='frequency')
        inverse=ictft(source,-1,1,3)
        self.assertIn('Expresión de la aproximación calculada',signal_summary(inverse).plain_text())
        self.assertFalse(can_send({'cas_answer':{'text':'formula'}}))

    def test_cas_resolves_report_samples_after_project_reimport(self):
        from signallab_pc.result_journal import snapshot
        project=Project()
        signal=Signal([1,2+3j],origin=-2)
        signal_key=project.add(signal)
        host=SimpleNamespace(project=project,published_value_id=lambda value:signal_key)
        report=project.add({'report':'Respuesta','calculated_data':snapshot(signal,host)},parents=[signal_key])
        self.assertTrue(can_send(project.get(report)))
        expected=payload(signal)
        self.assertEqual(payload(project.get(report),host),expected)
        host.published_value_id=lambda value:None
        self.assertEqual(payload(snapshot(signal,host),host),expected)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.json';project.export_record(report,path)
            reloaded=Project();self.assertEqual(reloaded.merge(path),2)
            loaded=reloaded.headers()[-1]['id']
            self.assertEqual(payload(reloaded.get(loaded),SimpleNamespace(project=reloaded)),expected)

    def test_unresolved_formula_cannot_be_imported_as_result_metadata(self):
        for result in (
            {'evaluated':False,'output_variable':'w','result':'Sum(a[n], (n, 0, oo))','frequency_points':501},
            {'evaluated':True,'branches':[{'expression':'1'},{'expression':'0'}]},
        ):
            with self.subTest(result=result):
                record={'request':{'operation':'dtft_expression'},'result':result}
                self.assertFalse(can_send(record))
                self.assertIsNone(payload(record))

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

    def test_cas_preserves_matrix_nonfinite_markers_and_integrates_wrapped_band(self):
        import sympy as sp
        from signallab_pc.cas_engine import restore
        from signallab_pc.result_journal import snapshot
        table={'calculated_data':snapshot(np.array([1.,np.nan,np.inf]),None)}
        result=import_result(dict(cell=1,payload=payload(table)))
        values=restore(result['encoded_value'])
        self.assertEqual(values.shape,(3,1));self.assertIs(values[1,0],sp.nan);self.assertEqual(values[2,0],sp.oo)
        definition=execute(dict(operation='frequency_definition',domain='discrete',period_origin='0',
                                expression='where(w<=pi/3,1,0)'))['definition']
        result=import_result(dict(cell=1,payload=payload({'result':definition})))
        area=calculate(dict(cell=2,state=result['state'],source='integrate(r1,(w,-5*pi,5*pi))'))
        self.assertEqual(restore(area['state']['results']['2']),5*sp.pi/3)

    def test_period_origin_and_folded_bands_round_trip(self):
        import sympy as sp
        from signallab_pc.symbolic import N
        from signallab_pc.cas_engine import restore
        for origin,expected in [('0',sp.Rational(1,6)),('-pi',sp.Rational(2,3)),('-pi/6',sp.Rational(1,4))]:
            result=execute(dict(operation='frequency_definition',expression='where(w<=pi/3,1,0)',
                                domain='discrete',period_origin=origin))
            inverse=execute(dict(operation='inverse_dtft_expression',expression=result['definition']['result']))
            for solved in (result['inverse'],inverse):
                self.assertEqual(restore(solved['cas_encoded']).subs(N,0),expected)
        direct=execute(dict(operation='inverse_dtft_expression',period_origin='0',
                            expression='where(w<=pi/3,1,0)'))
        self.assertEqual(restore(direct['cas_encoded']).subs(N,0),sp.Rational(1,6))
        response=execute(dict(operation='frequency_definition',domain='discrete',period_origin='0',
                              expression='1/(1-exp(-i*w)/2)'))['definition']
        self.assertTrue(execute(dict(operation='inverse_dtft_expression',expression=response['result']))['z_equivalent'])
        expression='sin(pi*(n-2)/5)/(pi*(n-2))*exp(i*9*pi*n/10)'
        spectrum=execute(dict(operation='dtft_expression',expression=expression,lower='-oo',upper='oo'))
        inverse=execute(dict(operation='inverse_dtft_expression',expression=spectrum['result']))
        self.assertTrue(inverse['evaluated'])
        samples=execute(dict(operation='inverse_dtft_samples',expression=spectrum['result'],solved=inverse,start=-3,count=9))
        expected=np.sinc((np.arange(-3,6)-2)/5)*np.exp(1j*.9*np.pi*np.arange(-3,6))/5
        assert_allclose([complex(*v) for v in samples['samples']],expected,atol=3e-15)

    def test_dtft_inverse_keeps_full_spectral_line_at_period_seam(self):
        from signallab_pc.symbolic import N
        from signallab_pc.cas_engine import restore
        for expression in ('2*pi*Dirac(w-pi)','2*pi*Dirac(w+pi)','pi*(Dirac(w-pi)+3*Dirac(w+pi))'):
            result=execute(dict(operation='inverse_dtft_expression',expression=expression))
            self.assertEqual([restore(result['cas_encoded']).subs(N,n) for n in (-2,-1,0,1,2)],[1,-1,1,-1,1])

    def test_inverse_rejects_missing_frequency_bands_and_keeps_isolated_limits(self):
        from signallab_pc.inverse_dtft import inverse_dtft
        for operation in ('inverse_dtft_expression','inverse_fourier_angular'):
            with self.assertRaisesRegex(ValueError,'tramos faltantes'):
                execute(dict(operation=operation,expression='1',input_frequency_condition='w>0'))
        result=execute(dict(operation='inverse_dtft_expression',expression='1',input_frequency_condition='Ne(w,0)'))
        self.assertTrue(result['evaluated'])
        spectrum=Signal([1]*4,0,np.pi/2,'rad/muestra',domain='frequency',
                        metadata={'source_frequency_condition':'Ne(w,0)'})
        with self.assertRaisesRegex(ValueError,'fuera del dominio'):
            inverse_dtft(spectrum,0,4)

    def test_inverse_fft_final_values_remain_finite_and_clock_follows_indices(self):
        from signallab_pc.operations import idft
        from signallab_pc.inverse_dtft import inverse_dtft
        from signallab_pc.fourier import dtft
        from signallab_pc.frequency_filter import analyze
        spectrum=Signal([1e308]*4,-np.pi,np.pi/2,'rad/muestra',domain='frequency')
        for signal in (idft(Signal([1e308]*4)),inverse_dtft(spectrum,0,4),analyze(spectrum,'discrete',0,4,1)[0][1]):
            assert_array_equal(signal.values,[1e308,0,0,0])
        source=Signal([1,0,0],5,metadata={'sample_rate_hz':100,'time_start_s':8.})
        restored=inverse_dtft(dtft(source,-np.pi,np.pi,65),3,6)
        self.assertEqual(restored.metadata['sample_rate_hz'],100)
        self.assertAlmostEqual(restored.metadata['time_start_s'],7.98)

    def test_ideal_conversion_preserves_clock_and_rejects_empty_sampled_band(self):
        from signallab_pc.ideal_conversion import convert_response
        from signallab_pc.frequency_filter import analyze
        with self.assertRaisesRegex(ValueError,'no muestrea'):
            convert_response('1',.01,'impulse',32,.05)
        response=convert_response('1',.1,'impulse',33,10)['signals'][0]
        source=Signal([1,0],3)
        values,_=analyze(response,'discrete',-2,5,1,source)
        self.assertEqual(values[1].metadata['sample_rate_hz'],10)
        self.assertAlmostEqual(values[1].metadata['time_start_s'],-.2)
        self.assertAlmostEqual(values[-1].metadata['time_start_s'],.3)
        with self.assertRaisesRegex(ValueError,'no coincide'):
            analyze(response,'discrete',0,3,1,source.copy_with(metadata={'sample_rate_hz':20}))

    def test_quantization_tracks_selected_roc_and_trig_masks_keep_close_points(self):
        import sympy as sp
        from signallab_pc.symbolic import W
        from signallab_pc.analytic_frequency import _condition_mask
        from signallab_pc.filters import Transfer
        from signallab_pc.precision import Encoding,quantize_coefficients
        from signallab_pc.transfer_plane import convergence
        source=Transfer([1],[1,-.74],roc={'mode':'radius','radius':.5})
        stored=quantize_coefficients(source,Encoding('fixed',2,1))['system']
        self.assertEqual(convergence(stored)['outer'],.5)
        self.assertEqual(source.roc['radius'],.5)
        axis=np.array([0.,1e-50,1e-16,1e-8,np.pi,2*np.pi])
        assert_array_equal(_condition_mask(sp.Ne(sp.cos(W),1),axis),[False,True,True,True,True,False])
        assert_array_equal(_condition_mask(sp.Ne(sp.sin(W),0),axis),[False,True,True,True,False,False])

if __name__=='__main__':unittest.main()
