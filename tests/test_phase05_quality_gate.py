"""Prevent incomplete Phase 05 reports from qualifying or authorizing publication."""

from hashlib import sha256
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

    def test_evidence_is_bound_to_the_integral_report_and_the_actual_demonstrators(self):
        with TemporaryDirectory() as root:
            folder = Path(root)
            windows = folder/'engineering-baseline-windows-2022-1'
            windows.mkdir()
            integral = b'{"records":[]}'
            (windows/'integral-checks.json').write_bytes(integral)
            report = {'schema':1,'phase':'05','commit':SHA,'clean_checkout':True,
                      'integral_sha256':sha256(integral).hexdigest(),'demonstrators':{}}
            examples = windows/'demonstrators'
            for key in 'ABCDE':
                file = examples/key/'report.json'
                file.parent.mkdir(parents=True)
                contents = b'{"checks":[{"actual":0.5,"reference":0.5,"absolute_tolerance":1e-10}]}'
                file.write_bytes(contents)
                report['demonstrators'][key] = {'passed':True,'reference_cases':1,'report':f'{key}/report.json',
                                                 'sha256':sha256(contents).hexdigest()}
            (windows/'statistical-qualification.json').write_text(json.dumps(report),encoding='utf-8')

            def integrity():
                self.assertEqual(self.gate(folder).returncode,1)
                data = json.loads((folder/'out'/'quality-gate-05.json').read_bytes())
                return data['platforms']['windows-2022']['checks']['statistical_evidence_integrity']

            self.assertTrue(integrity())
            file = examples/'E'/'report.json'
            modified = b'{"checks":[{"actual":0.6,"reference":0.5,"absolute_tolerance":1e-10}]}'
            file.write_bytes(modified)
            self.assertFalse(integrity())
            report['demonstrators']['E']['sha256'] = sha256(modified).hexdigest()
            (windows/'statistical-qualification.json').write_text(json.dumps(report),encoding='utf-8')
            self.assertFalse(integrity())

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

    def test_native_coverage_requires_both_paths_over_the_same_denominator(self):
        with TemporaryDirectory() as root:
            folder=Path(root)
            paths=[]
            for platform in ('windows-2022','ubuntu-22.04'):
                platform_dir=folder/f'engineering-baseline-{platform}-1'
                platform_dir.mkdir()
                paths.append(platform_dir/'coverage.json')

            def source(executed,missing,arcs,uncovered):
                return {'files': {'signallab_pc/campaign_files.py': {
                    'executed_lines':executed,'missing_lines':missing,
                    'executed_branches':arcs,'missing_branches':uncovered,
                    'summary': {'num_statements':len(executed)+len(missing),'covered_lines':len(executed),
                                'num_branches':len(arcs)+len(uncovered),'covered_branches':len(arcs),
                                'missing_lines':len(missing)},
                }}}

            windows=source([1,2,3],[4],[[2,3]],[[2,4]])
            linux=source([1,2,4],[3],[[2,4]],[[2,3]])

            def coverage():
                result=self.gate(folder)
                self.assertEqual(result.returncode,1,result.stderr)
                path=folder/'out'/'quality-gate-05.json'
                self.assertTrue(path.is_file(),result.stderr)
                report=json.loads(path.read_bytes())
                return report['combined_native_coverage']['campaign_files.py']

            paths[0].write_text(json.dumps(windows),encoding='utf-8')
            self.assertEqual(coverage()['lines']['state'],'missing')
            paths[1].write_text(json.dumps(linux),encoding='utf-8')
            combined=coverage()
            self.assertEqual((combined['lines']['covered'],combined['lines']['total']),(4,4))
            self.assertEqual((combined['branches']['covered'],combined['branches']['total']),(2,2))
            paths[1].write_text(json.dumps(windows),encoding='utf-8')
            self.assertEqual(coverage()['branches']['state'],'fail')
            paths[1].write_text(json.dumps(source([1,2,5],[3],[[2,5]],[[2,3]])),encoding='utf-8')
            self.assertEqual(coverage()['lines']['state'],'missing')
