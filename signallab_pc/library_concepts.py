"""Compatibility data for concepts and function references, authored outside Python."""
from .library_content import read_data,block_pairs
_concepts=read_data('concepts.json','concepts')
_fields=('title','course','introduction','formula','interpretation','scope')
if any(any(not isinstance(row.get(field),str) or not row[field].strip() for field in _fields) for row in _concepts):raise ValueError('Concepto incompleto en la biblioteca.')
TOPICS=[tuple(row[field] for field in _fields) for row in _concepts]
FUNCTION_BLOCKS=[block_pairs(row['blocks']) for row in read_data('functions.json','references')]
