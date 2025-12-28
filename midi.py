from file import Json
from machine import UART, Pin

class Midi:
    
    uart: UART

    def __init__(self, fileName: str = "config.json"):

        file = Json(fileName)
       
        tx_pin = file.data.get("midiPin", 0)
        self.uart = UART(1, baudrate=31250, tx=Pin(tx_pin))

    def send_pc(self, channel, program):
        status = 0xC0 | ((channel - 1) & 0x0F)
        self.uart.write(bytes([status, program & 0x7F]))
        print(f'Sent MIDI Program Change - Channel: {channel}, Program: {program}')

class Midi_preset:

    channel: int
    program: int

    def __init__(self, channel: int, program: int):
        self.channel = channel
        self.program = program