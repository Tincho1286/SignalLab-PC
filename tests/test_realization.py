import unittest
import numpy as np
from scipy import signal
from signallab_pc.filters import Transfer
from signallab_pc.realization import realize_system
from signallab_pc.realization_graph import Block, RealizationGraph, Wire, graph_from_realization
from signallab_pc.state_space import StateModel


class RealizationTests(unittest.TestCase):
    def test_analog_complex_and_cancellation_response(self):
        omega=np.array([.1,.5,1.3,3.])
        for source in (Transfer([1,2],[1,3,2],'analog'),Transfer([2,1+1j],[1,2,1],'analog'),Transfer([1,-1],[1,-1],'analog'),Transfer([0],[1,-1],'analog')):
            value=realize_system(source);model=value.to_model()
            np.testing.assert_allclose(model.response(omega)[:,0,0],source.response(omega),atol=2e-14,rtol=2e-13)
            self.assertEqual(model.states,len(source.a)-1)
        self.assertEqual(realize_system(Transfer([1,-1],[1,-1],'analog')).states,1)
    def test_digital_fir_delays_and_iir_impulses(self):
        impulse=np.r_[1.,np.zeros(29)]
        for source in (Transfer([0,0,2],[1]),Transfer([.2,.5,.2],[1,-.3,.1]),Transfer([1,0,1],[1]),Transfer([1e-30,1],[1,-.2])):
            realization=realize_system(source);model=realization.to_model(.1)
            _,actual,_=model.simulate(impulse)
            np.testing.assert_allclose(actual[:,0],signal.lfilter(source.b,source.a,impulse),atol=1e-15,rtol=2e-14)
            w=np.array([.1,.4,1.,2.]);np.testing.assert_allclose(model.response(w/.1)[:,0,0],source.response(w),atol=2e-14)
        value=realize_system(Transfer([1,0],[1,0]));self.assertEqual(value.states,0)
        value=realize_system(Transfer([1,-.2],[1,-.2]));self.assertEqual(value.states,1)
    def test_sos_preserved_and_state_import_matches_same_realization(self):
        sos=signal.butter(8,[.3,.9],btype='bandpass',fs=2*np.pi,output='sos');source=Transfer.from_sos(sos)
        value=realize_system(source);self.assertTrue(value.cascade);self.assertEqual(len(value.stages),len(sos))
        before=source.sos.copy();model=StateModel.from_transfer(source,.2)
        impulse=np.r_[1.,np.zeros(199)];_,actual,_=model.simulate(impulse)
        np.testing.assert_allclose(actual[:,0],signal.sosfilt(sos,impulse),atol=2e-15,rtol=2e-11)
        np.testing.assert_array_equal(source.sos,before)
        for k,stage in enumerate(value.stages):np.testing.assert_array_equal(stage.a,sos[k,3:]/sos[k,3])
    def test_static_zero_orders_and_explicit_unavailable_cases(self):
        for domain,dt in [('analog',None),('digital',.25)]:
            value=realize_system(Transfer([2j],[1],domain));model=value.to_model(dt)
            self.assertEqual(model.states,0);self.assertEqual(model.D[0,0],2j)
        with self.assertRaises(ValueError):realize_system(Transfer([1,1],[1],'analog'))
        with self.assertRaises(ValueError):realize_system(Transfer([1],[1]),1)
        for dt in (None,0,-1,np.inf):
            with self.assertRaises(ValueError):realize_system(Transfer([1],[1])).to_model(dt)
        with self.assertRaises(ValueError):realize_system(Transfer([1],[1],'analog')).to_model(.1)


class RealizationGraphTests(unittest.TestCase):
    def test_same_source_can_feed_both_sum_ports_without_losing_a_term(self):
        from signallab_pc.realization_equations import summary
        from signallab_pc.symbolic import S

        ports = RealizationGraph.empty('analog').blocks
        blocks = ports + (Block(3, 'transfer', 160, 0, formula='1/(s+1)'), Block(4, 'sum', 380, 0))
        forward = (Wire(1, 3), Wire(3, 4, target_port=1), Wire(4, 2))
        feedback = RealizationGraph('analog', blocks, forward + (Wire(4, 4, target_port=2),))
        self.assertEqual(feedback.transfer(), 1/(2*S+2))
        self.assertIn('V_4(s) = V_3(s) - V_4(s)', summary(feedback).plain_text())
        self.assertIn('2*V_4(s) = V_3(s)', summary(feedback).plain_text())

        cancelled = RealizationGraph('analog', blocks, forward + (Wire(3, 4, target_port=2),))
        self.assertEqual(RealizationGraph.from_document(cancelled.to_document()).transfer(), 0)
        self.assertIn('V_4(s) = V_3(s) - V_3(s)', summary(cancelled).plain_text())
        self.assertIn('V_4(s) = 0', summary(cancelled).plain_text())
        with self.assertRaisesRegex(ValueError, 'mismo puerto'):
            RealizationGraph('analog', blocks, cancelled.wires + (Wire(3, 4),)).connections()

        direct = (Wire(1, 4), Wire(1, 4, -1), Wire(4, 2))
        self.assertEqual(RealizationGraph('analog', ports + (blocks[-1],), direct).transfer(), 0)
        doubled = Block(4, 'sum', 380, 0, input_signs=(1, 1))
        self.assertEqual(RealizationGraph('analog', ports + (doubled,), direct).transfer(), 2)

    def test_sum_ports_keep_their_position_and_apply_independent_signs(self):
        import json
        import sympy as sp
        from signallab_pc.symbolic import S, Z

        wires = (Wire(1, 3), Wire(3, 4), Wire(4, 2), Wire(4, 3, -1))
        for domain, variable in (('analog', S), ('digital', Z)):
            for signs in ((1,-1), (1,1), (-1,-1), (-1,1)):
                with self.subTest(domain=domain, signs=signs):
                    ports = RealizationGraph.empty(domain).blocks
                    blocks = ports + (Block(3,'sum',180,0,input_signs=signs), Block(4,'memory',360,0))
                    graph = RealizationGraph(domain,blocks,wires)
                    expected = signs[0]/(variable-signs[1])
                    restored = RealizationGraph.from_document(json.loads(json.dumps(graph.to_document())))
                    self.assertEqual(restored,graph)
                    self.assertEqual(sp.cancel(restored.transfer()-expected),0)
                    self.assertEqual([wire.sum_port for wire in restored.connections()[3]],[1,2])

    def test_negative_feedback_uses_domain_and_preserves_exact_gain(self):
        from signallab_pc.symbolic import execute, parse, S, Z
        import sympy as sp

        blocks = (Block(1, 'input', 0, 0), Block(2, 'output', 500, 0),
                  Block(3, 'sum', 130, 0), Block(4, 'gain', 270, 0, '1/3'),
                  Block(5, 'memory', 400, 0))
        wires = (Wire(1, 3), Wire(3, 4), Wire(4, 5), Wire(5, 2), Wire(5, 3, -1))
        for domain, variable in (('analog', S), ('digital', Z)):
            graph = RealizationGraph(domain, blocks, wires)
            result = execute({'operation': 'system_realization', 'domain': domain, 'diagram': graph.to_document()})
            self.assertEqual(sp.cancel(parse(result['transfer']) - 1 / (3 * variable + 1)), 0)
            self.assertIn('numeric_b', result)

    def test_export_preserves_parallel_paths_and_pure_delay(self):
        from signallab_pc.symbolic import execute

        for original in (Transfer([0, 0, 2], [1]), Transfer([1, 0, .5], [1, -.25]),
                         Transfer([.25j, 1], [1, 2, 1], 'analog'),
                         Transfer.from_sos([[1, .5, 0, 1, -.25, 0], [0, 1, 0, 1, 0, 0]])):
            value = graph_from_realization(realize_system(original))
            data = execute({'operation': 'system_realization', 'domain': original.domain, 'diagram': value.to_document()})
            system = Transfer([complex(*v) for v in data['numeric_b']], [complex(*v) for v in data['numeric_a']], original.domain)
            omega = np.array([.1, .5, 1.3, 3.])
            np.testing.assert_allclose(system.response(omega), original.response(omega), atol=1e-14)

    def test_transfer_blocks_in_series_and_feedback(self):
        import sympy as sp
        from signallab_pc.symbolic import S, Z

        ports = (Block(1, 'input', 0, 0), Block(2, 'output', 500, 0))
        series = (Wire(1, 3), Wire(3, 4), Wire(4, 2))
        cases = (
            ('analog', '1/(s+1)', '2/(s+3)', 2 / ((S+1)*(S+3))),
            ('digital', 'z^(-1)', '1+z^(-1)/3', (1+1/(3*Z))/Z),
        )
        for domain, first, second, expected in cases:
            blocks = ports + (Block(3, 'transfer', 120, 0, formula=first),
                              Block(4, 'transfer', 250, 0, formula=second))
            graph = RealizationGraph(domain, blocks, series)
            document = graph.to_document()
            self.assertEqual(document['version'], 2)
            self.assertEqual(sp.cancel(RealizationGraph.from_document(document).transfer() - expected), 0)

        feedback = (Wire(1, 3), Wire(3, 4), Wire(4, 3, -1), Wire(4, 2))
        summer = ports + (Block(3, 'sum', 120, 0),)
        graph = RealizationGraph('analog', summer + (Block(4, 'transfer', 250, 0, formula='1/(s+1)'),), feedback)
        self.assertEqual(graph.transfer(), 1 / (S+2))
        with self.assertRaisesRegex(ValueError, 'lazo instantáneo'):
            RealizationGraph('analog', summer + (Block(4, 'transfer', 250, 0, formula='-(s+1)/(s+2)'),), feedback).transfer()

    def test_transfer_blocks_validate_domain_causality_and_clock(self):
        ports = (Block(1, 'input', 0, 0), Block(2, 'output', 500, 0))
        for formula, error in (('1/(s+1)', 'Usá z'), ('z', 'avance'), ('exp(z)', 'racional')):
            blocks = ports + (Block(3, 'transfer', 120, 0, formula=formula),)
            with self.assertRaisesRegex(ValueError, error):
                RealizationGraph('digital', blocks, (Wire(1, 3), Wire(3, 2))).transfer()
        blocks = ports + (Block(3, 'transfer', 120, 0, sample_period_s=.1),
                          Block(4, 'transfer', 250, 0, sample_period_s=.2))
        with self.assertRaisesRegex(ValueError, 'períodos de muestreo'):
            RealizationGraph('digital', blocks, (Wire(1, 3), Wire(3, 4), Wire(4, 2))).transfer()

    def test_singular_instantaneous_feedback_and_unconnected_branch(self):
        from sympy import Rational

        blocks = (Block(1, 'input', 0, 0), Block(2, 'output', 450, 0), Block(3, 'sum', 230, 0))
        direct = (Wire(1, 3), Wire(3, 2))
        with self.assertRaisesRegex(ValueError, 'lazo instantáneo'):
            RealizationGraph('analog', blocks, direct + (Wire(3, 3),)).transfer()
        self.assertEqual(RealizationGraph('analog', blocks, direct + (Wire(3, 3, -1),)).transfer(), Rational(1, 2))
        extra = blocks + (Block(4, 'gain', 140, 100),)
        with self.assertRaisesRegex(ValueError, 'camino hacia la salida'):
            RealizationGraph('analog', extra, direct + (Wire(1, 4),)).transfer()

if __name__=='__main__':unittest.main()
