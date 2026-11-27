"""Prevent incomplete Phase 05 reports from qualifying or authorizing publication."""

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from tools.github_release import validate_publication_files


SHA = '57' * 20


class PhaseFiveGateTests(unittest.TestCase):
    def gate(self, folder, version='2.3.0'):
        proc = subprocess.run(
            [sys.executable, '-B', '-X', 'utf8', 'tools/check_quality_gate_05.py',
             '--input', str(folder), '--output', str(folder / 'out'),
             '--candidate', SHA, '--version', version],
            capture_output=True, encoding='utf-8', timeout=20,
        )
        return proc

    def test_incomplete_candidate_fails_with_specific_platform_findings(self):
        with TemporaryDirectory() as root:
            folder = Path(root)
            windows = folder / 'engineering-baseline-windows-2022-1'
            windows.mkdir()
            report = {'schema': 1, 'phase': '05', 'commit': SHA, 'clean_checkout': True,
                      'headless': True, 'desktop': True, 'interface_parity': True,
                      'p0_open': 0, 'p1_internal_open': 0,
                      'requirements': {'ST-01': {'passed': True, 'reference_cases': 12}}}
            (windows / 'statistical-qualification.json').write_text(json.dumps(report), encoding='utf-8')
            result = self.gate(folder)
            self.assertEqual(result.returncode, 1, result.stderr)
            data = json.loads((folder / 'out' / 'quality-gate-05.json').read_bytes())
            self.assertFalse(data['automated_passed'])
            self.assertEqual((data['commit'], data['phase'], data['version']), (SHA, '05', '2.3.0'))
            windows_checks = data['platforms']['windows-2022']['checks']
            self.assertTrue(windows_checks['scientific_interface_parity'])
            self.assertFalse(windows_checks['scientific_requirements'])
            self.assertFalse(windows_checks['phase_04_controls'])
            self.assertFalse(windows_checks['statistical_profiles'])
            self.assertFalse(data['platforms']['ubuntu-22.04']['checks']['scientific_interface_parity'])

            report['commit'] = '94' * 20
            (windows / 'statistical-qualification.json').write_text(json.dumps(report), encoding='utf-8')
            self.assertEqual(self.gate(folder).returncode, 1)
            changed = json.loads((folder / 'out' / 'quality-gate-05.json').read_bytes())
            self.assertFalse(changed['platforms']['windows-2022']['checks']['scientific_interface_parity'])

    def test_rejects_non_phase_five_source_and_mismatched_release_evidence(self):
        with TemporaryDirectory() as root:
            folder = Path(root)
            result = self.gate(folder, '2.2.1')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('2.3.x', result.stderr)
            self.assertFalse((folder / 'out').exists())
        for gate in (
            {'phase': '04', 'version': '2.3.0'},
            {'phase': '05', 'version': '2.3.1'},
        ):
            with self.subTest(gate=gate), self.assertRaisesRegex(ValueError, 'Fase 05'):
                validate_publication_files('v2.3.0', SHA, 'preview', [], {
                    **gate, 'commit': SHA, 'automated_passed': True,
                })
