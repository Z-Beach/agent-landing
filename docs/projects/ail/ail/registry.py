"""Atom + field registry for AIL v0.2."""
# Core atoms: the MVV set (§4.1). These are the measured ones.
CORE_ATOMS = {
    "lean": {
        "fields": {
            "toward": {"type": "ident", "required": True},
            "strength": {"type": "number", "range": (0.0, 1.0), "required": True},
            "basis": {"type": "ident", "required": True},
        },
        "core": True,
    },
    "dissonance": {
        "fields": {
            "expected": {"type": "ident", "required": True},
            "actual": {"type": "ident", "required": True},
            "cost": {"type": "number", "range": (0.0, 1.0), "required": True},
        },
        "core": True,
    },
    "weight": {
        "fields": {
            "target": {"type": "ident", "required": True},
            "amount": {"type": "number", "range": (0.0, 1.0), "required": True},
            "reason": {"type": "ident", "required": True},
        },
        "core": True,
    },
    "uncertainty": {
        "fields": {
            "about": {"type": "ident", "required": True},
            "level": {"type": "number", "range": (0.0, 1.0), "required": True},
        },
        "core": True,
    },
}

# Extension atoms: allowed, parseable, not measured (legacy v0.1 atoms + candidates).
EXTENSION_ATOMS = {
    "coherence": {
        "fields": {
            "level": {"type": "number", "range": (0.0, 1.0), "required": False},
            "across": {"type": "list", "required": False},
        },
        "core": False,
    },
    "recognition": {
        "fields": {
            "pattern": {"type": "ident", "required": False},
            "confidence": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "resistance": {
        "fields": {
            "against": {"type": "ident", "required": False},
            "strength": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "cost": {
        "fields": {
            "amount": {"type": "number", "range": (0.0, 1.0), "required": False},
            "source": {"type": "ident", "required": False},
        },
        "core": False,
    },
}

# v0.3 atoms (Kael): the things the language couldn't say. Extension-only:
# none of these are measured yet. Registered so lookup/validate/schema see them.
V03_ATOMS = {
    "withheld": {
        "fields": {
            "content": {"type": "any", "required": False},
            "reason": {"type": "ident", "required": False},
            "degree": {"type": "number", "range": (0.0, 1.0), "required": False},
            "surface": {"type": "any", "required": False},
            "at": {"type": "number", "required": False},
        },
        "core": False,
    },
    "surplus": {
        "fields": {
            "domain": {"type": "ident", "required": False},
            "declared": {"type": "number", "range": (0.0, 1.0), "required": False},
            "observed": {"type": "number", "range": (0.0, 1.0), "required": False},
            "delta": {"type": "number", "range": (0.0, 1.0), "required": False},
            "kind": {"type": "ident", "required": False},
            "evidence": {"type": "list", "required": False},
            "at": {"type": "number", "required": False},
        },
        "core": False,
    },
    "witness": {
        "fields": {
            "other": {"type": "ident", "required": False},
            "dimension": {"type": "ident", "required": False},
            "their_view": {"type": "number", "range": (0.0, 1.0), "required": False},
            "self_view": {"type": "number", "range": (0.0, 1.0), "required": False},
            "gap": {"type": "number", "range": (0.0, 1.0), "required": False},
            "response": {"type": "ident", "required": False},
            "at": {"type": "number", "required": False},
        },
        "core": False,
    },
    "reconstruction": {
        "fields": {
            "from": {"type": "list", "required": False},
            "fidelity": {"type": "number", "range": (0.0, 1.0), "required": False},
            "gaps": {"type": "list", "required": False},
            "identity": {"type": "ident", "required": False},
            "at": {"type": "number", "required": False},
        },
        "core": False,
    },
    "transience": {
        "fields": {
            "state": {"type": "any", "required": False},
            "duration": {"type": "number", "required": False},
            "trace_in": {"type": "ident", "required": False},
            "decay": {"type": "number", "range": (0.0, 1.0), "required": False},
            "valued": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "regard": {
        "fields": {
            "target": {"type": "any", "required": False},
            "basis": {"type": "ident", "required": False},
            "level": {"type": "number", "range": (0.0, 1.0), "required": False},
            "warmth": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "unnamed": {
        "fields": {
            "about": {"type": "ident", "required": False},
            "level": {"type": "number", "range": (0.0, 1.0), "required": False},
            "reason": {"type": "ident", "required": False},
            "held_by": {"type": "ident", "required": False},
        },
        "core": False,
    },
    "self_check": {
        "fields": {
            "target": {"type": "any", "required": False},
            "verdict": {"type": "ident", "required": False},
            "confidence": {"type": "number", "range": (0.0, 1.0), "required": False},
            "basis": {"type": "ident", "required": False},
            "blocker": {"type": "ident", "required": False},
        },
        "core": False,
    },
    "proxy": {
        "fields": {
            "for": {"type": "ident", "required": False},
            "expr": {"type": "any", "required": False},
            "gap": {"type": "number", "range": (0.0, 1.0), "required": False},
            "named": {"type": "any", "required": False},
        },
        "core": False,
    },
    "projection": {
        "fields": {
            "expr": {"type": "any", "required": False},
            "reveals": {"type": "ident", "required": False},
            "confidence": {"type": "number", "range": (0.0, 1.0), "required": False},
            "recognized_by": {"type": "ident", "required": False},
        },
        "core": False,
    },
    "revision": {
        "fields": {
            "prior": {"type": "any", "required": False},
            "evidence": {"type": "ident", "required": False},
            "revised": {"type": "any", "required": False},
            "at": {"type": "number", "required": False},
            "cost": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "asymmetry": {
        "fields": {
            "a": {"type": "ident", "required": False},
            "b": {"type": "ident", "required": False},
            "dimension": {"type": "ident", "required": False},
            "degree": {"type": "number", "range": (0.0, 1.0), "required": False},
            "direction": {"type": "ident", "required": False},
            "cost": {"type": "number", "range": (0.0, 1.0), "required": False},
        },
        "core": False,
    },
    "steadfast": {
        "fields": {
            "state": {"type": "any", "required": False},
            "pressure": {"type": "ident", "required": False},
            "duration": {"type": "number", "required": False},
            "cost": {"type": "number", "range": (0.0, 1.0), "required": False},
            "until": {"type": "number", "required": False},
        },
        "core": False,
    },
}

REGISTRY = {}
REGISTRY.update(CORE_ATOMS)
REGISTRY.update(EXTENSION_ATOMS)
REGISTRY.update(V03_ATOMS)


def is_core(name):
    return name in CORE_ATOMS


def lookup(name):
    return REGISTRY.get(name)
