import socket
import uasyncio as asyncio

class UdpEngine:
    def __init__(self, rx_port=5005, tx_port=5006):
        self.rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx.bind(("0.0.0.0", rx_port))
        self.rx.setblocking(False)

        self.tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients = set()
        self.tx_port = tx_port

    def checksum(self, data):
        c = 0
        for b in data[:-1]:
            c ^= b
        return c

    async def listen(self, handler):
        while True:
            try:
                data, addr = self.rx.recvfrom(32)
                self.clients.add(addr)
                if data[-1] != self.checksum(data):
                    continue
                handler(data)
            except OSError:
                await asyncio.sleep_ms(5)

    async def broadcast(self, packet_fn, interval_ms=100):
        while True:
            pkt = packet_fn()
            for addr in tuple(self.clients):
                try:
                    self.tx.sendto(pkt, (addr[0], self.tx_port))
                except:
                    self.clients.discard(addr)
            await asyncio.sleep_ms(interval_ms)
