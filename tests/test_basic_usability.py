"""Clipboard contracts, reversible edits and authoritative pointwise alignment."""
import os,tempfile,unittest,csv
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication
from signallab_pc.model import Signal
from signallab_pc import sample_paste as paste
from signallab_pc.signal_segment import extract
from signallab_pc.signal_alignment import Alignment
from signallab_pc.signal_combinations import sum_signals
from signallab_pc.windowing import multiply_signals


class Arithmetic(unittest.TestCase):
    def test_clipboard_constants_complexes_and_matlab_vectors(self):
        assert_allclose(paste.parse('[pi 10^(-3) (1+2i)]').values,[np.pi,.001,1+2j]);assert_allclose(paste.parse('[1;2;3]').values,[1,2,3]);self.assertEqual(paste.parse('pi / 4').values[0],np.pi/4)
    def test_column_layout_header_decimal_comma_and_exact_large_indices(self):
        n=2**53+17;x=paste.parse(f'n;real;imag\n{n};1,5;2,5\n{n+1};0,0;-1,0',layout='axis_complex',decimal_comma=True,header=True);self.assertEqual(x.origin,n);assert_allclose(x.values,[1.5+2.5j,-1j]);assert_allclose(paste.parse('1,2\n3,4',decimal_comma=True).values,[1.2,3.4])
    def test_irregular_missing_nonfinite_and_ambiguous_tables_are_rejected(self):
        for text,options in [('0;1\n2;2',dict(layout='axis_value')),('0;1\n.1;2\n.21;3',dict(layout='axis_value',kind='continuous')),('1,\n2,3',{}),('nan',{}),('1\t2\n3\t4',{})]:
            with self.subTest(text=text),self.assertRaises(ValueError):paste.parse(text,**options)
    def test_segment_keeps_clock_and_single_continuous_point_without_remeshing(self):
        x=Signal([1,2,3],-4,metadata={'sample_rate_hz':4,'time_start_s':2});y=extract(x,-3,-2);self.assertEqual(y.origin,-3);self.assertEqual(y.metadata['time_start_s'],2.25);assert_allclose(y.values,[2,3]);self.assertEqual(x.origin,-4)
        t=Signal([1,2,3],.1,.1,'s','x','continuous');self.assertEqual(extract(t,.2,.2).values[0],2)
        with self.assertRaises(ValueError):extract(t,.15,.2)
    def test_discrete_alignment_and_zero_extension_use_exact_indices(self):
        n=2**53+17;x=Signal([1+2j,2],n);w=Signal([3,4],n+1);y=sum_signals(x,w);trace=Alignment(x,w,y);rows=trace.page();self.assertEqual([r[0] for r in rows],[n,n+1,n+2]);assert_allclose([r[3] for r in rows],[1+2j,5,4]);self.assertIn('Solo x',rows[0][4]);self.assertEqual(trace.offset_for(str(n+1)),1);x.values[:]=99;self.assertEqual(trace.page()[0][1],1+2j)
    def test_continuous_alignment_matches_existing_solver_and_product_support(self):
        x=Signal([1,3,5],0,.5,'s','x','continuous');w=Signal([2,4],.5,1,'s','w','continuous')
        for compute in (sum_signals,multiply_signals):
            y=compute(x,w);rows=Alignment(x,w,y).page();a=np.array([r[1] for r in rows]);b=np.array([r[2] for r in rows]);assert_allclose(a*b if compute==multiply_signals else a+b,y.values)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        self.host=Host();self.panels=[];self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *args:self.errors.append(str(args[2])));self.warning.start()
    def tearDown(self):
        self.warning.stop()
        for panel in self.panels:panel.close();panel.deleteLater()
        self.host.bar.close();self.app.processEvents()
    def editor(self):
        from signallab_pc.signal_editor_panel import SignalEditorPanel
        p=SignalEditorPanel(self.host);self.panels.append(p);p.receive(Signal([1,2,3],-1,expression='n+2'));return p
    def test_local_paste_is_editable_and_keeps_other_input_drafts(self):
        from signallab_pc.toolbox import LocalInput
        p=LocalInput('x');self.panels.append(p);x=Signal([7,8]);p.set_source(x,'saved');p.apply_pasted_signal(paste.parse('pi\n1+2i',origin='-2'));self.assertEqual(p.mode.currentIndex(),1);assert_allclose(p.read().values,[np.pi,1+2j]);self.assertIs(p.loaded,x);self.assertEqual(p.loaded_reference_id,'saved');self.assertEqual(p.expression.text(),'cos(pi*n/4)')
    def test_undo_redo_samples_and_fields_preserve_applied_snapshot(self):
        p=self.editor();p.table.item(1,1).setText('9');p.history.stack.undo();self.assertFalse(p.pending);self.assertEqual(p.current.values[1],2);p.history.stack.redo();applied=p.commit();p.history.stack.undo();self.assertTrue(p.pending);self.assertEqual(p.current.values[1],2);self.assertEqual(applied.values[1],9);p.name.setText('nueva');p.history.stack.undo();self.assertEqual(p.name.text(),'x');p.history.stack.redo();self.assertEqual(p.name.text(),'nueva')
    def test_bulk_paste_is_one_atomic_edit_and_bad_bounds_change_nothing(self):
        p=self.editor();p.paste_values(paste.parse('7+2i,8',origin='0'));assert_allclose(p.current.values,[1,7+2j,8]);p.history.stack.undo();assert_allclose(p.current.values,[1,2,3]);count=p.history.stack.count()
        with self.assertRaises(ValueError):p.paste_values(paste.parse('7,8',origin='1'))
        self.assertEqual(p.history.stack.count(),count);assert_allclose(p.current.values,[1,2,3])
    def test_extract_publishes_edited_subset_without_applying_whole_draft(self):
        p=self.editor();p.table.item(1,2).setText('4');y=p.extract_segment('0','1');assert_allclose(y.values,[2+4j,3]);self.assertTrue(p.pending);self.assertIsNone(p.applied);self.assertTrue(p.segment_output.result_ids);self.assertEqual(y.metadata['source_expression'],'n+2')
    def test_swap_complete_inputs_and_alignment_pagination_remain_independent(self):
        from signallab_pc.signal_combination_panel import SignalProductPanel
        p=SignalProductPanel(self.host,operation='sum');self.panels.append(p);p.first.mode.setCurrentIndex(1);p.first.samples.setText('1,2');p.first.origin.setText('0');source=Signal([3,4],1);key=self.host.publish(source);p.second.set_source(source,key);p.calculate();self.assertEqual(self.errors,[]);old=p.result;p.swap_inputs();self.assertEqual(p.first.loaded_reference_id,key);self.assertEqual(p.second.samples.text(),'1,2');self.assertIs(p.result,old);self.assertIn('modificados',p.state.text());p.calculate();assert_allclose(p.result.values,[1,5,4]);self.assertEqual(p.alignment.table.rowCount(),3);self.assertEqual(self.errors,[])
    def test_dialog_rejects_invalid_data_and_full_csv_keeps_complex_values(self):
        from signallab_pc.sample_paste_dialog import PasteSignalDialog
        from signallab_pc.signal_alignment_panel import AlignmentPanel
        from PySide6.QtWidgets import QDialogButtonBox
        dialog=PasteSignalDialog('1,2');self.panels.append(dialog);self.assertEqual(len(dialog.result_signal.values),2);dialog.text.setPlainText('1,,2');dialog.update_preview();self.assertIsNone(dialog.result_signal);self.assertFalse(dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled())
        panel=AlignmentPanel();self.panels.append(panel);x=Signal(np.arange(600)+1j);y=multiply_signals(x,Signal([2]));panel.set_trace(Alignment(x,Signal([2]),y))
        with tempfile.TemporaryDirectory() as folder:
            path=str(Path(folder)/'tabla.csv')
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(path,'CSV (*.csv)')):panel.export_table()
            rows=list(csv.reader(Path(path).read_text(encoding='utf-8').splitlines()));self.assertEqual(len(rows),601);self.assertEqual(rows[1][3],'(0+2j)')


if __name__=='__main__':unittest.main()
