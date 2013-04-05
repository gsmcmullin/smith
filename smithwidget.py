import gtk
import pango
import math
import cmath

import ranges
from transform import z_to_gamma, gamma_to_z, gamma_to_swr

# Drawing functions
def cairo_for_drawable(drawable):
    """Create cairo context and transform to gamma units."""
    cr = drawable.cairo_create()
    w, h = drawable.get_size()
    r = min(w, h)/2 - 10;
    cr.translate(w/2, h/2)
    cr.scale(r, -r)
    cr.set_line_width(0.005)
    return cr

def line_const_r(cr, r, x1, x2):
    gamma = z_to_gamma(complex(r, x1))
    cr.move_to(gamma.real, gamma.imag)
    for j in ranges.log(x1, x2):
		gamma = z_to_gamma(complex(r, j))
		cr.line_to(gamma.real, gamma.imag)

def line_const_x(cr, x, r1, r2):
    gamma = z_to_gamma(complex(r1, x))
    cr.move_to(gamma.real, gamma.imag)
    for j in ranges.log(r1, r2):
		gamma = z_to_gamma(complex(j, x))
		cr.line_to(gamma.real, gamma.imag)

def draw_chart_lines(cr):
    cr.new_path()
    # constant resistance
    for i in [0.2, 0.5, 1, 2, 5]:
        line_const_r(cr, i, -200, 200)
    # constant reactance
    for i in [-5, -2, -1, -0.5, -0.2, 0, 0.2, 0.5, 1, 2, 5]:
        line_const_x(cr, i, 0, 200)
    cr.stroke()

class SmithWidget(gtk.DrawingArea):
    def __init__(self):
        self.__gobject_init__()
        gtk.DrawingArea.__init__(self)
	self.connect("configure_event", self._configure_event)
	self.connect("expose_event", self._expose_event)
	self.connect("motion_notify_event", self._motion_event)
	self.add_events(gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.KEY_PRESS_MASK)
        self.set_flags(gtk.CAN_DEFAULT)
        self.set_can_focus(True)
	self.load = None
	self.component = None

    def gamma_to_xy(self, gamma):
        x = gamma.real * self._radius + self._width/2
        y = -gamma.imag * self._radius + self._height/2
        return x, y

    def xy_to_gamma(self, x, y):
	gamma = (x - self._width / 2.0) / self._radius
	gamma += 1.0j * (self._height / 2.0 - y) / self._radius
        if abs(gamma) > 0.99:
            gamma = cmath.rect(0.99, cmath.phase(gamma))
	return gamma


    def _draw_chart(self, drawable):
	"""Draw a smith chart on a gdk.Drawable"""
	c = cairo_for_drawable(self._chart)
        c.save()
	c.set_source_color(self.style.bg[self.state])
	c.paint()
	c.set_source_color(self.style.fg[self.state])
	c.set_line_width(0.005)

	# Draw pale admittance grid by scaling and translating
	c.save()
	c.scale(-1, -1)
	c.set_source_color(self.style.mid[self.state])
	draw_chart_lines(c)
	c.restore()

	# Draw impedance grid
	draw_chart_lines(c)

	# Draw chart outline and hard zero reactance line
	c.new_path()
        c.move_to(-1, 0)
        c.line_to(1, 0)
	c.stroke()

	c.set_line_width(0.01)
	c.new_path()
        c.arc(0, 0, 1, 0, 2*math.pi)
	c.stroke()
        c.restore()

    def _configure_event(self, w, event):
        self._width = event.width
        self._height = event.height
	self._radius = min(self._width, self._height)/2 - 10

        self._chart = gtk.gdk.Pixmap(self.window,
                              self._width, self._height, -1)
	self._draw_chart(self._chart)
        self._pixmap = gtk.gdk.Pixmap(self.window,
                              self._width, self._height, -1)
        self._cairo = self._pixmap.cairo_create()
	self._pixmap.draw_drawable(self.style.white_gc,self._chart,
			0, 0, 0, 0, self._width, self._height)

    def _expose_event(self, w, event):
	self.window.draw_drawable(self.style.white_gc, self._pixmap,
                    event.area.x, event.area.y,
                    event.area.x, event.area.y,
                    event.area.width, event.area.height)

    def _motion_event(self, w, event):
	gamma = self.xy_to_gamma(event.x, event.y)
	z = gamma_to_z(gamma)
        if self.load is not None and self.component is not None:
            z = self.component.contraint(self.load, z)
            gamma = z_to_gamma(z)

	text = u"\u0393 = %.1f%+.1fj\n" % (gamma.real, gamma.imag)
	text += "SWR = %.1f\n" % gamma_to_swr(gamma)
	text += "Z = %.1f%+.1fj\n" % (z.real, z.imag)
        try:
	    rl = "%.1f" % (-20*math.log10(abs(gamma)))
        except ValueError:
            rl = u"\u221e"
	text += "Rtn loss %s dB" % rl
	layout = pango.Layout(self.get_pango_context())
	layout.set_text(text)
	w, h = layout.get_pixel_size();
	self._cairo.set_source_color(self.style.bg[self.state])
	self._cairo.rectangle(10, 10, w, h)
	self._cairo.fill()
	self._cairo.set_source_color(self.style.text[self.state])
	self._cairo.move_to(10, 10)
	self._cairo.show_layout(layout)
	self.queue_draw_area(10, 10, w, h)

        if self.load is not None and self.component is not None:
            self.window.draw_drawable(self.style.white_gc,self._pixmap,
	    			0, 0, 0, 0, self._width, self._height)
            cr = cairo_for_drawable(self.window)
            cr.set_source_rgb(1, 0, 0)
            cr.set_line_width(0.005)
            cr.new_path()
            for p in self.component.range(self.load, z):
		gamma = z_to_gamma(p)
                cr.line_to(gamma.real, gamma.imag)
            cr.stroke()

    def set_load(self, z):
        self.load = z
        if z is None:
            return
        self._cairo.set_line_width(2)
	self._cairo.new_path()
	x, y = self.gamma_to_xy(z_to_gamma(self.load))
	self._cairo.arc(x, y, 2, 0, 2*math.pi)
	self._cairo.stroke()
	self.queue_draw()

    # FIXME: This must go and be replaced with a solution class...
    def commit_component(self):
        z = self.component.apply(self.load)
        cr = cairo_for_drawable(self._pixmap)
        cr.set_line_width(0.01)
        cr.new_path()
        for p in self.component.range(self.load, z):
	    gamma = z_to_gamma(p)
            cr.line_to(gamma.real, gamma.imag)
        cr.stroke()
        self.set_load(z)

