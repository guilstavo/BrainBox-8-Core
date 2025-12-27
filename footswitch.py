from machine import Pin
from typing import List, Optional
from file import Json

# One EffectSwitch represents a single button from the footswitch
class EffectSwitch:
    ACTIVE_PIN_VALUE: int = 1
    INACTIVE_PIN_VALUE: int = 0

    name: str
    pin: Pin
    active: bool = False
    order: int
    
    def __init__(self, name: str, pin: int):
        
        self.name = name
        self.pin = Pin(pin, Pin.OUT)
        self.order = pin
        
        print('Init Effect Switch', name)

    def activate(self):
        self.active = True
        self.pin.value(self.ACTIVE_PIN_VALUE) 
    
        print(f'Loop {self.name} activated')

    def deactivate(self):
        self.active = False
        self.pin.value(self.INACTIVE_PIN_VALUE) 
        
        print(f'Loop {self.name} deactivated')

    def get_css_class(self) -> str:
        return "enabled" if self.active else "disabled"

class FootSwitch:
    
    def __init__(self, fileName: str = "config.json"):
        self.__footSwitch:List[EffectSwitch] = []

        file = Json(fileName)
       
        for switch_name, switch_pin in file.data.get("footswitch", {}).items():
            self.add_effectSwitch(
                name = switch_name,
                pin = switch_pin
            )

    def add_effectSwitch(self, name: str,  pin: int):
        switch = EffectSwitch(name=name, pin=pin)
        self.__footSwitch.append(switch)
        print(f'Added switch {name} with pin {pin}')

    def get_footswitch(self) -> List[EffectSwitch]:
        return sorted(self.__footSwitch, key=lambda x: x.order)