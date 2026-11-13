"""Mathematical and real-control contracts for comparison and map readings."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import csv,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from matplotlib.figure import Figure
from signallab_pc.grid_probe import grid_trace
from signallab_pc.probe_data import collect,readings
from signallab_pc.result_comparison import compare,errors
from signallab_pc.comparison_trace import capture,export_csv
from signallab_pc.model import Signal
from signallab_pc.visible_curve import visible_indices


class MeasurementMath(unittest.TestCase):
    def test_image_orientation_extent_and_original_cell(self):
        for origin,value in [('lower',3),('upper',1)]:
            figure=Figure();axis=figure.add_subplot();artist=axis.imshow([[1,2],[3,4]],extent=(0,2,0,2),origin=origin)
            trace=grid_trace(axis,artist)
            self.assertEqual(trace.point(.1,1.9),(.5,1.5,value))
            self.assertIsNone(trace.point(2.1,1));self.assertIsNone(trace.point(1,-.1))
        artist=axis.imshow([[1,2],[3,4]],extent=(2,0,0,2),origin='lower')
        self.assertEqual(grid_trace(axis,artist).point(1.8,.2),(1.5,.5,1))

    def test_nonuniform_mesh_mask_and_unsupported_color_images(self):
        figure=Figure();axis=figure.add_subplot()
        values=np.ma.array([[1,2],[3,4]],mask=[[0,1],[0,0]])
        mesh=axis.pcolormesh([0,1,4],[3,2,-2],values,shading='flat')
        trace=grid_trace(axis,mesh)
        self.assertEqual(trace.point(.2,2.8),(.5,2.5,1))
        self.assertTrue(np.isnan(trace.point(2,2.8)[2]));self.assertEqual(trace.point(2,-1),(2.5,0,4))
        self.assertIsNone(grid_trace(axis,axis.imshow(np.ones((2,2,3)))))
        warped=axis.pcolormesh([[0,1,2],[.1,1.1,2.1],[.2,1.2,2.2]],[[0,0,0],[1,1,1],[2,2,2]],np.ones((2,2)))
        self.assertIsNone(grid_trace(axis,warped))

    def test_error_metrics_keep_small_differences_beside_huge_equal_values(self):
        m=errors(np.array([1e308,1e-300]),np.array([1e308,2e-300]))
        self.assertAlmostEqual(m['absolute_max']/1e-300,1);self.assertAlmostEqual(m['rms']/(1e-300/np.sqrt(2)),1)
        self.assertIsNone(m['relative_max'])
        tiny=errors(np.array([1e-320]),np.array([2e-320]));self.assertGreater(tiny['absolute_max'],0);self.assertAlmostEqual(tiny['relative_max'],.5)
        huge=errors(np.array([1e308]),np.array([-1e308]));self.assertIsNone(huge['absolute_max']);self.assertAlmostEqual(huge['relative_max'],2)

    def test_comparison_snapshot_and_csv_preserve_large_integer_indices(self):
        start=2**53+1;a=Signal([1+1j,2,3],start);b=Signal([5,7],start+1)
        data=compare(a,b);trace=data['trace']
        assert_allclose(trace['error'],[3,4]);self.assertEqual(trace['coordinates'].tolist(),[start+1,start+2])
        a.values[:]=0;b.values[:]=0;self.assertEqual(data['signals'][0].values[1],2)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'comparison.csv';export_csv(path,trace)
            with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream,delimiter=';'))
            self.assertEqual(rows[1][0],str(start+1));self.assertEqual(rows[1][5],'3')

    def test_physical_common_times_and_absent_overlap_are_explicit(self):
        a=Signal([1,2,3],8,metadata={'sample_rate_hz':2.,'time_start_s':0.})
        b=Signal([10,20],20,metadata={'sample_rate_hz':1.,'time_start_s':0.})
        data=compare(a,b,alignment='physical');assert_allclose(data['trace']['coordinates'],[0,1]);assert_allclose(data['trace']['error'],[9,17]);self.assertEqual(data['trace']['units'],'s')
        empty=compare(Signal([1],-2),Signal([1],3));self.assertEqual(empty['metrics']['count'],0);self.assertEqual(len(empty['trace']['error']),0)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'No hay coordenadas'):export_csv(Path(temp)/'empty.csv',empty['trace'])

    def test_system_difference_matches_an_independent_frequency_response(self):
        from scipy.signal import freqz
        from signallab_pc.filters import Transfer
        a=Transfer([1],[1,-.5]);b=Transfer([1],[1,-.25]);data=compare(a,b,-np.pi,np.pi,101)
        expected=freqz([1],[1,-.25],worN=data['omega'])[1]-freqz([1],[1,-.5],worN=data['omega'])[1]
        assert_allclose(data['trace']['error'],expected,atol=1e-14);self.assertEqual(data['trace']['units'],'rad/muestra')

    def test_csv_distinguishes_overflow_and_undefined_values(self):
        trace=capture([0.,1.],[1e308,np.nan],[-1e308,2],units='s',label='t')
        self.assertEqual(trace['overflow_count'],1);self.assertEqual(trace['undefined_count'],1)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'range.csv';export_csv(path,trace)
            with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream,delimiter=';'))
            self.assertEqual(rows[1][-1],'fuera de rango float64');self.assertEqual(rows[2][-1],'entrada no definida')
            self.assertEqual(rows[1][5:7],['',''])

    def test_dirac_weights_are_separate_from_zero_ordinary_parts(self):
        a=Signal([0,0],0,.5,'s','A','continuous',metadata={'dirac_at_zero':[2.,0.]})
        b=Signal([0,0],0,.5,'s','B','continuous',metadata={'dirac_at_zero':[5.,0.],'dirac_terms':[[.5,[0.,4.]]]})
        data=compare(a,b);self.assertEqual(data['metrics']['absolute_max'],0)
        trace=data['impulse_trace'];assert_allclose(trace['error'],[3,4j]);self.assertEqual(data['impulses']['metrics']['absolute_max'],4)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'impulses.csv';export_csv(path,data['trace'],trace)
            with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream,delimiter=';'))
            impulses=[row for row in rows if row['parte']=='peso de Dirac']
            self.assertEqual(len(impulses),2);self.assertEqual(impulses[1]['B-A imaginaria'],'4')

    def test_zoom_recovers_every_original_point_and_reduction_retains_extrema(self):
        x=np.linspace(0,1,100001);y=np.zeros(len(x));y[43210]=1;y[43211]=-7;y[80000]=np.nan
        ids=visible_indices(x,y,0,1,budget=1000)
        self.assertIn(43210,ids);self.assertIn(43211,ids);self.assertIn(80000,ids)
        close=visible_indices(x,y,x[43200],x[43220],budget=1000)
        self.assertEqual(close.tolist(),list(range(43199,43222)))

    def test_theme_does_not_replace_colors_from_a_scalar_map(self):
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.colors import ListedColormap
        from signallab_pc.plot_view import prepare_figure
        figure=Figure();FigureCanvasAgg(figure);axis=figure.add_subplot()
        mesh=axis.pcolormesh([[0,1]],cmap=ListedColormap(['#68c7b4','#8b9cfa']));figure.canvas.draw();before=mesh.get_facecolors().copy()
        prepare_figure(figure);assert_allclose(mesh.get_facecolors(),before)


class MeasurementUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):self.widgets=[]
    def tearDown(self):
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.app.processEvents()

    def probe(self,figure):
        from PySide6.QtWidgets import QWidget,QVBoxLayout
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
        from signallab_pc.plot_probe import PlotProbe
        widget=QWidget();self.widgets.append(widget);layout=QVBoxLayout(widget);canvas=FigureCanvasQTAgg(figure);toolbar=NavigationToolbar2QT(canvas,widget)
        layout.addWidget(toolbar);layout.addWidget(canvas);probe=PlotProbe(canvas,toolbar,layout);canvas.draw();return probe

    def test_grid_cursor_values_deltas_copy_and_legacy_lines(self):
        from PySide6.QtWidgets import QApplication
        figure=Figure();axis=figure.add_subplot();image=axis.imshow([[1,2],[3,9]],extent=(0,2,0,2),origin='lower');figure.colorbar(image,ax=axis,label='dB relativos')
        probe=self.probe(figure)
        probe.motion(SimpleNamespace(inaxes=axis,xdata=.2,ydata=.2),force=True);probe.pin('a')
        probe.motion(SimpleNamespace(inaxes=axis,xdata=1.8,ydata=1.8),force=True);probe.pin('b')
        self.assertEqual(probe.table.columnCount(),4);self.assertEqual(probe.table.item(2,1).text(),'1');self.assertEqual(probe.table.item(2,3).text(),'8')
        probe.copy_values();self.assertIn('B−A',QApplication.clipboard().text());self.assertIn('dB relativos',QApplication.clipboard().text())
        figure.clear();axis=figure.add_subplot();axis.plot([0,1],[2,3]);probe.canvas.draw()
        probe.motion(SimpleNamespace(inaxes=axis,xdata=0,ydata=2),force=True);self.assertEqual(probe.table.columnCount(),7)

    def test_new_map_data_resets_pins_and_cells_do_not_link_to_another_y_axis(self):
        figure=Figure();a,b=figure.subplots(2,1,sharex=True)
        image=a.imshow([[1,2],[3,4]],extent=(0,2,0,2),origin='lower');b.plot([0,1],[100,200])
        traces=collect(figure);values=readings(traces,b,1,200)
        self.assertNotIn(id(image),values)
        probe=self.probe(figure);probe.motion(SimpleNamespace(inaxes=a,xdata=.2,ydata=.2),force=True);probe.pin('a')
        image.set_data([[8,7],[6,5]]);probe.canvas.draw();self.assertIsNone(probe.a)

    def test_window_zoom_preserves_pins_and_controls_travel_with_figure(self):
        from signallab_pc.window_spectrum_view import WindowSpectrumView
        from signallab_pc.plot_view import install_enlarge
        widget=WindowSpectrumView();self.widgets.append(widget)
        x=np.linspace(0,np.pi,100001);magnitude=np.linspace(1,.001,len(x))
        widget.set_data(dict(frequency=x,magnitude=magnitude,metrics={'normalizable':True,'half_power_frequency':None}))
        install_enlarge(widget.toolbar);widget.canvas.draw();probe=widget.canvas._signallab_probe;axis=widget.figure.axes[0]
        self.assertIs(widget.scale.window(),widget.canvas._signallab_window)
        probe.motion(SimpleNamespace(inaxes=axis,xdata=x[12345],ydata=0),force=True);probe.pin('a');saved=dict(probe.a)
        axis.set_xlim(x[60000],x[60020]);widget.canvas.draw()
        self.assertEqual(probe.a,saved);self.assertEqual(len(widget.curve.line.get_xdata()),23)
        point=next(trace for trace in probe.traces if trace.key==id(widget.curve.line)).point(x[60007])
        self.assertEqual(point[0],x[60007]);self.assertAlmostEqual(point[1],20*np.log10(magnitude[60007]))

    def test_comparison_controls_export_the_last_result_without_duplicating_inputs(self):
        from PySide6.QtWidgets import QMainWindow
        from signallab_pc.project import Project
        from signallab_pc.result_journal import ResultJournal
        from signallab_pc.result_comparison import ComparisonDialog
        window=QMainWindow();self.widgets.append(window);window.project=Project();window.pages={};window.current_operation=None;window.refresh_project=lambda:None
        def publish(value,**options):
            journal=getattr(window,'_result_journal',None)
            if journal:value=journal.enrich(value)
            key=window.project.add(value,**options)
            if journal:journal.published(key,value)
            return key
        window.publish=publish;window._run_operation=lambda title,compute,accept:ResultJournal(window,title).accept(compute(),accept)
        publish(Signal([1,2,3],-1));publish(Signal([1,4,6],-1))
        dialog=ComparisonDialog(window);self.widgets.append(dialog);dialog.refresh();dialog.calculate_button.click()
        self.assertIsNotNone(dialog.data);self.assertEqual(len(window.project.headers('signal')),2);self.assertTrue(dialog.frequency_label.isHidden())
        dialog.trace_mode.setCurrentIndex(1);self.assertEqual(dialog.figure.axes[0].get_ylabel(),'Parte real')
        self.assertIs(dialog.mode.window(),dialog.canvas._signallab_window)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'difference.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'')):dialog.export_button.click()
            self.assertTrue(path.exists());self.assertIn('B-A real',path.read_text(encoding='utf-8-sig'))
        record=window.project.get(window.project.headers('calculation')[-1]['id']);self.assertIn('source_ids',record['calculated_data'])
        ka=publish(Signal([0,0],0,.5,'s','Impulso A','continuous',metadata={'dirac_at_zero':[2.,0.]}))
        kb=publish(Signal([0,0],0,.5,'s','Impulso B','continuous',metadata={'dirac_at_zero':[5.,0.]}))
        dialog.refresh();dialog.a.setCurrentIndex(dialog.a.findData(ka));dialog.b.setCurrentIndex(dialog.b.findData(kb));dialog.calculate_button.click()
        self.assertFalse(dialog.part.isHidden());dialog.part.setCurrentIndex(1)
        self.assertEqual(dialog.figure.axes[0].get_ylabel(),'Peso real')



if __name__=='__main__':unittest.main()
