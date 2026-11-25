"""The audit must distinguish incomplete evidence from a passing criterion."""
import json
from pathlib import Path
import tempfile
import unittest

from tools.check_quality_gate_02c import CANCELLATION_OPERATIONS, evidence, within_threshold


class QualityGateTests(unittest.TestCase):
    def test_missing_platform_artifacts_and_inconsistent_candidate_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            absent = evidence([folder], 'target', 'Windows')
            self.assertEqual(absent['checks']['clean_revision'], 'missing')
            self.assertEqual(absent['coverage']['lines']['state'], 'missing')
            (folder/'baseline.json').write_text(json.dumps({
                'commit': 'target', 'commit_after': 'previous',
                'os': 'Windows runner', 'stages': {'static': 0},
            }), encoding='utf-8')
            result = evidence([folder], 'target', 'Windows')
            self.assertEqual(result['checks']['clean_revision'], 'fail')
            self.assertEqual(result['checks']['static'], 'pass')
            self.assertEqual(result['checks']['portable'], 'missing')
            self.assertEqual(result['components']['project_archive.py']['branches']['state'], 'missing')

    def test_threshold_uses_exact_counts_instead_of_rounded_display(self):
        row = dict(num_statements=20001, covered_lines=17000, num_branches=4, covered_branches=3)
        measured = within_threshold(row, 85, 75)
        self.assertEqual(measured['lines']['state'], 'fail')
        self.assertEqual(measured['lines']['additional_required'], 1)
        self.assertEqual(measured['branches']['state'], 'pass')
        self.assertEqual(within_threshold(dict(row, covered_lines=20002), 85, None)['lines']['state'], 'fail')

    def test_cancellation_evidence_rejects_a_changed_output_and_missing_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            report = folder/'core-performance.json'
            cases = [dict(operation=name, status='cancelled', files_preserved=True)
                     for name in sorted(CANCELLATION_OPERATIONS)]
            cases += [dict(row, samples=1048576) for row in cases[:8]]

            def verdict():
                report.write_text(json.dumps({'cancellation': cases, 'symbolic_cancellation': {'ms': 50}}),
                                  encoding='utf-8')
                return evidence([folder], 'target', 'Windows')['checks']['cancellation_profiles']

            self.assertEqual(verdict(), 'pass')
            cases[0]['files_preserved'] = False
            self.assertEqual(verdict(), 'fail')
            cases[0]['files_preserved'] = True
            for row in cases:
                if row['operation'] == 'mat_hdf5':
                    row['operation'] = 'mat_classic'
            self.assertEqual(verdict(), 'fail')
