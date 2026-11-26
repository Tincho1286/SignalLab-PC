import base64
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from signallab_pc.release_policy import publication_version
from signallab_pc.update_download import fetch_release
from signallab_pc.update_manifest import FEED_URL, FILENAMES, REPOSITORY, UpdateError
from tools.check_release_target import revision_metadata, validate, validate_history
from tools.github_release import GitHub, require_publication_checkout, sha256, validate_publication_files


CANDIDATE = 'abcd' * 10


class Wire(io.BytesIO):
    def __init__(self, body, url):
        super().__init__(body)
        self.url = url
        self.headers = {}

    def geturl(self):
        return self.url


class ReleasePolicyTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes_raw()
        self.now = datetime.now(timezone.utc)

    def manifest(self, version, channel, binary=b'x'):
        assets = {}
        from hashlib import sha256 as digest
        for tag, template in FILENAMES.items():
            name = template.format(version=version)
            assets[tag] = dict(name=name, url=f'https://github.com/{REPOSITORY}/releases/download/v{version}/{name}',
                               size=len(binary), sha256=digest(binary).hexdigest())
        value = {'schema': 1, 'channel': channel, 'version': version, 'notes': 'Candidato de ensayo',
                 'published_at': self.now.isoformat().replace('+00:00', 'Z'),
                 'expires_at': (self.now+timedelta(days=2)).isoformat().replace('+00:00', 'Z'),
                 'assets': assets}
        data = json.dumps(value).encode()
        return json.dumps({'payload': base64.b64encode(data).decode('ascii'),
                           'signature': base64.b64encode(self.key.sign(data)).decode('ascii')}).encode()

    def test_release_lines_have_independent_numeric_namespaces(self):
        self.assertEqual(publication_version('2.0.12', 'stable'), (2, 0, 12))
        self.assertEqual(publication_version('2.1.0', 'preview'), (2, 1, 0))
        for version, channel in (('2.1.0', 'stable'), ('2.0.3', 'preview'), ('1.9.9', 'preview'),
                                 ('02.0.1', 'stable'), ('2.0.1', 'experimental')):
            with self.subTest(version=version, channel=channel), self.assertRaises(ValueError):
                publication_version(version, channel)

    def test_stable_transport_rejects_previews_and_wrong_family_even_with_valid_signature(self):
        for version, channel in (('2.1.0', 'preview'), ('2.1.0', 'stable')):
            raw = self.manifest(version, channel)
            with self.subTest(channel=channel), self.assertRaises(UpdateError):
                fetch_release(opener=lambda url: Wire(raw, url), key=self.public, now=self.now)
        lts = self.manifest('2.0.2', 'stable')
        preview = self.manifest('2.1.0', 'preview')
        reads = []

        def open_package(url):
            reads.append(url)
            return Wire(lts if url == FEED_URL else preview, url)

        def catalog(url):
            rows = [dict(tag_name='v2.1.0', draft=False, prerelease=True,
                         assets=[dict(name='SignalLab-updates.json')])]
            return Wire(json.dumps(rows).encode(), url)

        stable = fetch_release(opener=open_package, key=self.public, now=self.now)
        self.assertEqual(stable.version, '2.0.2')
        self.assertEqual(reads, [FEED_URL])
        selected = fetch_release(channel='preview', opener=open_package, metadata_opener=catalog,
                                 key=self.public, now=self.now)
        self.assertEqual(selected.version, '2.1.0')
        self.assertEqual(selected.channel, 'preview')

    def test_workflow_checks_exact_sha_channel_and_stable_tag(self):
        accepted = [('preview', 'refs/heads/develop', '2.1.0'), ('stable', 'refs/tags/v2.0.7', '2.0.7')]
        for channel, ref, version in accepted:
            validate(channel, ref, CANDIDATE, CANDIDATE, version, channel)
        wrong = [
            ('preview', 'refs/heads/main', CANDIDATE, CANDIDATE, '2.1.0', 'preview'),
            ('preview', 'refs/heads/develop', CANDIDATE, 'ff'*20, '2.1.0', 'preview'),
            ('preview', 'refs/heads/develop', CANDIDATE, CANDIDATE, '2.1.0', 'stable'),
            ('stable', 'refs/tags/v2.0.6', CANDIDATE, CANDIDATE, '2.0.7', 'stable'),
        ]
        for args in wrong:
            with self.subTest(args=args), self.assertRaises(ValueError):
                validate(*args)
        tip = 'ef'*20
        with patch('tools.check_release_target.subprocess.run') as check:
            check.return_value.returncode = 0
            validate_history('preview', CANDIDATE, tip)
            self.assertEqual(check.call_args.args[0], ['git', 'merge-base', '--is-ancestor', CANDIDATE, tip])
            check.return_value.returncode = 1
            with self.assertRaisesRegex(ValueError, 'historial de develop'):
                validate_history('preview', CANDIDATE, tip)
        validate_history('stable', CANDIDATE, CANDIDATE)
        with self.assertRaises(ValueError):
            validate_history('stable', CANDIDATE, tip)
        code = "__version__='2.1.0'\n__release_channel__='preview'\nraise RuntimeError('Do not execute')"
        self.assertEqual(revision_metadata(code), ('2.1.0', 'preview'))

    def test_checkout_routes_preserve_origin_and_detached_maintenance_base(self):
        origin = 'cd'*20
        tag_tip = 'ef'*20

        def fake_git(args, **kwargs):
            if args[1:3] == ['status', '--porcelain']:
                return ''
            if args[1:3] == ['rev-parse', 'HEAD']:
                return CANDIDATE
            if args[1:4] == ['rev-parse', '--abbrev-ref', 'HEAD']:
                return 'HEAD'
            if args[1:3] == ['ls-remote', '--tags']:
                return f'{origin} refs/tags/v2.0.0\n{tag_tip} refs/tags/v2.0.0^{{}}'
            return f'{origin} refs/heads/develop'

        with (patch('tools.github_release.subprocess.check_output', side_effect=fake_git),
              patch('tools.github_release.subprocess.run', return_value=Mock(returncode=0)) as relation):
            require_publication_checkout(Path('.'), CANDIDATE, 'preview', None)
            self.assertEqual(relation.call_args.args[0][-2:], [CANDIDATE, origin])
            require_publication_checkout(Path('.'), CANDIDATE, 'stable', 'v2.0.0')
            self.assertEqual(relation.call_args.args[0][-2:], [tag_tip, CANDIDATE])
            with self.assertRaises(ValueError):
                require_publication_checkout(Path('.'), CANDIDATE, 'stable', 'v2.1.1')
            with self.assertRaises(ValueError):
                require_publication_checkout(Path('.'), 'ff'*20, 'preview', None)

    def files(self, folder, version, channel):
        source = f'SignalLab-PC-{version}-source.zip'
        windows = [f'SignalLab-PC-{version}.exe', FILENAMES['windows-x86_64'].format(version=version),
                   'installer-windows.json', source]
        linux = [f'SignalLab-PC-{version}-linux-x86_64.tar.gz', FILENAMES['linux-x86_64'].format(version=version),
                 'installer-linux.json']
        for name in (*windows, *linux):
            (folder/name).write_bytes(b'x')
        for system, names in (('windows', windows), ('linux', linux)):
            files = {name: {'sha256': sha256(folder/name), 'size': (folder/name).stat().st_size} for name in names}
            proof = {'commit': CANDIDATE, 'version': version, 'channel': channel, 'platform': system,
                     'source_fingerprint': '11'*32, 'files': files}
            (folder/f'candidate-{system}.json').write_text(json.dumps(proof), encoding='utf-8')
        (folder/'SignalLab-updates.json').write_bytes(self.manifest(version, channel))
        sums = ''.join(f'{sha256(path)}  {path.name}\n' for path in sorted(folder.iterdir()))
        (folder/f'SHA256SUMS-{version}.txt').write_text(sums, encoding='utf-8')
        return list(folder.iterdir())

    def gate(self, folder):
        runners = {'windows-2022': 'windows', 'ubuntu-22.04': 'linux'}
        return {'commit': CANDIDATE, 'automated_passed': True,
                'platforms': {runner: {'candidate_bundle': json.loads(
                    (folder/f'candidate-{system}.json').read_text(encoding='utf-8'))}
                    for runner, system in runners.items()}}

    def test_checksums_and_candidate_receipts_are_mandatory(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            assets = self.files(folder, '2.1.0', 'preview')
            gate = self.gate(folder)
            validate_publication_files('v2.1.0', CANDIDATE, 'preview', assets, gate)
            with self.assertRaisesRegex(ValueError, 'Quality Gate'):
                validate_publication_files('v2.1.0', CANDIDATE, 'preview', assets, gate | {'commit': 'ff'*20})
            gate['platforms']['windows-2022']['candidate_bundle']['files']['SignalLab-PC-2.1.0.exe']['sha256'] = 'a0'*32
            with self.assertRaisesRegex(ValueError, 'expediente del Quality Gate'):
                validate_publication_files('v2.1.0', CANDIDATE, 'preview', assets, gate)
            (folder/'SignalLab-PC-2.1.0.exe').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'checksums'):
                validate_publication_files('v2.1.0', CANDIDATE, 'preview', assets, self.gate(folder))

    def test_preview_publication_flags_never_replace_latest_or_modify_published_release(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            assets = self.files(folder, '2.1.0', 'preview')
            gate = self.gate(folder)
            publisher = GitHub.__new__(GitHub)
            publisher.repository = REPOSITORY
            publisher.require_repository = Mock()
            publisher.ensure_release_tag = Mock()
            publisher.upload = Mock()
            publisher.assets = Mock(return_value=[{'name': item.name} for item in assets])
            draft = {'id': 42, 'draft': True, 'prerelease': True}
            activated = {'html_url': 'https://example.invalid/release'}

            def api(method, path, body=None):
                if method == 'GET':
                    raise HTTPError(path, 404, 'missing', {}, None)
                if method == 'POST':
                    self.assertTrue(body['draft'])
                    self.assertTrue(body['prerelease'])
                    return draft
                self.assertEqual(method, 'PATCH')
                self.assertTrue(body['prerelease'])
                self.assertFalse(body['draft'])
                self.assertEqual(body['make_latest'], 'false')
                return activated

            publisher.api = Mock(side_effect=api)
            with (patch('signallab_pc.update_manifest.public_key', return_value=self.public),
                  patch('tools.github_release.require_publication_checkout') as validate_checkout):
                result, _ = publisher.publish('v2.1.0', 'Preview', 'Notes', assets, CANDIDATE,
                                              allow_public=True, gate=gate)
                self.assertEqual(result, activated)
                validate_checkout.assert_called_once_with(Path(__file__).resolve().parents[1], CANDIDATE, 'preview', None)
                publisher.ensure_release_tag.assert_called_once_with('v2.1.0', CANDIDATE, 'Preview', detached_lts=False)
                publisher.api = Mock(return_value=draft | {'draft': False})
                publisher.ensure_release_tag.reset_mock()
                with self.assertRaisesRegex(ValueError, 'conserva'):
                    publisher.publish('v2.1.0', 'Preview', 'Notes', assets, CANDIDATE, gate=gate)
                publisher.ensure_release_tag.assert_not_called()

    def test_lts_tag_transfers_detached_commit_without_pushing_a_branch(self):
        publisher = GitHub.__new__(GitHub)
        publisher.repository = REPOSITORY
        publisher.headers = Mock(return_value={})
        publisher.api = Mock(side_effect=[HTTPError('reference', 404, 'missing', {}, None),
                                         {'id': 42, 'login': 'maintainer'}])
        publisher.opener = MagicMock()
        publisher.opener.open.return_value.__enter__.return_value.headers = {
            'Date': 'Tue, 20 Apr 2027 15:00:00 GMT',
        }
        with (patch('tools.github_release.subprocess.check_output', return_value='fe'*20+'\n') as git_tag,
              patch('tools.github_release.subprocess.run') as git_push):
            publisher.ensure_release_tag('v2.0.1', CANDIDATE, 'Maintenance', detached_lts=True)
        self.assertEqual(git_tag.call_args.args[0], ['git', 'mktag'])
        self.assertIn(f'object {CANDIDATE}\ntype commit\ntag v2.0.1\n', git_tag.call_args.kwargs['input'])
        self.assertEqual(git_push.call_args.args[0], [
            'git', 'push', '--no-follow-tags', f'https://github.com/{REPOSITORY}.git', 'fe'*20+':refs/tags/v2.0.1',
        ])
        self.assertTrue(git_push.call_args.kwargs['check'])
        self.assertEqual([call.args[0] for call in publisher.api.call_args_list], ['GET', 'GET'])


if __name__ == '__main__':
    unittest.main()
