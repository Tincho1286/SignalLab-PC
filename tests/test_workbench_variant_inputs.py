"""Draft handoffs remain explicit across related tools with different outputs."""
import numpy as np

from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.result_expressions import ExpressionResult
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class VariantInputContracts(DesktopSessionFixture):
    def test_discrete_series_reuses_full_period_definition_instead_of_just_the_plot(self):
        route = ROUTES['basic','generate']
        window = self.window()
        window.open_tool(route)
        generator = window.pages[route]
        field = generator.first
        field.expression.setText('2*n+1')
        field.repeat_period.setChecked(True)
        field.period.setText('3')
        field.period_origin.setText('-1')
        field.origin.setText('-3')
        field.count.setText('2')
        window.calculate_active()
        self.wait_for_calculation(window)
        preview = generator.basic_result.result
        self.assertIsNotNone(preview.full_definition)
        np.testing.assert_array_equal(preview.axis,[-3,-2])
        np.testing.assert_array_equal(preview.values,[1,3])
        headers = window.project.headers('signal')
        key = headers[-1]['id']
        series_route = ROUTES['fourier',5]
        window.send_signal(preview,key,series_route)
        page = window.pages[series_route]
        window.calculate_active()
        self.wait_for_calculation(window)
        coefficients = page.panel.result
        energies = np.asarray([1,3,-1])
        expected = [sum(energies*np.exp(-2j*np.pi*k*np.arange(-3,0)/3))/3 for k in range(3)]
        self.assertEqual(coefficients.metadata['period_samples'],3)
        np.testing.assert_allclose(coefficients.values,expected,atol=1e-14)

    def test_generate_a_continuous_waveform_from_samples_of_one_period(self):
        route = ROUTES['basic','generate']
        window = self.window()
        window.open_tool(route)
        generator = window.pages[route]
        generator.source_domain.setCurrentIndex(1)
        field = generator.first
        field.mode.setCurrentIndex(1)
        field.samples.setText('1,3')
        field.repeat_period.setChecked(True)
        field.step.setText('1/2')
        field.origin.setText('-1/2')
        field.period_origin.setText('0')
        field.count.setText('5')
        window.calculate_active()
        self.wait_for_calculation(window)
        result = generator.basic_result.result
        self.assertIn('RepeatSamples',result.full_definition)
        np.testing.assert_array_equal(result.axis,[-0.5,0,0.5,1,1.5])
        np.testing.assert_array_equal(result.values,[3,1,3,1,3])
        self.assertEqual(result.units,'s')
        self.assertIsNotNone(generator.basic_result.expression_key)

    def test_sum_and_product_keep_both_inputs_and_their_distinct_intervals(self):
        first = ('basic','sum')
        second = ('signal_product',0)
        window = self.window()
        window.open_tool(ROUTES[first])
        summing = window.pages[ROUTES[first]].panel
        x = Signal([2,3,4],origin=-1)
        v = Signal([5,-2,6],origin=0)
        x_key = window.publish(x,operation='Entrada x')
        v_key = window.publish(v,operation='Entrada v')
        summing.first.set_source(x,x_key)
        summing.second.set_source(v,v_key)
        window.calculate_active()
        self.wait_for_calculation(window)
        np.testing.assert_array_equal(summing.result.axis,[-1,0,1,2])
        np.testing.assert_array_equal(summing.result.values,[2,8,2,6])

        window.variant_strip.select(second)
        product = window.pages[ROUTES[second]].panel
        self.assertEqual(product.input_tabs[0].currentIndex(),1)
        self.assertEqual(product.first.loaded_reference_id,x_key)
        self.assertEqual(product.second.loaded_reference_id,v_key)
        self.assertIsNone(product.result)
        window.calculate_active()
        self.wait_for_calculation(window)
        np.testing.assert_array_equal(product.result.axis,[-1,0,1])
        np.testing.assert_array_equal(product.result.values,[0,15,-8])

        product.swap_inputs()
        self.assertEqual(product.first.loaded_reference_id,v_key)
        self.assertEqual(product.second.loaded_reference_id,x_key)
        window.variant_strip.select(first)
        self.assertEqual(summing.first.loaded_reference_id,x_key)
        window.variant_strip.copy_button.click()
        self.assertEqual(summing.first.loaded_reference_id,v_key)
        self.assertEqual(summing.second.loaded_reference_id,x_key)
        window.calculate_active()
        self.wait_for_calculation(window)
        np.testing.assert_array_equal(summing.result.values,[2,8,2,6])
        headers = window.project.headers()
        self.assertEqual(headers[-1]['parents'],[v_key,x_key])

    def test_periodic_and_global_measures_share_the_formula_but_not_edited_provenance(self):
        global_key = ('expression_measures','global')
        periodic_key = ('expression_measures','periodic')
        window = self.window()
        window.open_tool(ROUTES[global_key])
        global_panel = window.pages[ROUTES[global_key]].panel
        text = '2*cos(pi*n/2)'
        origin = window.project.add({'result':{'result':text,'evaluated':True,'output_variable':'n'}})
        global_panel.load_expression(ExpressionResult(text,'n',('n entero',)),origin)
        window.variant_strip.select(periodic_key)
        periodic = window.pages[ROUTES[periodic_key]].panel
        self.assertEqual(periodic.domain.currentIndex(),1)
        self.assertEqual(periodic.request()['input_conditions'],['n entero'])
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        self.assertEqual(periodic.period.text(),'4')
        self.assertEqual(periodic.last[1]['period_energy']['exact'],'8')
        self.assertEqual(periodic.last[1]['energy']['status'],'divergent')
        self.assertEqual(periodic.last[1]['mean_square']['exact'],'2')
        self.assertEqual(window.project.headers()[-1]['parents'],[origin])

        periodic.expression.setText('3*cos(pi*n)')
        window.variant_strip.select(global_key)
        window.variant_strip.copy_button.click()
        self.assertEqual(global_panel.request()['input_conditions'],[])
        self.assertIsNone(global_panel.parent_id)
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        self.assertEqual(global_panel.last[1]['energy']['status'],'divergent')
        self.assertEqual(global_panel.last[1]['mean_square']['exact'],'9')
        self.assertEqual(window.project.headers()[-1]['parents'],[])

    def test_frequency_to_temporal_retains_system_clock_but_rejects_loaded_advances(self):
        analysis_key = ('system_analysis',0)
        temporal_key = ('systems',9)
        window = self.window()
        window.open_tool(ROUTES[analysis_key])
        panel = window.pages[ROUTES[analysis_key]].panel
        ordinary = Transfer([2],[1,-0.5],sample_period_s=0.125)
        ordinary_key = window.publish(ordinary,operation='Sistema causal')
        panel.set_system(ordinary,ordinary_key)
        window.variant_strip.select(temporal_key)
        temporal = window.pages[ROUTES[temporal_key]].panel
        self.assertEqual(temporal._preserved_system.sample_period_s,0.125)
        self.assertEqual(temporal.parent_id, ordinary_key)

        window.open_tool(ROUTES[analysis_key])
        advanced = Transfer([1],[1,-0.25],advance=1,sample_period_s=0.25)
        panel.set_system(advanced,window.publish(advanced,operation='Sistema con adelanto'))
        window.variant_strip.select(temporal_key)
        self.assertIn('realización causal',window.statusBar().currentMessage())
        self.assertTrue(window.variant_strip.copy_button.isHidden())
        self.assertEqual(temporal._preserved_system.sample_period_s,0.125)
        self.assertEqual(temporal.parent_id,ordinary_key)

    def test_gain_to_phase_respects_domain_and_the_selected_reconstruction_mode(self):
        gain_key = ('course_tools','gain')
        phase_key = ('course_tools','phase')
        window = self.window()
        window.open_tool(ROUTES[gain_key])
        gain = window.pages[ROUTES[gain_key]].panel
        continuous = Transfer([2],[1,1],'analog')
        gain.set_system(continuous,window.publish(continuous,operation='Sistema RC'))
        window.variant_strip.select(phase_key)
        phase = window.pages[ROUTES[phase_key]].panel
        self.assertIn('necesita H(z)',window.statusBar().currentMessage())
        self.assertIsNone(phase.parent_id)

        def phase_mode(key):
            select = phase.fields['phase_mode']
            select.setCurrentIndex(select.findData(key))

        phase_mode('reconstruct')
        window.variant_strip.select(gain_key)
        self.assertIn('datos de módulo o fase independientes',window.statusBar().currentMessage())
        digital = Transfer([1,-1.5],[1,-0.25],sample_period_s=0.2)
        origin = window.publish(digital,operation='Sistema digital')
        gain.set_system(digital,origin)
        window.variant_strip.select(phase_key)
        self.assertTrue(window.variant_strip.copy_button.isHidden())
        self.assertIsNone(phase.parent_id)
        phase_mode('factor')
        window.variant_strip.select(gain_key)
        window.variant_strip.select(phase_key)
        window.variant_strip.copy_button.click()
        self.assertEqual(phase.parent_id,origin)
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        minimum,allpass,complement = phase.items
        frequencies = np.array([0.13,0.75,2.9])
        np.testing.assert_allclose(minimum.response(frequencies)*allpass.response(frequencies),
                                   digital.response(frequencies),rtol=1e-13)
        np.testing.assert_allclose(allpass.response(frequencies)*complement.response(frequencies),1,rtol=1e-13)
        self.assertAlmostEqual(abs(minimum.poles_zeros()[0][0]),2/3)
        self.assertTrue(all(value.sample_period_s==0.2 for value in phase.items))
