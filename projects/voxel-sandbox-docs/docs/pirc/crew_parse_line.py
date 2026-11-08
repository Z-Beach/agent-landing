import re

def parse_line(line):
    cmd, target, text = 'UNKNOWN', 'UNKNOWN', 'UNKNOWN'
    if line:
        line = line.strip()
        line = line[1:] if line.startswith(':') else line
        cmd, target, text = line.split(' ', 2)
        cmd = cmd.upper()
        if cmd == 'PRIVMSG':
            target, text = target.split(' ', 1)
    return {'cmd': cmd, 'target': target, 'text': text}
