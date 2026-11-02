"""Small shared lexical normalization; scientific notation stays a NUMBER token."""
import io
import tokenize


def normalize(source):
    source=source.strip().replace('π','pi').replace('−','-').replace('^','**')
    tokens=list(tokenize.generate_tokens(io.StringIO(source).readline));out=[];previous=None
    for token in tokens:
        if previous is not None and previous.type==tokenize.NUMBER and (token.type==tokenize.NAME and token.string not in ('and','or','not','if','else') or token.string=='('):
            out.append((tokenize.OP,'*'))
        out.append((token.type,token.string))
        if token.type not in (tokenize.NL,tokenize.NEWLINE,tokenize.ENDMARKER):previous=token
    return tokenize.untokenize(out)
