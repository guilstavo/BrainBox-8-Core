from machine import Pin
from typing import List, Optional
from file import Json

class Pedal:
    id: int
    name: str

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

        print('Init Pedal', name)

class Loop:
    pedal: Pedal
    active: bool = False
    order: int

    def __init__(self, pedal: Pedal, order: int, active: bool = False):
        self.pedal = pedal
        self.order = order
        self.active = active

        print('Init Loop', pedal.name)
    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False
        print(f'Loop {self.pedal.name} deactivated')

    def get_css_class(self) -> str:
        return "enabled" if self.active else "disabled"
    
