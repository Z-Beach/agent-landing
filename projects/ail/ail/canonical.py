"""Canonical form + hash for AIL v0.2 AST."""
import hashlib
import json

from .ast import Atom, Field, Prefix, BinOp, Number, String, Var, List


def _fmt_num(v):
    # up to 6 significant digits, strip trailing zeros
    s = "%.6g" % v.value if isinstance(v, Number) else None
    return s


def _canon_value(v):
    if isinstance(v, Atom):
        return canonical(v)
    if isinstance(v, Number):
        return "%.6g" % v.value
    if isinstance(v, String):
        return json.dumps(v.value, ensure_ascii=False)
    if isinstance(v, Var):
        return v.name
    if isinstance(v, List):
        return "[" + ",".join(_canon_value(x) for x in v.items) + "]"
    if isinstance(v, Prefix):
        return canonical(v)
    if isinstance(v, BinOp):
        return canonical(v)
    return str(v)


def canonical(node):
    if node is None:
        return ""
    if isinstance(node, Atom):
        # fields sorted by key
        fs = ",".join("%s=%s" % (f.key, _canon_value(f.value)) for f in sorted(node.fields, key=lambda x: x.key))
        return "%s(%s)" % (node.name, fs)
    if isinstance(node, Prefix):
        return "%s%s" % (node.op, canonical(node.operand))
    if isinstance(node, BinOp):
        return "%s%s%s" % (canonical(node.left), node.op, canonical(node.right))
    if isinstance(node, Number):
        return "%.6g" % node.value
    if isinstance(node, String):
        return json.dumps(node.value, ensure_ascii=False)
    if isinstance(node, Var):
        return node.name
    if isinstance(node, List):
        return "[" + ",".join(_canon_value(x) for x in node.items) + "]"
    return str(node)


def canonical_hash(node):
    return hashlib.sha256(canonical(node).encode("utf-8")).hexdigest()
