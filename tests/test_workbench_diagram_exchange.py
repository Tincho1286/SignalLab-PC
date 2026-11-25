"""Editable realization, imported clock and image export contracts."""
import json
from unittest.mock import patch

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QFileDialog, QInputDialog
import sympy as sp

from signallab_pc.filters import Transfer
from signallab_pc.realization import realize_system
from signallab_pc.realization_diagram import RealizationWindow
from signallab_pc.realization_editor import RealizationEditor
from signallab_pc.realization_graph import Block, RealizationGraph, Wire
from signallab_pc.realization_transfer_input import TransferBlockDialog
from signallab_pc.symbolic import S, Z
from test_desktop_session import DesktopSessionFixture


class DiagramExchangeContracts(DesktopSessionFixture):
    def test_cancel_connection_delete_signed_wire_and_restore_gain(self):
        window = self.window()
        editor = RealizationEditor(RealizationGraph.empty('analog'),window,owner=window)
        self.addCleanup(editor.close)
        editor.show()
        self.app.processEvents()
        with patch.object(QInputDialog,'getText',return_value=('4/3',True)):
            editor.palette_buttons[1].click()
        self.assertEqual(editor.blocks[3].block.gain,'4/3')
        view = editor.view
        start = view.mapFromScene(editor.blocks[1].output.scenePos())
        QTest.mousePress(view.viewport(),Qt.MouseButton.LeftButton,pos=start)
        self.assertIsNotNone(view.cable_source)
        QTest.keyClick(view,Qt.Key.Key_Escape)
        self.assertIsNone(view.cable_source)
        QTest.mouseRelease(view.viewport(),Qt.MouseButton.LeftButton,pos=start)
        self.assertFalse(editor.wires)

        editor.start_connection(-1)
        editor.connect_block(editor.blocks[2])
        self.assertIn('sólo recibe',editor.hint.text())
        QTest.keyClick(view,Qt.Key.Key_Escape)
        self.assertIsNone(editor.connection_sign)
        editor.start_connection(-1)
        editor.connect_block(editor.blocks[1])
        editor.connect_block(editor.blocks[3])
        editor.start_connection(1)
        editor.connect_block(editor.blocks[3])
        editor.connect_block(editor.blocks[2])
        self.assertEqual(editor.graph().transfer(),-sp.Rational(4,3))
        signed = next(item for item in editor.wires.values() if item.wire.sign == -1)
        editor.scene.clearSelection()
        signed.setSelected(True)
        self.assertIn('Conexión 1 → 3',editor.selection_label.text())
        self.assertTrue(editor.delete_button.isEnabled())
        editor.delete_button.click()
        self.assertFalse(editor.connection_state.property('complete'))
        with self.assertRaisesRegex(ValueError,'Conectá una señal a ganancia 3'):
            editor.graph().transfer()
        editor.finish_wire(Wire(1,3))
        editor.scene.clearSelection()
        editor.blocks[3].setSelected(True)
        with patch.object(QInputDialog,'getText',return_value=('5/2',True)):
            editor.edit_button.click()
        self.assertEqual(editor.graph().transfer(),sp.Rational(5,2))

    def test_transfer_block_same_formula_keeps_clock_and_edit_requires_new_clock(self):
        window = self.window()
        selected = Transfer.from_sos(
            [[.5,.25,0,1,-.25,0],[1,0,0,1,.5,0]], 'Dos secciones',sample_period_s=.125,
        )
        key = window.publish(selected)
        base = RealizationGraph.empty('digital')
        block = Block(3,'transfer',175,0)
        dialog = TransferBlockDialog(block,'digital',window,window)
        self.addCleanup(dialog.close)
        dialog.importer.load_result(key)
        imported = dialog.definition()
        self.assertEqual(imported.sample_period_s,.125)
        graph = RealizationGraph(base.domain,base.blocks+(imported,),(Wire(1,3),Wire(3,2)))
        reopened = RealizationGraph.from_document(graph.to_document())
        self.assertEqual(reopened.sample_period_s,.125)
        w = np.array([0.,.4,1.])
        z = np.exp(1j*w)
        curve = np.array([complex(reopened.transfer().subs(Z,value).evalf()) for value in z])
        np.testing.assert_allclose(curve,(.5+.25/z)/((1-.25/z)*(1+.5/z)),atol=1e-14)

        edit = TransferBlockDialog(imported,'digital',window,window)
        self.addCleanup(edit.close)
        edit.formula.setText('z^(-1)/2')
        result = edit.definition()
        self.assertIsNone(result.sample_period_s)
        self.assertEqual(result.formula,'z^(-1)/2')
        changed = RealizationGraph(base.domain,base.blocks+(result,),graph.wires)
        self.assertIsNone(changed.sample_period_s)
        self.assertEqual(sp.cancel(changed.transfer()-1/(2*Z)),0)

    def test_cascade_exports_a_readable_vector_image_and_editable_network(self):
        window = self.window()
        diagram = RealizationWindow(window)
        self.addCleanup(diagram.close)
        diagram.fit_width()
        diagram.export()
        system = Transfer.from_sos([[2,0,0,1,0,0],[1,.5,0,1,-.25,0]])
        value = realize_system(system)
        diagram.set_realization(value)
        self.assertTrue(value.cascade)
        self.assertEqual(tuple(stage.order for stage in value.stages),(0,1))
        diagram.resize(660,450)
        diagram.show()
        self.app.processEvents()
        diagram.fit_width()
        self.assertGreater(diagram.view.transform().m11(),0)
        with patch.object(QFileDialog,'getSaveFileName',return_value=('','')):
            diagram.export()
        for extension,label in [('svg','Diagrama vectorial SVG'),('png','Imagen PNG'),
                                ('json','Diagrama editable JSON')]:
            with self.subTest(extension=extension):
                target = self.path/('cascada-'+extension)
                with patch.object(QFileDialog,'getSaveFileName',return_value=(str(target),label)):
                    diagram.export()
                path = target.with_suffix('.'+extension)
                self.assertTrue(path.is_file())
                if extension=='svg':
                    vector = QSvgRenderer(str(path))
                    self.assertTrue(vector.isValid())
                    self.assertGreater(vector.defaultSize().height(),100)
                elif extension=='png':
                    bitmap = QImageReader(str(path))
                    self.assertTrue(bitmap.canRead())
                    self.assertGreater(bitmap.size().width(),100)
                else:
                    graph = RealizationGraph.from_document(json.loads(path.read_text(encoding='utf-8')))
                    self.assertEqual(sp.cancel(graph.transfer()-2*(1+sp.Rational(1,2)/Z)/(1-sp.Rational(1,4)/Z)),0)
        self.warning.assert_not_called()
        diagram.set_realization(realize_system(Transfer([3],[1,2],'analog')))
        target = self.path/'analogica.json'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(target),'Diagrama editable JSON')):
            diagram.export()
        graph = RealizationGraph.from_document(json.loads(target.read_text(encoding='utf-8')))
        self.assertEqual(sp.cancel(graph.transfer()-3/(S+2)),0)
