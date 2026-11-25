"""Local photo import, managed copies and readable translucent backgrounds."""
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QImage, QPainter

from signallab_pc import wallpaper
from test_desktop_session import DesktopSessionFixture


class WallpaperContracts(DesktopSessionFixture):
    def write_photo(self,name,color):
        image=QImage(24,12,QImage.Format.Format_RGB32)
        image.fill(QColor(color))
        path=self.path/name
        self.assertTrue(image.save(str(path)))
        return path

    def test_managed_copies_keep_source_and_clean_only_matching_old_files(self):
        first=self.write_photo('original.png','#336699')
        second=self.write_photo('other.bmp','#ff0000')
        folder=self.path/'appearance'
        one=Path(wallpaper.save_photo(first,folder))
        self.assertEqual(one.parent,folder)
        self.assertEqual(one.read_bytes(),first.read_bytes())
        self.assertEqual(wallpaper.save_photo(one,folder),str(one))
        two=Path(wallpaper.save_photo(second,folder))
        self.assertNotEqual(one,two)
        cached=wallpaper.pixmap(one)
        self.assertEqual(cached.toImage().pixelColor(1,1).name(),'#336699')
        self.assertEqual(wallpaper.pixmap(one).cacheKey(),cached.cacheKey())
        note=folder/'proyecto.json'
        note.write_text('{}',encoding='utf-8')
        with patch('signallab_pc.wallpaper.appearance_folder',return_value=folder):
            wallpaper.clean_previous(first)
            self.assertTrue(one.exists())
            wallpaper.clean_previous(two)
        self.assertFalse(one.exists())
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertTrue(two.exists())
        self.assertTrue(note.exists())
        self.assertTrue(wallpaper.pixmap(one).isNull())

    def test_photo_rejects_non_raster_and_paints_cover_and_contain_at_calculated_opacity(self):
        photo=self.write_photo('red.png','#ff0000')
        bad=self.path/'unreadable.png'
        bad.write_text('Datos sin imagen.',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'imagen'):
            wallpaper.save_photo(bad,self.path/'managed')
        self.assertFalse((self.path/'managed').exists())
        with self.assertRaises(OSError):
            wallpaper.read_photo(self.path/'missing.jpg')

        def canvas(fit):
            image=QImage(40,40,QImage.Format.Format_RGB32)
            painter=QPainter(image)
            try:
                wallpaper.paint(painter,QRectF(image.rect()),{'window':'#000000'},
                                {'fit':fit,'photo':str(photo),'opacity':50})
            finally:
                painter.end()
            return image

        contained=canvas('contain')
        covered=canvas('cover')
        self.assertEqual(contained.pixelColor(20,2).red(),0)
        for image,point in [(contained,(20,20)),(covered,(20,2))]:
            color=image.pixelColor(*point)
            self.assertLessEqual(abs(color.red()-128),1)
            self.assertEqual((color.green(),color.blue()),(0,0))
