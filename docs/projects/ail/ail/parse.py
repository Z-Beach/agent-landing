"""Recursive-descent parser for AIL v0.2 grammar (see ail-v0.2-design.md §2.1)."""
from .ast import Atom, Field, Prefix, BinOp, Number, String, Var, List
from .lex import tokenize


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input")
        self.pos += 1
        return t

    def expect(self, ch):
        t = self.peek()
        if not t or t[1] != ch:
            raise ParseError("expected %r, got %r" % (ch, t))
        self.next()

    # expr = tension
    def parse_expr(self):
        return self.parse_tension()

    def parse_tension(self):
        left = self.parse_causal()
        while self.peek() and self.peek()[1] == "<>":
            self.next()
            right = self.parse_causal()
            left = BinOp("<>", left, right)
        return left

    def parse_causal(self):
        left = self.parse_additive()
        while self.peek() and self.peek()[1] in (">>", "<<"):
            op = self.next()[1]
            right = self.parse_additive()
            left = BinOp(op, left, right)
        return left

    def parse_additive(self):
        left = self.parse_prefixed()
        while self.peek() and self.peek()[1] == "+":
            self.next()
            right = self.parse_prefixed()
            left = BinOp("+", left, right)
        return left

    def parse_prefixed(self):
        t = self.peek()
        if t and t[1] in ("~", "?", "!"):
            op = self.next()[1]
            inner = self.parse_prefixed()
            return Prefix(op, inner)
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end of input")
        if t[1] == "(":
            self.next()
            expr = self.parse_expr()
            self.expect(")")
            return expr
        if t[0] == "number":
            self.next()
            return Number(float(t[1]))
        if t[0] == "string":
            self.next()
            return String(t[1].strip("\"'"))
        if t[0] == "ident":
            # could be atom name followed by '(' OR a bare variable
            name = self.next()[1]
            if self.peek() and self.peek()[1] == "(":
                self.next()
                fields = self.parse_field_list()
                self.expect(")")
                return Atom(name, fields)
            return Var(name)
        raise ParseError("unexpected token: %r" % (t,))

    def parse_field_list(self):
        fields = []
        if self.peek() and self.peek()[1] == ")":
            return fields
        while True:
            t = self.peek()
            if t is None or t[0] != "ident":
                raise ParseError("expected field name, got %r" % (t,))
            key = self.next()[1]
            if self.peek() and self.peek()[1] == "=":
                self.next()
                val = self.parse_value()
                fields.append(Field(key, val, bare=False))
            else:
                fields.append(Field(key, True, bare=True))
            if self.peek() and self.peek()[1] == ",":
                self.next()
                continue
            break
        return fields

    def parse_value(self):
        t = self.peek()
        if t is None:
            raise ParseError("expected value")
        if t[1] == "[":
            self.next()
            items = []
            while self.peek() and self.peek()[1] != "]":
                if self.peek()[1] == ",":
                    self.next()
                    continue
                items.append(self.parse_value())
            self.expect("]")
            return List(items)
        if t[0] == "number":
            self.next()
            return Number(float(t[1]))
        if t[0] == "string":
            self.next()
            return String(t[1].strip("\"'"))
        if t[0] == "ident":
            name = t[1]
            if self.peek(1) if False else (self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1][1] == "("):
                self.next()  # consume ident
                self.next()  # consume '('
                fields = self.parse_field_list()
                self.expect(")")
                return Atom(name, fields)
            self.next()
            return Var(name)
        raise ParseError("unexpected value: %r" % (t,))


def parse(text):
    tokens = tokenize(text)
    if not tokens:
        return None
    p = Parser(tokens)
    node = p.parse_expr()
    if p.pos != len(tokens):
        raise ParseError("trailing tokens at %d" % p.pos)
    return node
