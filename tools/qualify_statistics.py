"""Assemble Phase 05 scientific evidence from a clean integral run and saved studies."""

import argparse
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.abc import MetaPathFinder
from io import StringIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from check_engineering_baseline import clean_revision


REFERENCE_SUITES = {
    'ST-01': ('test_probability',),
    'ST-02': ('test_descriptive_statistics', 'test_statistical_inference'),
    'ST-03': ('test_stochastic_processes', 'test_stochastic_noise', 'test_stochastic_covariance'),
    'ST-04': ('test_ar_estimation', 'test_time_series_identification'),
    'ST-05': ('test_statistical_spectra',),
    'ST-06': ('test_optimal_estimation', 'test_kalman_filter', 'test_adaptive_filter'),
    'ST-07': ('test_monte_carlo',),
    'ST-08': ('test_probability_desktop','test_arma_desktop','test_estimation_desktop','test_monte_carlo_desktop',
              'test_communications_desktop'),
    'ST-09': ('test_monte_carlo', 'test_math_scientific_storage', 'test_math_project_archive'),
}


class WithoutQt(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'PySide6','shiboken6','PyQt5','PyQt6','qtpy'}:
            raise AssertionError(f'Importación de Qt durante la calificación sin pantalla: {fullname}.')


def parity():
    from signallab_pc import session
    from signallab_pc.__main__ import main
    from signallab_pc.descriptive_statistics import describe_record
    from signallab_pc.probability import Distribution, generate_realizations

    def invoke(arguments):
        stdout = StringIO()
        with redirect_stdout(stdout):
            if main(arguments) != 0:
                raise AssertionError('No se pudo calcular por consola.')
        return json.loads(stdout.getvalue())

    with TemporaryDirectory(prefix='sl05-parity-') as directory:
        source, result = (Path(directory)/filename for filename in ('source.slproj','result.slproj'))
        count, seed, origin, rate = 64, 2026113500, -5, 200
        expected, = generate_realizations(Distribution('poisson',{'rate':2}),count,seed,origin=origin,rate=rate)
        generated = invoke(['probability','generate','--family','poisson','--parameters','{"rate":2}',
                            '--count',str(count),'--seed',str(seed),'--origin',str(origin),'--rate',str(rate),
                            '--output',str(source)])
        project, _ = session.load(source)
        key, = generated['result_ids']
        actual = project.get(key)
        if (not (actual.values == expected.values).all() or actual.origin != expected.origin or
                actual.metadata != expected.metadata):
            raise AssertionError('Las realizaciones de Python y de la consola difieren.')
        analyzed = invoke(['statistics','describe','--session',str(source),'--record',key,'--output',str(result)])
        archive, _ = session.load(result)
        report = archive.get(analyzed['result_id'])
        if report != describe_record(expected) or analyzed['source_id']!=key:
            raise AssertionError('La estadística o la procedencia cambia al usar Python y la consola.')
        return {'records':2,'case':'Poisson con reloj, semilla, índice y análisis descriptivo'}


def requirement_evidence(integral):
    records = integral.get('records',[])
    evidence = {}
    for requirement, suites in REFERENCE_SUITES.items():
        selected = [[row for row in records if row['id'].split('.')[0]==name] for name in suites]
        passed = all(group and all(row['passed'] is True for row in group) for group in selected)
        evidence[requirement] = {'passed':bool(passed), 'reference_cases':sum(map(len,selected)),
                                 'suites':list(suites)}
    return evidence


def run(output, defects):
    revision = clean_revision()
    baseline = json.loads((output/'baseline.json').read_bytes())
    integral_bytes = (output/'integral-checks.json').read_bytes()
    integral = json.loads(integral_bytes)
    if baseline.get('commit')!=revision or baseline.get('commit_after')!=revision or integral.get('passed') is not True:
        raise ValueError('El informe científico requiere una ejecución integral aprobada en este SHA.')
    requirements = requirement_evidence(integral)
    defect_register = json.loads(defects.read_bytes())
    rows = defect_register['findings']
    current = [row for row in rows if row['status']!='closed']
    p0 = sum(row['priority']=='P0' for row in current)
    p1 = sum(row['priority']=='P1' and row['internal'] for row in current)

    finder = WithoutQt()
    sys.meta_path.insert(0,finder)
    try:
        from statistical_demonstrators import run as demonstrate
        from signallab_pc.atomic_file import write_json
        equivalence = parity()
        examples = demonstrate(output/'demonstrators')
    finally:
        sys.meta_path.remove(finder)
    if clean_revision()!=revision:
        raise ValueError('El checkout cambió durante la calificación.')
    report = {'schema':1,'phase':'05','commit':revision,'clean_checkout':True,
              'integral_sha256':sha256(integral_bytes).hexdigest(),'requirements':requirements,
              'demonstrators':examples,'headless':True,'desktop':requirements['ST-08']['passed'],
              'interface_parity':bool(equivalence) and requirements['ST-08']['passed'],
              'interface_case':equivalence,'p0_open':p0,'p1_internal_open':p1}
    write_json(output/'statistical-qualification.json',report)
    return 0 if p0==p1==0 and all(row['passed'] for row in requirements.values()) else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--defects',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(run(args.output,args.defects))
