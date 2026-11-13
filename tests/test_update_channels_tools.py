"""Signed preview selection and practical controls added in 1.8.3."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import base64,csv,hashlib,io,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from threading import Event
from unittest.mock import Mock,patch
import numpy as np
from numpy.testing import assert_allclose
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from signallab_pc.update_manifest import REPOSITORY,FILENAMES,FEED_URL,verify_manifest,UpdateError
from signallab_pc.update_download import fetch_release,Cancelled
from signallab_pc.update_channels import page_url,PER_PAGE


class Wire(io.BytesIO):
    def __init__(self,data,url):super().__init__(data);self.url=url;self.headers={}
    def geturl(self):return self.url


class PreviewContracts(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate();self.public=self.key.public_key().public_bytes_raw();self.now=datetime.now(timezone.utc);self.manifests={}
        self.manifests[FEED_URL]=self.envelope('2.0.0','stable')

    def envelope(self,version,channel,targets=None):
        assets={}
        for tag in targets or FILENAMES:
            name=FILENAMES[tag].format(version=version)
            assets[tag]=dict(name=name,url=f'https://github.com/{REPOSITORY}/releases/download/v{version}/{name}',size=1,sha256=hashlib.sha256(b'x').hexdigest())
        payload=dict(schema=1,channel=channel,version=version,published_at=self.now.isoformat().replace('+00:00','Z'),expires_at=(self.now+timedelta(days=30)).isoformat().replace('+00:00','Z'),notes=version+' '+channel,assets=assets)
        raw=json.dumps(payload).encode();return json.dumps(dict(payload=base64.b64encode(raw).decode(),signature=base64.b64encode(self.key.sign(raw)).decode())).encode()

    def preview(self,version,*,signed=True,targets=None):
        if signed:self.manifests[f'https://github.com/{REPOSITORY}/releases/download/v{version}/SignalLab-updates.json']=self.envelope(version,'preview',targets)
        return dict(tag_name='v'+version,draft=False,prerelease=True,assets=[{'name':'SignalLab-updates.json','state':'uploaded'}] if signed else [])

    def query(self,pages,**options):
        def metadata(url):return Wire(json.dumps(pages[url]).encode(),url)
        return fetch_release(channel='preview',key=self.public,now=self.now,opener=lambda url:Wire(self.manifests[url],url),metadata_opener=metadata,**options)

    def test_preview_requires_opt_in_and_selects_highest_version_not_list_order(self):
        rows=[self.preview('2.0.1'),self.preview('2.0.3'),self.preview('2.0.2')]
        release=self.query({page_url(1):rows});self.assertEqual(release.version,'2.0.3');self.assertEqual(release.channel,'preview')
        raw=self.manifests[f'https://github.com/{REPOSITORY}/releases/download/v2.0.3/SignalLab-updates.json']
        with self.assertRaises(UpdateError):verify_manifest(raw,key=self.public,now=self.now)
        with self.assertRaises(UpdateError):verify_manifest(raw,key=self.public,now=self.now,expected_channel='preview',expected_version='2.0.4')

    def test_missing_invalid_and_incompatible_previews_leave_verified_choices(self):
        unsigned=self.preview('2.0.8',signed=False);wrong=self.preview('2.0.7');windows=self.preview('2.0.6',targets=['windows-x86_64']);good=self.preview('2.0.5')
        self.manifests[f'https://github.com/{REPOSITORY}/releases/download/v2.0.7/SignalLab-updates.json']=b'unsigned'
        release=self.query({page_url(1):[unsigned,wrong,windows,good]},target='linux-x86_64')
        self.assertEqual(release.version,'2.0.5');self.assertGreaterEqual(len(release.notices),2)

    def test_pagination_and_official_urls_are_used(self):
        rows=[dict(draft=False,prerelease=False,tag_name='v1.0.0') for _ in range(PER_PAGE)]
        candidate=self.preview('2.0.1');candidate['assets'][0]['browser_download_url']='https://evil.example/installer'
        release=self.query({page_url(1):rows,page_url(2):[candidate]});self.assertEqual(release.version,'2.0.1')

    def test_metadata_failure_retains_stable_and_cancellation_is_not_swallowed(self):
        def denied(url):raise OSError('offline')
        release=fetch_release(channel='preview',key=self.public,now=self.now,opener=lambda url:Wire(self.manifests[url],url),metadata_opener=denied)
        self.assertEqual(release.version,'2.0.0');self.assertTrue(release.notices)
        cancel=Event();cancel.set()
        with self.assertRaises(Cancelled):self.query({page_url(1):[]},cancel=cancel)

    def test_release_publisher_refuses_unsigned_or_wrong_channel_installers_before_network(self):
        from tools.github_release import GitHub
        publisher=GitHub.__new__(GitHub);publisher.require_repository=Mock()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);installer=root/'SignalLab-PC-2.0.0-setup.exe';installer.write_bytes(b'x')
            with self.assertRaisesRegex(ValueError,'manifiesto'):publisher.publish('v2.0.0','Title','Notes',[installer],'commit',allow_public=True)
            manifest=root/'SignalLab-updates.json';manifest.write_bytes(self.envelope('2.0.0','stable',targets=['windows-x86_64']))
            with patch('signallab_pc.update_manifest.public_key',return_value=self.public),self.assertRaises(UpdateError):
                publisher.publish('v2.0.0','Title','Notes',[installer,manifest],'commit',prerelease=True,allow_public=True)
            publisher.require_repository.assert_not_called()


class ResamplingContracts(unittest.TestCase):
    def test_requested_rate_and_actual_intermediate_filter_match_the_sum_definition(self):
        from scipy.signal import firwin
        from signallab_pc.model import Signal
        from signallab_pc.resampling_tools import convert,rate_ratio
        self.assertEqual(rate_ratio(48000,'44.1e3'),(147,160));self.assertEqual(rate_ratio(48000,'44100,0'),(147,160))
        source=Signal([1,2,-1],-4,metadata={'sample_rate_hz':12.,'time_start_s':2.})
        data=convert(source,2,3,half_width=2,beta=5);system=data['filter'];out=data['signal'];kernel=2*firwin(13,1/3,window=('kaiser',5))
        assert_allclose(system.b,kernel);self.assertAlmostEqual(system.sample_period_s,1/24)
        expected=[sum(source.values[k]*kernel[j*3-k*2+6] for k in range(3) if 0<=j*3-k*2+6<len(kernel)) for j in range(2)]
        assert_allclose(out.values,expected,atol=1e-14);self.assertEqual(out.metadata['sample_rate_hz'],8)

    def test_identity_and_clock_reinterpretation_keep_their_meaning(self):
        from signallab_pc.model import Signal
        from signallab_pc.resampling_tools import convert,rate_ratio
        source=Signal([1,2,3],metadata={'sample_rate_hz':48000.,'time_start_s':0.})
        data=convert(source,1,1,target='48000');assert_allclose(data['signal'].values,source.values);assert_allclose(data['filter'].b,[1])
        self.assertEqual(data['signal'].metadata['up'],1)
        with self.assertRaises(ValueError):rate_ratio(48000,'pi')
        with self.assertRaises(ValueError):convert(source,1,1,rate=32000,start=0)


class PracticalUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def setUp(self):self.widgets=[]
    def tearDown(self):
        for widget in self.widgets:widget.close();widget.deleteLater()
        self.app.processEvents()

    def controller(self,folder):
        from PySide6.QtWidgets import QMainWindow
        from PySide6.QtCore import QSettings
        from signallab_pc.update_ui import UpdateController
        host=QMainWindow();host._workers=[];host.settings=QSettings(str(Path(folder)/'settings.ini'),QSettings.Format.IniFormat);self.widgets.append(host)
        with patch('signallab_pc.update_ui.installed',return_value=None):controller=UpdateController(host)
        return controller

    def test_channel_choice_persists_and_invalidates_a_prepared_installer(self):
        with tempfile.TemporaryDirectory() as folder:
            controller=self.controller(folder);controller.path=Path('old');controller.asset=object();controller.dialog.apply.setEnabled(True)
            controller.dialog.channel.setCurrentIndex(1)
            self.assertEqual(controller.channel,'preview');self.assertIsNone(controller.path);self.assertIsNone(controller.asset);self.assertFalse(controller.dialog.apply.isEnabled())
            other=self.controller(folder);self.assertEqual(other.dialog.channel.currentData(),'preview')

    def test_cancellation_after_worker_finished_does_not_accept_a_queued_result(self):
        with tempfile.TemporaryDirectory() as folder:
            controller=self.controller(folder);accept=Mock();controller._start(lambda *_:'finished',accept);job=controller.job
            self.assertTrue(job.wait(3000));controller.cancel();self.app.processEvents()
            accept.assert_not_called();self.assertIsNone(controller.job);self.assertTrue(controller.dialog.channel.isEnabled())

    def test_target_rate_ignores_hidden_factors_and_exposes_the_filter(self):
        from test_workflow_contracts import Host
        from signallab_pc.rational_resampling_panel import RationalResamplingPanel
        host=Host();self.widgets.append(host.bar);panel=RationalResamplingPanel(host);self.widgets.append(panel)
        panel.source.mode.setCurrentIndex(1);panel.source.samples.setText('1, 2, 3');panel.rate.setText('12');panel.mode.setCurrentIndex(1);panel.target.setText('8')
        panel.up.setText('invalid hidden field');panel.down.setText('invalid hidden field');panel.width.setText('2')
        with patch('PySide6.QtWidgets.QMessageBox.warning') as warning:panel.calculate_button.click();warning.assert_not_called()
        self.assertIsNotNone(panel.filter_actions.system);self.assertTrue(panel.result.views.isTabVisible(panel.filter_index))
        self.assertIn('2/3',panel.result.text.toPlainText());self.assertAlmostEqual(panel.filter_actions.system.sample_period_s,1/24)

    def test_cas_operations_use_selected_reference_keep_draft_and_choose_its_variable(self):
        from test_workflow_contracts import Host
        from signallab_pc.cas_panel import CasWorksheet
        host=Host();self.widgets.append(host.bar);sheet=CasWorksheet(host);self.widgets.append(sheet)
        sheet.input.setPlainText('(z+1)/(z-2)');sheet.calculate();sheet.input.setPlainText('draft + 1')
        sheet.operate_result('apart');self.assertEqual(sheet.input.toPlainText(),'draft + 1');self.assertEqual(sheet.entries[-1]['source'],'apart(r1,z)');self.assertEqual(sheet.entries[-1]['status'],'done')
        sheet.result_digits.setText('30');sheet.operate_result('approx');self.assertEqual(sheet.entries[-1]['source'],'approx(r2,30)');self.assertEqual(sheet.entries[-1]['status'],'done')
        sheet.input.clear();sheet.insert_template('diff(expr,x)');self.assertEqual(sheet.input.toPlainText(),'diff(r3,z)')

    def test_plot_button_reserves_a_separate_menu_zone_and_opens_the_chosen_figure(self):
        from PySide6.QtWidgets import QWidget,QVBoxLayout,QStyleOptionToolButton,QStyle
        from PySide6.QtCore import Qt,QTimer,QPoint
        from PySide6.QtTest import QTest
        from signallab_pc.plot_actions import PlotLauncher
        from signallab_pc.desktop_theme import desktop_style
        host=QWidget();self.widgets.append(host);host.setStyleSheet(desktop_style());layout=QVBoxLayout(host);button=PlotLauncher(host);layout.addWidget(button)
        canvases=[QWidget(),QWidget()]
        for canvas in canvases:self.widgets.append(canvas);canvas._signallab_has_plot_result=True;button.register(canvas,[],'Figura')
        host.show();self.app.processEvents();option=QStyleOptionToolButton();button.initStyleOption(option)
        menu=button.style().subControlRect(QStyle.ComplexControl.CC_ToolButton,option,QStyle.SubControl.SC_ToolButtonMenu,button)
        self.assertGreaterEqual(menu.width(),28);self.assertGreater(menu.left(),button.fontMetrics().horizontalAdvance(button.text())+10)
        with patch.object(button,'open_entry') as opened:
            QTest.mouseClick(button,Qt.MouseButton.LeftButton,pos=button.rect().topLeft()+QPoint(12,button.height()//2));self.assertEqual(opened.call_count,1)
            opened.reset_mock()
            def select():button.menu.actions()[1].trigger();button.menu.close()
            QTimer.singleShot(50,select);QTest.mouseClick(button,Qt.MouseButton.LeftButton,pos=menu.center())
            self.assertEqual(opened.call_count,1);self.assertIs(opened.call_args.args[0][0](),canvases[1])


if __name__=='__main__':unittest.main()
