"""Independent oracles and rejected domain transitions for the Core."""

from cmath import exp
from dataclasses import replace
from math import inf, pi, tau
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc import fourier, sampling
from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
from signallab_pc.dsp_application import FIRRequest, PSDRequest, ResampleRequest, apply_fir, estimate_psd
from signallab_pc.dsp_pipeline import DSPPipelineRequest, PipelineStageError, run_pipeline, store_pipeline
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.operation_provenance import content_digest
from signallab_pc.project import Project
from signallab_pc.scientific_storage import load_binary_signal, save_binary_signal


def frequency(values, *, units='rad/s', origin=0., step=1., operation=None):
    return Signal(values, origin, step, units, domain='frequency', metadata={'operation': operation})


class FourierGate(unittest.TestCase):
    def test_unrepresentable_sampling_grids_are_rejected(self):
        cases = [(inf, 2, 8, 'finitos'), (0, 1, 1, 'dos puntos'),
                 (2, 1, 8, 'crecientes'), (1e16, 1e16+2, 4, 'float64')]
        for start, stop, count, detail in cases:
            with self.subTest(start=start, stop=stop, count=count), self.assertRaisesRegex(ValueError, detail):
                fourier.grid(start, stop, count)
        signal = Signal([1, 2], 1e160, 1e160, 's', domain='continuous')
        with np.errstate(over='ignore'), self.assertRaisesRegex(ValueError, 'producto de coordenadas'):
            fourier.ctft(signal, 1e160, 3e160, 2)

    def test_synthesis_and_quadrature_reject_different_scientific_quantities(self):
        for source, detail in (
            (frequency([1, 2], operation='spectral_fraction'), 'acumulada'),
            (frequency([1, 2], operation='periodogram'), 'espectro complejo'),
            (frequency([1, 2], units='rad/muestra'), 'rad/s'),
            (frequency([1], operation='CTFT_rectangle'), 'dos frecuencias'),
        ):
            with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, detail):
                fourier.ictft(source, -1, 1, 5)
        with self.assertRaisesRegex(ValueError, 'paso positivo'):
            fourier.ctft(Signal([1, 2]), -pi, pi, 5)
        with self.assertRaisesRegex(ValueError, 'Serie discreta'):
            fourier.synthesize_discrete(Signal([1, 2], units='k'))
        with self.assertRaisesRegex(ValueError, 'Serie continua'):
            fourier.synthesize_continuous(Signal([1, 2]), -1, 1, 5)
        with self.assertRaisesRegex(ValueError, 'líneas espectrales'):
            fourier.synthesize_continuous(frequency([1, 2], operation='continuous_fourier_series'), -1, 1, 5)

    def test_complex_series_has_expected_harmonics_and_time_origin(self):
        source = Signal([2j, 1, -2j, -1], -1, metadata={'sample_rate_hz': 8, 'time_start_s': -.5})
        coefficients = fourier.discrete_series(source)
        expected = [sum(x * exp(-1j*tau*k*n/4) for n,x in zip(range(-1,3),source.values))/4 for k in range(4)]
        assert_allclose(coefficients.values, expected, atol=2e-15)
        rebuilt = fourier.synthesize_discrete(coefficients)
        assert_allclose(rebuilt.values, source.values, atol=2e-15)
        self.assertEqual((rebuilt.origin, rebuilt.metadata['time_start_s']), (-1, -.5))
        for start, harmonics, detail in ((0, -1, 'entero no negativo'), (1e18, 1, 'centros de celda')):
            with self.subTest(start=start), self.assertRaisesRegex(ValueError, detail):
                fourier.continuous_series('cos(t)', start, 2., 8, harmonics)

    def test_psd_validation_and_zero_and_legacy_power(self):
        x = Signal([1., -1., 1., -1.], metadata={'sample_rate_hz': 8})
        for kwargs, detail in (
            ({'rate': 16}, 'reloj'),
            ({'method': 'unknown'}, 'Estimador'),
            ({'segment': 5}, 'segmento'),
            ({'overlap': 4}, 'solape'),
            ({'window': 'unknown'}, 'Ventana'),
            ({'beta': -1}, 'Beta'),
            ({'segment': 2, 'overlap': 0, 'window': 'hann'}, 'energía nula'),
        ):
            options = {'rate': 8, 'segment': 4, 'overlap': 0, 'window': 'boxcar', **kwargs}
            with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, detail):
                fourier.spectral_density(x, **options)
        legacy = fourier.spectral_density(x, 8, method='legacy', window='boxcar')
        assert_array_equal(legacy.values, [4, 0, 0, 0])
        self.assertEqual(legacy.metadata['density_units'], 'amplitude²')
        for source in (Signal([0., 0., 0., 0.]), Signal([1., 1., 1., 1.])):
            result = fourier.spectral_density(source, 8, segment=4, overlap=0, window='boxcar', remove_mean=True)
            assert_array_equal(result.values, np.zeros(4))
        with self.assertRaisesRegex(FloatingPointError, 'potencia espectral'):
            fourier.spectral_density(Signal([1e308]), 1., method='periodogram', window='boxcar')

    def test_energy_report_distinguishes_inadmissible_spectra_and_finite_bands(self):
        for source, detail in (
            (frequency([1, 2], operation='spectral_fraction'), 'fracción'),
            (Signal([1, 2]), 'registro temporal'),
            (frequency([1, 2], units='Hz'), 'rad/s'),
            (frequency([1, 2], operation='continuous_fourier_series'), 'señal periódica'),
            (frequency([1, 2], operation='periodogram'), 'ya es una densidad'),
            (frequency([1, 2], operation='frequency_response'), 'respuesta de un filtro'),
        ):
            with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, detail):
                fourier.energy_density(source)
        reversed_spectrum = frequency([1, 2], step=-1.)
        with self.assertRaisesRegex(ValueError, 'eje creciente'):
            fourier.energy_report(reversed_spectrum)
        single = fourier.energy_report(frequency([1]))
        self.assertIn('ancho cero', single)
        short = fourier.energy_report(frequency([1, 1], step=tau), Signal([1, 0, 0]))
        self.assertIn('N+1 frecuencias', short)
        self.assertIn('Diferencia absoluta: 0', short)
        continuous = Signal([2+1j, 2+1j], 0., .5, 's', domain='continuous')
        self.assertIn('Δt·Σ|x(tk)|² = 5', fourier.energy_report(frequency([2, 2]), continuous))


class SamplingGate(unittest.TestCase):
    def test_domain_validation_and_reconstructing_with_overridden_clock(self):
        x = Signal([1, 3], -1, metadata={'sample_rate_hz': 4, 'time_start_s': -.25})
        cases = [
            (lambda: sampling.sample_expression('Dirac(t)', 0, 4, 2), 'peso'),
            (lambda: sampling.sample_expression('t', inf, 4, 2), 'inicial'),
            (lambda: sampling.alias_frequency(inf, 4), 'finita'),
            (lambda: sampling.alias_angular_frequency(inf, 4), 'finita'),
            (lambda: sampling.alias_angular_frequency(1, 1e308), 'representable'),
            (lambda: sampling.resample(x, 2, 'decimate', phase=2), 'fase'),
            (lambda: sampling.resample(x, 3, 'decimate', phase=2), 'sin muestras'),
            (lambda: sampling.resample(x, 2, 'invalid'), 'desconocido'),
            (lambda: sampling.resample(Signal([1], 2**62), 2, 'expand'), '64 bits'),
            (lambda: sampling.reconstruct(x, 4, 0, 2, 'linear'), 'instante'),
            (lambda: sampling.reconstruct(Signal([1, 2]), 4, None, 2, 'linear'), 'primera muestra'),
            (lambda: sampling.reconstruct(x, 4, inf, 2, 'linear', override_clock=True), 'finito'),
            (lambda: sampling.reconstruct(x, 4, None, 2, 'invalid'), 'Elegí'),
            (lambda: sampling.resample_rational(x, 2, 1, boundary='invalid'), 'extensión'),
            (lambda: sampling.resample_rational(Signal([1]), 2, 1, boundary='line'), 'dos muestras'),
            (lambda: sampling.resample_rational(x, 2, 1, beta=inf), 'Beta'),
            (lambda: sampling.resample_rational(x, 2, 1, start=0), 'inicial'),
            (lambda: sampling.resample_rational(x, 2, 1, start=inf, override_clock=True), 'finito'),
        ]
        for run, detail in cases:
            with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, detail):
                run()
        restored = sampling.reconstruct(x, 2, 3., 2, 'linear', override_clock=True)
        assert_array_equal(restored.axis, [3., 3.25, 3.5])
        assert_array_equal(restored.values, [1, 2, 3])
        unclocked = sampling.resample(Signal([1, 2, 3], metadata={'time_start_s': .5}), 2, 'decimate', phase=1)
        assert_array_equal(unclocked.values, [2])
        self.assertNotIn('time_start_s', unclocked.metadata)

    def test_precision_and_quantizer_range_errors_do_not_return_partial_results(self):
        signal = Signal([0])
        cases = [
            (lambda: sampling.quantize(signal, 53, -1, 1), '52 bits'),
            (lambda: sampling.quantize(Signal([1j]), 2, -1, 1), 'reales'),
            (lambda: sampling.quantize(signal, 2, 1, 1), 'máximo'),
            (lambda: sampling.quantize(signal, 2, -1, 1, method='invalid'), 'nivel inferior'),
            (lambda: sampling.quantize(signal, 2, 1, 2, align_zero=True), 'incluya cero'),
            (lambda: sampling.quantize(signal, 2, 0, 5e-324), 'paso'),
            (lambda: sampling.quantize(signal, 2, 1e16, 1e16+2), 'distinguen'),
            (lambda: sampling.quantize(signal, 2, 0, 3, last=1), 'intervalo SNR'),
            (lambda: sampling.fixed_point(1, 2, -1), 'fraccionarios'),
            (lambda: sampling.fixed_point(1, 2, 1, 'invalid'), 'desconocido'),
            (lambda: sampling.fixed_point(inf, 2, 1), 'finito'),
        ]
        for run, detail in cases:
            with self.subTest(detail=detail), self.assertRaisesRegex(ValueError, detail):
                run()
        exact_zero = sampling.quantize(signal, 2, 0, 3, method='floor')
        self.assertIsNone(exact_zero.snr_db)
        assert_array_equal(exact_zero.error.values, [0])


class ApplicationGate(unittest.TestCase):
    def test_dft_request_and_unsealed_result_errors_are_atomic(self):
        for request, diagnosis in ((DFTRequest([1]), 'Signal'),
                                   (DFTRequest(Signal([1]), centered=1), 'booleano')):
            with self.subTest(diagnosis=diagnosis), self.assertRaisesRegex((TypeError, ValueError), diagnosis):
                calculate_dft(request)
        source = Signal([1, 2], metadata={'sample_rate_hz': np.int64(8)})
        outcome = calculate_dft(DFTRequest(source))
        ordinary = source.copy_with(metadata={'sample_rate_hz': 8})
        project = Project()
        source_id = project.add(ordinary)
        with self.assertRaisesRegex(ValueError, 'procedencia válida'):
            store_dft(project, replace(outcome, estimated_work_bytes=0), source_id=source_id)
        with self.assertRaisesRegex(ValueError, 'señal nueva'):
            store_dft(project, outcome, source=ordinary, source_id=source_id)
        self.assertEqual([r['id'] for r in project.headers()], [source_id])

    def test_invalid_dsp_configuration_and_imported_unverified_result(self):
        x = Signal([1, 2])
        fir = Transfer([1], [1])
        cases = [
            (lambda: apply_fir(FIRRequest(x, fir, 'circular')), 'modo FIR'),
            (lambda: apply_fir(FIRRequest(Signal([1, 2], units='s', domain='continuous'), fir)), 'discreta'),
            (lambda: estimate_psd(PSDRequest(x)), 'Indicá Fs'),
            (lambda: estimate_psd(PSDRequest(x, 8, sidedness='invalid')), 'bilateral'),
        ]
        for run, diagnosis in cases:
            with self.subTest(diagnosis=diagnosis), self.assertRaisesRegex(ValueError, diagnosis):
                run()
        source = Signal([1, 2, 3, 4], metadata={'sample_rate_hz': 8})
        choice = DSPPipelineRequest(ResampleRequest(source, 1, 1), fir,
                                    psd_segment=4, psd_window='boxcar')
        with self.assertRaisesRegex(PipelineStageError, 'PSD.*supera'):
            run_pipeline(replace(choice, psd_segment=5))
        output = run_pipeline(choice)
        project = Project()
        with self.assertRaisesRegex(ValueError, 'antialias cambió'):
            store_pipeline(project, choice, replace(output, resampled=replace(output.resampled, antialias=fir)))
        self.assertEqual(project.headers(), [])
        links = store_pipeline(project, choice, output)
        self.assertIsNone(links.antialias)
        self.assertEqual(project.headers()[2]['parents'], [links.source])
        self.assertAlmostEqual(float(output.psd.values.real.sum()*output.psd.step), 7.5)

    def test_project_rejects_invalid_proof_and_recovers_sos_model(self):
        project = Project()
        original = Transfer.from_sos([[1, 0, 0, 1, -.25, 0]], sample_period_s=.125)
        checkpoint = lambda: None
        model_id = project.add(original, verification=(content_digest(original, checkpoint), (), checkpoint))
        source = Signal([3, 1])
        result = calculate_dft(DFTRequest(source))
        _, record = store_dft(project, result, source=source)
        document = project.document()
        expanded = Project.from_document(document)
        assert_allclose(expanded.get(model_id).response([.25]), 1/(1-.25*exp(-.25j)))
        self.assertEqual(expanded.get(model_id).sample_period_s, .125)
        proof = document['records'][-1]['verified_provenance']
        proof['schema'] = True
        with self.assertRaisesRegex(ValueError, 'formato inválido'):
            Project.from_document(document)
        self.assertEqual(project.headers()[-1]['id'], record)

    def test_scientific_file_rejections_leave_valid_destination_intact(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'scientific.slbin'
            with self.assertRaisesRegex(ValueError, 'regular'):
                load_binary_signal(folder)
            path.write_text('ordinary text document', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'desconocido'):
                load_binary_signal(path)
            original = Signal([1+3j, 4], -1)
            save_binary_signal(original, path)
            old_contents = path.read_bytes()
            large = original.copy_with(metadata={'notes': 'x' * (1024 * 1024)})
            with self.assertRaisesRegex(ValueError, '1 MiB'):
                save_binary_signal(large, path)
            self.assertEqual(path.read_bytes(), old_contents)
            assert_array_equal(load_binary_signal(path).values, original.values)
