# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
from gi.repository import GObject

import components

class Solution(GObject.GObject):
    __gsignals__ = {
            'changed' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (int,))
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self._components = []

    def push_component(self, component):
        index = len(self._components)
        self._components.append(component)
        component.connect("notify::normval", self._component_changed, index)
        self.emit('changed', index)

    def pop_component(self):
        index = len(self._components)
        comp = self._components.pop()
        comp.disconnect_by_func(self._component_changed)
        self.emit('changed', index)
        return comp

    def apply(self, load, comp = None):
        for c in self._components:
            if c == comp:
                return load
            load = c.apply(load)
        return load

    def _component_changed(self, component, paramstring, index):
        self.emit('changed', index)

    def __iter__(self):
        return self._components.__iter__()

    def __getitem__(self, item):
        return self._components[item]

GObject.type_register(Solution)

