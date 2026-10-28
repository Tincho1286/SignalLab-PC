"""Esquemas legibles que se adaptan al ancho de la biblioteca."""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QTextDocument,QTextCursor
from .report_view import ReportView

class ResponsiveHelpView(ReportView):
    def resizeEvent(self,event):
        super().resizeEvent(event)
        width=min(680,max(120,self.viewport().width()-50));block=self.document().begin()
        while block.isValid():
            iterator=block.begin()
            while not iterator.atEnd():
                fragment=iterator.fragment();fmt=fragment.charFormat()
                if fmt.isImageFormat():
                    image_format=fmt.toImageFormat();name=image_format.name()
                    if name.startswith('help-diagram-'):
                        image=self.document().resource(QTextDocument.ResourceType.ImageResource,QUrl(name))
                        if image is not None and hasattr(image,'width') and image.width()>0 and image_format.width()!=width:
                            image_format.setWidth(width);image_format.setHeight(image.height()*width/image.width())
                            cursor=QTextCursor(self.document());cursor.setPosition(fragment.position());cursor.setPosition(fragment.position()+fragment.length(),QTextCursor.MoveMode.KeepAnchor);cursor.setCharFormat(image_format)
                iterator+=1
            block=block.next()
