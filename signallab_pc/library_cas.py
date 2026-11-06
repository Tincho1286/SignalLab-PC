"""CAS educational content loaded from the unified library assets."""
from .library_content import read_data,block_pairs
BLOCKS=block_pairs(read_data('cas.json','blocks'))
