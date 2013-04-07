
def _logscalegen(points, minn, maxn):
    mul = (maxn/minn) ** (1.0/(points-1))
    x = minn
    for i in range(points):
        yield x
        x *= mul

def log(minn=0.001, maxn=100, points=200):
    if minn == maxn:
        return [minn]
    if maxn < minn:
        minn, maxn = maxn, minn
        reverse = True
    else:
        reverse = False
    if minn == 0:
        minn = 0.01
    if maxn == 0:
        maxn = -0.01
    if minn*maxn < 0:
        ret = (list(_logscalegen(points/2, minn, -0.01)) +
            list(_logscalegen(points/2, 0.01, maxn)))
    else:
        ret = list(_logscalegen(points, minn, maxn))
    if reverse:
        ret.reverse()
    return ret

def lin(minn, maxn, points=200, step=None):
    if step is None:
        step = (maxn - minn) / points
    else:
        points = (maxn - minn) / step

    for i in range(points):
        yield minn
        minn += step
    yield maxn

