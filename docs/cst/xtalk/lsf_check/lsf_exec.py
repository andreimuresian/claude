"""Execute the simple LSF subset used by the scripted elements, in numpy. Test-only."""
import re, numpy as np
def translate(src):
    out, ind = [], 0
    for raw in src.splitlines():
        s = raw.split('#')[0].strip()
        if not s: continue
        s = s.replace('1i', '1j').rstrip(';').strip()
        closes = s.startswith('}')
        if closes:
            ind -= 1; s = s[1:].strip()
            if not s: continue
        m = re.match(r'(if|for)\s*\((.*)\)\s*\{(.*)\}$', s)   # one-line block
        if m:
            kw, cond, body = m.groups()
            out.append('    '*ind + hdr(kw, cond)); out.append('    '*(ind+1) + stmt(body.strip().rstrip(';'))); continue
        m = re.match(r'(if|for)\s*\((.*)\)\s*\{$', s)
        if m:
            out.append('    '*ind + hdr(*m.groups())); ind += 1; continue
        out.append('    '*ind + stmt(s))
    return '\n'.join(out)
def hdr(kw, cond):
    if kw == 'for':
        v, rng = cond.split('='); a, b = rng.split(':')
        return f'for {v.strip()} in range({a}, ({b})+1):'
    cond = stmt(cond)
    return 'if ' + cond + ':'
def stmt(s):
    if s == 'break': return 'raise SystemExit(LOG)'
    s = re.sub(r'(\w+)\(:, (\d+)\)', lambda m: f'{m.group(1)}[:, {int(m.group(2))-1}]', s)
    s = re.sub(r'(\w+)\((\d+)\)', lambda m: m.group(0) if m.group(1) in FUN else f'{m.group(1)}[{int(m.group(2))-1}]', s)
    s = re.sub(r'\[(\w+)\[0\]; (\w+)\]', r'np.r_[\1[0], \2]', s)
    s = s.replace('fr(nf)', 'fr[nf-1]')
    s = s.replace('[0; fr]', 'np.r_[0.0, fr]').replace('max([', 'max_([')
    return s
FUN = {'abs','exp','sqrt','log','angle','unwrap','length','matrix','max','fileexists','readdata','num2str','logmessage','setfir','read'}
def run(path, props, readdata):
    S = {}
    LOG = []
    def setsp(o, i, kind, T): S[(o, i)] = T[:, 1] * np.exp(1j * T[:, 2])
    env = dict(np=np, abs=np.abs, exp=np.exp, sqrt=np.sqrt, log=np.log, angle=np.angle,
               unwrap=np.unwrap, pi=np.pi, length=lambda x: len(x), matrix=lambda a, b: np.zeros((a, b)),
               max=np.max, max_=lambda l: max(l), fileexists=lambda p: 1, readdata=readdata,
               num2str=str, logmessage=LOG.append, setfir=lambda *a: None, setsparameter=setsp, LOG=LOG)
    env.update(props)
    code = translate(open(path).read())
    exec(code, env)
    return S, LOG, code
