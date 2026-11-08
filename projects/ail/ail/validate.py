"""Validation for AIL v0.2 AST."""
from dataclasses import dataclass
from .ast import Atom, Prefix, BinOp, Number, String, Var, List, Field
from .registry import REGISTRY, is_core


@dataclass
class Diagnostic:
    level: str  # 'error' | 'warning'
    message: str
    path: str = ""


def validate(node, path=""):
    diags = []
    _walk(node, path, diags)
    # prefix exclusivity check is structural; handled in _walk_prefix
    return diags


def _walk(node, path, diags):
    if node is None:
        return
    if isinstance(node, Atom):
        spec = REGISTRY.get(node.name)
        if spec is None:
            diags.append(Diagnostic("warning", "unknown atom %r (not in registry)" % node.name, path))
        else:
            # field checks
            field_map = {f.key: f for f in node.fields}
            for key, f in field_map.items():
                if key not in spec["fields"]:
                    diags.append(Diagnostic("warning", "unknown field %r on atom %r" % (key, node.name), path))
                    continue
                fdef = spec["fields"][key]
                _check_field(f, fdef, "%s.%s" % (path, key) if path else key, diags)
            # required fields
            if spec is not None:
                for key, fdef in spec["fields"].items():
                    if fdef.get("required") and key not in field_map:
                        diags.append(Diagnostic("warning", "missing required field %r on atom %r" % (key, node.name), path))
        for f in node.fields:
            _walk(f.value, ("%s.%s" % (path, f.key)) if path else f.key, diags)
    elif isinstance(node, Prefix):
        if node.op == "?" and _has_prefix(node.operand, "!"):
            diags.append(Diagnostic("error", "mutually exclusive prefixes ? and !", path))
        if node.op == "!" and _has_prefix(node.operand, "?"):
            diags.append(Diagnostic("error", "mutually exclusive prefixes ? and !", path))
        _walk(node.operand, path, diags)
    elif isinstance(node, BinOp):
        _walk(node.left, path, diags)
        _walk(node.right, path, diags)
    elif isinstance(node, List):
        for i, it in enumerate(node.items):
            _walk(it, "%s[%d]" % (path, i), diags)
    # Number/String/Var: no checks


def _has_prefix(node, op):
    if isinstance(node, Prefix):
        if node.op == op:
            return True
        return _has_prefix(node.operand, op)
    return False


def _check_field(f, fdef, path, diags):
    t = fdef.get("type")
    if t == "number":
        if not isinstance(f.value, Number):
            diags.append(Diagnostic("error", "field %s expected number, got %s" % (path, type(f.value).__name__), path))
            return
        lo, hi = fdef.get("range", (None, None))
        if lo is not None and f.value.value < lo:
            diags.append(Diagnostic("error", "field %s below minimum %s" % (path, lo), path))
        if hi is not None and f.value.value > hi:
            diags.append(Diagnostic("error", "field %s above maximum %s" % (path, hi), path))
    elif t == "ident":
        if not isinstance(f.value, Var):
            # allow string as ident-like? v0.2 requires ident token
            if isinstance(f.value, String):
                pass  # lenient
            else:
                diags.append(Diagnostic("error", "field %s expected ident, got %s" % (path, type(f.value).__name__), path))
    elif t == "list":
        if not isinstance(f.value, List):
            diags.append(Diagnostic("error", "field %s expected list, got %s" % (path, type(f.value).__name__), path))
    # bare flag fields are allowed only if type bool-ish; ignore
    if f.bare:
        # bare flag means True; acceptable only if field not required-numeric
        pass
