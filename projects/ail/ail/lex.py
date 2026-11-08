"""Tokenizer for AIL v0.2."""
import re

TOKEN_RE = re.compile(
    r"(?P<ws>\s+)"
    r"|(?P<comment>#[^\n]*)"
    r"|(?P<number>\d+\.\d+|\d+)"
    r"|(?P<string>\"[^\"]*\"|'[^']*')"
    r"|(?P<op>>>|<<|<>|[+=~?!])"
    r"|(?P<paren>[(),\[\]])"
    r"|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)"
)


class LexError(Exception):
    pass


def tokenize(text):
    tokens = []
    pos = 0
    n = len(text)
    for m in TOKEN_RE.finditer(text):
        if m.start() != pos:
            raise LexError("unexpected character at %d: %r" % (pos, text[pos:pos + 5]))
        pos = m.end()
        kind = m.lastgroup
        if kind in ("ws", "comment"):
            continue
        tokens.append((kind, m.group()))
    if pos != n:
        raise LexError("unexpected trailing input at %d: %r" % (pos, text[pos:pos + 5]))
    return tokens
