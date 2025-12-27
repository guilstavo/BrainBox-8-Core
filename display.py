from machine import Pin, SoftI2C
from lib_lcd1602_2004_with_i2c import LCD
from typing import Optional

class Display:

    off_loop: str
    on_loop: str
    lcd: Optional[LCD]
    
    def __init__(self, sclPin: int = 1, sdaPin: int = 0):
        try:
            self.lcd = LCD(SoftI2C(scl=Pin(sclPin), sda=Pin(sdaPin), freq=100000))

            off_pedal_char = [
            0b11111,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b11111]

            on_pedal_char = [
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111]

            off_switch_char = [
            0b00000,
            0b01110,
            0b10001,
            0b10001,
            0b10001,
            0b10001,
            0b01110,
            0b00000]

            on_switch_char = [
            0b00000,
            0b01110,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b01110,
            0b00000]

            self.lcd.create_charactor(0,off_pedal_char)
            self.lcd.create_charactor(1,on_pedal_char)
            self.lcd.create_charactor(2,off_switch_char)
            self.lcd.create_charactor(3,on_switch_char)

            print('Init Display')
        
        except:
            self.lcd = None
            print('Display not available')
        
        self.off_loop = chr(0)
        self.on_loop = chr(1)
        self.off_switch = chr(2)
        self.on_switch = chr(3)

    def print(self, line1: str = "", line2: str = "", line3: str = "", switch_values: str = "", midi_value: int = 0, switch_letters: str = ""):

        midi = "MIDI" + "{:02}".format(int(midi_value))
        
        print('Display Print: ', line1, line2, line3, switch_values, midi)
        
        if self.lcd is None:
            return
        
        self.lcd.puts(line1, 0, 0)
        self.lcd.puts(line2, 1, 0)
        
        self.lcd.puts(line3, 2, 0)
        self.lcd.puts(switch_letters, 2, 16)

        self.lcd.puts(midi, 3, 0)
        self.lcd.puts(switch_values, 3, 16)

