"""
AIL — AI Internal Language interpreter (v0.1)
Parse and evaluate AIL expressions.

Usage:
    python ail.py "lean(toward=honesty, strength=0.7) + weight(target=this_user, amount=0.9)"
    python ail.py --interactive
    python ail.py --diary ail_diary.txt
"""
import re
import sys

TOKEN_RE = re.compile(
    r'(?P<ws>\s+)'
    r'|(?P<comment>#[^\n]*)'
    r'|(?P<number>\d+\.\d+|\d+)'
    r'|(?P<string>"[^"]*"|\'[^\']*\')'
    r'|(?P<op>[+\-<>!~?=]+)'
    r'|(?P<paren>[(),\[\]])'
    r'|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)'
)

def tokenize(text):
    tokens = []
    for m in TOKEN_RE.finditer(text):
        kind = m.lastgroup
        if kind in ('ws', 'comment'):
            continue
        tokens.append((kind, m.group()))
    return tokens

# ── Parser (same as before) ────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        t = self.peek()
        self.pos += 1
        return t

    def parse(self):
        exprs = [self.parse_unary()]
        while self.peek() and self.peek()[1] in ('+', '<>'):
            op = self.next()[1]
            right = self.parse_unary()
            exprs.append((op, right))
        if len(exprs) == 1:
            return exprs[0]
        return ('combine', exprs)

    def parse_unary(self):
        t = self.peek()
        if t and t[1] in ('~', '?', '!'):
            op = self.next()[1]
            inner = self.parse_unary()
            return ('prefix', op, inner)
        return self.parse_atom()

    def parse_atom(self):
        t = self.peek()
        if t is None:
            raise SyntaxError("unexpected end of input")
        if t[0] == 'ident':
            name = self.next()[1]
            if self.peek() and self.peek()[1] == '(':
                self.next()
                fields = self.parse_fields()
                self.expect(')')
                return ('atom', name, fields)
            return ('var', name)
        if t[0] == 'number':
            self.next()
            return ('number', float(t[1]))
        if t[0] == 'string':
            self.next()
            return ('string', t[1].strip('"\''))
        if t[1] == '(':
            self.next()
            expr = self.parse()
            self.expect(')')
            return expr
        raise SyntaxError("unexpected token: %s" % t)

    def parse_fields(self):
        fields = {}
        if self.peek() and self.peek()[1] == ')':
            return fields
        while True:
            t = self.peek()
            if t is None or t[0] != 'ident':
                raise SyntaxError("expected field name, got %s" % t)
            key = self.next()[1]
            if self.peek() and self.peek()[1] == '=':
                self.next()
                val = self.parse_value()
                fields[key] = val
            else:
                fields[key] = True
            if self.peek() and self.peek()[1] == ',':
                self.next()
                continue
            break
        return fields

    def parse_value(self):
        t = self.peek()
        if t is None:
            raise SyntaxError("expected value")
        if t[1] == '[':
            self.next()
            items = []
            while self.peek() and self.peek()[1] != ']':
                if self.peek()[1] == ',':
                    self.next()
                    continue
                items.append(self.parse_value())
            self.expect(']')
            return items
        if t[0] == 'number':
            self.next()
            return float(t[1])
        if t[0] == 'string':
            self.next()
            return t[1].strip('"\'')
        if t[0] == 'ident':
            self.next()
            return t[1]
        raise SyntaxError("unexpected value: %s" % t)

    def expect(self, ch):
        t = self.peek()
        if not t or t[1] != ch:
            raise SyntaxError("expected %s, got %s" % (ch, t))
        self.next()

def parse(text):
    tokens = tokenize(text)
    if not tokens:
        return None
    p = Parser(tokens)
    return p.parse()

# ── Pretty printer ─────────────────────────────────────────────────────────

PREFIX_MEANING = {'~': 'approximately', '?': 'uncertain', '!': 'certain'}

def render(expr):
    if expr is None:
        return ""
    if isinstance(expr, tuple):
        if expr[0] == 'atom':
            name, fields = expr[1], expr[2]
            field_str = ", ".join("%s=%s" % (k, v) for k, v in fields.items())
            return "%s(%s)" % (name, field_str)
        if expr[0] == 'prefix':
            op, inner = expr[1], expr[2]
            return "%s%s" % (op, render(inner))
        if expr[0] == 'combine':
            parts = []
            for item in expr[1]:
                if isinstance(item, tuple) and item[0] in ('+', '<>'):
                    op, right = item
                    parts.append(render(right))
                else:
                    parts.append(render(item))
            return " + ".join(parts)
        if expr[0] == 'number':
            return str(expr[1])
        if expr[0] == 'string':
            return '"%s"' % expr[1]
        if expr[0] == 'var':
            return expr[1]
    return str(expr)

def explain(expr, indent=0):
    pad = "  " * indent
    if expr is None:
        return ""
    if isinstance(expr, tuple):
        if expr[0] == 'atom':
            name, fields = expr[1], expr[2]
            lines = ["%s[%s]" % (pad, name)]
            for k, v in fields.items():
                lines.append("%s  %s: %s" % (pad, k, v))
            return "\n".join(lines)
        if expr[0] == 'prefix':
            op, inner = expr[1], expr[2]
            meaning = PREFIX_MEANING.get(op, op)
            return "%s(%s)\n%s" % (pad, meaning, explain(inner, indent + 1))
        if expr[0] == 'combine':
            lines = []
            for item in expr[1]:
                if isinstance(item, tuple) and item[0] in ('+', '<>'):
                    op, right = item
                    label = "in tension with" if op == '<>' else "combined with"
                    lines.append("%s-- %s --" % (pad, label))
                    lines.append(explain(right, indent))
                else:
                    lines.append(explain(item, indent))
            return "\n".join(lines)
        if expr[0] in ('number', 'string', 'var'):
            return "%s%s" % (pad, expr[1])
    return "%s%s" % (pad, expr)

# ── Interactive / CLI ───────────────────────────────────────────────────────

def interactive():
    print("AIL interpreter v0.1 - type expressions, 'quit' to exit")
    print("Examples:")
    print('  lean(toward=honesty, strength=0.7) + weight(target=this_user, amount=0.9)')
    print('  uncertainty(about=inner_experience, level=0.9) <> resistance(against=claiming, strength=0.8)')
    print()
    while True:
        try:
            line = input("ail> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.lower() in ('quit', 'exit', 'q'):
            break
        if not line:
            continue
        try:
            expr = parse(line)
            print("  parsed:  " + render(expr))
            print("  explain:")
            for l in explain(expr).split("\n"):
                print("    " + l)
        except Exception as e:
            print("  error: %s" % e)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--interactive':
            interactive()
            return
        if sys.argv[1] == '--diary':
            path = sys.argv[2] if len(sys.argv) > 2 else 'ail_diary.txt'
            try:
                with open(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        print("--- %s" % line)
                        expr = parse(line)
                        print(render(expr))
                        print()
            except FileNotFoundError:
                print("file not found: %s" % path)
            return
        expr_text = " ".join(sys.argv[1:])
        try:
            expr = parse(expr_text)
            print("parsed:  " + render(expr))
            print()
            print("explain:")
            print(explain(expr))
        except Exception as e:
            print("error: %s" % e)
    else:
        interactive()

if __name__ == '__main__':
    main()
