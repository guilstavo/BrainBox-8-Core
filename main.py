from async_web_server import AsyncWebServer
import uasyncio as asyncio

server = AsyncWebServer("network_config.json")
asyncio.run(server.run())