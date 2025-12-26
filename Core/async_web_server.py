import uasyncio as asyncio
import network
import socket
import json
from typing import Optional
import time
from patch import Patch
from bank_manager import BankManager
from file import Html, Json

UDP_PORT = 5005


class AsyncWebServer:
    def __init__(self, config_file="network_config.json"):
        config = Json(config_file).data
        self.access_point = config.get("access_point", False)

        self.webPage = WebPage()
        self.bankManager = BankManager()
        self.current_patch: Optional[Patch] = self.bankManager.get_active_patch()
        self.sse_clients = set()

        # ---------- Network ----------
        if self.access_point:
            self.ap = self.access_point_setup(config)
            self.ip = self.ap.ifconfig()[0]
        else:
            self.wlan = self.connect(config)
            self.ip = self.wlan.ifconfig()[0]

        print("Network ready, IP:", self.ip)

        # ---------- UDP ----------
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.bind(("0.0.0.0", UDP_PORT))
        self.udp_sock.setblocking(False)
        print("UDP listening on", UDP_PORT)

    # =====================================================
    # NETWORK
    # =====================================================

    def connect(self, cfg):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        if cfg.get("ip"):
            wlan.ifconfig((
                cfg["ip"],
                cfg["subnet"],
                cfg["gateway"],
                cfg["dns"]
            ))

        wlan.connect(cfg["ssid"], cfg["password"])
        while not wlan.isconnected():
            pass

        print("Connected:", wlan.ifconfig())
        return wlan

    # def access_point_setup(self, cfg):
    #     ap = network.WLAN(network.AP_IF)
    #     ap.active(True)
    #     ap.config(
    #         essid=cfg.get("ap_ssid", "PicoServer"),
    #         password=cfg.get("ap_password", "12345678")
    #     )
    #     return ap
    def access_point_setup(self, cfg):

        network.country("GB")  # VERY IMPORTANT (use your country)

        ap = network.WLAN(network.AP_IF)
        ap.active(True)

        params = {
            "essid": cfg.get("ap_ssid", "PicoServer"),
            "password": cfg.get("ap_password", "12345678"),
            "authmode": getattr(network, "AUTH_WPA2_PSK", 3),  # fallback if stub missing
            "channel": 6,
        }

        # Try to set all params; if the port rejects unknown keys, retry with only
        # supported keys or set keys individually and ignore unsupported ones.
        try:
            ap.config(**params)
        except ValueError as e:
            print("ap.config rejected some params, retrying with supported keys:", e)
            try:
                supported = ap.config()
                if isinstance(supported, dict):
                    allowed = {k: v for k, v in params.items() if k in supported}
                    ap.config(**allowed)
                else:
                    # Some ports return non-dict or don't support ap.config() without args;
                    # fall back to setting keys individually and ignore failures.
                    for k, v in params.items():
                        try:
                            ap.config(**{k: v})
                        except Exception:
                            pass
            except Exception:
                for k, v in params.items():
                    try:
                        ap.config(**{k: v})
                    except Exception:
                        pass

        # Wait until AP is fully active
        timeout = 10
        while not ap.active() and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not ap.active():
            raise RuntimeError("AP failed to start")

        print("AP ready:", ap.ifconfig())
        return ap

    # =====================================================
    # UDP LISTENER (BINARY)
    # =====================================================

    async def udp_listener(self):
        while True:
            try:
                data, _ = self.udp_sock.recvfrom(8)
                self.handle_udp_packet(data)
            except OSError:
                await asyncio.sleep_ms(5)

    def handle_udp_packet(self, data: bytes):
        if len(data) < 1:
            return

        cmd = data[0]

        if cmd == 0x01:
            print("UDP: BANK UP")
            self.bankManager.move_up_bank()
            self.current_patch = self.bankManager.get_active_patch()

        elif cmd == 0x02:
            print("UDP: BANK DOWN")
            self.bankManager.move_down_bank()
            self.current_patch = self.bankManager.get_active_patch()

        elif cmd == 0x03 and len(data) >= 2:
            patch_idx = data[1]
            print("UDP: PATCH", patch_idx)
            self.current_patch = self.bankManager.select_patch(patch_idx)

    # =====================================================
    # SSE BROADCAST (TEXT ONLY)
    # =====================================================

    async def broadcast(self):
        while True:
            if not self.sse_clients:
                await asyncio.sleep(0.5)
                continue

            patch = self.current_patch

            payload = {
                "bank": self.bankManager.get_active_bank_name(),
                "patch": self.bankManager.get_active_patch_name(),
                "midi_data": patch.get_midi_list_html() if patch else "",
                "classes": {}
            }

            loops = patch.get_loops() if patch else []
            switches = patch.footSwitch.get_footswitch() if patch else []

            for i, loop in enumerate(loops, 1):
                payload["classes"][f"loop{i}_status"] = loop.get_css_class()

            for i, sw in enumerate(switches, 1):
                payload["classes"][f"switch{i}_status"] = sw.get_css_class()

            msg = f"data: {json.dumps(payload)}\n\n"

            dead = set()
            for client in list(self.sse_clients):
                try:
                    await client.awrite(msg)
                except Exception:
                    dead.add(client)

            self.sse_clients -= dead
            await asyncio.sleep(0.5)

    # =====================================================
    # HTTP SERVER
    # =====================================================

    async def serve_client(self, reader, writer):
        try:
            request = await reader.readline()
            if not request:
                await writer.aclose()
                return

            method, path, *_ = request.decode().split()

            headers = {}
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b""):
                    break
                k, v = line.decode().split(":", 1)
                headers[k.lower()] = v.strip()

            # ---------- SSE ----------
            if method == "GET" and path == "/events":
                await writer.awrite(
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/event-stream\r\n"
                    "Cache-Control: no-cache\r\n"
                    "Connection: keep-alive\r\n\r\n"
                )
                self.sse_clients.add(writer)
                return

            # ---------- POST ----------
            if method == "POST":
                length = int(headers.get("content-length", 0))
                body = await reader.read(length)
                data = body.decode()
                print(f"POST received: {data}")

                # Parse application/x-www-form-urlencoded
                for pair in data.split("&"):
                    pair = pair.strip()
                    if pair:
                        print(f"Processing: {pair}")
                        self.current_patch = self.switch(pair)

                await writer.awrite(
                    "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
                )
                await writer.aclose()
                return

            # ---------- HTML ----------
            html = self.webPage.render(
                self.bankManager.get_html_context(self.current_patch)
            )

            await writer.awrite(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html\r\n"
                f"Content-Length: {len(html)}\r\n\r\n{html}"
            )
            await writer.aclose()

        except Exception as e:
            print("HTTP error:", e)
            try:
                await writer.aclose()
            except:
                pass

    # =====================================================
    # SWITCH FROM HTTP
    # =====================================================

    def switch(self, cmd: str):
        if cmd == "bank=up":
            self.bankManager.move_up_bank()
        elif cmd == "bank=down":
            self.bankManager.move_down_bank()
        elif cmd.startswith("patch="):
            idx = int(cmd.split("=")[1]) - 1
            print(f"Selecting patch {idx}")
            return self.bankManager.select_patch(idx)

        return self.bankManager.get_active_patch()

    # =====================================================
    # RUN
    # =====================================================

    async def run(self):
        await asyncio.start_server(self.serve_client, "0.0.0.0", 80)
        asyncio.create_task(self.broadcast())
        asyncio.create_task(self.udp_listener())

        while True:
            await asyncio.sleep(3600)


class WebPage:
    def __init__(self):
        self.html = Html("index.html").data

    def render(self, context):
        page = self.html
        for k, v in context.items():
            page = page.replace(f"{{{{ {k} }}}}", str(v))
        return page
