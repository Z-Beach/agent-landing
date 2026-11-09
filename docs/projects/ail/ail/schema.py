"""JSON Schema export for the AIL v0.2 atom registry."""
import json

from .registry import REGISTRY


def to_json_schema():
    props = {}
    for name, spec in REGISTRY.items():
        field_props = {}
        for fname, fdef in spec["fields"].items():
            t = fdef.get("type")
            if t == "number":
                sch = {"type": "number"}
                if "range" in fdef:
                    sch["minimum"] = fdef["range"][0]
                    sch["maximum"] = fdef["range"][1]
            elif t == "ident":
                sch = {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
            elif t == "list":
                sch = {"type": "array"}
            else:
                sch = {}
            if fdef.get("required"):
                sch["_required"] = True
            field_props[fname] = sch
        props[name] = {
            "type": "object",
            "properties": field_props,
            "additionalProperties": False,
            "x-core": bool(spec.get("core", False)),
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "ail-core-0.2",
        "title": "AIL v0.2 atom registry",
        "type": "object",
        "properties": props,
        "additionalProperties": False,
    }


def dump(path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(to_json_schema(), fh, indent=2)
        fh.write("\n")
