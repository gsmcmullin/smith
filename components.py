import gobject
import math
import cmath
import ranges
from transform import z_to_gamma, gamma_to_z
import spicenum

class Component(gobject.GObject):
    __gproperties__ = {
        'normval' : (gobject.TYPE_DOUBLE, 'normalized value',
                     'normalized value',
                     -gobject.G_MAXDOUBLE, gobject.G_MAXDOUBLE, 1,
                     gobject.PARAM_READWRITE),
    }
    def __init__(self, normval = 1):
        gobject.GObject.__init__(self)
        self.normval = normval

    def do_get_property(self, property):
        if property.name == 'normval':
            return self.normval
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'normval':
            self.normval = value
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def contraint(self, load, target):
        raise NotImplementedError()

    def range(self, load, target):
        raise NotImplementedError()

gobject.type_register(Component)


class Reactance(Component):
    def contraint(self, load, target):
        self.set_property("normval", target.imag - load.imag)
        return complex(load.real, target.imag)

    def range(self, load, target):
	for x in ranges.log(load.imag, target.imag):
            yield complex(load.real, x)

    def apply(self, load):
        return load + complex(0, self.normval)

    def format_type(self):
        return "Series Capactitor" if self.normval < 0 else "Series Inductor"

    def format_physval(self, z0, freq):
        x = self.normval * z0
        if x < 0:
            return spicenum.format(-1/(2*math.pi*freq*x))+'F'
        else:
            return spicenum.format(x/(2*math.pi*freq))+'H'

class Susceptance(Component):
    def contraint(self, load, target):
	target = 1 / target
	load = 1 / load
        self.set_property("normval", target.imag - load.imag)
        return 1 / complex(load.real, target.imag)

    def range(self, load, target):
	target = 1 / target
	load = 1 / load
	for x in ranges.log(load.imag, target.imag):
            yield 1/complex(load.real, x)

    def apply(self, load):
        return 1/(1/load + complex(0, self.normval))

    def format_type(self):
        return "Shunt Inductor" if self.normval < 0 else "Shunt Capacitor"

    def format_physval(self, z0, freq):
        x = -z0 / self.normval
        if x < 0:
            return spicenum.format(-1/(2*math.pi*freq*x))+'F'
        else:
            return spicenum.format(x/(2*math.pi*freq))+'H'

class Resistance(Component):
    def contraint(self, load, target):
        if load.real > target.real:
            return load
        self.set_property("normval", target.real - load.real)
        return complex(target.real, load.imag)

    def range(self, load, target):
	for r in ranges.log(load.real, target.real):
            yield complex(r, load.imag)

    def apply(self, load):
        return load + self.normval

    def format_type(self):
        return "Series Resistor"

    def format_physval(self, z0, freq):
        return spicenum.format(self.normval * z0) + "ohm"

class Conductance(Component):
    def contraint(self, load, target):
	target = 1 / target
	load = 1 / load
        if load.real > target.real:
            return 1 / load
        self.set_property("normval", target.real - load.real)
        return 1/complex(target.real, load.imag)

    def range(self, load, target):
	target = 1 / target
	load = 1 / load
	for s in ranges.log(load.real, target.real):
            yield 1/complex(s, load.imag)

    def apply(self, load):
        return 1/(1/load + self.normval)

    def format_type(self):
        return "Shunt Resistor"

    def format_physval(self, z0, freq):
        return spicenum.format(z0 / self.normval) + "ohm"

class TLine(Component):
    def contraint(self, load, target):
        gl = z_to_gamma(load)
	gt = z_to_gamma(target)
        pl = cmath.phase(gl)
        pt = cmath.phase(gt)
        if pt > pl:
            pt -= 2 * math.pi
        self.set_property("normval", (pt - pl)/(-4*math.pi))
        return gamma_to_z(cmath.rect(abs(gl), cmath.phase(gt)))

    def range(self, load, target):
        gl = z_to_gamma(load)
	gt = z_to_gamma(target)

        pl = cmath.phase(gl)
        pt = cmath.phase(gt)
        if pt > pl:
            pt -= 2 * math.pi

        for phase in ranges.lin(pl, pt):
            yield gamma_to_z(cmath.rect(abs(gl), phase))

    def apply(self, load):
        rotate = cmath.rect(1, -4 * self.normval * math.pi)
        return gamma_to_z(z_to_gamma(load) * rotate)

    def format_type(self):
        return "Transmission Line"

    def format_physval(self, z0, freq):
        return "%.2fl" % self.normval

types = [Reactance, Susceptance, Resistance, Conductance, TLine]

