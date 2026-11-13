"""Short editorial titles and subject groups; identifiers and search aliases stay stable."""
TOPICS=('Primeros pasos','Señales','Convolución y correlación','Sistemas','Filtros','Fourier y espectros','Laplace y Z','Muestreo','Ecuaciones','Señales aleatorias','Matemática y CAS')
CONCEPT_CATEGORIES={
 'Glosario: siglas y palabras frecuentes':0,
 'Señal, eje y dominio':0,
 'Energía, potencia y valor eficaz':1,
 'Sistemas LTI y convolución':3,
 'Fourier: serie, DTFT, DFT y FFT':5,
 'Laplace, Z, polos y región de convergencia':6,
 'Muestreo, reconstrucción y aliasing':7,
 'Fase y retardo de grupo':8,
 'Espacio de estados: qué representan las matrices':8,
 'FIR, IIR y especificaciones de diseño':9,
 'Filtros ideales y funciones por tramos':9,
 'Detección y estimación: dos preguntas distintas':12,
 'Realizaciones, estacionariedad y ergodicidad':12,
 'Correlación, covarianza y densidad de potencia':12,
 'Modelos aleatorios y alcance del programa':12,
}
SHORT={
 'tool:basic:shift':'Desplazar x[n]',
 'tool:basic:reverse':'Invertir el índice n',
 'tool:basic:scale':'Escalar x[n]',
 'tool:basic:parity':'Partes par e impar de x[n]',
 'tool:time_transform:1':'Desplazar x(t)',
 'tool:time_transform:2':'Invertir el tiempo t',
 'tool:time_transform:3':'Escalar x(t)',
 'tool:time_transform:4':'Partes par e impar de x(t)',
 'tool:time_transform:0':'Transformar x(t)',
 'reference:Glosario: siglas y palabras frecuentes':'Glosario',
 'reference:Detección y estimación: dos preguntas distintas':'Detección y estimación',
 'reference:Realizaciones, estacionariedad y ergodicidad':'Estacionariedad y ergodicidad',
 'reference:Correlación, covarianza y densidad de potencia':'Correlación y espectro',
 'reference:Laplace, Z, polos y región de convergencia':'Polos y convergencia',
 'reference:Espacio de estados: qué representan las matrices':'Matrices de estado',
 'reference:Modelos aleatorios y alcance del programa':'Modelos aleatorios',
 'reference:Coeficientes · constantes, pi y notación científica':'Coeficientes y constantes',
 'reference:DiracDelta · impulso continuo por posición y peso':'DiracDelta: posición y peso',
 'reference:Where y condiciones · funciones por tramos':'Funciones por tramos',
 'tool:system_analysis:0':'Analizar H(s) y H(z)',
 'tool:state_space:analysis':'Analizar estados',
 'tool:state_space:discretize':'Discretizar estados',
 'tool:state_space:simulation':'Simular estados',
 'tool:state_space:frequency':'Respuesta MIMO',
 'tool:frequency_filter:0':'Filtros definidos en frecuencia',
 'tool:fir_window:0':'Enventanar h[n]',
 'tool:rational_resampling:0':'Cambiar tasa de muestreo',
 'tool:fourier:0':'DTFT y DFT superpuestas',
 'tool:course_tools:convert':'Conversión analógico-digital',
 'tool:course_tools:mapping':'Relación entre Ω, ω y T',
 'tool:random_model:model':'Modelos AR, MA y ARMA',
 'example:fourier-envolvente-hiperbolica':'Envolvente hiperbólica',
 'example:laplace-anticausal':'Laplace anticausal',
 'example:z-impulso-desplazado':'Z de un impulso desplazado',
 'example:z-anticausal':'Z de una secuencia izquierda',
 'example:sistema-estable-anticausal':'Sistema estable anticausal',
 'example:ventana-rectangular-dtft':'DTFT de una ventana rectangular',
 'example:recurrencia-prehistoria':'Recurrencia con memoria inicial',
 'example:edo-impulso-origen':'Salto por un impulso',
}


def topic(category):
    from .library_catalog import CATEGORIES
    return TOPICS[(0,1,1,3,2,5,6,7,3,4,8,5,9,10)[CATEGORIES.index(category)]]


def apply(sections):
    for section in sections:
        section['original_title']=section['title']
        section['title']=SHORT.get(section['article_id'],section['title'].removeprefix('Ejemplo: '))
        section['topic']=topic(section['category'])
    by_id={s['article_id']:s for s in sections}
    for section in sections:
        if section.get('examples'):section['examples']=[(identifier,by_id['example:'+identifier]['title']) for identifier,_ in section['examples']]
