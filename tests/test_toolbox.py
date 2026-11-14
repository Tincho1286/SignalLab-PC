import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication,QPushButton
from PySide6.QtCore import QElapsedTimer
from PySide6.QtTest import QTest
from signallab_pc.toolbox import ToolboxWindow,MENUS
from signallab_pc.model import Signal

class ToolboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.window=ToolboxWindow();self.warnings=[]
        self.patcher=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.warnings.append(a[2]));self.patcher.start()
    def tearDown(self):
        self.window._thread_pool.waitForDone();self.app.processEvents();self.window.project.dirty=False
        self.window.close();self.window.deleteLater();self.app.processEvents();self.patcher.stop()
    def open(self,category,title):
        item=next(i for i in MENUS[category] if i[0]==title)
        self.window.show_menu(category);self.window.open_tool(item)
        return self.window.pages[tuple(item)]
    def finish(self):
        timer=QElapsedTimer();timer.start()
        while self.window._workers and timer.elapsed()<15000:QTest.qWait(10)
        self.assertFalse(self.window._workers);self.assertEqual(self.warnings,[])
    def test_home_search_and_direct_menu_need_no_signal(self):
        from PySide6.QtWidgets import QLineEdit,QListWidget
        self.assertEqual(self.window.category,'Inicio')
        home=self.window.pages[('menu','Inicio')]
        search=home.findChild(QLineEdit);matches=home.findChild(QListWidget)
        search.setText('laplace inversa')
        from PySide6.QtCore import Qt
        target=next((matches.item(i) for i in range(matches.count()) if matches.item(i).data(Qt.ItemDataRole.UserRole)[1:3]==('symbolic',1)),None)
        self.assertIsNotNone(target)
        matches.itemActivated.emit(target);self.assertEqual(self.window.title.text(),'Laplace inversa')
        self.assertEqual(self.window.project.headers(),[])
        menu=next(action.menu() for action in self.window.menuBar().actions() if action.text()=='Control')
        menu.actions()[0].trigger();self.assertEqual(self.window.title.text(),'Análisis en espacio de estados')
        self.assertEqual(self.window.project.headers(),[])
    def test_state_simulation_channels_and_provenance(self):
        import numpy as np
        panel=self.open('Control','Simulación en espacio de estados').panel
        source=panel.inputs.field(0);source.count.setText('11');source.step.setText('.1');panel.calculate_button.click();self.finish()
        models=self.window.project.headers('state_space');self.assertEqual(len(models),2)
        run=next(record for record in self.window.project.headers('calculation') if record['operation']=='Simulación MIMO')
        signals=self.window.project.headers('signal');self.assertEqual(len(signals),6)
        self.assertTrue(all(model['id'] in run['parents'] for model in models))
        y=next(record for record in signals if record['title']=='y1')
        result=self.window.project.get(y['id']);self.assertEqual(y['parents'],[run['id']])
        np.testing.assert_allclose(result.values.real,1-np.exp(-np.arange(11)*.1),atol=1e-13)
        fourier=self.open('Fourier','Fourier continua');fourier.context.source.set_source(result,y['id'])
        fourier.panel.ctft();self.finish();self.assertEqual(self.window.project.headers('signal')[-1]['parents'],[y['id']])
    def test_state_transfer_conversion_reusable_from_project(self):
        from signallab_pc.filters import Transfer
        import numpy as np
        key=self.window.publish(Transfer([0,1],[1]),operation='Retardo')
        panel=self.open('Control','Estados a función de transferencia').panel;panel.step.setText('.2')
        with patch.object(self.window,'choose_record',return_value=key):panel.choose_transfer()
        self.finish();model=self.window.project.headers('state_space')[-1];self.assertEqual(model['parents'],[key])
        panel.calculate_button.click();self.finish();record=self.window.project.headers('system')[-1]
        np.testing.assert_allclose(self.window.project.get(record['id']).response([.1,1]),np.exp(-1j*np.array([.1,1])),atol=1e-13)
        parent=self.window.project.headers('state_space')[-1];self.assertEqual(record['parents'],[parent['id']]);self.assertEqual(parent['parents'],[model['id']])
    def test_algebraic_measures_window_and_fourier_lineage(self):
        panel=self.open('Señales','Energía y potencia globales').panel
        panel.calculate_button.click();self.finish()
        exact=self.window.project.headers('calculation')[-1]
        self.assertEqual(self.window.project.get(exact['id'])['result']['energy']['exact'],'1')
        panel.start.setText('-2');panel.stop.setText('2');panel.count.setText('101');panel.sample_button.click();self.finish()
        window_measure=self.window.project.headers('calculation')[-1];sampled=self.window.project.headers('signal')[-1]
        self.assertEqual(window_measure['parents'],[exact['id']]);self.assertEqual(sampled['parents'],[window_measure['id']])
        source=self.window.project.get(sampled['id']);self.assertEqual(source.domain,'continuous')
        self.assertLess(source.metadata['energy'],1)
        fourier=self.open('Fourier','Fourier continua');fourier.context.source.set_source(source,sampled['id']);fourier.panel.ctft();self.finish()
        self.assertEqual(self.window.project.headers('signal')[-1]['parents'],[sampled['id']])
    def test_periodic_measure_and_stale_expression_sample_button(self):
        panel=self.open('Señales','Energía y potencia periódicas').panel
        panel.domain.setCurrentIndex(1);panel.calculate_button.click();self.finish()
        result=self.window.project.get(self.window.project.headers('calculation')[-1]['id'])['result']
        self.assertTrue(result['period_verified']);self.assertEqual(result['mean_square']['exact'],'1/2')
        self.assertTrue(panel.sample_button.isEnabled());panel.expression.setText('2');self.assertFalse(panel.sample_button.isEnabled())
    def test_measure_definition_reuse_keeps_parent(self):
        first=self.open('Señales','Energía algebraica por intervalo').panel
        first.expression.setText('1+i*t');first.calculate_button.click();self.finish()
        key=self.window.project.headers('calculation')[-1]['id']
        second=self.open('Señales','Energía y potencia globales').panel
        with patch.object(self.window,'choose_record',return_value=key):second.choose()
        self.assertEqual(second.expression.text(),'1+i*t');second.calculate_button.click();self.finish()
        record=self.window.project.headers('calculation')[-1];self.assertEqual(record['parents'],[key])
        self.assertEqual(self.window.project.get(record['id'])['result']['mean_square']['status'],'divergent')
    def test_continuous_result_goes_to_fourier_with_provenance(self):
        page=self.open('Operaciones','Convolución continua numérica')
        for field in (page.first,page.second):
            field.mode.setCurrentIndex(1);field.samples.setText('1, 1');field.step.setText('0.5')
        next(b for b in page.findChildren(QPushButton) if b.text()=='Calcular').click();self.finish()
        record=self.window.project.headers('signal')[-1];self.assertEqual(len(record['parents']),2)
        result=self.window.project.get(record['id']);self.assertEqual(list(result.values.real),[0,.5,0])
        fourier=self.open('Fourier','Fourier continua')
        fourier.context.source.set_source(result,record['id']);fourier.panel.ctft();self.finish()
        self.assertEqual(self.window.project.headers('signal')[-1]['parents'],[record['id']])
    def test_rational_rate_and_input_reference(self):
        source=Signal([1]*100,metadata={'sample_rate_hz':48000,'time_start_s':2})
        key=self.window.publish(source,operation='test source')
        panel=self.open('Muestreo','Cambio racional de tasa con antialias').panel
        panel.source.set_source(source,key);panel.read_clock();panel.calculate_button.click();self.finish()
        record=self.window.project.headers('signal')[-1];result=self.window.project.get(record['id'])
        self.assertEqual(record['parents'],[key]);self.assertEqual(result.metadata['sample_rate_hz'],44100)
        self.assertEqual(result.metadata['time_start_s'],2)
    def test_algebraic_fourier_samples_feed_numeric_inverse(self):
        panel=self.open('Fourier','Fourier continua algebraica').panel
        panel.calculate_button.click();self.finish()
        exact=self.window.project.headers('calculation')[-1]
        panel.sample_button.click();self.finish()
        sampled=self.window.project.headers('signal')[-1];source=self.window.project.get(sampled['id'])
        self.assertEqual(sampled['parents'],[exact['id']]);self.assertEqual(source.units,'rad/s')
        page=self.open('Fourier','Fourier continua inversa')
        page.context.source.set_source(source,sampled['id']);page.panel.t0.setText('-1');page.panel.t1.setText('1');page.panel.nt.setText('101')
        page.panel.inverse();self.finish()
        reconstructed=self.window.project.headers('signal')[-1]
        self.assertEqual(reconstructed['parents'],[sampled['id']])
        self.assertAlmostEqual(self.window.project.get(reconstructed['id']).values[50].real,1,delta=.001)
    def test_dtft_algebraic_sampling_retains_units(self):
        panel=self.open('Fourier','DTFT algebraica').panel
        panel.calculate_button.click();self.finish();self.assertTrue(panel.sample_button.isEnabled())
        panel.count.setText('5');panel.sample_button.click();self.finish()
        result=self.window.project.get(self.window.project.headers('signal')[-1]['id'])
        self.assertEqual(result.units,'rad/muestra');self.assertAlmostEqual(result.values[2].real,2)
    def test_circular_correlation_options_and_parents(self):
        panel=self.open('Operaciones','Correlación discreta y autocorrelación').panel
        panel.kind.setCurrentIndex(1);panel.model.setCurrentIndex(1);panel.normalization.setCurrentIndex(2)
        for field,values in [(panel.left,'1, 2'),(panel.right,'3, 4')]:field.mode.setCurrentIndex(1);field.samples.setText(values)
        panel.calculate_button.click();self.finish()
        record=self.window.project.headers('signal')[-1];result=self.window.project.get(record['id'])
        self.assertEqual(list(result.values.real),[5.5,5]);self.assertEqual(len(record['parents']),2)
        panel.model.setCurrentIndex(0);self.assertEqual(panel.normalization.currentIndex(),0)
    def test_periodic_continuous_auto_options(self):
        panel=self.open('Operaciones','Correlación continua y periódica').panel
        panel.model.setCurrentIndex(1);panel.normalization.setCurrentIndex(1)
        panel.left.mode.setCurrentIndex(1);panel.left.samples.setText('1, 1');panel.left.step.setText('0.5')
        panel.calculate_button.click();self.finish()
        result=self.window.project.get(self.window.project.headers('signal')[-1]['id'])
        self.assertEqual(result.metadata['period_s'],1);self.assertTrue(result.metadata['autocorrelation'])
        self.assertAlmostEqual(result.values[0].real,1)
    def test_editor_page_and_original_are_preserved(self):
        source=Signal([0]*2005,origin=-3);key=self.window.publish(source)
        editor=self.open('Señales','Tabla y edición de muestras').panel
        editor.source.set_source(source,key);editor.load_button.click();editor.change_page(1)
        editor.table.item(3,1).setText('7');editor.table.item(3,2).setText('2')
        self.assertTrue(editor.pending);self.assertEqual(editor.current.values[1003],7+2j)
        editor.commit();result=self.window.project.get(self.window.project.headers('signal')[-1]['id'])
        self.assertEqual(result.values[1003],7+2j);self.assertEqual(result.values[3],0)
        self.assertEqual(self.window.project.get(key).values[1003],0)
        self.assertEqual(self.window.project.headers('signal')[-1]['parents'],[key])
    def test_project_save_includes_editor_draft(self):
        import tempfile
        from pathlib import Path
        from signallab_pc.project import Project
        editor=self.open('Señales','Tabla y edición de muestras').panel
        editor.source.mode.setCurrentIndex(1);editor.source.samples.setText('1, 2');editor.load_button.click();editor.table.item(1,1).setText('8')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edited.json'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'')):self.window.save_project()
            loaded=Project();loaded.merge(path)
            self.assertEqual(loaded.get(loaded.headers('signal')[-1]['id']).values[1],8)
            self.assertFalse(editor.pending)
    def test_switching_local_and_project_input_keeps_correct_origin(self):
        source=Signal([9,8],origin=-4);key=self.window.publish(source)
        field=self.open('Señales','Generar y graficar').first
        field.set_source(source,key);field.read();self.assertEqual(field.reference_id,key)
        field.mode.setCurrentIndex(0);field.expression.setText('n');field.read();self.assertNotEqual(field.reference_id,key)
        field.mode.setCurrentIndex(2);value=field.read()
        self.assertEqual(field.reference_id,key);self.assertEqual(value.origin,-4)

if __name__=='__main__':unittest.main()
