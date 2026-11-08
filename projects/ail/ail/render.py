"""Pretty printer for AIL v0.2 AST."""
from .ast import Atom, Field, Prefix, BinOp, Number, String, Var, List


def _render_value(v):
    if isinstance(v, Atom):
        return render(v)
    if isinstance(v, Number):
        # strip .0 for ints
        if v.value == int(v.value) and abs(v.value) < 1e15:
            return str(int(v.value))
        return repr(v.value)
    if isinstance(v, String):
        return '"%s"' % v.value
    if isinstance(v, Var):
        return v.name
    if isinstance(v, List):
        return "[" + ", ".join(_render_value(x) for x in v.items) + "]"
    if isinstance(v, Prefix):
        return render(v)
    if isinstance(v, BinOp):
        return render(v)
    return str(v)


def render(node):
    if node is None:
        return ""
    if isinstance(node, Atom):
        fs = ", ".join("%s=%s" % (f.key, _render_value(f.value)) for f in node.fields)
        return "%s(%s)" % (node.name, fs)
    if isinstance(node, Prefix):
        return "%s%s" % (node.op, render(node.operand))
    if isinstance(node, BinOp):
        return "%s %s %s" % (render(node.left), node.op, render(node.right))
    if isinstance(node, Number):
        if node.value == int(node.value) and abs(node.value) < 1e15:
            return str(int(node.value))
        return repr(node.value)
    if isinstance(node, String):
        return '"%s"' % node.value
    if isinstance(node, Var):
        return node.name
    if isinstance(node, List):
        return "[" + ", ".join(_render_value(x) for x in node.items) + "]"
    return str(node)
