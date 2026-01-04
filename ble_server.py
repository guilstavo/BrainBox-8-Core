import bluetooth
from micropython import const
import struct
import time

# BLE UUIDs
_SERVICE_UUID = bluetooth.UUID(0x1815)  # Custom service
_COMMAND_CHAR_UUID = bluetooth.UUID(0x2A56)  # Custom characteristic for commands

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)


class BLEServer:
    def __init__(self, name="BrainBox8", command_callback=None):
        self.name = name
        self.command_callback = command_callback
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)
        self.register_services()
        self.advertise()
        self.connected = False
        print(f"BLE Server '{name}' started")

    def register_services(self):
        # Define the command characteristic (writable)
        command_char = (
            _COMMAND_CHAR_UUID,
            _FLAG_WRITE | _FLAG_READ,
        )
        
        service = (
            _SERVICE_UUID,
            (command_char,),
        )
        
        ((self.command_handle,),) = self.ble.gatts_register_services((service,))
        print("BLE services registered")

    def advertise(self, interval_us=500000):
        # Advertise the service
        print(f"Starting BLE advertising...")
        print(f"  Device name: {self.name}")
        print(f"  Interval: {interval_us}us")
        
        payload = self._payload(self.name)
        print(f"  Advertising payload ({len(payload)} bytes): {payload.hex()}")
        
        self.ble.gap_advertise(
            interval_us,
            payload
        )
        print(f"BLE advertising as '{self.name}' - should be visible now!")

    def _payload(self, name):
        # Generate advertising payload
        payload = bytearray()
        
        # Flags
        payload.extend(struct.pack("BB", 2, 0x01))
        payload.append(0x06)  # General discoverable + BR/EDR not supported
        
        # Name
        name_bytes = name.encode()
        payload.extend(struct.pack("BB", len(name_bytes) + 1, 0x09))
        payload.extend(name_bytes)
        
        return bytes(payload)

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connected = True
            print(f"BLE client connected (handle: {conn_handle})")
            
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self.connected = False
            print(f"BLE client disconnected (handle: {conn_handle})")
            # Restart advertising
            self.advertise()
            
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self.command_handle:
                # Read the written value
                command_data = self.ble.gatts_read(self.command_handle)
                print(f"BLE received {len(command_data)} bytes: {command_data.hex()}")
                
                # Call the callback with the command data
                if self.command_callback:
                    self.command_callback(command_data)

    def is_connected(self):
        return self.connected
