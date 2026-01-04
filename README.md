# BrainBox8 Communication Modes

The BrainBox8 system supports two communication modes: **WiFi** and **BLE** (Bluetooth Low Energy).

## Configuration

### Core (BrainBox8 Main Unit)

Edit `network_config.json` and set the `communication_mode` field:

```json
{
    "communication_mode": "wifi",  // Options: "wifi", "ble", or "both"
    "access_point": true,
    ...
}
```

### FootProxy (Foot Controller)

Edit `network_config.json` and set the `communication_mode` field:

```json
{
    "communication_mode": "wifi",  // Options: "wifi", "ble", or "both"
    ...
}
```

**Important:** Both devices must use compatible communication modes!

## Both WiFi and BLE Mode

**Advantages:**
- Maximum flexibility - FootProxy can use either connection method
- Redundancy - if one fails, the other still works
- Can control from both WiFi and BLE devices simultaneously

**Setup:**
1. Set `"communication_mode": "both"` in Core's network_config.json
2. FootProxy can use either "wifi" or "ble" mode
3. Both UDP and BLE listeners will be active on Core
4. Commands from either source are processed identically

**Use Cases:**
- Development/testing with multiple controllers
- Fallback connectivity
- Mixed environment (some controllers WiFi, some BLE)

## WiFi Mode

**Advantages:**
- Longer range (~50-100m)
- Lower latency
- Can use web interface simultaneously

**Setup:**
1. Set `"communication_mode": "wifi"` in both configs
2. Core creates WiFi access point "BrainBox8_CoreAP"
3. FootProxy connects to the access point
4. Commands sent via UDP packets

**Configuration (Core - network_config.json):**
```json
{
    "communication_mode": "wifi",
    "access_point": true,
    "ap_ssid": "BrainBox8_CoreAP",
    "ap_password": "abcd102030",
    ...
}
```

**Configuration (FootProxy - network_config.json):**
```json
{
    "communication_mode": "wifi",
    "ssid": "BrainBox8_CoreAP",
    "password": "abcd102030",
    "server_ip": "192.168.4.1",
    "server_port": 5005
}
```

## BLE Mode

**Advantages:**
- No WiFi network needed
- Lower power consumption
- Direct peer-to-peer connection
- More portable

**Disadvantages:**
- Shorter range (~10-30m)
- Slightly higher latency
- Web interface not available in BLE-only mode

**Setup:**
1. Set `"communication_mode": "ble"` in both configs
2. Core advertises as BLE peripheral "BrainBox8"
3. FootProxy scans and connects
4. Commands sent via BLE characteristic writes

**LED Behavior (FootProxy):**
- **Blinking**: Searching/connecting
- **Solid ON**: Connected successfully
- **OFF**: Disconnected or failed

## Command Protocol

Both modes use the same command byte protocol:

| Command | Byte 1 | Byte 2 | Description |
|---------|--------|--------|-------------|
| Bank Up | 0x01 | - | Move to next bank |
| Bank Down | 0x02 | - | Move to previous bank |
| Select Patch | 0x03 | 0-7 | Select patch (0-7) |

## Files

- `network_config.json` - Communication mode and WiFi settingsth communication_mode
- `network_config.json` - WiFi settings
- `async_web_server.py` - Main server with mode selection
- `ble_server.py` - BLE peripheral implementation

**FootProxy:**
- `network_config.json` - Communication mode and WiFi settings
- `main.py` - Main controller with mode selection
- `ble_client.py` - BLE central implementation

## Troubleshooting

**WiFi Mode:**
- Ensure FootProxy gets IP 192.168.4.x (not 10.x.x.x)
- Check Core shows "UDP listening on 5005"
- Check Core shows "UDP listener task started"

**BLE Mode:**
- Ensure both Picos have Bluetooth support (Pico W)
- FootProxy LED should turn solid when connected
- Check Core shows "BLE server started"
- Scan timeout is 10 seconds - Core must be running first

## Switching Modes

1. Change `communication_mode` in both config files
2. Reboot both devices
3. Wait for connection indicator (LED on FootProxy)
