"""Escritura de archivos completos antes de sustituir el destino."""
from contextlib import contextmanager
from pathlib import Path
import os
import tempfile
import json

@contextmanager
def atomic_text_file(path,*,encoding='utf-8',newline=None):
    target=Path(path)
    descriptor,temporary=tempfile.mkstemp(prefix=target.name+'.',suffix='.tmp',dir=target.parent)
    try:
        try:stream=os.fdopen(descriptor,'w',encoding=encoding,newline=newline)
        except BaseException:
            os.close(descriptor)
            raise
        with stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)

def write_json(path,document):
    with atomic_text_file(path) as stream:
        json.dump(document,stream,ensure_ascii=False,allow_nan=False,indent=2)

def write_text(path,text):
    with atomic_text_file(path) as stream:stream.write(text)
