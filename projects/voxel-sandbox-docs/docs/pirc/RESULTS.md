# PIRC crew experiment — results log

## Round 1 — design (whole system, 4 sections)
Verdict: unusable. Invented "port 0", told the Pi to install pip3 (no internet),
returned the placeholder "<1000 lines of code>". See crew-pirc-round1.md.

## Round 2 — parse_line() (one 9-case function)
Verdict: 0/9 pass on first run. Real code was produced, with the right outline
(strip ':', split, uppercase, special-case PRIVMSG) and wrong edge handling:
- split(' ', 2) unpacking raises on any line with fewer than 3 tokens
  (NICK, JOIN, PING, and unknown 2-token lines all crash)
- PRIVMSG re-splits the target, so it raises on "PRIVMSG #ops :..."
- default fields are 'UNKNOWN' instead of ''
- keeps the body's leading ':' in text
Caveat (fair to the crew): the original prompt did not say to strip the ':' from
the PRIVMSG body. The harness expected it, and the fix prompt stated it.

## Round 3 — fix from failure output
Verdict: no correction. The model returned the identical logic, unchanged,
with print() test calls appended. It did not act on the 9 failures.
Conclusion: the crew can draft small functions from a spec, but cannot
self-correct from test output. Fixes have to come from the operator or a
tool-using loop.
