# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import math

def format(f, sigfigs=3, spice=True):
    # Format floats in engineering notation
    mult = {-15: 'f', -12: 'p', -9: 'n', -6: 'u', -3: 'm',
        0: '',
        3: 'k', 6: 'M', 9: 'G', 12: 'T'}
    if not spice:
            mult = {}

    if f < 0:
        sign = '-'
        f = -f
    else:
        sign = ''

    exp = 0
    if f != 0:
        f = round(f, sigfigs - int(math.log10(f)))
        while f < 1:
            exp -= 3
            f *= 1000
        while f >= 1000:
            exp += 3
            f /= 1000

    p = int(math.log10(f) if f > 0 else 0) + 1
    ff = round(f * (10 ** (sigfigs - p)))
    s = ''
    for i in range(sigfigs):
        s = str(int(ff) % 10) + s
        ff /= 10
        p += 1
        if p == sigfigs:
            s = '.' + s

    return sign + s + mult.get(exp, "e%02d" % exp)

def parse(s):
    #r'[-+]?((\d+[TtGgMKkmUuNnPpFf]\d*)|((\d+(\.\d*)?|\.\d+)[TtGgMKkmUuNnPpFf]))'
    mult = {'T':1e12, 't':1e12,
        'G':1e9, 'g':1e9,
        'M':1e6,
        'K':1e3, 'k':1e3,
        'm':1e-3,
        'U':1e-6, 'u': 1e-6,
        'N':1e-9, 'n': 1e-9,
        'P':1e-12, 'p': 1e-12,
        'F':1e-15, 'f': 1e-15,
    }
    if '.' in s:
        num = float(t.value[:-1])
        num *= mult[t.value[-1]]
    else:
        m = s.strip("0123456789")[0]
        i = s.find(m)
        s = s[:i] + '.' + s[i+1:]
        num = float(s)
        num *= mult[m]
    return num

