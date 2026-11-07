"""Exercise the actual .run payload and installed executable in a private home."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('installer', type=Path)
    args = parser.parse_args()
    if sys.platform != 'linux': raise SystemExit('Run on native Linux.')
    with tempfile.TemporaryDirectory(prefix='signallab-install-smoke-') as name:
        home = Path(name); root = home / '.local/share/SignalLab-PC'
        env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(home / '.local/share'),
                   XDG_CONFIG_HOME=str(home / '.config'), XDG_CACHE_HOME=str(home / '.cache'),
                   QT_QPA_PLATFORM='offscreen', PYINSTALLER_RESET_ENVIRONMENT='1')
        settings = home / '.config/SignalLab/saved-theme.json'; settings.parent.mkdir(parents=True)
        settings.write_text('{"theme":"keep"}')
        command = ['/bin/sh', str(args.installer.resolve()), '--headless', '--target', str(root)]
        subprocess.run(command, env=env, check=True, timeout=180)
        binary = root / 'current/SignalLab-PC'; assert binary.is_file()
        check = home / 'packaged-check.json'
        subprocess.run([str(binary), '--self-check', str(check)], env=env, check=True, timeout=180)
        proof = json.loads(check.read_text()); assert proof['ok'] and proof['frozen'] and all(proof['checks'].values())
        assert proof['checks']['packaged_update_verification']
        subprocess.run(command, env=env, check=True, timeout=180)
        assert settings.read_text() == '{"theme":"keep"}'
        note = root / 'my-notes.txt'; note.write_text('keep user file')
        subprocess.run([str(binary), '--install-linux', '--headless', '--uninstall', '--target', str(root)], env=env, check=True, timeout=120)
        assert not (root / 'current').is_symlink(); assert note.read_text() == 'keep user file'
        assert settings.read_text() == '{"theme":"keep"}'
    output = ROOT / 'work/installer-contract-linux.json'; output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(dict(passed=True, checks=['real_run_payload', 'installed_packaged_self_check', 'repair_in_place', 'uninstall_preserves_data'], packaged=proof), indent=2))
    print('Native packaged Linux installer: PASS')


if __name__ == '__main__': main()
