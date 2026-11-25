"""Draft copies and Fourier results through the real variant selector."""
import math

import numpy as np
import sympy as sp
from scipy.integrate import quad

from signallab_pc.cas_engine import restore
from signallab_pc.model import Signal
from signallab_pc.result_expressions import ExpressionResult, send_expression
from signallab_pc.symbolic import N, W, parse
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class FourierVariantContracts(DesktopSessionFixture):
    def test_continuous_window_copies_impulses_at_both_ends_to_algebraic_fourier(self):
        numerical = ('fourier',1)
        algebraic = ('fourier_symbolic',0)
        window = self.window()
        window.open_tool(ROUTES[numerical])
        field = window.pages[ROUTES[numerical]].context.source
        field.expression.setText('cos(2*t)+2*DiracDelta(t)+DiracDelta(t-1)')
        field.origin.setText('0')
        field.step.setText('1/8')
        field.count.setText('9')
        window.variant_strip.select(algebraic)
        panel = window.pages[ROUTES[algebraic]].panel
        self.assertIn('soporte finito',window.statusBar().currentMessage())
        self.assertTrue(any('pesos de Dirac' in text for text in panel._input_conditions))
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=15000)
        key,result = panel.last
        self.assertTrue(result['evaluated'])
        exact = restore(result['cas_encoded']) if 'cas_encoded' in result else parse(result['result'])
        dc = sp.limit(exact,W,0) if exact.subs(W,0).is_finite is not True else exact.subs(W,0)
        self.assertAlmostEqual(complex(dc.evalf()),3+math.sin(2)/2,places=11)
        for frequency in (-1.7,0.35):
            ordinary = quad(lambda t: math.cos(2*t)*np.exp(-1j*frequency*t),0,1,complex_func=True)[0]
            self.assertAlmostEqual(complex(exact.subs(W,frequency).evalf()),
                                   ordinary+2+np.exp(-1j*frequency),places=11)
        self.assertIn('pesos de Dirac',panel.report.toPlainText())
        self.assertEqual(window.project.get(key)['request']['input_conditions'],list(panel._input_conditions))

    def test_dtft_variant_maps_finite_sample_indices_and_keeps_dft_inverse_separate(self):
        numerical = ('basic','dft')
        algebraic = ('dtft_symbolic',0)
        window = self.window()
        window.open_tool(ROUTES[numerical])
        field = window.pages[ROUTES[numerical]].first
        field.mode.setCurrentIndex(0)
        field.expression.setText('n+3')
        field.origin.setText('-3')
        field.count.setText('4')
        window.variant_strip.select(algebraic)
        panel = window.pages[ROUTES[algebraic]].panel
        self.assertEqual(panel.lower.text(),'-3')
        self.assertEqual(parse(panel.upper.text()).doit(),0)
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        result = panel.last[1]
        transform = restore(result['cas_encoded']) if 'cas_encoded' in result else parse(result['result'])
        for frequency in (0.,.3,1.2):
            expected = sum((n+3)*np.exp(-1j*frequency*n) for n in range(-3,1))
            self.assertAlmostEqual(complex(transform.subs(W,frequency).evalf()),expected,places=12)
        window.variant_strip.select(('basic','idft'))
        self.assertIn('N coeficientes X[k]',window.statusBar().currentMessage())
        self.assertEqual(field.origin.text(),'-3')
        before = len(window.project.headers())
        window.variant_strip.select(('fourier',1))
        self.assertEqual(len(window.project.headers()),before)

    def test_dtft_variant_keeps_an_analytic_draft_when_switching_from_samples(self):
        numerical = ('fourier',0)
        algebraic = ('dtft_symbolic',0)
        window = self.window()
        window.open_tool(ROUTES[algebraic])
        target = window.pages[ROUTES[algebraic]].panel
        target.expression.setText('impulse(n-2)')
        window.variant_strip.select(numerical)
        source = window.pages[ROUTES[numerical]].context.source
        samples = Signal([3,1,4],origin=-1)
        source.set_source(samples,window.publish(samples,operation='Muestras importadas'))
        window.variant_strip.select(algebraic)
        self.assertIn('no define una fórmula analítica única',window.statusBar().currentMessage())
        self.assertTrue(window.variant_strip.copy_button.isHidden())
        self.assertEqual(target.expression.text(),'impulse(n-2)')

    def test_inverse_copy_rejects_wrong_units_and_nonperiodic_grid_without_replacing_draft(self):
        numerical = ('inverse_dtft',0)
        algebraic = ('dtft_symbolic',1)
        window = self.window()
        window.open_tool(ROUTES[algebraic])
        target = window.pages[ROUTES[algebraic]].panel
        target.expression.setText('2*cos(w)')
        window.open_tool(ROUTES[numerical])
        panel = window.pages[ROUTES[numerical]].panel
        field = panel.source
        field.expression.setText('cos(w)')
        field.frequency_units.setCurrentText('rad/s')
        window.variant_strip.select(algebraic)
        self.assertEqual(target.expression.text(),'2*cos(w)')
        self.assertIn('no se convierten',window.statusBar().currentMessage())
        window.open_tool(ROUTES[numerical])
        field.frequency_units.setCurrentText('rad/muestra')
        field.origin.setText('-pi')
        field.count.setText('11')
        field.step.setText('pi/10')
        window.variant_strip.select(algebraic)
        self.assertIn('cubrir un período',window.statusBar().currentMessage())
        self.assertEqual(target.expression.text(),'2*cos(w)')

        window.open_tool(ROUTES[numerical])
        field.count.setText('21')
        panel.start.setText('-2')
        panel.count.setText('5')
        window.variant_strip.select(algebraic)
        window.variant_strip.copy_button.click()
        self.assertEqual(target.start.text(),'-2')
        self.assertEqual(target.count.text(),'5')
        self.assertEqual(target._frequency_origin,'-pi')
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        answer = target.last[1]
        exact = restore(answer['cas_encoded'])
        self.assertEqual([sp.simplify(exact.subs(N,n)) for n in range(-2,3)],
                         [0,sp.S.Half,0,sp.S.Half,0])
        self.assertEqual(field.expression.text(),'cos(w)')

    def test_inverse_ctft_preserves_conditions_only_on_the_copied_frequency_interval(self):
        numerical = ('fourier',3)
        algebraic = ('fourier_symbolic',1)
        window = self.window()
        origin = window.project.add({'result':{'result':'1/(1+w^2)','evaluated':True,
                     'output_variable':'w','frequency_units':'rad/s','frequency_condition':'Ne(w,0)'}})
        window.open_tool(ROUTES[algebraic])
        target = window.pages[ROUTES[algebraic]].panel
        target.load_expression(ExpressionResult('exp(-t)','t'))
        self.assertIn('espera una expresión en w',self.info.call_args.args[-1])
        target.load_expression(ExpressionResult('cos(w)','w',units='rad/muestra'))
        self.assertIn('No se convierte',self.info.call_args.args[-1])
        send_expression(window,origin,'fourier_inverse')
        window.variant_strip.select(numerical)
        field = window.pages[ROUTES[numerical]].context.source
        self.assertEqual(field._expression_origin[1],origin)
        field.origin.setText('-1')
        field.count.setText('5')
        field.step.setText('1/2')
        window.variant_strip.select(algebraic)
        window.variant_strip.copy_button.click()
        validity = parse(target._frequency_condition)
        self.assertIs(sp.simplify(validity.subs(W,0)),sp.false)
        self.assertIs(sp.simplify(validity.subs(W,2)),sp.true)
        self.assertEqual(target._expression_origin[1],origin)
        finite = parse(target.expression.text())
        self.assertEqual(sp.simplify(finite.subs(W,2)),0)
        self.assertEqual(sp.simplify(finite.subs(W,sp.S.Half)),sp.Rational(4,5))
