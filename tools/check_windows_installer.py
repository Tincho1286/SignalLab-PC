"""Native Inno upgrade/uninstall check with a unique, isolated test identity."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import uuid
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--iscc', type=Path, required=True)
    parser.add_argument('--installer', type=Path, required=True)
    parser.add_argument('--allow-local-test-install', action='store_true')
    args = parser.parse_args()
    if sys.platform != 'win32': raise SystemExit('Run this test on Windows.')
    if os.environ.get('GITHUB_ACTIONS') != 'true' and not args.allow_local_test_install:
        raise SystemExit('This test installs a disposable fixture. Run it in the Windows build job.')
    import winreg
    identity = 'SignalLab.Setup.Contract.' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='signallab-installer-contract-') as name:
        work = Path(name); application = work / 'application'; data = work / 'user-data'; data.mkdir()
        (data / 'theme.json').write_text('{"theme":"custom"}')
        for version in ('1.0.0', '1.0.1'):
            payload = work / ('payload-' + version); payload.mkdir()
            (payload / 'SignalLab-PC.exe').write_bytes(('inert installer fixture ' + version).encode())
            (payload / 'LICENSE').write_text('Installer fixture only; never run this payload.')
            result = subprocess.run([str(args.iscc), '/DAppVersion=' + version, '/DPayloadDir=' + str(payload),
                '/DOutputDir=' + str(work), '/DInstallerAppId=' + identity,
                str(ROOT / 'packaging/windows-installer.iss')], capture_output=True, text=True)
            if result.returncode: raise RuntimeError(result.stdout + result.stderr)
            command = [str(work / f'SignalLab-PC-{version}-setup.exe'), '/VERYSILENT', '/SP-', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOLAUNCH']
            if version == '1.0.0': command.append('/DIR=' + str(application))
            subprocess.run(command, check=True, timeout=90)
            assert (application / 'SignalLab-PC.exe').read_bytes() == ('inert installer fixture ' + version).encode()
        assert (data / 'theme.json').read_text() == '{"theme":"custom"}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Uninstall' + '\\' + identity + '_is1', 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            assert winreg.QueryValueEx(key, 'DisplayVersion')[0] == '1.0.1'
        extra = application / 'my-notes.txt'; extra.write_text('preserve untracked user file')
        subprocess.run([str(application / 'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], check=True, timeout=90)
        assert not (application / 'SignalLab-PC.exe').exists()
        assert extra.read_text() == 'preserve untracked user file'
        assert (data / 'theme.json').is_file()
        real = work / 'real-application'
        subprocess.run([str(args.installer.resolve()), '/VERYSILENT', '/SP-', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOLAUNCH', '/DIR=' + str(real)], check=True, timeout=180)
        packaged = work / 'real-packaged-check.json'
        subprocess.run([str(real / 'SignalLab-PC.exe'), '--self-check', str(packaged)], check=True, timeout=180)
        proof = json.loads(packaged.read_text()); assert proof['ok'] and proof['frozen'] and all(proof['checks'].values())
        assert proof['checks']['packaged_update_verification']
        before = (real / 'SignalLab-PC.exe').read_bytes()
        older = subprocess.run([str(args.iscc), '/DAppVersion=0.0.1', '/DPayloadDir=' + str(payload),
            '/DOutputDir=' + str(work), str(ROOT / 'packaging/windows-installer.iss')], capture_output=True, text=True)
        if older.returncode: raise RuntimeError(older.stdout + older.stderr)
        rejected = subprocess.run([str(work / 'SignalLab-PC-0.0.1-setup.exe'), '/VERYSILENT', '/SP-', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOLAUNCH', '/DIR=' + str(real)], timeout=90)
        assert rejected.returncode != 0 and (real / 'SignalLab-PC.exe').read_bytes() == before
        subprocess.run([str(real / 'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'], check=True, timeout=120)
    output = ROOT / 'work/installer-contract-windows.json'; output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(dict(passed=True, checks=['native_upgrade_same_installation', 'per_user_registration', 'uninstall_preserves_untracked_files', 'real_installed_application_self_check', 'native_downgrade_rejected'], packaged=proof), indent=2))
    print('Native Windows installer: PASS')


if __name__ == '__main__': main()
