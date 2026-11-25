"""Check the illustrations and links shown to students by the help catalog."""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument

from signallab_pc.library_catalog import sections
from signallab_pc.visual_help import diagrams_for
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class HelpCatalogContracts(DesktopSessionFixture):
    def test_every_tool_guide_has_a_rendered_diagram_and_a_caption(self):
        guides = [guide for guide in sections() if guide['content_kind']=='tool']
        route_titles = {
            ('sampling',3): 'Núcleos, reloj y aportes',
            ('basic','measures'): 'Intervalo, distribución y componentes',
            ('systems',6): 'Cargar una raíz exacta',
            ('course_tools','convert'): 'Mapeo y corte efectivo',
            ('course_tools','phase'): 'Diseñar un compensador FIR',
            ('course_tools','bandpass_sampling'): 'Banda de la señal y frecuencia de muestreo',
            ('basic','sum'): 'Sumar en el mismo índice',
            ('fir_window',0): 'Enventanado punto a punto',
            ('transform_lab','z'): 'Cómo elegir la región de convergencia',
            ('transform_lab','laplace'): 'ROC y soporte temporal',
            ('dtft_symbolic',1): 'Un período y sus muestras',
        }
        visited = set()
        self.assertGreater(len(guides),60)
        for guide in guides:
            route = tuple(guide['route'][1:3])
            with self.subTest(route=route):
                visited.add(route)
                diagrams = diagrams_for(guide)
                self.assertTrue(diagrams)
                if route in route_titles:
                    self.assertIn(route_titles[route],[title for title,_,_ in diagrams])
                for title,picture,caption in diagrams:
                    self.assertTrue(title.strip())
                    self.assertTrue(caption.strip())
                    self.assertFalse(picture.isNull())
                    self.assertGreater(picture.width(),200)
                    self.assertGreater(picture.height(),100)
                    pixels = {picture.pixel(x,y)
                              for x in range(0,picture.width(),21)
                              for y in range(0,picture.height(),17)}
                    self.assertGreater(len(pixels),3,f'{title}: el dibujo sólo contiene un fondo')
        self.assertTrue(route_titles.keys() <= visited)

    def test_context_help_exposes_real_resources_and_preserves_the_return_destination(self):
        window = self.window()
        route = ROUTES['course_tools','bandpass_sampling']
        window.open_tool(route)
        original = window.pages[route]
        window.open_help()
        library = window.pages['menu','Biblioteca']
        document = library.text.document()
        images = []
        block = document.begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fmt = iterator.fragment().charFormat()
                if fmt.isImageFormat():
                    url = QUrl(fmt.toImageFormat().name())
                    images.append(document.resource(QTextDocument.ResourceType.ImageResource,url))
                iterator += 1
            block = block.next()
        self.assertTrue(images)
        self.assertTrue(all(image is not None and not image.isNull() for image in images))
        self.assertIn('Ωs separa las réplicas',library.text.toPlainText())
        library.follow_reference(QUrl('library:fields'))
        self.assertEqual(library.return_route,route)
        library.follow_reference(QUrl('library:glossary'))
        self.assertIn('Glosario',library.search.text())
        self.assertEqual(library.return_route,route)
        library.return_to_tool()
        self.assertIs(window.pages[window.current_operation],original)
