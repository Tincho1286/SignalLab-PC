"""Escritura de archivos completos antes de sustituir el destino."""
from contextlib import contextmanager
from pathlib import Path
import os
import tempfile
import json

@contextmanager
def _atomic_stream(path,mode,*,before_commit=None,**options):
    target=Path(path)
    descriptor,temporary=tempfile.mkstemp(prefix=target.name+'.',suffix='.tmp',dir=target.parent)
    try:
        try:stream=os.fdopen(descriptor,mode,**options)
        except BaseException:
            os.close(descriptor)
            raise
        with stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        if before_commit is not None:before_commit()
        os.replace(temporary,target)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)

def atomic_text_file(path,*,encoding='utf-8',newline=None,before_commit=None):
    return _atomic_stream(path,'w',encoding=encoding,newline=newline,before_commit=before_commit)

def atomic_binary_file(path,*,before_commit=None):
    return _atomic_stream(path,'wb',before_commit=before_commit)

def write_json(path,document,*,before_commit=None):
    with atomic_text_file(path,before_commit=before_commit) as stream:
        json.dump(document,stream,ensure_ascii=False,allow_nan=False,indent=2)

def write_text(path,text):
    with atomic_text_file(path) as stream:stream.write(text)
