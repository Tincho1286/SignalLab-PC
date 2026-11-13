"""What stored samples describe, independently of the axis used to plot them."""


def signal_kind(domain, units, metadata):
    operation=metadata.get('operation')
    if operation=='spectral_fraction':return 'spectral_measurement'
    if domain=='frequency' and metadata.get('distribution'):return 'spectral_lines'
    if operation in {'energy_density','spectral_density','welch','periodogram'}:return 'density'
    if domain=='discrete' and (units=='bin k' or operation=='DFT'):return 'dft_bins'
    if units=='k' or operation in {'continuous_fourier_series','discrete_fourier_series'}:return 'harmonics'
    if domain!='frequency':return 'temporal'
    if operation in {'frequency_filter','frequency_response','state_space_frequency'}:return 'frequency_response'
    if operation in {'DFT','DTFT','CTFT_rectangle','stft'}:return 'spectrum'
    return 'frequency_values'


def require_temporal(source):
    if source.data_kind!='temporal':
        raise ValueError('Esta entrada requiere muestras de una señal temporal. Para usar coeficientes de Fourier, reconstruí primero la señal.')


def require_frequency_response(source):
    if source.data_kind not in {'frequency_response','frequency_values'}:
        raise ValueError('Definí H(ω) o cargá valores de una respuesta de filtro. Los espectros, densidades y líneas de Fourier describen otros resultados.')
