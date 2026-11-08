"""Contract test for the crew-written parse_line().

The crew was told: return exactly {cmd, target, text}; strip a leading ':';
uppercase cmd; PRIVMSG -> channel + body; NICK/JOIN/PING -> target, empty text;
empty/unrecognised -> {'cmd':'UNKNOWN','target':'','text':''}.

Run:  python3 test_parse_line.py pirc_parse.py
Exit code 0 only if every case passes.
"""
import importlib.util
import sys

CASES = [
    # (line, expected dict)
    (":vesh!u@h PRIVMSG #fleet :hello world",
     {"cmd": "PRIVMSG", "target": "#fleet", "text": "hello world"}),
    ("PRIVMSG #ops :no prefix here",
     {"cmd": "PRIVMSG", "target": "#ops", "text": "no prefix here"}),
    ("NICK vesh", {"cmd": "NICK", "target": "vesh", "text": ""}),
    ("JOIN #pirc", {"cmd": "JOIN", "target": "#pirc", "text": ""}),
    ("PING :abc123", {"cmd": "PING", "target": "abc123", "text": ""}),
    ("", {"cmd": "UNKNOWN", "target": "", "text": ""}),
    ("SOMETHING else", {"cmd": "UNKNOWN", "target": "", "text": ""}),
    ("PRIVMSG #a :", {"cmd": "PRIVMSG", "target": "#a", "text": ""}),
    ("privmsg #lower :shout", {"cmd": "PRIVMSG", "target": "#lower", "text": "shout"}),
]


def load(path):
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_line


def main():
    if len(sys.argv) != 2:
        print("usage: python3 test_parse_line.py <file-with-parse_line.py>")
        return 2
    fn = load(sys.argv[1])
    failed = 0
    for line, want in CASES:
        try:
            got = fn(line)
        except Exception as exc:  # noqa: BLE001 - report, do not crash the harness
            print(f"FAIL  {line!r}\n      raised {type(exc).__name__}: {exc}")
            failed += 1
            continue
        if got != want:
            print(f"FAIL  {line!r}\n      want {want}\n      got  {got}")
            failed += 1
        else:
            print(f"ok    {line!r}")
    print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
