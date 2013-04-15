# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import math
import cmath

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Gdk
import cairo

import ranges
from transform import z_to_gamma, gamma_to_z, gamma_to_swr
from solution import Solution

# Drawing functions
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

class SmithWidget(Gtk.DrawingArea):
    def __init__(self):
        Gtk.DrawingArea.__init__(self)
        self.connect("draw", self._draw)
        self.connect("configure_event", self._configure_event)
        self.connect("motion_notify_event", self._motion_event)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK)
        self.set_can_default(True)
        self.set_can_focus(True)
        self.solution = Solution()
        self.solution.connect("changed", self._solution_changed)
        self.load = None
        self.wload = None
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

    def _draw_chart(self, c):
        """Draw a smith chart on a cairo.Context"""
        style = self.get_style_context()
        # Draw pale admittance grid by scaling and translating
        c.save()
        c.scale(-1, -1)
        color = self.get_style().mid[self.get_state()]
        c.set_source_rgb(color.red, color.green, color.blue)
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

    def _configure_event(self, w, event):
        self._width = event.width
        self._height = event.height
        self._radius = min(self._width, self._height)/2 - 10

    def cairo_to_gamma(self, cr):
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        r = min(w, h)/2 - 10;
        cr.translate(w/2, h/2)
        cr.scale(r, -r)
        cr.set_line_width(0.005)

    def _draw(self, w, cr):
        self.cairo_to_gamma(cr)
        self._draw_chart(cr)
        self._paint_solution(cr)

    def _motion_event(self, w, event):
        gamma = self.xy_to_gamma(event.x, event.y)
        z = gamma_to_z(gamma)
        if self.load is not None and self.component is not None:
            z = self.component.contraint(self.wload, z)
            gamma = z_to_gamma(z)

        y = 1/z
        text = "Z = %.1f%+.1fj; Y = %.1f%+.1fj\n" % (z.real, z.imag, y.real, y.imag)
        text += "\u0393 = %.1f%+.1fj\n" % (gamma.real, gamma.imag)
        text += "SWR = %.1f\n" % gamma_to_swr(gamma)
        try:
            rl = "%.1f" % (-20*math.log10(abs(gamma)))
        except ValueError:
            rl = "\u221e"
        text += "S<sub>11</sub> = -%s dB" % rl
        return
        layout = pango.Layout(self.get_pango_context())
        layout.set_markup(text)
        w, h = layout.get_pixel_size();
        w += 20
        self._pixmap.draw_drawable(self.style.white_gc,self._chart,
                                  10, 10, 10, 10, w, h)
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
            for p in self.component.range(self.wload, z):
                gamma = z_to_gamma(p)
                cr.line_to(gamma.real, gamma.imag)
            cr.stroke()

    def set_load(self, z):
        self.load = z
        if z is None:
            self.wload = None
        else:
            self.wload = self.solution.apply(self.load, self.component)
        self.queue_draw()

    def _paint_solution(self, cr):
        if self.load is None:
            return
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.set_line_width(0.01)
        cr.new_path()
        l = self.load
        gamma = z_to_gamma(self.load)
        cr.arc(gamma.real, gamma.imag, 0.005, 0, 2*math.pi)
        cr.move_to(gamma.real, gamma.imag)
        for comp in self.solution:
            z = comp.apply(l)
            if comp != self.component:
                for p in comp.range(l, z):
                    gamma = z_to_gamma(p)
                    cr.line_to(gamma.real, gamma.imag)
            l = z
        cr.stroke()

        # Paint working component in transparent red
        if self.component is not None:
            cr.save()
            cr.set_source_rgba(1, 0, 0, 0.5)
            cr.new_path()
            z = self.component.apply(self.wload)
            for p in self.component.range(self.wload, z):
                gamma = z_to_gamma(p)
                cr.line_to(gamma.real, gamma.imag)
            cr.stroke()
            cr.restore()

    def _solution_changed(self, solution, index):
        if self.load is None:
            return
        self.wload = self.solution.apply(self.load, self.component)
        self.queue_draw()

GObject.type_register(SmithWidget)

