"""Verified finite inverses and ROC-sensitive transform reuse in the workbench."""
from types import SimpleNamespace

import numpy as np
import sympy as sp

from signallab_pc.cas_engine import restore
from signallab_pc.cas_panel import CAS_ROUTE
from signallab_pc.model import Signal
from signallab_pc.symbolic import N, Z, parse
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class TransformReuseContracts(DesktopSessionFixture):
    def test_loading_library_transform_examples_replaces_stale_input_mode_and_bounds(self):
        from signallab_pc.library_catalog import example_records

        window=self.window()
        route=ROUTES['transform_lab','z']
        window.open_tool(route)
        panel=window.pages[route].panel
        panel.use_finite_input()
        panel.source.entry_modes.select(1)
        panel.source.samples.setText('99,8')
        panel.lower.setText('4')
        panel.upper.setText('7')
        library={example['id']:example for example in example_records()}
        direct=library['z-impulso-desplazado']
        window.open_library_example(direct)
        self.assertEqual(panel.direct_input.currentIndex(),0)
        self.assertEqual(panel.lower.text(),str(direct['request']['lower']))
        self.assertEqual(panel.upper.text(),str(direct['request']['upper']))
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(sp.cancel(parse(panel.last['result'])-Z**-3),0)
        panel.sample_scope.setCurrentIndex(1)
        panel.start.setText('100')
        panel.count.setText('1')
        inverse=library['z-anticausal']
        window.open_library_example(inverse)
        self.assertEqual(panel.roc.currentIndex(),1)
        self.assertEqual(panel.start.text(),str(inverse['request'].get('start',-16)))
        self.assertEqual(panel.count.text(),str(inverse['request'].get('count',65)))
        window.calculate_active()
        self.wait_for_calculation(window)
        exact=restore(panel.last['cas_encoded'])
        for index in range(-3,3):
            expected=-sp.Integer(2)**index if index<0 else 0
            self.assertEqual(sp.simplify(exact.subs(N,index)),expected)

    def test_finite_z_roundtrip_keeps_origin_and_both_cas_destinations(self):
        window=self.window()
        route=ROUTES['transform_lab','z']
        x=Signal([3,2+1j,4],-2,name='Secuencia original')
        source=window.publish(x,operation='Entrada')
        window.send_signal(x,source,route)
        panel=window.pages[route].panel
        window.calculate_active()
        self.wait_for_calculation(window)
        direct=panel.records[panel.record_key()]
        expected=3*Z**2+(2+sp.I)*Z+4
        self.assertEqual(sp.cancel(parse(direct[1]['result'])-expected),0)
        self.assertEqual(window.project.headers()[-1]['parents'],[source])
        panel.prepare_reuse()
        next(action for action in panel.reuse_button.menu().actions() if action.text()=='Z inversa').trigger()
        self.assertEqual(panel.mode.currentIndex(),1)
        self.assertEqual(panel.sample_scope.currentIndex(),1)
        window.calculate_active()
        self.wait_for_calculation(window)
        inverse=panel.records[panel.record_key()]
        saved=panel.output.result_ids[0]
        samples=window.project.get(saved)
        np.testing.assert_array_equal(samples.axis,[-2,-1,0])
        np.testing.assert_array_equal(samples.values,x.values)
        provenance={record['id']:record['parents'] for record in window.project.headers()}
        self.assertEqual(provenance[saved],[inverse[2]])
        self.assertEqual(provenance[inverse[2]],[direct[2]])
        panel.prepare_cas()
        self.assertEqual([action.text() for action in panel.cas_menu.actions()],
                         ['Fórmula de la secuencia','Muestras de la inversa'])
        panel.cas_menu.actions()[1].trigger()
        self.wait_for_calculation(window)
        worksheet=window.pages[CAS_ROUTE]
        matrix=restore(worksheet.state['results']['1'])
        self.assertIsInstance(matrix,sp.MatrixBase)
        self.assertEqual(list(matrix[:,0]),[-2,-1,0])
        np.testing.assert_array_equal([complex(value) for value in matrix[:,1]],x.values)
        self.assertEqual(window.project.headers()[-1]['parents'],[saved])

    def test_explorer_rejects_a_pole_and_applies_a_bilateral_region_to_inverse_and_analysis(self):
        window=self.window()
        route=ROUTES['transform_lab','z']
        window.open_tool(route)
        panel=window.pages[route].panel
        panel.mode.setCurrentIndex(1)
        panel.expression.setText('z/((z-1/2)*(z-2))')
        panel.roc.setCurrentIndex(-1)
        panel.start.setText('-2')
        panel.count.setText('5')
        panel.roc_button.click()
        self.wait_for_calculation(window)
        picker=panel.roc_picker
        self.assertIsNotNone(picker)
        axis=picker.figure.axes[0]
        picker.clicked(SimpleNamespace(inaxes=axis,xdata=2.,ydata=0.,button=1))
        self.assertEqual(picker.choice.currentIndex(),-1)
        self.assertIn('borde',picker.status.text())
        picker.clicked(SimpleNamespace(inaxes=axis,xdata=1.,ydata=0.,button=1))
        self.assertEqual(picker.choice.currentIndex(),1)
        picker.calculate_button.click()
        self.wait_for_calculation(window)
        self.assertEqual(panel.roc.currentIndex(),2)
        exact=restore(panel.records[panel.record_key()][1]['cas_encoded'])
        for n,expected in zip(range(-2,3),[-sp.Rational(1,6),-sp.Rational(1,3),
                                         -sp.Rational(2,3),-sp.Rational(1,3),-sp.Rational(1,6)]):
            self.assertEqual(sp.simplify(exact.subs(N,n)),expected)
        panel.input_reuse_button.menu().actions()[0].trigger()
        analysis=window.pages[ROUTES['system_analysis',0]].panel
        self.assertEqual(analysis.roc_choice.currentIndex(),2)
        analysis.count.setText('17')
        window.calculate_active()
        self.wait_for_calculation(window, timeout_ms=15000)
        data=analysis.frequency_data
        self.assertIsNotNone(data)
        z=np.exp(1j*data.omega)
        np.testing.assert_allclose(data.response,z/((z-.5)*(z-2)),atol=1e-13)
