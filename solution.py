import gobject

import components

class Solution(gobject.GObject):
    __gsignals__ = {
            'changed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (int,))
        }

    def __init__(self):
        gobject.GObject.__init__(self)
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

    def apply(self, load):
        for c in self._components:
            load = c.apply(load)
        return load

    def _component_changed(self, component, paramstring, index):
        self.emit('changed', index)

    def __iter__(self):
        return self._components.__iter__()

    def __getitem__(self, item):
        return self._components[item]

gobject.type_register(Solution)

