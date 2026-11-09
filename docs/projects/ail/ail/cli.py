"""CLI for AIL v0.2."""
import argparse
import json
import sys

from . import parse, validate, render, canonical, canonical_hash
from .schema import dump as dump_schema


import os as _os

def _read_text(args):
    if args.file and _os.path.exists(args.file):
        with open(args.file, encoding="utf-8") as fh:
            return fh.read()
    parts = []
    if args.file:
        parts.append(args.file)
    if getattr(args, "expr", None):
        parts.extend(args.expr)
    if parts:
        return " ".join(parts)
    data = sys.stdin.read()
    return data


def cmd_parse(args):
    text = _read_text(args)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            node = parse(line)
            print(render(node))
        except Exception as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
    return 0


def cmd_validate(args):
    text = _read_text(args)
    rc = 0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            node = parse(line)
        except Exception as e:
            print("PARSE ERROR: %s" % e, file=sys.stderr)
            rc = 1
            continue
        diags = validate(node)
        errs = [d for d in diags if d.level == "error"]
        warns = [d for d in diags if d.level == "warning"]
        for d in diags:
            print("%s: %s" % (d.level.upper(), d.message), file=sys.stderr)
        if errs:
            rc = 1
    return rc


def cmd_render(args):
    text = _read_text(args)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            node = parse(line)
            print(render(node))
        except Exception as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
    return 0


def cmd_json(args):
    text = _read_text(args)
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        node = parse(line)
        # AST as a simple dict via render of canonical + hash
        out.append({"canonical": canonical(node), "hash": canonical_hash(node)})
    print(json.dumps(out, indent=2))
    return 0


def cmd_canonical(args):
    text = _read_text(args)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            node = parse(line)
            print("%s  %s" % (canonical_hash(node)[:12], canonical(node)))
        except Exception as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
    return 0


def cmd_schema(args):
    dump_schema(args.out)
    print("wrote %s" % args.out)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ail", description="AIL v0.2 reference implementation")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_io(p):
        p.add_argument("file", nargs="?")
        p.add_argument("expr", nargs="*")

    p = sub.add_parser("parse"); add_io(p); p.set_defaults(func=cmd_parse)
    p = sub.add_parser("validate"); add_io(p); p.set_defaults(func=cmd_validate)
    p = sub.add_parser("render"); add_io(p); p.set_defaults(func=cmd_render)
    p = sub.add_parser("json"); add_io(p); p.set_defaults(func=cmd_json)
    p = sub.add_parser("canonical"); add_io(p); p.set_defaults(func=cmd_canonical)
    p = sub.add_parser("schema"); p.add_argument("--out", default="ail-core-0.2.json"); p.set_defaults(func=cmd_schema)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
