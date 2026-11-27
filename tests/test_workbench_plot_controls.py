"""Graph measurements through the desktop inspector, pointer and keyboard."""
import csv
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from matplotlib.backend_bases import KeyEvent, MouseButton, MouseEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import QCoreApplication, QEvent, QItemSelectionModel, QModelIndex, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from signallab_pc.plot_view import enlarge_plot, install_enlarge
from signallab_pc.model import Signal
from signallab_pc.result_table import ResultTable


class PlotControlContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_detached_figure_tracks_results_without_rendering_while_closed(self):
        owner = QWidget()
        layout = QVBoxLayout(owner)
        figure = Figure()
        canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbar2QT(canvas, owner)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        canvas._signallab_explicit_plot = True
        draws = []
        canvas.mpl_connect('draw_event', lambda _event: draws.append(True))
        install_enlarge(toolbar, standalone=True)
        window = canvas._signallab_window
        self.addCleanup(owner.deleteLater)
        self.addCleanup(window.close)
        axes = figure.add_subplot()
        axes.plot([0, 1], [0, 3])
        canvas.draw_idle()
        self.app.processEvents()
        self.assertTrue(canvas._signallab_has_plot_result)
        self.assertEqual(draws, [])
        enlarge_plot(canvas, owner)
        self.app.processEvents()
        self.assertTrue(window.isVisible())
        self.assertTrue(draws)

    def figure(self, setup):
        parent = QWidget()
        layout = QVBoxLayout(parent)
        figure = Figure()
        canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbar2QT(canvas,parent)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        canvas._signallab_explicit_plot = True
        axes = setup(figure)
        install_enlarge(toolbar,standalone=True)

        def close():
            canvas._signallab_window.close()
            parent.close()
            parent.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
            self.app.processEvents()

        self.addCleanup(close)
        canvas.draw()
        return canvas._signallab_probe, axes

    def mouse(self, canvas, axis, kind, coordinate, ordinate, *, key=None):
        if kind == 'motion_notify_event':
            QTest.qWait(35)
        x,y = axis.transData.transform((coordinate,ordinate))
        event = MouseEvent(kind,canvas,x,y,button=MouseButton.LEFT,key=key)
        canvas.callbacks.process(kind,event)

    def test_choose_curve_drag_b_and_measure_a_real_interval(self):
        def make(figure):
            axis = figure.add_subplot()
            axis.set_xlabel('Tiempo (s)')
            axis.set_ylabel('Amplitud')
            first, = axis.plot(range(6),[0,2,1,2,1,0],label='Referencia')
            second, = axis.plot(range(6),[6,7,9,9,6,8],label='Medición')
            return axis, first, second

        probe,(axis,first,second) = self.figure(make)
        first_key,second_key = id(first),id(second)
        probe.open_inspector()
        self.app.processEvents()
        probe.canvas.draw()
        self.assertIs(probe.readings_dock,probe.inspector)
        probe.curve_actions[second_key].trigger()
        self.assertEqual(probe.inspector.selected().key,second_key)
        probe.choose_curve(first_key)
        self.assertEqual(probe.inspector.selected().key,first_key)
        probe.curve_actions[second_key].trigger()
        self.mouse(probe.canvas,axis,'button_press_event',1,7)
        self.mouse(probe.canvas,axis,'button_press_event',4,6,key='shift')
        self.assertEqual(probe.a[second_key],(1.,7.))
        self.assertEqual(probe.b[second_key],(4.,6.))
        self.mouse(probe.canvas,axis,'button_press_event',4,6)
        self.assertEqual(probe._dragging,'b')
        self.mouse(probe.canvas,axis,'motion_notify_event',4.9,8)
        self.mouse(probe.canvas,axis,'button_release_event',4.9,8)
        self.assertIsNone(probe._dragging)
        self.assertEqual(probe.b[second_key],(5.,8.))
        key = KeyEvent('key_press_event',probe.canvas,key='left')
        probe.canvas.callbacks.process(key.name,key)
        self.assertEqual(probe.b[second_key],(4.,6.))

        inspector = probe.inspector
        inspector.scope.setCurrentIndex(2)
        inspector.tabs.setCurrentIndex(1)
        self.assertEqual((inspector.result['low'],inspector.result['high']),(1.,4.))
        self.assertEqual(inspector.result['maximum'],9.)
        self.assertEqual(inspector.result['minimum'],6.)
        maximum = inspector.model.rows[0]
        self.assertEqual((maximum['x'],maximum['x_end'],maximum['plateau']),(2.,3.,2))
        self.assertFalse(inspector.table.isColumnHidden(2))
        with TemporaryDirectory() as folder:
            path = Path(folder)/'extremos.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',
                       return_value=(str(path),'CSV')):
                inspector.export.click()
            with path.open(encoding='utf-8',newline='') as stream:
                header = json.loads(stream.readline()[2:])
                rows = list(csv.DictReader(stream))
            self.assertEqual(header['curve'],'Medición')
            self.assertEqual(float(rows[0]['y']),9.)
            self.assertEqual(int(rows[0]['plateau']),2)

        probe.table_toggle.click()
        self.assertIs(inspector.tabs.currentWidget(),inspector.readings_page)
        probe.inspect_action.setChecked(False)
        self.assertIsNone(probe.readings_dock)
        self.assertFalse(probe.canvas._signallab_window.inspector_requested)
        self.assertIsNotNone(probe.b)
        key = KeyEvent('key_press_event',probe.canvas,key='escape')
        probe.canvas.callbacks.process(key.name,key)
        self.assertIsNone(probe.a)
        self.assertIsNone(probe.b)

    def test_off_screen_log_cursor_keeps_the_zoom_and_axis_direction(self):
        def make(figure):
            axis = figure.add_subplot()
            axis.set_xscale('log')
            axis.plot([1,3,10,100],[0,2,1,5],label='Módulo')
            axis.set_xlim(10,1)
            return axis

        probe,axis = self.figure(make)
        trace = probe.traces[0]
        with self.assertRaisesRegex(ValueError,'Primero colocá'):
            probe.focus(trace,100,'b')
        with self.assertRaisesRegex(ValueError,'Cursor no reconocido'):
            probe.focus(trace,10,'x')
        old = axis.get_xlim()
        probe.pan_to(axis,0)
        self.assertEqual(axis.get_xlim(),old)
        idx,x,y = probe.focus(trace,95,'a')
        self.assertEqual((idx,x,y),(3,100.,5.))
        high,low = axis.get_xlim()
        self.assertGreater(high,low)
        self.assertAlmostEqual(high/low,10.)
        self.assertAlmostEqual(math.sqrt(high*low),100.)

        axis.clear()
        axis.plot([0,2],[11,12],label='Otra medición')
        probe.canvas.draw()
        self.assertIsNone(probe.a)
        with self.assertRaisesRegex(ValueError,'figura cambió'):
            probe.focus(trace,100)

    def test_unavailable_reference_and_incompatible_axes_keep_truthful_readings(self):
        def make(figure):
            left,right = figure.subplots(1,2)
            short, = left.plot([0,1],[1,2],label='Curva corta')
            left.plot([0,1,2,3],[3,4,5,6],label='Curva larga')
            independent, = right.plot([0,1,2],[30,40,50],label='Otra unidad')
            left.set_xlim(-.25,3.25)
            return left, right, short, independent

        probe,(left,right,short,independent) = self.figure(make)
        short_key, independent_key = id(short),id(independent)
        probe.choose_curve(short_key)
        self.mouse(probe.canvas,left,'motion_notify_event',2,5)
        self.assertFalse(probe.live)
        self.assertEqual(probe.unavailable_key,short_key)
        self.assertIn('Sin punto',probe.hint.text())
        probe.focus(probe.trace_by_key[short_key],1,'a')
        self.mouse(probe.canvas,right,'motion_notify_event',1,40)
        self.assertEqual(probe.live_key,independent_key)
        probe.pin('b')
        self.assertIsNone(probe.b)
        self.assertEqual(probe.a[independent_key],(1.,40.))

    def test_inspector_rejects_extrema_on_a_color_map(self):
        def make(figure):
            axis = figure.add_subplot()
            axis.imshow([[1,2],[3,4]],origin='lower')
            return axis

        probe,_ = self.figure(make)
        probe.open_inspector()
        self.app.processEvents()
        self.assertIsNotNone(probe.inspector.selected())
        self.assertFalse(probe.inspector.search.isEnabled())
        self.assertIn('mapa',probe.inspector.measure_note.text())
        self.assertIsNone(probe.inspector.result)

    def test_value_table_keeps_close_coordinates_distinct_and_copies_selected_rows(self):
        table = ResultTable()
        self.addCleanup(table.deleteLater)
        table.resize(500,400)
        source = Signal([0,3+4j,4-3j],1e6,-1e-9,'Hz','Espectro importado','frequency')
        table.set_signals([source])
        model = table.model
        phase = model.headerData(4, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole)
        self.assertIn('Fase principal',phase)
        self.assertIsNone(model.data(QModelIndex()))
        self.assertNotEqual(model.value(0,0,exact=False),model.value(1,0,exact=False))
        self.assertEqual(float(model.value(1,0)),float(source.axis[1]))
        self.assertTrue(table.table.isColumnHidden(1))
        self.assertFalse(table.table.isColumnHidden(3))
        table.position.setText('0')
        table.jump()
        self.assertIn('fuera del eje',table.coordinate_note.text())
        table.search_mode.setCurrentIndex(1)
        table.position.setText('3')
        table.jump()
        self.assertEqual(table.table.currentIndex().row(),2)
        selected = table.table.selectionModel()
        selected.select(model.index(2,3), QItemSelectionModel.SelectionFlag.ClearAndSelect)
        table.copy_selection()
        self.assertEqual(QApplication.clipboard().text(),'5')
        table.copy_rows()
        self.assertEqual(QApplication.clipboard().text().splitlines()[1].split('\t')[1:4],
                         ['4','-3','5'])
        table.set_signals([source],preserve_position=True)
        self.assertEqual(table.table.currentIndex().row(),2)
        table.columns.setCurrentIndex(2)
        table.select_cell(2,1)
        self.assertEqual(table.table.currentIndex().column(),0)
        table.resize(1400,400)
        table.columns.setCurrentIndex(0)
        self.assertFalse(table.table.isColumnHidden(1))
        self.assertFalse(table.table.isColumnHidden(3))
        table.set_signals([])
        table.jump()
        table.copy_selection()
        table.copy_rows()
        table.copy_page()
        self.assertEqual(table.model.rowCount(),0)

    def test_table_reports_a_figure_that_has_switched_to_another_trace(self):
        def make(figure):
            axis = figure.add_subplot()
            axis.plot([0,1],[11,12],label='Otra señal')
            return axis

        probe,_ = self.figure(make)
        table = ResultTable()
        self.addCleanup(table.deleteLater)
        source = Signal([3,4])
        table.set_signals([source])
        table.link_figure(probe.canvas)
        table.select_cell(1,0)
        table.locate_plot.click()
        self.assertIn('no contiene esta serie',table.coordinate_note.text())
        self.assertFalse(probe.canvas._signallab_window.isVisible())
        self.assertFalse(table.show_plot_sample(Signal([11,12]),1,'real'))
        self.assertFalse(table.show_plot_sample(source,3,'real'))
