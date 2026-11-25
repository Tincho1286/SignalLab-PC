"""Check spectra and frequency mapping through the visible tool actions."""
import math
import re

import numpy as np

from signallab_pc.model import Signal
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class SpectralStudyContracts(DesktopSessionFixture):
    def select(self, panel, name, key):
        field = panel.fields[name]
        field.setCurrentIndex(field.findData(key))

    def test_frequency_mapping_covers_inverses_alias_branches_and_ignored_fields(self):
        route = ROUTES['course_tools','mapping']
        window = self.window()
        window.open_tool(route)
        panel = window.pages[route].panel
        for method,direction,fields,expected,units in [
            ('bilinear','to_digital',('','8','1/4',''),math.pi/2,'rad/muestra'),
            ('bilinear','to_analog',('pi/2','','1/4',''),8,'rad/s'),
            ('bilinear','period',('-pi/2','-8','',''),0.25,'s'),
            ('impulse','to_digital',('','5*pi','1/2',''),math.pi/2,'rad/muestra'),
            ('impulse','to_analog',('pi/2','','1/2','-1'),-3*math.pi,'rad/s'),
            ('impulse','period',('pi/2','5*pi','','1'),0.5,'s'),
        ]:
            with self.subTest(method=method,direction=direction):
                self.select(panel,'method',method)
                self.select(panel,'direction',direction)
                for name,text in zip(('omega','analog','period','branch'),fields):
                    panel.fields[name].setText(text)
                previous = len(window.project.headers())
                window.calculate_active()
                self.wait_for_calculation(window)
                self.assertEqual(len(window.project.headers()),previous+1)
                report = panel.report.toPlainText()
                value,actual_units = re.search(r'Resultado: (\S+) (\S+)',report).groups()
                self.assertAlmostEqual(float(value),expected,places=10)
                self.assertEqual(actual_units,units)

        self.select(panel,'method','bilinear')
        self.select(panel,'direction','to_analog')
        panel.fields['omega'].setText('pi')
        panel.fields['period'].setText('1/2')
        previous = window.project.headers()
        report = panel.report.toPlainText()
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(window.project.headers(),previous)
        self.assertEqual(panel.report.toPlainText(),report)
        self.assertIn('Revisá los datos',window.statusBar().currentMessage())
        panel.fields['omega'].setText('0')
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIn('Resultado: 0 rad/s',panel.report.toPlainText())

    def test_spectral_line_weights_inherit_period_and_switch_back_to_manual_input(self):
        route = ROUTES['course_tools','lines']
        window = self.window()
        window.open_tool(route)
        panel = window.pages[route].panel
        source = Signal([1j,2,-1j],origin=-1,name='Serie de seno desplazado',
                        metadata={'period_s':8,'operation':'continuous_fourier_series'})
        key = window.publish(source,operation='Coeficientes de serie continua')
        panel.source.set_source(source,key)
        self.assertTrue(panel.fields['period'].isReadOnly())
        window.calculate_active()
        self.wait_for_calculation(window)
        result = window.project.get(panel.records[0])
        np.testing.assert_allclose(result.axis,[-math.pi/4,0,math.pi/4],rtol=1e-14)
        np.testing.assert_allclose(result.values,2*math.pi*np.array([1,4,1]),rtol=1e-14)
        self.assertTrue(result.metadata['power_line_weights'])
        record = next(row for row in window.project.headers() if row['id']==panel.records[0])
        self.assertEqual(record['parents'],[key])
        self.assertIn('Potencia de los armónicos disponibles: 6',panel.report.toPlainText())

        panel.source.mode.setCurrentIndex(0)
        self.assertFalse(panel.fields['period'].isReadOnly())
        panel.source.expression.setText('3*impulse(n)')
        panel.source.origin.setText('0')
        panel.source.count.setText('2')
        panel.fields['period'].setText('4')
        window.calculate_active()
        self.wait_for_calculation(window)
        result = window.project.get(panel.records[0])
        np.testing.assert_allclose(result.axis,[0,math.pi/2],rtol=1e-14)
        np.testing.assert_allclose(result.values,[18*math.pi,0],rtol=1e-14)
